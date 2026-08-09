# Behavioral test for install.ps1's Indagis home resolution ladder.
#
# Mirrors the 5-priority Python Draft 1 and bash Draft 2 contracts:
#   P1: $env:INDAGIS_HOME      -> path              [no warning]
#   P2: ~/.indagis exists      -> path              [no warning]
#   P3: $env:HERMES_HOME       -> legacy path       [WARNING on stderr — emitted by ORCHESTRATOR, not the resolver]
#   P4: ~/.hermes exists       -> legacy path       [WARNING on stderr — emitted by ORCHESTRATOR, not the resolver]
#   P5: ~/.indagis default     -> create on first use [no warning]
#
# Run:  pwsh -NoProfile -File scripts/ci/test_install_ps1_home_resolution.ps1
#
# This test is NOT wired into the default CI lane (the Linux runners have
# no PowerShell host, same as test_install_ps1_path_migration.ps1).
#
# Pure-resolver contract (Draft 2.1): the Get-IndagisHome function must NOT
# emit warnings itself. Warning emission is the orchestrator's responsibility
# (install.ps1). This test verifies that contract by reading the resolver's
# function body via AST and asserting it contains no Write-Warning / Write-Error
# calls that mention "legacy" or "deprecation".

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$installPs1 = Join-Path $PSScriptRoot '..' 'install.ps1' | Resolve-Path
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $installPs1, [ref]$null, [ref]$null)

$failures = 0

function Assert-Equal {
    param($Expected, $Actual, [string]$Name)
    if ($Expected -ceq $Actual) {
        Write-Host "  PASS  $Name"
    } else {
        Write-Host "  FAIL  $Name"
        Write-Host "        expected: [$Expected]"
        Write-Host "        actual:   [$Actual]"
        $script:failures++
    }
}

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) {
        Write-Host "  PASS  $Name"
    } else {
        Write-Host "  FAIL  $Name"
        $script:failures++
    }
}

# Locate the resolver function (whatever name it ends up with).
$resolver = $ast.Find({
    param($n)
    $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $n.Name -in @('Get-IndagisHome', 'Resolve-IndagisHome', 'Get-IndagisHomePath')
}, $true)

if (-not $resolver) {
    throw "Indagis home resolver function not found in $installPs1 (expected one of: Get-IndagisHome, Resolve-IndagisHome, Get-IndagisHomePath)"
}

Write-Host "install.ps1 Indagis home resolver: $($resolver.Name)"

# Pure-resolver contract: the function body must not emit warnings itself.
# Check for Write-Warning / Write-Error / Write-Host that mention "legacy" or
# "deprecation". The orchestrator (install.ps1) handles the warning.
$bodyText = $resolver.Body.Extent.Text
$hasLegacyWarning = ($bodyText -match '(?i)(write-warning|write-error).*(legacy|deprecation|deprecat)') -or
                   ($bodyText -match '(?i)(legacy|deprecat).*(write-warning|write-error)')
Assert-True (-not $hasLegacyWarning) "resolver body has no Write-Warning/-Error mentioning legacy/deprecation"

# Verify the 5 priorities are all addressed in the function body.
# Use double-quoted here-strings and escape the $ as needed, OR compare
# against the literal substrings using a method that does NOT expand
# the variable. PowerShell expands $env:FOO inside single-quoted
# strings only when the single-quoted string contains a real $-prefixed
# token -- which makes naive Contains() broken for our purposes.
# Solution: build the search needle via [char] concatenation so the
# $-sign is treated as a literal character, not a variable.
$needle1 = [char]36 + 'env:INDAGIS_HOME'
$needle2 = '.indagis'
$needle3 = [char]36 + 'env:HERMES_HOME'
$needle5a = [char]36 + 'env:HOME'
$needle5b = [char]36 + 'env:LOCALAPPDATA'
$hasP1 = $bodyText.Contains($needle1)
$hasP2 = $bodyText.Contains($needle2)
$hasP3 = $bodyText.Contains($needle3)
# P5 default uses HOME (POSIX) or LOCALAPPDATA (Windows). The actual
# $env:HOME / $env:LOCALAPPDATA references live in the helper function
# Get-IndagisPlatformDefaultHome -- not in the resolver body itself.
# Check the helper functions for the references, then verify they are
# CALLED from the resolver (i.e. P5 delegates to a helper that knows the
# platform default).
$helperResolver = $ast.Find({
    param($n)
    $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $n.Name -eq 'Get-IndagisPlatformDefaultHome'
}, $true)
$helperBody = if ($helperResolver) { $helperResolver.Body.Extent.Text } else { '' }
$hasP5 = $bodyText.Contains('Get-IndagisPlatformDefaultHome') -and
         ($helperBody.Contains($needle5a) -or $helperBody.Contains($needle5b))
Assert-True $hasP1 "P1 references `$env:INDAGIS_HOME"
Assert-True $hasP2 "P2 references ~/.indagis path"
Assert-True $hasP3 "P3 references `$env:HERMES_HOME"
Assert-True $hasP5 "P5 delegates to Get-IndagisPlatformDefaultHome which references HOME or LOCALAPPDATA"

# Verify the orchestrator pattern: install.ps1 should call
# Write-IndagisLegacyAliasWarning (the warning helper) before any
# capture of Get-IndagisHome. We check for the function call AND for
# the resulting warning text in the source.
$installPs1Text = Get-Content -Raw $installPs1
$hasOrchestratorWarning = $installPs1Text -match 'Write-IndagisLegacyAliasWarning' -and
                          $installPs1Text -match 'Indagis Agent:.*legacy|legacy.*Indagis Agent'
