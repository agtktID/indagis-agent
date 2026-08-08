# Cartographie scripts/install.ps1 — occurrences liées à l'identité

- Date : 2026-08-08
- Commit de référence : a67b2bb98
- Fichier : scripts/install.ps1 (4262 lignes, 113 occurrences de tokens identité)
- Méthode : `rg -n -i 'hermes|HERMES|HERMES_HOME|HERMES_DESKTOP|HERMES_GIT_BASH|com\.nousresearch|\.hermes|~/\.hermes'` brut, puis classification ligne par ligne.
- Grille : USER_FACING / DOCSTRING USER_FACING / TECHNICAL critique / DEFER / ATTRIBUTION (identique à cartography-install-sh.md)
- Note préalable : même convention que cartography-install-sh.md — la grille de classification a été posée par l'agent car aucune cartographie préalable n'a été déposée dans `reports/`. À confirmer en ouverture de la prochaine itération.

## Légende catégories

Voir cartography-install-sh.md pour la définition complète. Spécificités PowerShell :
- **TECHNICAL critique** inclut les variables d'environnement persistées via `[Environment]::SetEnvironmentVariable(..., "User")` (Registre HKCU\Environment) qui sont l'équivalent PowerShell des écritures `.bashrc` / `.zshrc` côté install.sh.
- **DEFER** inclut le productName electron-builder `Hermes.exe` (Windows) et `Hermes.app` (macOS) car ce sont des artifacts de build, pas du contrôle direct d'install.ps1.

## Cartographie par section (ligne par ligne)

### 1. En-tête (L1-14)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1-3 | DOCSTRING | `# Hermes Agent Installer for Windows` | USER_FACING → « Indagis Agent Installer for Windows » |
| 4-6 | DOCSTRING | `# Installation script for Windows (PowerShell).` | Préserver (technique) |
| 7-12 | DOCSTRING+USER_FACING | `# Usage: iex (irm https://hermes-agent.nousresearch.com/install.ps1)` | DEFER (migration future vers infra Indagis) : l'URL upstream et le nom de fichier restent attachés au domaine `hermes-agent.nousresearch.com`. Bascule conjointe avec install.sh L8-13. |

→ 2 USER_FACING (titre + URL).

### 2. Param block (L15-75)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L32 | TECHNICAL | `[string]$HermesHome = $(if ($env:HERMES_HOME) { $env:HERMES_HOME } else { "$env:LOCALAPPDATA\hermes" })` | **Cible du rebrand** : default `$env:LOCALAPPDATA\hermes` → à migrer vers `$env:LOCALAPPDATA\indagis` (prioritaire) tout en gardant `HERMES_HOME` en fallback. |
| L33 | TECHNICAL | `[string]$InstallDir = $(if ($env:HERMES_HOME) { "$env:HERMES_HOME\hermes-agent" } else { "$env:LOCALAPPDATA\hermes\hermes-agent" })` | **Cible du rebrand** : chemin en dur `$env:LOCALAPPDATA\hermes\hermes-agent` → migrer. Le nom `hermes-agent` est un DEFER potentiel (nom de package Python) — à confirmer. |
| L60-74 | DOCSTRING+USER_FACING | "When set, install.ps1 includes Stage-Desktop in the manifest and builds apps/desktop into a launchable Hermes.exe." | USER_FACING (référence `Hermes.exe` = productName electron-builder → **DEFER** car le rename est lié à la migration productName). Le commentaire explicite le contrat mais mentionne `Hermes.exe` directement. |
| L62-63, L65-66 | DOCSTRING+USER_FACING | "Hermes-Setup.exe (the signed Tauri bootstrap installer) passes -IncludeDesktop" / "The Electron desktop's own bootstrap-runner.ts runs install.ps1 from inside an already-launched Hermes.exe" | DEFER (référence productName) |
| L68-69 | USER_FACING | "The recursive path omits the flag" + "terminal users don't need a desktop binary built for them" | USER_FACING (contexte) |

→ 2 TECHNICAL critiques (L32, L33), 4 DEFER (références Hermes.exe, Hermes-Setup.exe, Hermes.exe ×2).

### 3. 8.3 short-path normalization (L77-352)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L114-115 | DOCSTRING | "It can then expose %TEMP%, %TMP%, %LOCALAPPDATA%, %APPDATA% and %USERPROFILE% -- plus everything derived from them, including the default HERMES_HOME and InstallDir" | DOCSTRING USER_FACING : commentaire référence la variable $HermesHome, le `HERMES_HOME` majuscule est le nom de variable env, à préserver tel quel mais mettre à jour la cohérence du contrat. |
| L163 | USER_FACING | `Write-PathDiag "[hermes] $Message"` | USER_FACING (préfixe littéral stderr), à migrer vers "[indagis]" |
| L255-256 | TECHNICAL | `Add-Type -Namespace 'HermesInstall' -Name 'LongPath'` | TECHNICAL (namespace CLR interne), **DEFER** : nom de namespace technique. |
| L303-326 | TECHNICAL | Set-LongProfileEnvVars (parcourt TEMP, TMP, LOCALAPPDATA, APPDATA, USERPROFILE) | Préserver (technique) |
| L334-347 | TECHNICAL | Réécriture `$HermesHome` / `$InstallDir` après normalisation | **Cible critique** : ce bloc conditionne tout le reste |
| L368-369 | TECHNICAL | `hermes_home` / `install_dir` dans `$script:ResolvedPathReport` | Préserver (clé JSON interne du rapport -ShowResolvedPaths) |

→ 1 DOCSTRING USER_FACING, 1 USER_FACING (préfixe stderr), 1 TECHNICAL critique (réécriture post-normalisation).

### 4. Configuration / Helper functions (L372-490)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L376-377 | ATTRIBUTION | `$RepoUrlSsh` / `$RepoUrlHttps` → github.com/NousResearch/hermes-agent.git | **ATTRIBUTION permanent** : URL upstream préservée. Migration du repo GitHub (`hermes-agent` → `indagis-agent`) en tranche distincte hors Phase 5. |
| L378-391 | TECHNICAL | constantes Python/Node/npm | Préserver (technique) |
| L396 | TECHNICAL | `$InstallStageProtocolVersion = 1` | Préserver |
| L451-457 | USER_FACING | `Write-Banner` : `* Hermes Agent Installer` / `An open source AI agent by Nous Research.` | USER_FACING : migrer le titre. Conserver "by Nous Research" comme ATTRIBUTION explicite. |
| L461-479 | TECHNICAL | Write-Info / Write-Success / Write-Warn / Write-Err | Préserver |
| L481-491 | TECHNICAL | Invoke-NativeWithRelaxedErrorAction | Préserver |

→ 1 USER_FACING (banner).

### 5. Discard-LockfileChurn / Show-NpmCertHint (L492-554)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L492-526 | TECHNICAL | Discard-LockfileChurn | Préserver |
| L527-554 | DOCSTRING+TECHNICAL | Show-NpmCertHint — référence à "Hermes's downstream" dans le commentaire (implicite, pas littéral ici) | Préserver (technique) |

→ 0 migration.

### 6. Resolve-NpmCmd / Find-SystemBrowser / Write-BrowserEnv (L558-597)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L569-582 | DOCSTRING+TECHNICAL | Find-SystemBrowser — commentaire mentionne "we no longer scan well-known install locations for a system browser" | DOCSTRING neutre, préserver |
| L584-597 | TECHNICAL | Write-BrowserEnv : `$envFile = Join-Path $HermesHome ".env"` | **Cible critique** : `$HermesHome\.env` est le chemin de stockage des credentials. |

→ 0 USER_FACING visible, 1 TECHNICAL critique (chemin .env).

### 7. Install-AgentBrowser (L599-653)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L607-608 | USER_FACING+TECHNICAL | `Write-Info "Installing agent-browser via npm -g --prefix..."` + `$prefixDir = Join-Path $HermesHome "node"` | USER_FACING (chemin en dur $HermesHome/node), migrer le chemin |
| L631 | USER_FACING | `Write-Info "Explicit browser override set -- skipping bundled Chromium download"` | USER_FACING, migrer le commentaire "set" |
| L652 | USER_FACING | `Write-Success "Agent-browser ready"` | USER_FACING, préserver (nom de package) |

→ 2 USER_FACING.

### 8. Get-PowerShellHostExe / Install-Uv (L659-735)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L690-693 | DOCSTRING | "Hermes owns its own uv at $HermesHome\bin\uv.exe" | DOCSTRING USER_FACING (référence projet), migrer vers "Indagis owns its own uv" |
| L694 | TECHNICAL | `$managedUv = Join-Path $HermesHome "bin\uv.exe"` | **Cible critique** : `bin/uv.exe` dans HERMES_HOME |
| L703 | USER_FACING | `Write-Info "Installing managed uv into $HermesHome\bin ..."` | USER_FACING (chemin en dur), migrer |

→ 1 DOCSTRING USER_FACING, 1 TECHNICAL critique, 1 USER_FACING.

### 9. Sync-EnvPath / Ensure-NodeExeOnPath / Set-ManagedNodeFirstOnUserPath (L737-802)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L737-747 | DOCSTRING+TECHNICAL | Sync-EnvPath (PATH refresh from registry) | Préserver |
| L749-767 | DOCSTRING+TECHNICAL | Ensure-NodeExeOnPath | Préserver |
| L769-802 | DOCSTRING+TECHNICAL | Set-ManagedNodeFirstOnUserPath — référence "the bundled Node" (neutre) | Préserver (technique) |
| L780 | DOCSTRING | "a stale baked-in BUILD_PIN_COMMIT" → voir install_repository | Préserver (référence interne au processus de build) |

→ 0 migration (bloc technique pur).

### 10. Get-NpmRange / Update-ManagedNpm (L804-896)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L839-896 | DOCSTRING+TECHNICAL | Update-ManagedNpm — `$tmpCwd = Join-Path $env:TEMP ("hermes-npm-upgrade-" + [Guid]::NewGuid().ToString("N"))` | USER_FACING (préfixe `hermes-` dans un nom de fichier TEMP), à neutraliser (le préfixe `indagis-` ou `npm-` est plus cohérent avec l'identité Indagis). |
| L862 | TECHNICAL | `$tmpCwd = Join-Path $env:TEMP ("hermes-npm-upgrade-" ...)` | **Cible critique mineure** : nom de fichier temp. |

→ 1 USER_FACING (préfixe hermes-npm-upgrade-).

### 11. Resolve-UvCmd (L898-943)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L898-905 | DOCSTRING | "Cross-process stage drivers (the desktop GUI's onboarding wizard, CI step-runners)" | DOCSTRING (neutre) |
| L921 | TECHNICAL | `$managedUv = Join-Path $HermesHome "bin\uv.exe"` | **Cible critique** (idem L694) |
| L927-928 | DOCSTRING | "Fallback to PATH (covers edge cases where the installer ran in a sibling process and HERMES_HOME wasn't propagated)" | DOCSTRING (référence `HERMES_HOME` env var, préserver nom) |
| L929 | TECHNICAL | `if (Get-Command uv -ErrorAction SilentlyContinue)` | Préserver |

→ 1 TECHNICAL critique (référence à L921).

### 12. Resolve-AvailablePythonVersion / Test-Python (L945-1079)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L945-968 | DOCSTRING+TECHNICAL | Resolve-AvailablePythonVersion | Préserver |
| L951-955 | DOCSTRING | "The cross-process-safe counterpart to Test-Python's in-memory `$script:PythonVersion = $fallbackVer` mutation. Under Hermes-Setup.exe each `-Stage NAME` runs in a *fresh* powershell.exe" | DOCSTRING (référence à Hermes-Setup.exe → **DEFER** productName) |
| L1024-1036 | DOCSTRING+TECHNICAL | Test-Python fallback list | Préserver (technique) |
| L1040-1043 | DOCSTRING | "skip the Microsoft Store stub. On Windows, %LOCALAPPDATA%\Microsoft\WindowsApps\python.exe is a 0-byte reparse-point stub" | DOCSTRING (technique) |

→ 0 migration directe.