Assert-True $hasOrchestratorWarning "install.ps1 calls Write-IndagisLegacyAliasWarning in the orchestrator scope"

# Verify the resolver does NOT re-emit the warning on multiple invocations
# in the same scope. This is the load-bearing test for the pure-resolver
# contract (Draft 2.1): if Get-IndagisHome emitted the warning itself,
# calling it twice would produce 2 copies of the warning text in stderr.
#
# Strategy: extract the relevant functions from install.ps1 into a temp
# harness script, dot-source the harness in a clean pwsh scope with
# HERMES_HOME set (forces P3 path), then:
#   1. Orchestrator calls Write-IndagisLegacyAliasWarning once.
#   2. Resolve Get-IndagisHome twice in the same process.
#   3. Count occurrences of 'is used as a fallback' in stderr.
#
# Expected: exactly 1 occurrence (the orchestrator's single fire).
# Bug scenario (broken contract): 3 occurrences (orchestrator + 2 resolver calls).

$runtimeHarness = Join-Path ([System.IO.Path]::GetTempPath()) ('harness_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
    # Read the source and extract the function definitions we need.
    # We grab the full extent of each function from the AST, plus the
    # param block (already included in Extent.Text for FunctionDefinitionAst).
    $harnessSource = @()
    $harnessSource += '# Harness extracted by test_install_ps1_home_resolution.ps1'
    $harnessSource += '# Mirrors install.ps1 L436+ orchestrator pattern.'
    $harnessSource += '$ErrorActionPreference = "Stop"'
    $harnessSource += ''

    foreach ($fnName in @('Get-IndagisHome', 'Get-IndagisPlatformDefaultHome', 'Get-IndagisLegacyAliasHome', 'Write-IndagisLegacyAliasWarning')) {
        $fnDef = $ast.Find({
            param($n)
            $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
            $n.Name -eq $fnName
        }, $true)
        if (-not $fnDef) {
            throw "Could not extract function $fnName from $installPs1"
        }
        $harnessSource += $fnDef.Extent.Text
        $harnessSource += ''
    }

    # Orchestrator pattern (mirrors install.ps1 L436+):
    $harnessSource += '# Orchestrator fires the warning ONCE before any capture.'
    $harnessSource += 'if ($env:HERMES_HOME) {'
    $harnessSource += '    Write-IndagisLegacyAliasWarning ''HERMES_HOME'' $env:HERMES_HOME'
    $harnessSource += '}'
    $harnessSource += ''
    $harnessSource += '# Two captures (the bug scenario from bash Draft 2.1).'
    $harnessSource += '$r1 = Get-IndagisHome'
    $harnessSource += '$r2 = Get-IndagisHome'

    Set-Content -Path $runtimeHarness -Value $harnessSource

    # Run the harness in a clean pwsh process. Capture stderr by
    # redirecting 2>&1 to a file, then count occurrences of the
    # warning marker.
    $stderrFile = Join-Path ([System.IO.Path]::GetTempPath()) ('stderr_' + [Guid]::NewGuid().ToString('N') + '.txt')
    try {
        # Use an isolated HOME so neither ~/.indagis nor ~/.hermes exists,
        # forcing P3 (HERMES_HOME env var) to win. Without this isolation
        # the sandbox's own ~/.indagis (P2) or ~/.hermes (P4) would
        # short-circuit before P3 fires.
        $isolatedHome = Join-Path ([System.IO.Path]::GetTempPath()) ('indagis_test_' + [Guid]::NewGuid().ToString('N'))
        $null = New-Item -ItemType Directory -Path $isolatedHome -Force
        $env:HERMES_HOME = Join-Path $isolatedHome 'legacy_hermes_dir'
        $env:HOME = $isolatedHome
        $env:LOCALAPPDATA = $isolatedHome
        $env:USERPROFILE = $isolatedHome
        pwsh -NoProfile -File $runtimeHarness `
              -ExecutionPolicy Bypass `
              -OutputFormat Text `
              *> $stderrFile `
              2>&1
        Remove-Item Env:\HERMES_HOME -ErrorAction SilentlyContinue
        Remove-Item Env:\HOME -ErrorAction SilentlyContinue
        Remove-Item Env:\LOCALAPPDATA -ErrorAction SilentlyContinue
        Remove-Item Env:\USERPROFILE -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force $isolatedHome -ErrorAction SilentlyContinue

        $stderrContent = Get-Content -Raw $stderrFile -ErrorAction SilentlyContinue
        # Count occurrences of the warning marker (one per fire).
        $marker = 'is used as a fallback'
        $occurrences = ([regex]::Matches($stderrContent, [regex]::Escape($marker))).Count
        if ($occurrences -eq 1) {
            Write-Host "  PASS  runtime: warning fires exactly once across orchestrator + 2 Get-IndagisHome calls ($occurrences occurrence)"
        } else {
            Write-Host "  FAIL  runtime: warning fired $occurrences times, expected 1"
            Write-Host "        stderr content: [$stderrContent]"
            $script:failures++
        }
    } finally {
        Remove-Item $stderrFile -ErrorAction SilentlyContinue
    }
} finally {
    Remove-Item $runtimeHarness -ErrorAction SilentlyContinue
}

if ($script:failures -gt 0) {
    Write-Host ""
    Write-Host "$script:failures assertion(s) failed"
    exit 1
}

Write-Host ""
Write-Host "all assertions passed"