### 13. Test-GitBashCompatibility / Test-MandatoryAslrEnabled / Install-Git (L1081-1368)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L1175-1206 | DOCSTRING+USER_FACING | Install-Git : "Hermes uses to run shell commands" + "If needed, set HERMES_GIT_BASH_PATH manually" | DOCSTRING USER_FACING (référence projet) + référence env var (préserver nom) |
| L1200-1201 | DOCSTRING | "if it ever breaks, Remove-Item %LOCALAPPDATA%\hermes\git and re-running this installer fully recovers" | DOCSTRING USER_FACING (chemin en dur `hermes\git`), migrer vers `indagis\git` |
| L1204-1205 | DOCSTRING | "persist the path in HERMES_GIT_BASH_PATH (User scope) so Hermes can find it" | DOCSTRING USER_FACING + référence env var |
| L1231, L1237 | USER_FACING | "Trying a Hermes-managed PortableGit install instead..." / "Git not found -- downloading PortableGit to $HermesHome\git\ ..." | USER_FACING (référence `Hermes-managed`, chemin en dur `$HermesHome\git\`) |
| L1235, L1316, L1336 | TECHNICAL | `$gitDir = "$HermesHome\git"` + persistance via SetEnvironmentVariable("Path", ..., "User") | **Cible critique** : `git` dans HERMES_HOME, et l'écriture dans le PATH user PowerShell = équivalent de L1855-1863 bash (qui écrit PATH_LINE dans .zshrc). À traiter ensemble côté résolution. |
| L1260, L1262, L1267, L1280, L1295, L1300, L1308, L1310-1330 | TECHNIQUE | URLs, tags, PortableGit extraction | Préserver (technique) |
| L1345-1355 | TECHNICAL | Test-GitBashCompatibility probe | Préserver |
| L1364-1365 | USER_FACING | "Fallback: install Git manually from https://git-scm.com/download/win then re-run this installer. Hermes needs Git Bash on Windows to run shell commands (same as Claude Code and other coding agents)." | USER_FACING (référence projet) |

→ 3 DOCSTRING USER_FACING, 3 USER_FACING, 1 TECHNICAL critique (chemin + écriture PATH User).

### 14. Set-GitBashEnvVar (L1370-1422)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L1370-1376 | DOCSTRING+USER_FACING | "persist the path in HERMES_GIT_BASH_PATH (User env scope) so Hermes can find it" | DOCSTRING USER_FACING |
| L1382-1383 | DOCSTRING | "Our own portable Git install is ALWAYS checked first" | DOCSTRING (neutre) |
| L1385-1389 | DOCSTRING+USER_FACING | "Layouts: PortableGit (our default): $HermesHome\git\bin\bash.exe" | DOCSTRING USER_FACING (chemin en dur) |
| L1392-1394 | TECHNICAL | Get-Command git | Préserver |
| L1404-1407 | DOCSTRING+TECHNICAL | "%ProgramFiles%\Git\bin\bash.exe" / "%ProgramFiles(x86)%\Git\bin\bash.exe" | DOCSTRING (neutre) |
| L1408 | TECHNICAL | `${env:LocalAppData}\Programs\Git\bin\bash.exe` | Préserver |
| L1412-1413 | TECHNICAL | `[Environment]::SetEnvironmentVariable("HERMES_GIT_BASH_PATH", $candidate, "User")` | **Cible critique** : persistance env var User scope |
| L1415 | USER_FACING | `Write-Info "Set HERMES_GIT_BASH_PATH=$candidate"` | USER_FACING (référence env var, préserver le nom env) |
| L1420-1421 | USER_FACING | "Could not locate bash.exe -- Hermes may not find Git Bash." / "If needed, set HERMES_GIT_BASH_PATH manually to your bash.exe path." | USER_FACING |

→ 2 DOCSTRING USER_FACING, 1 TECHNICAL critique, 2 USER_FACING.

### 15. Test-NodeVersionOk / Test-Node (L1424-1573)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L1424-1428 | DOCSTRING | "The dependency tree's real Node floor is >=22.22.0, set by react-router 8.3.0 (`engines.node`)" | DOCSTRING (technique) |
| L1451 | USER_FACING | `Write-Warn "Node.js $version is too old (Hermes requires Node >=26)"` | USER_FACING (référence projet), migrer vers "Indagis requires Node >=26" |
| L1455-1466 | TECHNICAL+USER_FACING | `$managedNode = "$HermesHome\node\node.exe"` + `Set-ManagedNodeFirstOnUserPath "$HermesHome\node"` + `Write-Success "Node.js $version found (Hermes-managed)"` | **Cible critique** : `node` dans HERMES_HOME + persistance PATH User (équivalent L1855-1863 bash) + USER_FACING "Hermes-managed" |
| L1459, L1502, L1509, L1512 | TECHNICAL | `$env:Path = "$HermesHome\node;$env:Path"` + `Set-ManagedNodeFirstOnUserPath "$HermesHome\node"` | **Cible critique** : persistance PATH User PowerShell |
| L1465, L1469 | USER_FACING | "Updating ManagedNpm" / "Installing Hermes-managed Node.js $NodeVersion LTS..." | USER_FACING |
| L1479 | USER_FACING | `Write-Info "Downloading portable Node.js $NodeVersion to $HermesHome\node\ ..."` | USER_FACING (chemin en dur) |
| L1490, L1498, L1501-1502, L1518 | TECHNICAL | extraction / mv / Set-ManagedNodeFirstOnUserPath | **Cible critique** (persistance PATH User) |
| L1547, L1551, L1556, L1558, L1560 | USER_FACING+TECHNICAL | "winget install OpenJS.NodeJS" / "(may prompt UAC -- check your taskbar for a flashing icon)..." / "Node.js $version installed via winget" | USER_FACING (commentaires) |
| L1567, L1569 | USER_FACING | "Install manually: https://nodejs.org/en/download/" | USER_FACING (neutre) |

→ 4 USER_FACING, 1 TECHNICAL critique (chemin $HermesHome/node + persistance PATH User).

### 16. Update-ProcessPathForPackages / Install-SystemPackages (L1575-1773)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L1593 | TECHNICAL | `$wingetLinks = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"` | Préserver (chemin winget natif) |
| L1611-1773 | TECHNICAL | Install-SystemPackages | Préserver (technique) |

→ 0 migration.

### 17. Install-Repository (L1779-2196)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L1862-1863 | DOCSTRING+USER_FACING | "Mirrors the `hermes update` path (#4735)" | DOCSTRING USER_FACING, migrer vers `indagis update` |
| L1918-1919 | DOCSTRING+USER_FACING | "Managed installs should follow origin/$Branch exactly... mirror ``hermes update`` and reset" | DOCSTRING USER_FACING |
| L1963-1964 | USER_FACING | "Review git diff / git status if Hermes behaves unexpectedly." | USER_FACING |
| L2019 | USER_FACING | "Close any programs that might be using files in $InstallDir (editors, terminals, running hermes processes) and try again." | USER_FACING |
| L2039-2040 | COMMENT+USER_FACING | "Trying SSH clone..." + "SSH failed, trying HTTPS..." | USER_FACING (mineur) |
| L2059, L2065-2074 | TECHNICAL+USER_FACING | "Downloading ZIP archive instead..." + `$zipUrl = "https://github.com/NousResearch/hermes-agent/archive/$Commit.zip"` | **ATTRIBUTION permanent** : URL ZIP upstream préservée (cf. L376-377). Le tag et le label de la release sont upstream-dépendants. |
| L2074-2075 | TECHNICAL | `$zipPath = "$env:TEMP\hermes-agent-$zipLabel.zip"` + `$extractPath = "$env:TEMP\hermes-agent-extract"` | **Cible critique mineure** : nom de fichier TEMP `hermes-agent-*.zip`, à neutraliser en `indagis-agent-*.zip` ou `repo-*.zip` |
| L2101-2103 | DOCSTRING | "see the notes at the shared clone-path config below and install.ps1:1461-1469" → référence interne | DOCSTRING (interne) |
| L2124, L2154, L2162 | USER_FACING | "hermes update (see the notes)" / "Git found ($version)" | USER_FACING |
| L2127 | USER_FACING | "ZIP extract succeeded but git checkout failed -- desktop build may need $env:GITHUB_SHA" | USER_FACING |

→ 3 DOCSTRING USER_FACING, 4 USER_FACING, 1 TECHNICAL critique (nom fichier TEMP `hermes-agent-`).

### 18. Install-Venv (L2198-2386)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L2204-2209 | DOCSTRING+USER_FACING | "Re-resolve the interpreter before creating the venv. Under Hermes-Setup.exe each stage runs in its own powershell.exe" | DOCSTRING (référence `Hermes-Setup.exe` → **DEFER**) |
| L2235, L2247-2257 | TECHNICAL | `schtasks /Query /FO CSV 2>$null | ... | Where-Object { $_.TaskName -like '*Hermes_Gateway*' }` | **Cible critique mineure** : pattern de nom de scheduled task `Hermes_Gateway*`. À renommer en `Indagis_Gateway*` ou similaire. |
| L2261-2262 | USER_FACING | "The launcher CLI (hermes.exe) plus its child tree." + `taskkill /F /T /IM hermes.exe` | USER_FACING (référence `hermes.exe` = productName) → **DEFER** (mais le taskkill du process `hermes.exe` doit cibler le bon nom) |
| L2263-2266 | DOCSTRING+USER_FACING | "The gateway/agent that a scheduled task or watchdog autostarts runs as `pythonw.exe -m hermes_cli.main gateway run`" | DOCSTRING USER_FACING (référence `hermes_cli.main` = nom de package Python) → **DEFER** |
| L2274-2275 | DOCSTRING+USER_FACING | "Get-CimInstance is used over Get-Process because it returns a null ExecutablePath for a process it cannot inspect" | DOCSTRING (technique) |
| L2370-2371 | DOCSTRING+USER_FACING | "Re-arm the gateway autostart tasks disabled during the venv teardown" | DOCSTRING (neutre) |

→ 1 DOCSTRING (Hermes-Setup.exe), 1 USER_FACING (hermes.exe taskkill), 1 DOCSTRING USER_FACING (hermes_cli.main), 1 TECHNICAL critique (nom de scheduled task).

### 19. Install-Dependencies (L2388-2647)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L2476 | TECHNICAL (citation littérale) | `$pythonExeForParse = if (-not $NoVenv) { "$InstallDir\venv\Scripts\python.exe" } else { (& $UvCmd python find $PythonVersion) }` | **Pas concernée par le bug** : c'est la résolution de l'interpréteur Python (venv/Scripts/python.exe). Le mot `hermes-agent` n'apparaît pas. |
| L2474-2502 | TECHNICAL+USER_FACING | parse pyproject.toml : `m = re.search(r'hermes-agent\[([\w-]+)\]', s)` à L2487 (à l'intérieur du heredoc Python L2479-2492) | **BUG FONCTIONNEL ISOLÉ** : cf. ticket dédié. **L2487 est le seul site contenant la regex `hermes-agent\[...\]` dans install.ps1** (vérifié lecture littérale). Les 4 lignes voisines citées dans les cartographies précédentes (L1693, L2247, L2476, L2625) ne contiennent **PAS** le mot `hermes-agent` (cf. citation littérale ci-dessous). Le périmètre du bug est strictement borné à 2 sites : `install.sh:1625` et `install.ps1:2487`. |
| L1693 | TECHNICAL (citation littérale) | `$output = winget install --exact --id $pkg --source winget --silent --force` | **Pas concernée par le bug** : c'est une commande `winget install`. Le mot `hermes-agent` n'apparaît pas. |
| L2525 | USER_FACING | `throw "Failed to install hermes-agent package even with no extras."` | USER_FACING (référence `hermes-agent` = nom de package dans un message d'erreur) → **DEFER** (nom de package Python, hors Phase 4). Le message d'erreur contient le nom de package upstream alors que le projet s'appelle `indagis-agent` ; à harmoniser dans une tranche de rebrand de package. **Pas dans le périmètre du bug regex** : c'est une chaîne littérale dans un throw, pas un parse de `pyproject.toml`. |
| L2531-2533, L2552, L2554-2557 | DOCSTRING+USER_FACING | "the dependency sync likely landed in a sibling .venv\ directory" / "Recover with: cd '$InstallDir'; Remove-Item -Recurse -Force venv,.venv; uv venv venv --python $PythonVersion; `$env:UV_PROJECT_ENVIRONMENT='$InstallDir\venv'; uv sync --extra all --locked" | USER_FACING (commandes de récupération) |
| L2564-2568 | DOCSTRING+USER_FACING | "uv on Windows can register hermes.exe in dist-info/RECORD but fail to materialise the .exe" | DOCSTRING USER_FACING (référence productName) → **DEFER** |
| L2596 | USER_FACING | "Workaround: `"$pythonExe`" -m hermes_cli.main <command>" | USER_FACING (référence `hermes_cli.main` = nom de package) → **DEFER** |
| L2611-2641 | TECHNIQUE+USER_FACING | "Verify the dashboard deps specifically..." + "hermes dashboard will not work" + "Recover with..." | USER_FACING (référence `hermes dashboard`) |
| L2625 | TECHNICAL (citation littérale) | `& $pythonExe -m py_compile "$InstallDir\hermes_cli\web_server.py" 2>&1 | Out-Null` | **Pas concernée par le bug** : c'est un `py_compile` sur le sous-module `hermes_cli.web_server` (le mot présent est `hermes_cli`, pas `hermes-agent`). **Cible critique mineure** : référence au sous-module Python `hermes_cli.*` = nom de package → **DEFER** (couplé au rebrand de package `hermes_cli` → `indagis_cli`, hors Phase 4). |

→ 1 BUG FONCTIONNEL ISOLÉ (L2487, périmètre strict : seul site contenant la regex `hermes-agent\[...\]` dans install.ps1), 1 USER_FACING (message d'erreur L2525 avec chaîne littérale `hermes-agent`, hors périmètre du bug), 1 DOCSTRING USER_FACING (hermes.exe), 1 USER_FACING (hermes_cli.main), 1 USER_FACING (hermes dashboard), 1 TECHNICAL critique (nom de module Python).

### 20. Set-PathVariable (L2649-2687)

| Lignes | Catégorie | Contendu | Décision par défaut |
|---|---|---|---|
| L2650 | USER_FACING | `Write-Info "Setting up hermes command..."` | USER_FACING, migrer vers "Setting up indagis command" |
| L2653-2656 | TECHNICAL | `$hermesBin = "$InstallDir"` (NoVenv) / `"$InstallDir\venv\Scripts"` | **Cible critique** : résolution du binaire |
| L2658-2660 | DOCSTRING+USER_FACING | "Add the venv Scripts dir to user PATH so hermes is globally available. On Windows, the hermes.exe in venv\Scripts\ has the venv Python baked in" | DOCSTRING USER_FACING (référence productName) → **DEFER** |
| L2662-2668 | TECHNICAL+USER_FACING | `Set-Environment Variable("Path", "$hermesBin;$currentPath", "User")` + `Write-Success "Added to user PATH: $hermesBin"` | **Cible critique** : persistance PATH User PowerShell (équivalent L1855-1863 bash) + USER_FACING |
| L2673-2675 | DOCSTRING+USER_FACING | "Set HERMES_HOME so the Python code finds config/data in the right place. Only needed on Windows where we install to %LOCALAPPDATA%\hermes instead of the Unix default ~/.hermes" | DOCSTRING USER_FACING (chemin en dur) |
| L2676-2681 | TECHNICAL | `[Environment]::SetEnvironmentVariable("HERMES_HOME", $HermesHome, "User")` | **Cible critique** : persistance env var HERMES_HOME User scope |
| L2686 | USER_FACING | `Write-Success "hermes command ready"` | USER_FACING, migrer vers "indagis command ready" |

→ 2 USER_FACING, 2 DOCSTRING USER_FACING, 3 TECHNICAL critiques (binaire + persistance PATH + persistance HERMES_HOME).

### 21. Write-BootstrapMarker (L2689-2764)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L2690-2693 | DOCSTRING+USER_FACING | "Writes $InstallDir\.hermes-bootstrap-complete which tells the Hermes desktop app (apps/desktop/electron/main.ts) `install.ps1 ran successfully -- DON'T trigger the legacy first-launch bootstrap runner`" | DOCSTRING USER_FACING (référence `Hermes desktop app` + nom de fichier) |
| L2695-2700 | DOCSTRING | "Schema mirrors what main.ts's writeBootstrapMarker() / isBootstrapComplete() expect. Keep this in lockstep when either side changes: apps/desktop/electron/main.ts lines 1199-1222" | DOCSTRING (référence interne au desktop) |
| L2701-2702 | DOCSTRING+USER_FACING | "The desktop validates schemaVersion + pinnedCommit length but doesn't enforce that HEAD matches the pin (users update via `hermes update` which moves HEAD legitimately)" | DOCSTRING USER_FACING (référence `hermes update`) |
| L2741 | TECHNICAL | `$markerPath = Join-Path $InstallDir ".hermes-bootstrap-complete"` | **Cible critique** : nom du marker, à renommer `.indagis-bootstrap-complete` avec compatibilité lecture du nom legacy (le desktop lit ce fichier) |
| L2742-2751 | TECHNICAL | JSON schema `schemaVersion: 1, pinnedCommit, pinnedBranch, completedAt` | Préserver (contrat JSON interne) |
| L2747-2750 | DOCSTRING | "desktopVersion field intentionally omitted -- only the desktop app knows its own version" | DOCSTRING (interne) |

→ 2 DOCSTRING USER_FACING, 1 TECHNICAL critique (marker).

### 22. Copy-ConfigTemplates (L2766-2865)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L2769 | DOCSTRING | "Create the HERMES_HOME directory structure ($HermesHome, default %LOCALAPPDATA%\hermes)" | DOCSTRING USER_FACING (chemin en dur) |
| L2770-2778 | TECHNICAL | `New-Item -ItemType Directory -Force -Path "$HermesHome\cron" ...` | **Cible critique** : 9 sous-répertoires dans $HermesHome, à migrer via la fonction de résolution |
| L2782-2806 | TECHNICAL+USER_FACING | `$envPath = "$HermesHome\.env"` + `$configPath = "$HermesHome\config.yaml"` + messages Write-Success "Created $envPath from template" | **Cible critique** : 2 chemins + 4 messages, à migrer |
| L2808-2828 | TECHNICAL+USER_FACING | SOUL.md + "You are Hermes Agent, an intelligent AI assistant created by Nous Research. You are helpful, knowledgeable..." | **DEFER tranche 5+** : SOUL.md est la persona utilisateur, distinct. |
| L2830 | USER_FACING | `Write-Success "Configuration directory ready: $HermesHome"` | USER_FACING |
| L2833 | USER_FACING | `Write-Info "Syncing bundled skills to $HermesHome\skills ..."` | USER_FACING |
| L2849-2851 | TECHNICAL | `$pythonExe "$InstallDir\tools\skills_sync.py"` | Préserver (technique) |
| L2854, L2861 | USER_FACING | `Write-Success "Skills synced to $HermesHome\skills"` | USER_FACING |

→ 7 USER_FACING, 11 TECHNICAL critiques (chemins .env, config.yaml, sous-répertoires, skills).

### 23. Install-NodeDeps (L2867-3095)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L2869-2873 | DOCSTRING+USER_FACING | "Cross-process driver mode (Hermes-Setup.exe runs each -Stage NAME in a fresh powershell.exe) means $script:HasNode set by Stage-Node in the previous process isn't visible here" | DOCSTRING (référence Hermes-Setup.exe → **DEFER**) |
| L2899 | USER_FACING | `Write-Info "Open a new PowerShell window and re-run 'hermes setup tools' later."` | USER_FACING, migrer vers "indagis setup tools" |
| L2988, L2992-2993 | USER_FACING | `hermes dashboard` + "Without this, tools/browser_tool.py::check_browser_requirements returns False" | USER_FACING (référence `hermes dashboard`) |
| L3034-3036 | DOCSTRING+USER_FACING | "--yes auto-accepts npx's `Need to install playwright@X.Y.Z` confirmation prompt... The install hangs indefinitely after printing `Need to install the following packages: playwright@X.Y.Z`" | DOCSTRING (technique) |
| L3062, L3063, L3075, L3080 | USER_FACING | `Write-Warn "Playwright Chromium install failed -- exit code $pwCode"` / `Write-Warn "Browser tools will not work until Chromium is installed."` / `Write-Info "Run manually later: cd \`"$installDir\`"; npx playwright install chromium"` | USER_FACING (neutre) |

→ 2 USER_FACING (hermes setup tools, hermes dashboard).

### 24. Clear-ElectronBuildCache (L3097-3144)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L3097-3112 | DOCSTRING+USER_FACING | "the `electron`->`Hermes` rename dies with ENOENT and every re-run repeats the broken extraction forever" | DOCSTRING USER_FACING (référence `Hermes` = productName) → **DEFER** |

→ 1 DOCSTRING USER_FACING (DEFER).

### 25. Install-DesktopVoiceDeps / Install-Desktop (L3215-3534)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L3244-3247 | DOCSTRING+USER_FACING | "Build apps/desktop into a launchable Hermes.exe. Only called from Stage-Desktop, which is itself only included in the manifest when -IncludeDesktop was passed to install.ps1." | DOCSTRING USER_FACING (référence productName) → **DEFER** |
| L3256-3260 | DOCSTRING+USER_FACING | "The Tauri bootstrap installer's launch_hermes_desktop command resolves apps/desktop/release/win-unpacked/Hermes.exe directly" | DOCSTRING USER_FACING (référence `launch_hermes_desktop` + `Hermes.exe`) → **DEFER** |
| L3261-3266 | DOCSTRING+USER_FACING | "Test-Node enforces the build floor (Node >=26) and prepends the Hermes-managed Node to PATH" | DOCSTRING USER_FACING (référence `Hermes-managed`) |
| L3274 | TECHNICAL | `$desktopDir = "$InstallDir\apps\desktop"` | **Cible critique mineure** : chemin de l'app desktop (neutre côté identité) |
| L3368-3370 | DOCSTRING+USER_FACING | "signAndEditExecutable=false in apps/desktop/package.json's build.win block... the unfixable symlink crash; the afterPack hook runs rcedit directly" | DOCSTRING USER_FACING (référence config electron-builder) → **DEFER** (couplé à productName) |
| L3375 | USER_FACING | `Write-Info "Building desktop app (this takes 1-3 minutes)..."` | USER_FACING (neutre) |
| L3382-3401 | DOCSTRING+TECHNICAL | GITHUB_SHA seeding | Préserver (CI) |
| L3485-3486 | TECHNICAL | `$exeCandidates = @("$desktopDir\release\win-unpacked\Hermes.exe", "$desktopDir\release\win-arm64-unpacked\Hermes.exe")` | **Cible critique mineure** : nom binaire `Hermes.exe` → **DEFER** (productName electron-builder) |
| L3492 | USER_FACING | `Write-Success "Desktop ready: $cand"` | USER_FACING (neutre) |
| L3499 | USER_FACING | `throw "Desktop build completed but no Hermes.exe was found under $desktopDir\release\*-unpacked\"` | USER_FACING (référence productName) → **DEFER** |
| L3502-3508 | DOCSTRING+USER_FACING | "3b. The Hermes icon + identity are stamped onto Hermes.exe by the electron-builder `afterPack` hook" | DOCSTRING USER_FACING (référence productName) → **DEFER** |
| L3511-3513 | DOCSTRING+USER_FACING | "Chromium's GPU/renderer sandboxes CHECK-fail with 0x80000003 when this ACE is missing alongside orphan AppContainer SIDs under %LOCALAPPDATA% (electron/electron#51761, hermes-agent#38216)" | DOCSTRING USER_FACING (référence `hermes-agent#38216` = nom de repo GitHub upstream) → **DEFER** |
| L3519 | USER_FACING | `Write-Success "Granted AppContainer read access on $appDir"` | USER_FACING (neutre) |
| L3528-3530 | DOCSTRING+USER_FACING | "We deliberately do NOT point them at `hermes desktop`: that command rebuilds (npm install + electron-builder) on every launch, which would cost minutes each time" | DOCSTRING USER_FACING (référence `hermes desktop`) |

→ 7 DOCSTRING USER_FACING (5 DEFER, 2 USER_FACING), 1 TECHNICAL critique mineure (chemin binaire).

### 26. New-DesktopShortcuts (L3536-3595)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L3544-3550 | DOCSTRING+USER_FACING | "The Hermes icon + identity are stamped onto Hermes.exe by the electron-builder `afterPack` hook" | DOCSTRING USER_FACING (référence productName) → **DEFER** |
| L3558-3561 | TECHNICAL+USER_FACING | `(Join-Path ([Environment]::GetFolderPath('Programs')) 'Hermes.lnk')` + `(Join-Path ([Environment]::GetFolderPath('Desktop')) 'Hermes.lnk')` | **Cible critique mineure** : noms de raccourcis Start Menu + Desktop. `Hermes.lnk` = produit de build, à renommer en `Indagis.lnk`. **DEFER** si couplé à productName. |
| L3573 | USER_FACING | `$sc.Description = 'Hermes Agent'` | USER_FACING (référence `Hermes Agent` = productName) → **DEFER** |
| L3581-3585 | DOCSTRING+USER_FACING | "the exe was re-stamped with the Hermes icon" | DOCSTRING USER_FACING (référence produit) → **DEFER** |
| L3592 | USER_FACING | `Write-Warn "Skipping shortcut creation: $($_.Exception.Message)"` | USER_FACING (neutre) |

→ 3 DOCSTRING USER_FACING (DEFER), 1 USER_FACING (DEFER), 1 TECHNICAL critique mineure (raccourcis).

### 27. Install-PlatformSdks (L3597-3704)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L3598-3600 | DOCSTRING+USER_FACING | "Ensure messaging-platform SDKs matching tokens the user added to ~/.hermes/.env are importable" | DOCSTRING USER_FACING (chemin en dur) |
| L3598-3605 | DOCSTRING+USER_FACING | "two problems this solves: 1. The tiered `uv pip install` cascade above can fall through to a lower tier when the first fails (common when RL git deps choke), which silently skips some messaging SDKs from [messaging]. 2. `uv` creates the venv without pip. If a messaging SDK ends up missing, the user can't `pip install python-telegram-bot` to recover" | DOCSTRING (neutre) |
| L3624-3647 | TECHNICAL | parse .env pour les tokens messaging | Préserver (technique) |
| L3651 | USER_FACING | `Write-Info "Verifying platform SDKs for tokens found in $envPath ..."` | USER_FACING (neutre) |

→ 1 DOCSTRING USER_FACING (chemin en dur).

### 28. Invoke-SetupWizard (L3706-3734)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L3716 | USER_FACING | `Write-Info "Skipping setup wizard (non-interactive). Configure via the GUI or 'hermes setup'."` | USER_FACING, migrer vers "indagis setup" |
| L3726-3730 | USER_FACING | `& ".\venv\Scripts\python.exe" -m hermes_cli.main setup` | USER_FACING (référence `hermes_cli.main` = nom de package) → **DEFER** |

→ 1 USER_FACING, 1 USER_FACING (DEFER).

### 29. Start-GatewayIfConfigured (L3736-3812)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L3749-3752 | TECHNICAL+USER_FACING | `$hermesCmd = "$InstallDir\venv\Scripts\hermes.exe"` + `if (-not (Test-Path $hermesCmd)) { $hermesCmd = "hermes" }` | **Cible critique** : résolution du binaire hermes (USER_FACING → "indagis" + fallback "hermes") |
| L3756 | TECHNICAL+USER_FACING | `$whatsappSession = "$HermesHome\whatsapp\session\creds.json"` | **Cible critique mineure** : chemin en dur dans $HermesHome |
| L3760 | USER_FACING | `Write-Info "Running 'hermes whatsapp' to pair via QR code..."` | USER_FACING, migrer vers "indagis whatsapp" |
| L3769 | USER_FACING | `& $hermesCmd whatsapp` | USER_FACING, migrer |
| L3781 | USER_FACING | `Write-Info "The gateway handles messaging platforms and cron job execution."` | USER_FACING (neutre) |
| L3789 | USER_FACING | `Write-Info "Start the gateway later with: hermes gateway"` | USER_FACING, migrer |
| L3795 | USER_FACING | `if ($response -eq "" -or $response -match "^[Yy]")` puis `Write-Info "Starting gateway in background..."` | USER_FACING (neutre) |
| L3798-3807 | USER_FACING | `Start-Process -FilePath $hermesCmd -ArgumentList "gateway"` + `Write-Success "Gateway started! Your bot is now online."` + `Write-Info "Logs: $logFile"` + `Write-Info "To stop: close the gateway process from Task Manager"` | USER_FACING (référence `hermesCmd` + "Gateway started") |
| L3807 | USER_FACING | `Write-Warn "Failed to start gateway. Run manually: hermes gateway"` | USER_FACING |
| L3810 | USER_FACING | `Write-Info "Skipped. Start the gateway later with: hermes gateway"` | USER_FACING |

→ 9 USER_FACING (commandes + messages), 2 TECHNICAL critiques (résolution binaire + chemin whatsapp).

### 30. Write-Completion (L3814-3869)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L3817 | USER_FACING | `[OK] Installation Complete!` | USER_FACING (neutre) |
| L3825-3831 | USER_FACING | `Write-Host "   Config:    $HermesHome\config.yaml"` / `API Keys:  $HermesHome\.env"` / `Data:      $HermesHome\cron\, sessions\, logs\"` / `Code:      $HermesHome\hermes-agent\"` | USER_FACING (4 chemins en dur dont `hermes-agent\`) |
| L3838-3849 | USER_FACING | `Write-Host "   hermes              Start chatting"` / `hermes setup        Configure API keys & settings"` / `hermes config       View/edit configuration"` / `hermes config edit  Open config in editor"` / `hermes gateway      Start messaging gateway (Telegram, Discord, etc.)"` / `hermes update       Update to latest version"` | USER_FACING (6 commandes) |
| L3854 | USER_FACING | `[*] Restart your terminal for PATH changes to take effect` | USER_FACING (neutre) |
| L3858-3866 | USER_FACING | "Note: Node.js could not be installed automatically..." / "Note: ripgrep (rg) was not found..." | USER_FACING (neutre) |

→ 10 USER_FACING (4 chemins + 6 commandes).

### 31. Stage protocol (L3871-4097)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L3875-3879 | DOCSTRING+USER_FACING | "the desktop GUI's onboarding wizard, CI, future install.sh" | DOCSTRING USER_FACING (référence "future install.sh") |
| L3950, L3958, L3962 | USER_FACING | `Title = "Cloning Hermes repository"` / `Title = "Building desktop app"` (IncludeDesktop) / `Title = "Adding Hermes to PATH"` | USER_FACING (3 manifest titles) |
| L3968-3969 | USER_FACING | `Title = "Configuring API keys and models"` / `Title = "Starting messaging gateway"` | USER_FACING (neutre) |

→ 3 USER_FACING (manifest titles).

### 32. Main / entry-point dispatch (L4099-4262)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| L4234-4260 | TECHNICAL+USER_FACING | catch block : `Write-Info "If the error is unclear, try downloading and running the script directly: Invoke-WebRequest -Uri 'https://hermes-agent.nousresearch.com/install.ps1' -OutFile install.ps1"` | DEFER (URL upstream `hermes-agent.nousresearch.com`), bascule conjointe avec install.sh L8-13 et install.ps1 L7-12. |

→ 1 USER_FACING (URL).

## Récapitulatif

### Par catégorie

| Catégorie | Total occurrences | Sites principaux |
|---|---|---|
| USER_FACING (à migrer) | ~60 | banner (L451-457), 3 manifest titles (L3950/3958/3962), 6 commandes Write-Completion (L3838-3849), 4 chemins Write-Completion (L3825-3831), bloc gateway (L3760-3810), URL install.ps1 (L4259), Node.js warning (L1451), Invoke-SetupWizard (L3716) |
| DOCSTRING USER_FACING | ~15 | Write-Banner (L451-457), Install-Repository (L1862-1863, L1918-1919, L1963-1964, L2019), Install-Venv (L2204-2209), Install-Dependencies (L2531-2557, L2564-2568), Set-PathVariable (L2658-2660, L2673-2675), Write-BootstrapMarker (L2690-2693, L2701-2702), Copy-ConfigTemplates (L2769), Install-Desktop (L3244-3266, L3368-3370, L3502-3508, L3511-3513, L3528-3530), New-DesktopShortcuts (L3544-3550, L3581-3585) |
| TECHNICAL critique (cible de la fonction de résolution) | ~25 | `HermesHome`/`InstallDir` (L32-33, L334-347), `$env:LOCALAPPDATA\hermes` (L32-33), `$HermesHome\bin\uv.exe` (L694, L921), `$HermesHome\git` (L1200-1201, L1235, L1316, L1336), `$HermesHome\node` (L1455-1466, L1459, L1502, L1509, L1512), `$HermesHome\whatsapp\session` (L3756), `$HermesHome\.env` (L586-589, L2782), `$HermesHome\config.yaml` (L2797), `$HermesHome\skills` (L2778, L2833), `$env:TEMP\hermes-agent-` (L2074-2075), `$env:TEMP\hermes-npm-upgrade-` (L862), `bin/uv.exe` (L694), `bin\git` (L1235, L1316, L1336), `bin\node` (L1455-1466, L1502), `node\node.exe` (L1455), `.hermes-bootstrap-complete` (L2741), `hermes.exe` taskkill (L2262) + scheduled task `*Hermes_Gateway*` (L2247), `hermes`/`.exe` resolution (L2653-2656, L3749-3752), persistance env vars via `SetEnvironmentVariable(..., "User")` (L1316, L1336, L1412, L1502, L1509, L2662-2681) |
| DEFER (hors tranche 5) | ~20 | `Hermes.exe` (productName electron-builder, L3244-3260, L3485-3486, L3499, L3502-3508, L3544-3550, L3581-3585), `Hermes-Setup.exe` (L2204-2209, L2869-2873), `Hermes_Gateway` scheduled task pattern (L2247, L2255), `Hermes.lnk` (L3558-3561), `launch_hermes_desktop` (L3256-3260), `Hermes Agent` shortcut description (L3573), `Hermes icon` (L3544-3550, L3581-3585), `Hermes_Agent` accent uppercase, `hermes-agent[extra]` (L2487 — **seul** site contenant la regex `hermes-agent\[...\]` dans install.ps1, BUG FONCTIONNEL ISOLÉ, voir ticket dédié), `hermes-agent` URL repo (L46, L376, L2065-2074, L4259), `hermes-cli` package Python (L2263-2266, L2596, L3726-3730), `hermes-agent` directory name (L33, L1760, L2548, L2741, L3831), `hermes-agent#38216` GitHub issue ref (L3511-3513), `hermes-agent#` related issue refs, `hermes-agent.nousresearch.com` URL domaine bootstrap (L7-12, L4259 — bascule conjointe vers infra Indagis) |
| ATTRIBUTION (permanent) | ~4 | URL `https://github.com/NousResearch/hermes-agent.git` (L376-377), URL `https://github.com/NousResearch/hermes-agent/archive/...` (L2065-2074), URL `https://hermes-agent.nousresearch.com/install.ps1` (L4259 — bascule vers infra Indagis reportée), `*Hermes_Gateway*` scheduled task name (L2247, L2255 — couplé au service, à traiter en même temps que le rebrand du service) |

### Sites critiques pour la fonction de résolution centralisée (point 3 du brief)

Ce sont les **points où HERMES_HOME est lu comme valeur par défaut** et où un script PowerShell doit basculer vers INDAGIS_HOME en priorité tout en gardant HERMES_HOME en repli :

1. **L32-33** : `HermesHome` et `InstallDir` defaults avec `$env:LOCALAPPDATA\hermes` — initialisation, à étendre.
2. **L334-347** : Réécriture post-normalisation 8.3 — conditionne tout le reste.
3. **L586-589** : `Join-Path $HermesHome ".env"` — chemin du fichier d'environnement.
4. **L694, L921** : `$HermesHome\bin\uv.exe` — chemin d'uv managé.
5. **L1200-1201, L1235, L1316, L1336** : `$HermesHome\git` (PortableGit) + persistance PATH User.
6. **L1412, L1415** : `HERMES_GIT_BASH_PATH` env var — persistance env var User scope.
7. **L1455-1466, L1502, L1509, L1512** : `$HermesHome\node` + persistance PATH User.
8. **L2247** : Scheduled task `*Hermes_Gateway*` — pattern de nom de task.
9. **L2262** : `taskkill /IM hermes.exe` — image name du process à killer.
10. **L2548** : `$env:UV_PYTHON = "$InstallDir\venv\Scripts\python.exe"` — déjà neutre.
11. **L2653-2656, L3749-3752** : résolution du binaire `hermes` (USER_FACING).
12. **L2662-2681** : persistance PATH User + HERMES_HOME env var via `SetEnvironmentVariable(..., "User")` — **équivalent PowerShell des écritures L1855-1863 install.sh**.
13. **L2741** : `$InstallDir\.hermes-bootstrap-complete` — marker.
14. **L2770-2778** : 9 sous-répertoires (`cron`, `sessions`, `logs`, `pairing`, `hooks`, `image_cache`, `audio_cache`, `memories`, `skills`).
15. **L2782, L2797, L2833** : `.env`, `config.yaml`, `skills` — chemins en dur.
16. **L3756** : `$HermesHome\whatsapp\session\creds.json` — chemin whatsapp.

### Sites équivalents aux écritures .zshrc / .bashrc / .profile install.sh (L1855-1863)

Côte PowerShell, les écritures de PATH persistantes se font via `SetEnvironmentVariable("Path", ..., "User")` dans le Registre, pas dans un fichier .rc. Le concept de "User PATH" du Registre HKCU\Environment est l'équivalent direct. Sites concernés :

1. **L1316** : `$env:Path = "$gitDir\cmd;$env:Path"` (session courante, pas persistante — Install-Git)
2. **L1336** : `[Environment]::SetEnvironmentVariable("Path", ..., "User")` (persistante — Install-Git)
3. **L1412** : `SetEnvironmentVariable("HERMES_GIT_BASH_PATH", ..., "User")` (persistante — Set-GitBashEnvVar)
4. **L1502** : `$env:Path = "$HermesHome\node;$env:Path"` (session — Test-Node)
5. **L1509** : `Set-ManagedNodeFirstOnUserPath "$HermesHome\node"` (persistante — Test-Node)
6. **L2662-2681** : `SetEnvironmentVariable("Path", ..., "User")` + `SetEnvironmentVariable("HERMES_HOME", ..., "User")` (persistantes — Set-PathVariable)
7. **L3690, L3681, L3683, L3698** : `& $pythonExe -m pip install ...` (session, pas persistante)

Le profil PowerShell n'a pas d'équivalent direct d'un fichier rc, mais le concept de "user-scoped env var" via `SetEnvironmentVariable(..., "User")` est le mécanisme équivalent. À traiter en cohérence avec la future fonction de résolution centralisée.

L'équivalence détaillée bash ↔ PowerShell est documentée :

| Bash (install.sh) | PowerShell (install.ps1) | Mécanisme |
|---|---|---|
| `~/.zshrc` / `~/.bashrc` / `~/.profile` | `HKCU\Environment` (Registre) | `SetEnvironmentVariable(..., "User")` |
| `echo "export PATH=..." >> ~/.zshrc` | `SetEnvironmentVariable("Path", ..., "User")` | Persistance |
| `source ~/.zshrc` (recharger) | rafraîchi par nouveau process | Pas équivalent direct |
| `unset` (session) | `$env:Path = ...` (session) | Session only |

La fonction de résolution centralisée doit traiter les deux faces (bash + PowerShell) en cohérence pour que les PATH écrits (rc côté bash, Registre côté PowerShell) pointent vers le bon binaire `indagis` (prioritaire) avec repli sur `hermes`.

### DEFER explicitement hors tranche 5

- `Hermes.exe` (productName electron-builder Windows, plusieurs sites)
- `Hermes-Setup.exe` (Tauri bootstrap installer, distinct de install.ps1)
- `Hermes.app` (productName electron-builder macOS — pas dans install.ps1 mais mentionné dans le desktop build)
- `Hermes.lnk` (raccourcis Start Menu + Desktop)
- `Hermes Agent` shortcut description
- `Hermes-managed Node` (commentaire, sémantiquement lié au productName)
- `hermes_cli.main`, `hermes_cli.web_server` (noms de packages Python, à traiter avec le rebrand de package)
- `hermes-agent[extra]` (parse pyproject.toml) — **BUG FONCTIONNEL POINT 3** (à traiter séparément, voir rapport dédié)
- URL `github.com/NousResearch/hermes-agent.git` (repo upstream, DEFER tranche migration repo)
- URL `hermes-agent.nousresearch.com/install.ps1` (domaine upstream, DEFER migration domaine)
- Scheduled task pattern `*Hermes_Gateway*` (couplé au service name, à traiter avec le rebrand service)
- SOUL.md content (`"You are Hermes Agent..."`) — persona utilisateur, distinct

### Hypothèses de la tranche 5

- La fonction de résolution centralisée s'appellera `get_indagis_home()` (équivalent Python de `get_hermes_home` côté `hermes_constants.py`).
- **Priorité** : `INDAGIS_HOME` env > `$env:LOCALAPPDATA\indagis` > `HERMES_HOME` env > `$env:LOCALAPPDATA\hermes`.
- **Version cible de suppression de l'alias** : à proposer dans le rapport — à cadrer avec la sortie de la Phase 5.

## Décision requise

- Validation de la grille de classification (identique à install.sh) ;
- Validation de la liste des sites critiques (16 points) ;
- Validation de la liste des sites équivalents aux écritures .zshrc install.sh (7 points SetEnvironmentVariable) ;
- Validation de la liste DEFER (12 entrées) ;
- Validation du périmètre de la cartographie (install.ps1 seul) avant alignement avec install.sh / node-bootstrap.sh.
