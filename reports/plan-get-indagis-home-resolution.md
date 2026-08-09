# Plan — fonction de résolution centralisée `get_indagis_home()` (3 versions en parallèle)

> **Statut** : proposition pour validation. Aucun fichier source touché. Cette proposition est la **suite de la Tranche 1 (contrat installeur)** du brief 2026-08-08, point 3 : « Une fois 1 et 2 validés séparément : proposer, sans l'appliquer, une fonction de résolution centralisée (bash) équivalente à get_hermes_home()/display_hermes_home() côté Python, à insérer aux points identifiés en 338/345 (install.ps1) et aux points équivalents d'install.sh. Un seul fichier à la fois, diff soumis avant commit. »
>
> **Note nomenclature** : le nom de fichier historique `plan-get-indagis-home-3-versions.md` fait référence aux **3 versions d'implémentation** (Python, bash, PowerShell) — pas à un numéro de tranche. Le terme « Tranche 3 » est réservé à l'issue #8 (gateway.py, remap systemd non-root), hors périmètre de ce travail.

> **Note 2026-08-08** : la vérification de la fonction Python existante (hermes_constants.py:114) montre qu'elle est en mode "Indagis-only" (override contextuel → INDAGIS_HOME env → default plateforme), **sans repli sur HERMES_HOME / ~/.hermes**. La fonction de test `get_real_home()` à L876 est distincte (elle retourne le home du user OS, pas le home Indagis). **Aucune des 3 versions (Python, bash, PowerShell) n'a la double lecture avec repli aujourd'hui.** La consigne du brief 2026-08-08 point 5 s'applique : « Écrire les trois en parallèle avec la même échelle de priorité. »

## Échelle de priorité (commune aux 3 versions)

| Priorité | Source | Comportement | Log/warning ? |
|---|---|---|---|
| 1 | `$INDAGIS_HOME` env var, si défini et non vide | Utiliser ce chemin. **CHEMIN PRIORITAIRE** | Non |
| 2 | `~/.indagis` (POSIX) ou `%LOCALAPPDATA%\indagis` (Windows), si existe | Utiliser ce chemin par défaut. **CHEMIN PRIORITAIRE par défaut** | Non |
| 3 | `$HERMES_HOME` env var, si défini et non vide (legacy alias) | Utiliser ce chemin. **REPLI** | **Oui** : warning explicite |
| 4 | `~/.hermes` (POSIX) ou `%LOCALAPPDATA%\hermes` (Windows), si existe (legacy alias) | Utiliser ce chemin. **REPLI** | **Oui** : warning explicite |
| 5 | (sinon) | Créer le chemin par défaut (priorité 2) | Non |

**Wording du warning** (identique dans les 3 versions) :

```
⚠ Indagis Agent: HERMES_HOME / ~/.hermes is used as a fallback. The deprecation
  alias will be removed in a future Indagis Agent release. Migrate by running:
    mv ~/.hermes ~/.indagis                                (Linux/macOS)
    move %LOCALAPPDATA%\hermes %LOCALAPPDATA%\indagis     (Windows, PowerShell)
  Then re-source your shell or restart the desktop app.
```

## Décision préalable au Draft 1 — A1 + B2 actées

### A1 — isolation des tests

Les tests de résolution emploieront la fixture pytest `monkeypatch` pour modifier les variables d’environnement, `Path.home()` et les helpers observés. Ils n’utiliseront pas `unittest.mock.patch` brut. Cette décision évite les restaurations manuelles et garantit le retour automatique à l’état initial à la fin de chaque test.

### B2 — cache context-local (cohérence de scope, pas optimisation)

**Portée réelle du cache** : `_INDAGIS_HOME_CACHE` est un mécanisme de **cohérence intra-scope avec override actif**. Il garantit que, pendant toute la durée d'un `_profile_runtime_scope`, plusieurs lectures successives de `get_indagis_home()` observent la **même** valeur de l'override, sans risque qu'un `_warn_*_once()` ou qu'une résolution partielle altère la valeur visible depuis un autre contexte concurrent.

Le cache **n'est PAS** un mécanisme de performance visant à éviter de relire `INDAGIS_HOME` / `HERMES_HOME` / `Path.exists()` aux 30+ sites d'import. Hors override, ces opérations sont déjà peu coûteuses (quelques `os.environ.get()` et un `Path.exists()` par appel), et cacher la résolution env-based se révèle **dangereux** : tout code qui mute `INDAGIS_HOME` ou `HERMES_HOME` via `monkeypatch.setenv` (les tests, mais aussi certains scénarios runtime) verrait ses changements ignorés tant que le cache n'est pas invalidé.

**Forme obligatoire** : `_INDAGIS_HOME_CACHE` est un `ContextVar` et non une variable globale de module, parce que le gateway multiplexé, les appels MCP et les sous-agents peuvent exécuter simultanément plusieurs contextes portant des overrides `_INDAGIS_HOME_OVERRIDE` différents dans un même processus.

**Contrat de B2 (formulation corrigée)** :

1. `_INDAGIS_HOME_CACHE` a pour valeur par défaut `_UNSET`.
2. `get_indagis_home()` ne consulte le cache **que lorsqu'un override est actif** (override `!= None`). Sans override, le cache est ignoré et la résolution ladder est re-parcourue à chaque appel.
3. Lorsque l'override est actif et que le cache est rempli (`!= _UNSET`), `get_indagis_home()` retourne la valeur cachée sans re-résolution.
4. Lorsque l'override est actif et que le cache est vide (`== _UNSET`), `get_indagis_home()` résout `Path(override)`, stocke le résultat dans le cache, et le retourne.
5. `set_indagis_home_override()` invalide `_INDAGIS_HOME_CACHE` en toute première instruction exécutable, avant la conversion de `path` et avant l'écriture de `_INDAGIS_HOME_OVERRIDE`.
6. `reset_indagis_home_override()` invalide `_INDAGIS_HOME_CACHE` en toute première instruction exécutable, avant le reset de `_INDAGIS_HOME_OVERRIDE`.
7. Le cache n'est jamais partagé entre deux contextes concurrents (ContextVar) et ne survit pas à une entrée ou à une sortie de scope de profil.

**Conséquence sur les appels sans override** (P1/P2/P3/P4/P5 du ladder) : `_INDAGIS_HOME_CACHE` est purement dormant. `_INDAGIS_HOME_CACHE.set(...)` n'est jamais appelé dans ce chemin, et `_INDAGIS_HOME_CACHE.get()` retourne toujours `_UNSET`. Toute mutation de `INDAGIS_HOME` ou `HERMES_HOME` est immédiatement visible au prochain appel de `get_indagis_home()`. C'est ce comportement qui a été validé par les tests de régression (notamment `TestGetHermesDir` dans `tests/test_hermes_constants.py`, qui mute `INDAGIS_HOME` via `monkeypatch.setenv` entre chaque test).

### Ordre réel sous `_profile_runtime_scope`

Le contrôle ne repose pas seulement sur l’ordre apparent de `gateway/run.py`. Un probe d’exécution instrumenté doit tracer les événements réels lors de l’entrée et de la sortie de `_profile_runtime_scope(profile_home)`. Le contrat attendu est :

```text
cache.invalidate
override.set
get_indagis_home.read
...
cache.invalidate
override.reset
get_indagis_home.read
```

À l’entrée, `gateway/run.py:1909` appelle `set_indagis_home_override()` avant `hydrate_profile_secret_sources()` et `build_profile_secret_scope()`, qui sont les premières opérations susceptibles d’entraîner des lectures de chemins profilés. L’invalidation doit donc apparaître avant toute lecture observée de `get_indagis_home()` dans le nouveau scope. À la sortie, l’invalidation doit précéder le rétablissement de l’override parent, afin que la première lecture revenue dans le scope parent soit également fraîche. Ce probe fera partie des tests du Draft 1.

#### Résultat du probe runtime (2026-08-09)

Script `/tmp/probe_profile_scope.py` qui monkey-patch `set_indagis_home_override`, `reset_indagis_home_override`, `get_indagis_home` et lit `_INDAGIS_HOME_CACHE.get()` après chaque appel pour vérifier l’invalidation effective. Sortie réelle (verbatim) :

```
=== import gateway.run ===
OK — _profile_runtime_scope importé.

=== Émission d'événements sous _profile_runtime_scope ===

set_indagis_home_override(path='/tmp/fake_probe_profile')
  cache_after(set)=UNSET
get_indagis_home.read
  -- inside scope: result=/tmp/fake_probe_profile
reset_indagis_home_override(token)
  cache_after(reset)=UNSET

=== Analyse ===
set_indagis_home_override à l'index 0
cache_after(set)=UNSET à l'index 1
premier get_indagis_home.read DANS scope à l'index 2

PREUVE 1 — invalidation enregistrée juste après set(): True
PREUVE 2 — cache UNSET avant la 1ère lecture dans le scope: True

reset_indagis_home_override à l'index 4
cache_after(reset)=UNSET à l'index 5
PREUVE 3 — invalidation enregistrée après reset(): True

=== Verdict ===
PASS — l'invalidation précède toute lecture dans _profile_runtime_scope.
```

Les 3 preuves sont vertes :
- **PREUVE 1** : juste après `set_indagis_home_override()`, le cache est bien revenu à `UNSET` (lignes 39 et 41 de `hermes_constants.py` exécutent `_INDAGIS_HOME_CACHE.set(_UNSET)` avant tout autre travail).
- **PREUVE 2** : la 1ère lecture de `get_indagis_home()` à l’intérieur du scope (index 2) est strictement postérieure à l’invalidation (index 1), donc le cache est nécessairement invalidé avant cette lecture.
- **PREUVE 3** : à la sortie du scope, `reset_indagis_home_override()` ré-invalide le cache, garantissant que la 1ère lecture revenue dans le scope parent sera également fraîche.

**Conclusion** : l’invalidation en première instruction de `set_indagis_home_override()` et `reset_indagis_home_override()` est confirmée par observation runtime, pas seulement par lecture du code. Le contrat B2 est tenu en pratique.

## Draft 1 — Python (`hermes_constants.py:114`)

**Fichier** : `hermes_constants.py`
**Sites d'insertion** : L62-74 (`_indagis_home_from_env`) et L114-139 (`get_indagis_home`)
**Stratégie** : la fonction Python est la source de vérité. Les versions bash/PowerShell doivent s'aligner sur elle.

**Helper `_indagis_home_from_env()` (L62-74)** :
```python
def _indagis_home_from_env() -> Path:
    val = os.environ.get("INDAGIS_HOME", "").strip()
    if val:
        return Path(val)
    return _get_platform_default_indagis_home()
```

**Helper `_warn_profile_fallback_once()` (L77-111)** — texte exact actuel :

```python
def _warn_profile_fallback_once() -> None:
    """Warn once when falling back to the default home while a profile is active.

    Guard: if a non-default profile is sticky-active but ``INDAGIS_HOME`` is
    unset, the fallback to the default profile is almost certainly wrong.
    """
    global _profile_fallback_warned
    if _profile_fallback_warned:
        return
    try:
        fallback_home = _get_platform_default_indagis_home()
        active_path = fallback_home / "active_profile"
        active = active_path.read_text(encoding="utf-8").strip() if active_path.exists() else ""
    except (UnicodeDecodeError, OSError):
        active = ""
    if active and active != "default":
        _profile_fallback_warned = True
        # Write directly to stderr.  We intentionally do NOT route this
        # through ``logging`` because (a) this function is called at
        # module-import time from 30+ sites, often before logging is
        # configured, and (b) root-logger propagation would double-emit
        # on consoles where a StreamHandler is already attached.
        msg = (
            f"[INDAGIS_HOME fallback] INDAGIS_HOME is unset but active "
            f"profile is {active!r}. Falling back to {fallback_home}, which "
            f"is the DEFAULT profile — not {active!r}. Any data this "
            f"process writes will land in the wrong profile. The "
            f"subprocess spawner should pass INDAGIS_HOME explicitly "
            f"(see issue #18594)."
        )
        try:
            sys.stderr.write(msg + "\n")
            sys.stderr.flush()
        except Exception:
            pass
```

**Analyse du non-chevauchement avec `_warn_legacy_alias_in_use_once()` (proposé)** :

Les 2 warnings ont des déclencheurs **sémantiquement distincts** :

| Warning | Déclencheur | Cible d'écriture | But |
|---|---|---|---|
| `_warn_profile_fallback_once()` (existant) | `INDAGIS_HOME` non défini ET profil non-default actif | `sys.stderr` | Alerter que les données vont dans le mauvais profil (problème d'alignement profile) |
| `_warn_legacy_alias_in_use_once()` (proposé) | Résolution via priorité 3-4 (legacy alias `$HERMES_HOME` / `~/.hermes`) | `sys.stderr` | Alerter que l'utilisateur utilise un alias à migrer (problème de migration) |

**Cas où les 2 warnings peuvent se déclencher simultanément** (P3 + profil non-default) : **bruit visuel pour l'utilisateur**.

**Décision actée** : `_warn_profile_fallback_once()` est **désactivé** quand la résolution vient des priorités 3-4 (legacy alias). Justification : dans ce cas, l'utilisateur a un problème de migration à régler d'abord (legacy alias) — le warning profile-fallback est moins urgent et créerait du bruit. Le warning legacy-alias (priorité 3-4) reste émis en priorité. C'est un seul warning par run, le plus utile en premier.

**Implémentation** : `get_indagis_home()` réécrit skippe l'appel à `_warn_profile_fallback_once()` (L137) quand la résolution vient de la branche legacy (priorités 3-4). Les priorités 1-2-5 conservent l'appel existant. Voir le Draft 1 plus bas.

```python
# Nouvelle fonction helper, à insérer après _indagis_home_from_env (L74)

def _indagis_home_from_legacy_alias() -> Path | None:
    """Return the legacy Indagis home directory, or None if no legacy alias exists.

    Used by :func:`get_indagis_home` to implement the deprecation-window
    fallback (priorities 3 and 4 of the path-resolution ladder). Returns
    ``$HERMES_HOME`` if set and non-empty, else ``~/.hermes`` /
    ``%LOCALAPPDATA%\\hermes`` if that path exists, else ``None``.

    This helper does NOT issue the deprecation warning — the caller is
    responsible (so the warning is emitted exactly once per process).
    """
    val = os.environ.get("HERMES_HOME", "").strip()
    if val:
        return Path(val)
    platform_default = _get_platform_default_indagis_home()
    # platform_default returns the Indagis default. The legacy equivalent
    # is the same platform-native location under the Hermes name:
    legacy_default = _legacy_home_from_platform_default(platform_default)
    if legacy_default and legacy_default.exists():
        return legacy_default
    return None


def _legacy_home_from_platform_default(indagis_default: Path) -> Path:
    """Translate an Indagis platform default into its Hermes-era equivalent.

    Indagis default is ``~/.indagis`` on POSIX / ``%LOCALAPPDATA%\\indagis`` on
    Windows. The legacy Hermes equivalent is the same path with the last
    component replaced by ``hermes``.
    """
    return indagis_default.parent / "hermes"


def _warn_legacy_alias_in_use_once() -> None:
    """Emit the deprecation-window warning exactly once per process.

    Mirrors the wording in apps/desktop/README.md's "Path resolution"
    section. Writes to stderr (not the user-facing log) to keep the
    warning visible without polluting machine logs.
    """
    msg = (
        "\n⚠ Indagis Agent: HERMES_HOME / ~/.hermes is used as a fallback. "
        "The deprecation\n"
        "  alias will be removed in a future Indagis Agent release. "
        "Migrate by running:\n"
        "    mv ~/.hermes ~/.indagis                                "
        "(Linux/macOS)\n"
        "    move %LOCALAPPDATA%\\hermes %LOCALAPPDATA%\\indagis     "
        "(Windows, PowerShell)\n"
        "  Then re-source your shell or restart the desktop app.\n"
    )
    try:
        sys.stderr.write(msg)
        sys.stderr.flush()
    except Exception:
        pass


# Fonction get_indagis_home() réécrite (L114-139)

def get_indagis_home() -> Path:
    """Return the Indagis home directory.

    Resolution order (path-resolution ladder, see apps/desktop/README.md
    "Compat-contract notes" — Path resolution section):

    1. ``$INDAGIS_HOME`` env var, if set and non-empty
    2. ``~/.indagis`` (POSIX) or ``%LOCALAPPDATA%\\indagis`` (Windows), if it exists
    3. ``$HERMES_HOME`` env var, if set and non-empty (legacy alias, deprecation warning)
    4. ``~/.hermes`` (POSIX) or ``%LOCALAPPDATA%\\hermes`` (Windows), if it exists (legacy alias, deprecation warning)
    5. Create the platform default ``~/.indagis`` / ``%LOCALAPPDATA%\\indagis``

    The context-local override set by :func:`set_indagis_home_override` (used
    by tests and profile-scoped code) takes precedence over all of the above
    and is checked first.

    When the resolved path comes from priority 3 or 4 (legacy alias), the
    deprecation warning is emitted to stderr exactly once per process.
    """
    override = get_indagis_home_override()
    if override:
        return Path(override)

    # Track whether we resolved via a legacy alias (priorities 3-4). When
    # True, we skip the profile-fallback warning to avoid emitting two
    # warnings simultaneously: the legacy-alias migration message is
    # strictly more actionable than the profile-misalignment message.
    resolved_via_legacy_alias = False

    val = os.environ.get("INDAGIS_HOME", "").strip()
    if val:
        # Priority 1: explicit env var, no warning
        return _indagis_home_from_env()

    platform_default = _get_platform_default_indagis_home()
    if platform_default.exists():
        # Priority 2: new default exists, profile-fallback warning may fire
        if not os.environ.get("INDAGIS_HOME", "").strip():
            _warn_profile_fallback_once()
        return platform_default

    legacy = _indagis_home_from_legacy_alias()
    if legacy is not None:
        # Priority 3 or 4: legacy alias. Emit the deprecation warning
        # once; skip the profile-fallback warning to avoid noise.
        resolved_via_legacy_alias = True
        _warn_legacy_alias_in_use_once()
        return legacy

    # Priority 5: create new default (do not create; let the caller decide
    # whether to mkdir). Same behavior as the current implementation —
    # the platform default is returned even if it doesn't exist yet.
    # The profile-fallback warning may still fire if a non-default
    # profile is sticky-active and we fell back to the platform default.
    if not resolved_via_legacy_alias and not os.environ.get("INDAGIS_HOME", "").strip():
        _warn_profile_fallback_once()
    return platform_default
```

**Modifications de cohérence** :
- `display_indagis_home()` à L779 : la docstring dit « default: `~/.hermes` » (L784). À mettre à jour : « default: `~/.indagis` (legacy alias: `~/.hermes` during deprecation window) ».
- Le test qui couvre `get_indagis_home()` doit être étendu pour tester les 5 priorités (cf. section "Tests de non-régression" plus bas).

**Sites d'insertion** :
- Nouvelles fonctions `_indagis_home_from_legacy_alias()`, `_legacy_home_from_platform_default()`, `_warn_legacy_alias_in_use_once()` : après `_indagis_home_from_env()` (L74) ou après la zone `_warn_profile_fallback_once()` (L77-111).
- `get_indagis_home()` : L114-139 (réécriture complète de la fonction).

## Draft 2 — Bash (`scripts/install.sh:48`)

**Fichier** : `scripts/install.sh`
**Site d'insertion** : L48 (où `HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"` est actuellement initialisé).
**Stratégie** : remplacer la ligne L48 par une fonction `get_indagis_home()` que tous les sites ultérieurs peuvent appeler.

```bash
# Nouvelle fonction helper, à insérer avant detect_os() (L503) ou après les
# variables globales (L67). Proposition : après install_uv() ou avant
# resolve_install_layout().

# === Centralized path resolution: get_indagis_home() ===
# Mirrors the Python function hermes_constants.get_indagis_home() — see
# apps/desktop/README.md "Compat-contract notes" for the policy.
#
# Resolution order:
#   1. $INDAGIS_HOME env var, if set and non-empty
#   2. $HOME/.indagis (POSIX) or $LOCALAPPDATA\indagis (Windows Git Bash), if it exists
#   3. $HERMES_HOME env var, if set and non-empty  (legacy alias — emits warning)
#   4. $HOME/.hermes (POSIX) or $LOCALAPPDATA\hermes (Windows), if it exists  (legacy alias — emits warning)
#   5. Otherwise: create $HOME/.indagis (POSIX) or $LOCALAPPDATA\indagis (Windows)
#
# The function is cached: subsequent calls return the same value within
# the same process.
#
# Returns the absolute path to the Indagis home directory. Also sets the
# global $HERMES_HOME and $INDAGIS_HOME variables (legacy + new) so existing
# call sites that read $HERMES_HOME keep working during the deprecation
# window.

_INDAGIS_HOME_LEGACY_WARNED=0

get_indagis_home() {
    # Honor a previously-resolved value (cached).
    if [ -n "${_INDAGIS_HOME:-}" ]; then
        echo "$_INDAGIS_HOME"
        return 0
    fi

    # Priority 1: $INDAGIS_HOME env var
    if [ -n "${INDAGIS_HOME:-}" ]; then
        _INDAGIS_HOME="$INDAGIS_HOME"
        echo "$_INDAGIS_HOME"
        return 0
    fi

    # Priority 2: $HOME/.indagis (POSIX) or $LOCALAPPDATA\indagis (Windows Git Bash)
    if [ -n "${HOME:-}" ] && [ -d "$HOME/.indagis" ]; then
        _INDAGIS_HOME="$HOME/.indagis"
        echo "$_INDAGIS_HOME"
        return 0
    fi
    if [ -n "${LOCALAPPDATA:-}" ] && [ -d "$LOCALAPPDATA/indagis" ]; then
        _INDAGIS_HOME="$LOCALAPPDATA/indagis"
        echo "$_INDAGIS_HOME"
        return 0
    fi

    # Priority 3: $HERMES_HOME env var (legacy alias — emit warning)
    if [ -n "${HERMES_HOME:-}" ]; then
        _INDAGIS_HOME="$HERMES_HOME"
        _warn_indagis_home_legacy_used
        echo "$_INDAGIS_HOME"
        return 0
    fi

    # Priority 4: $HOME/.hermes (POSIX) or $LOCALAPPDATA\hermes (Windows) (legacy alias)
    if [ -n "${HOME:-}" ] && [ -d "$HOME/.hermes" ]; then
        _INDAGIS_HOME="$HOME/.hermes"
        _warn_indagis_home_legacy_used
        echo "$_INDAGIS_HOME"
        return 0
    fi
    if [ -n "${LOCALAPPDATA:-}" ] && [ -d "$LOCALAPPDATA/hermes" ]; then
        _INDAGIS_HOME="$LOCALAPPDATA/hermes"
        _warn_indagis_home_legacy_used
        echo "$_INDAGIS_HOME"
        return 0
    fi

    # Priority 5: create the default. The function returns the path even
    # if it does not exist yet — the caller is expected to mkdir -p as
    # needed (see copy_config_templates L1924 and setup_venv L1400).
    if [ -n "${LOCALAPPDATA:-}" ] && [[ "$(uname -s)" == "CYGWIN"* || "$(uname -s)" == "MINGW"* || "$(uname -s)" == "MSYS"* ]]; then
        _INDAGIS_HOME="$LOCALAPPDATA/indagis"
    else
        _INDAGIS_HOME="${HOME:-.}/.indagis"
    fi
    echo "$_INDAGIS_HOME"
    return 0
}

_warn_indagis_home_legacy_used() {
    if [ "$_INDAGIS_HOME_LEGACY_WARNED" = "1" ]; then
        return 0
    fi
    _INDAGIS_HOME_LEGACY_WARNED=1
    # IMPORTANT: this warning goes to STDERR (>&2), not stdout. The function
    # `get_indagis_home()` above uses `echo "$path"` on stdout so callers
    # can capture the resolved path via $(get_indagis_home). If the
    # warning were on stdout, it would be captured as part of the path
    # string and break every call site that uses $(get_indagis_home).
    # Redirecting to stderr (cat >&2 <<'EOF') keeps stdout clean for
    # capture while still surfacing the warning to the user. The
    # here-document uses single-quoted 'EOF' to suppress shell variable
    # expansion inside the warning text.
    cat >&2 <<'EOF'

⚠ Indagis Agent: HERMES_HOME / ~/.hermes is used as a fallback. The deprecation
  alias will be removed in a future Indagis Agent release. Migrate by running:
    mv ~/.hermes ~/.indagis                                (Linux/macOS)
    move %LOCALAPPDATA%\hermes %LOCALAPPDATA%\indagis     (Windows, PowerShell)
  Then re-source your shell or restart the desktop app.
EOF
}

# Remplacement de la ligne L48 d'origine:
#   HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
# par:
HERMES_HOME="${HERMES_HOME:-$(get_indagis_home)}"
INDAGIS_HOME="${INDAGIS_HOME:-$HERMES_HOME}"
export HERMES_HOME INDAGIS_HOME
```

**Sites d'appel à mettre à jour** : tous les sites de `install.sh` qui lisent `$HERMES_HOME` continuent à fonctionner (la variable est exportée). Idem pour `$INDAGIS_HOME`. Le `setup_path` (L1697-1918), `copy_config_templates` (L1920-1991), `maybe_start_gateway` (L3736-3812), etc. fonctionnent sans modification.

**Test de non-régression** : `bash -c 'source scripts/install.sh; echo $HERMES_HOME'` (sans install complet) doit résoudre au moins les priorités 1-2-5.

## Draft 3 — PowerShell (`scripts/install.ps1:32-33`)

**Fichier** : `scripts/install.ps1`
**Sites d'insertion** : L32-33 (param block `$HermesHome` et `$InstallDir`) + L334-347 (réécriture post-normalisation 8.3).
**Stratégie** : remplacer la résolution inline par une fonction `Get-IndagisHome` (analogue à `Get-LongProfileRoot` à L166).

```powershell
# Nouvelle fonction helper, à insérer après Get-LongProfileRoot (L213) ou
# avant ConvertTo-LongPath (L245).

$script:IndagisHomeLegacyWarned = $false

function Get-IndagisHome {
    <#
    .SYNOPSIS
    Resolve the Indagis home directory using the deprecation-window ladder.

    .DESCRIPTION
    Mirrors the Python function hermes_constants.get_indagis_home() and
    the bash get_indagis_home() in scripts/install.sh. Resolution order:

    1. $env:INDAGIS_HOME, if set and non-empty
    2. $HOME\.indagis (POSIX via Git Bash) or $env:LOCALAPPDATA\indagis (Windows), if it exists
    3. $env:HERMES_HOME, if set and non-empty  (legacy alias — emits warning)
    4. $HOME\.hermes (POSIX) or $env:LOCALAPPDATA\hermes (Windows), if it exists  (legacy alias — emits warning)
    5. Otherwise: return the platform default $HOME\.indagis or $env:LOCALAPPDATA\indagis

    The function is cached: subsequent calls return the same value within
    the same process. The deprecation warning is emitted exactly once per
    process when the resolved path comes from priority 3 or 4.
    #>

    # Honor a previously-resolved value (cached)
    if ($script:IndagisHome -and (Test-Path -LiteralPath $script:IndagisHome)) {
        return $script:IndagisHome
    }

    # Priority 1: $env:INDAGIS_HOME
    $envIndagisHome = $env:INDAGIS_HOME
    if ($envIndagisHome -and $envIndagisHome.Trim()) {
        $script:IndagisHome = $envIndagisHome.Trim()
        return $script:IndagisHome
    }

    # Determine platform: Windows uses %LOCALAPPDATA%, POSIX (Git Bash) uses $HOME
    $isWindows = $env:OS -eq "Windows_NT"

    # Priority 2: $HOME\.indagis or $env:LOCALAPPDATA\indagis
    $platformDefault = $null
    if ($isWindows) {
        $localAppData = [Environment]::GetEnvironmentVariable("LOCALAPPDATA", "User")
        $platformDefault = Join-Path $localAppData "indagis"
    } else {
        $home = $env:HOME
        $platformDefault = Join-Path $home ".indagis"
    }
    if ($platformDefault -and (Test-Path -LiteralPath $platformDefault)) {
        $script:IndagisHome = $platformDefault
        return $script:IndagisHome
    }

    # Priority 3: $env:HERMES_HOME (legacy alias)
    $envHermesHome = $env:HERMES_HOME
    if ($envHermesHome -and $envHermesHome.Trim()) {
        $script:IndagisHome = $envHermesHome.Trim()
        Write-IndagisHomeLegacyWarning
        return $script:IndagisHome
    }

    # Priority 4: $HOME\.hermes or $env:LOCALAPPDATA\hermes (legacy alias)
    $legacyDefault = $null
    if ($isWindows) {
        $legacyDefault = Join-Path $localAppData "hermes"
    } else {
        $legacyDefault = Join-Path $home ".hermes"
    }
    if ($legacyDefault -and (Test-Path -LiteralPath $legacyDefault)) {
        $script:IndagisHome = $legacyDefault
        Write-IndagisHomeLegacyWarning
        return $script:IndagisHome
    }

    # Priority 5: return the platform default (caller decides to mkdir)
    $script:IndagisHome = $platformDefault
    return $script:IndagisHome
}

function Write-IndagisHomeLegacyWarning {
    if ($script:IndagisHomeLegacyWarned) { return }
    $script:IndagisHomeLegacyWarned = $true
    Write-Host @"

⚠ Indagis Agent: HERMES_HOME / ~/.hermes is used as a fallback. The deprecation
  alias will be removed in a future Indagis Agent release. Migrate by running:
    mv ~/.hermes ~/.indagis                                (Linux/macOS)
    move %LOCALAPPDATA%\hermes %LOCALAPPDATA%\indagis     (Windows, PowerShell)
  Then re-source your shell or restart the desktop app.
"@ -ForegroundColor Yellow
}

# Remplacement des L32-33 d'origine:
#   [string]$HermesHome = $(if ($env:HERMES_HOME) { $env:HERMES_HOME } else { "$env:LOCALAPPDATA\hermes" }),
#   [string]$InstallDir = $(if ($env:HERMES_HOME) { "$env:HERMES_HOME\hermes-agent" } else { "$env:LOCALAPPDATA\hermes\hermes-agent" }),
# par:
[string]$HermesHome = $(Get-IndagisHome),
[string]$IndagisHome = $(Get-IndagisHome),
[string]$InstallDir = $(if ($HermesHome) { Join-Path $HermesHome "hermes-agent" } else { "" }),

# Et le bloc L334-347 (réécriture post-normalisation 8.3):
if ($PSBoundParameters.ContainsKey('HermesHome')) {
    $HermesHome = ConvertTo-LongPath $HermesHome
} else {
    $HermesHome = ConvertTo-LongPath (Get-IndagisHome)
}
if ($PSBoundParameters.ContainsKey('IndagisHome')) {
    $IndagisHome = ConvertTo-LongPath $IndagisHome
}
$InstallDir = ConvertTo-LongPath (Join-Path $HermesHome "hermes-agent")
```

**Sites d'appel à mettre à jour** : tous les sites qui lisent `$HermesHome` continuent à fonctionner (la variable est settée). Le test `scripts/ci/test_install_ps1_path_migration.ps1` continue à fonctionner car il teste `Set-ManagedNodeFirstOnUserPath` (orthogonal).

**Test de non-régression** : `pwsh -NoProfile -File scripts/install.ps1 -ShowResolvedPaths` doit retourner le bon chemin selon la priorité applicable.

## Tests de non-régression

Pour les 3 versions, ajouter 5 tests minimum (un par priorité). Les tests doivent couvrir à la fois le **setup d'environnement** (variables d'env) et le **mock filesystem** (existence de `~/.indagis`, `~/.hermes`).

| Test | Setup env | Mock filesystem (`Path.exists()`) | Expected | Warning capturé ? |
|---|---|---|---|---|
| **P1** | `INDAGIS_HOME=/tmp/custom` | n/a (P1 ignore le filesystem) | `get_indagis_home() == /tmp/custom` | Non |
| **P2** | `INDAGIS_HOME` non défini | `~/.indagis.exists() == True` | `get_indagis_home() == ~/.indagis` | Non |
| **P3** | `HERMES_HOME=/tmp/legacy`, `INDAGIS_HOME` non défini | `~/.indagis.exists() == False`, `~/.hermes` n'a pas besoin d'exister (P3 utilise l'env var) | `get_indagis_home() == /tmp/legacy` | **Oui** (stderr/stdout selon version) |
| **P4** | `INDAGIS_HOME` non défini, `HERMES_HOME` non défini | `~/.indagis.exists() == False`, `~/.hermes.exists() == True` | `get_indagis_home() == ~/.hermes` | **Oui** |
| **P5** | Aucun env | `~/.indagis.exists() == False`, `~/.hermes.exists() == False` | `get_indagis_home() == ~/.indagis` (default, ne crée pas le dossier) | Non (mais profile-fallback peut fire si profil non-default actif) |

**Channel de warning par version** (cohérence entre les 3 versions) :

| Version | Channel de warning | Justification | Test de capture |
|---|---|---|---|
| **Python** | `sys.stderr.write` (stderr) | Identique à `_warn_profile_fallback_once()` existant. Pas de pollution du `Path` retourné. | `capsys` (pytest fixture) ou `capfd` |
| **Bash** | `cat >&2 <<'EOF'` (stderr) | Le path est retourné via `echo "$path"` sur stdout, capturable par `$(get_indagis_home)`. Le warning sur stderr ne pollue pas la capture (cf. note explicite dans le code). | `bash -c '... 2>err.log; grep "Indagis Agent" err.log'` |
| **PowerShell** | `Write-Host -ForegroundColor Yellow` (stdout, mais via pipeline dédié) | PowerShell n'a pas de `Write-Error` non-bloquant dans ce contexte. Le warning est visible par l'utilisateur mais ne corrompt pas le path retourné (la fonction retourne via `return $script:IndagisHome`). | `pwsh -c '... 2>&1 | Select-String "Indagis Agent"'` |

**Mock `Path.exists()` Python** (tâche 4) : utiliser `unittest.mock.patch` sur `pathlib.Path.exists` ou mocker `_get_platform_default_indagis_home()` et `_indagis_home_from_legacy_alias()` directement. Le mock `Path.exists()` est **nécessaire en plus des variables d'environnement** car :
- `P2` : le path est résolu via `platform_default.exists()` → le mock doit retourner `True` pour `~/.indagis`
- `P4` : le path est résolu via `legacy_default.exists()` (où `legacy_default = _legacy_home_from_platform_default(platform_default)`) → le mock doit retourner `True` pour `~/.hermes`
- `P5` : tous les `.exists()` retournent `False` → le path retourné est `platform_default` (qui n'existe pas en mémoire)

Exemple de mock Python pour P2 :

```python
def test_priority_2_default_exists(self, monkeypatch, tmp_path):
    """P2: ~/.indagis exists, INDAGIS_HOME unset → returns ~/.indagis, no warning."""
    monkeypatch.delenv("INDAGIS_HOME", raising=False)
    monkeypatch.delenv("HERMES_HOME", raising=False)
    indagis_dir = tmp_path / ".indagis"
    indagis_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    # Path.exists() returns True for ~/.indagis, False for everything else
    real_exists = Path.exists
    def mock_exists(self):
        return real_exists(self) or str(self) == str(indagis_dir)
    monkeypatch.setattr(Path, "exists", mock_exists)
    
    with warnings.catch_warnings(record=True) as w:
        result = get_indagis_home()
    
    assert result == indagis_dir
    # No legacy-alias warning
    assert not any("deprecation" in str(warning.message).lower() for warning in w)
```

**Python** : `tests/hermes_cli/test_hermes_constants_path_migration.py` (nouveau fichier, ~5 tests, ~150 lignes).
**Bash** : `tests/scripts/test_install_sh_path_migration.sh` (nouveau fichier, utilise `mktemp -d` pour créer/détruire des fixtures, ~80 lignes).
**PowerShell** : `scripts/ci/test_install_ps1_path_migration.ps1` (extension du fichier existant ; ajout de 5 cas en plus des 13 cas existants de migration de l'ordre PATH, ~+80 lignes).

## Plan d'application (parcours de validation)

1. **Appliquer Draft 1 (Python)** : éditer `hermes_constants.py`. Tester localement (cf. tests ci-dessus). Commit isolé.
2. **Appliquer Draft 2 (Bash)** : éditer `install.sh` (L48 + L503-... pour la fonction helper). Tester. Commit isolé.
3. **Appliquer Draft 3 (PowerShell)** : éditer `install.ps1` (L32-33 + L213-... pour la fonction helper). Tester. Commit isolé.
4. **Étendre le test AST** `scripts/ci/test_install_ps1_path_migration.ps1` pour couvrir les 5 priorités. Commit isolé.
5. **Créer `tests/hermes_cli/test_hermes_constants_path_migration.py`** pour Python. Commit isolé.
6. **Créer `tests/scripts/test_install_sh_path_migration.sh`** pour Bash. Commit isolé.
7. **Merger les 3 sur la branche `feat/rebranding`** : 6 commits atomiques au total.

Conformément à la convention de la branche : **un commit par fichier, validation lecture-par-lecture, push après tous les commits green**.

## Hors scope de cette proposition

- La migration effective des installations existantes (mv / move) — c'est un changement côté utilisateur, pas code.
- Le rebrand de `get_hermes_home()` / `get_real_home()` (ces noms ne sont plus dans le code ; les helpers sont déjà en mode "Indagis-only").
- Le rebrand du fichier `hermes_constants.py` lui-même → `indagis_constants.py`. C'est une autre tranche (impacte 100+ imports, c'est un rebrand de package Python).
- L'implémentation du `set_indagis_home_override()` côté Python (déjà implémenté, c'est juste un contexte de test).

## Statut d'ouverture

**OUVERT — à programmer en tranche dédiée** après validation de ce plan + des 3 drafts. Conformément à la consigne 5 du brief 2026-08-08, l'application se fera **un fichier à la fois, avec diff soumis avant commit** pour chaque fichier (Python, bash, PowerShell, et les 3 fichiers de test).

## Rapport Draft 2 — Bash (2026-08-09)

### Implémentation effective

- **`scripts/install_helpers.sh`** (NOUVEAU, ~140 lignes) — contient `resolve_indagis_home()` + helpers. Source-able par install.sh et par les tests.
- **`scripts/install.sh`** (MODIFIÉ, L48-58) — remplace `HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"` par un appel à `resolve_indagis_home` via le helper.
- **`tests/scripts/test_install_helpers_home_resolution.sh`** (NOUVEAU) — 8 tests bash (5 priorités + stdout purity + warning-once + stderr canal).

### Contrat stdout/stderr — confirmation explicite

Le warning de dépréciation legacy (P3/P4) est émis sur **stderr (`>&2`)** exclusivement. Le path résolu est émis sur **stdout** exclusivement. Vérification runtime :

```bash
$ env -i HOME=/tmp/foo USERPROFILE=/tmp/foo LOCALAPPDATA="" bash -c \
    "mkdir -p /tmp/foo/.hermes; source scripts/install_helpers.sh; \
     resolved=\"\$(resolve_indagis_home)\"; echo \"captured: \$resolved\""
captured: /tmp/foo/.hermes        ← stdout propre
⚠ Indagis Agent: ~/.hermes (/tmp/foo/.hermes) is used as a fallback.
  The deprecation alias will be removed in a future Indagis Agent release.
  Migrate by running:
    mv ~/.hermes ~/.indagis
  Then re-source your shell or restart the desktop app.    ← stderr séparé
```

Tout appelant qui capture `$(resolve_indagis_home)` reçoit **uniquement** le path, sans contamination. C'est la garantie testée par les 2 tests "stdout stays clean" / "stdout is exactly the resolved path".

### Pourquoi un fichier helper séparé (et non inline dans install.sh)

`install.sh` est un script de 3370 lignes avec une structure de fonctions longues. Tester `resolve_indagis_home` directement nécessiterait soit : (a) sourcer tout install.sh dans chaque test (lourd, charge de nombreux helpers), soit (b) extraire la fonction dans un fichier source-able léger. L'option (b) garde la fonction pure (pas de side-effects au source), testable en isolation, et réutilisable depuis d'autres scripts à venir.

### TDD discipline observée

1. Tests bash écrits d'abord, ciblant le comportement CIBLE.
2. Helper `install_helpers.sh` implémenté.
3. Tests exécutés : **7 fails / 1 pass** au premier essai (erreurs de harness — `;` en trop quand env_setup vide, sortie non capturée par $(), $TEST_TMP non interpolé dans le subshell).
4. Harness corrigé, fonction validée : **8/8 verts**.
5. `install.sh` branché sur le helper, syntax `bash -n` OK, `--help` rendu inchangé.
6. Régression check : `tests/test_install_sh_install_method_stamp.py`, `tests/test_install_no_initial_commit.py`, `tests/test_install_unmerged_index.py`, `tests/test_install_ps1_ascii_only.py` → **4/4 verts**.

### Différences vs spec initiale du plan

- **Pas de cache process-global** : la fonction relit l'env à chaque appel, contrairement au draft Python (qui cache pour la cohérence intra-scope). Raison : bash n'a pas d'équivalent direct aux `ContextVar` ; un cache global bash (`_INDAGIS_HOME=`) survivrait aux entrées de scope mais perdrait l'invalidation automatique dont bénéficie Python. **Décision** : pas de cache en bash. Le coût de relecture (5 `test -d` / `${VAR:-}`) est négligeable.

- **L48 — substitution inline plutôt que déclaration séparée** : le helper est appelé dans la commande de substitution `$(...)` directement à L48, pas dans une fonction dédiée d'install.sh. Raison : `install.sh` est lu top-to-bottom, la variable `HERMES_HOME` doit être définie tôt pour que le parser d'arguments L150+ puisse la voir. *Note : ce point a été révisé en Draft 2.1 — voir section dédiée ci-dessous.*

## Rapport Draft 2.1 — Contrat de pureté du résolveur (2026-08-09)

### Bug identifié

Le Draft 2 livrait `resolve_indagis_home()` avec le warning de dépréciation legacy émis **à l'intérieur** de la fonction (P3 + P4). Reproduction factuelle du bug, capturée dans `tests/scripts/test_install_helpers_home_resolution.sh` :

```
Scenario install.sh L48-55 :
  1. Orchestrateur fire le warning explicitement  →  1 fire
  2. resolved1=$(resolve_indagis_home)            →  1 fire (BUG)
  3. resolved2=$(resolve_indagis_home)            →  1 fire (BUG)
  Total : 3 fires attendus avant fix, 1 attendu après fix.
```

Le warning est répété à chaque `$(resolve_indagis_home)` parce que **chaque substitution de commande spawn un subshell frais**, dont les variables sont invisibles au shell parent et aux subshells successeurs. Le guard `_INDAGIS_LEGACY_ALIAS_WARNED` à l'intérieur de la fonction est reset à chaque appel.

### Solution prescrite dans le brief (NON retenue)

Le brief proposait : geler `_INDAGIS_USER_HERMES_HOME="${HERMES_HOME:-}"` avant la 1ère capture, et faire lire P3 sur cette variable figée.

**Test factuel** : cette approche ne résout PAS le bug. J'ai rejoué le scénario avec ce design, et le warning continuait à firer à chaque `$(...)` capture. Raison : la variable figée est dans le shell parent ; les subshells `$(...)` en héritent par export, mais ne peuvent pas la modifier pour signaler aux appels suivants "warning déjà émis". Le problème est sur le **guard** (doit survivre aux subshells), pas sur la **valeur lue par P3**.

### Solution retenue — contrat de pureté du résolveur

Le résolveur `resolve_indagis_home()` est désormais une **fonction pure** : elle retourne le chemin résolu sur stdout et n'émet **jamais** rien sur stderr. Le warning de dépréciation est déplacé vers **l'orchestrateur** (`install.sh` L48-55), qui le fire explicitement une fois avant toute capture `$(...)`.

**Contrat formel** (à respecter par tout futur appelant du helper) :

1. `resolve_indagis_home()` ne fait JAMAIS `>&2` (aucun side-effect sur stderr).
2. Toute décision d'émettre un avertissement utilisateur est de la responsabilité de l'appelant.
3. Si l'appelant veut informer l'utilisateur du fallback legacy, il doit :
   - détecter lui-même la condition (P3 : `$HERMES_HOME` set, P4 : `~/.hermes` existe),
   - appeler `_indagis_warn_legacy_alias_in_use_once "..." "..."` une seule fois,
   - **puis** capturer `$(resolve_indagis_home)` pour la valeur.
4. Le warning n'est jamais émis depuis un subshell `$(...)` — toujours depuis le shell orchestrateur.

**Avantages** :

- Le warning est émis **une seule fois par invocation** de l'orchestrateur, indépendamment du nombre de captures `$(...)`.
- Le résolveur est testable en isolation, sans side-effect polluant.
- La logique "décider d'informer l'utilisateur" reste explicite et lisible dans l'orchestrateur.

**Inconvénient** :

- Duplication apparente de la logique de détection P3/P4 dans l'orchestrateur (l'orchestrateur doit savoir si P3 ou P4 s'applique pour décider d'émettre le warning, sans appeler le résolveur — sinon on retombe dans le bug).

### Implémentation effective

**`scripts/install_helpers.sh`** (+32/-7) : P3 et P4 retirent leur appel à `_indagis_warn_legacy_alias_in_use_once`. Commentaire détaillé ajouté au-dessus de chaque bloc expliquant pourquoi le warning n'est plus là.

**`scripts/install.sh`** (+18/-1) : source le helper une fois, fire le warning explicitement avant la 1ère capture :

```bash
_SCRIPT_DIR_HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$_SCRIPT_DIR_HERE/install_helpers.sh"
if [ -n "${HERMES_HOME:-}" ]; then
    _indagis_warn_legacy_alias_in_use_once "HERMES_HOME" "$HERMES_HOME"
elif [ -d "${HOME:-}/.hermes" ]; then
    _indagis_warn_legacy_alias_in_use_once "~/.hermes" "${HOME}/.hermes"
fi
HERMES_HOME="$(resolve_indagis_home)"
export HERMES_HOME
```

**`tests/scripts/test_install_helpers_home_resolution.sh`** : refonte des tests P3/P4 (le warning n'est plus dans la fonction, donc stderr doit être vide à l'appel du résolveur) + nouveau test "warning fires exactly once" qui wrappe `_indagis_warn_legacy_alias_in_use_once` avec un compteur fichier (pour compter les invocations à travers les subshells, là où les variables shell ne traversent pas).

### TDD discipline observée

1. **Test ROUGE avant fix** : P3 + P4 firent toujours le warning → compteur = 3 (1 orchestrateur + 2 captures) → 8/9 verts, 1 fail. Sortie verbatim :

   ```
   FAIL: warning fired 3 times, expected 1
   ```

2. **Fix appliqué** : warning retiré de P3 et P4, déplacé dans install.sh.

3. **Test VERT après fix** : compteur = 1 (orchestrateur uniquement) → 8/8 verts. Sortie verbatim :

   ```
   PASS: warning fires exactly once total across orchestrator + 2 $(...) captures
   === Summary: 8 passed, 0 failed ===
   ```

4. **Non-régression** : `tests/test_install_sh_install_method_stamp.py`, `tests/test_install_no_initial_commit.py`, `tests/test_install_unmerged_index.py`, `tests/test_install_ps1_ascii_only.py` → 4/4 verts. `bash -n scripts/install.sh` → OK.

### Point d'attention pour Draft 4 (node-bootstrap.sh) — contrat à respecter

Le helper `install_helpers.sh` est conçu pour être réutilisable par d'autres scripts shell du projet. Si **Draft 4** (`scripts/node-bootstrap.sh`) doit aussi résoudre le home Indagis et informer l'utilisateur d'un fallback legacy, il **doit** respecter le contrat de pureté :

- **NE PAS** appeler `_indagis_warn_legacy_alias_in_use_once` depuis P3/P4 (il n'y est plus).
- **DOIT** détecter lui-même la condition P3/P4 et fire le warning explicitement avant la 1ère capture `$(resolve_indagis_home)`.
- **DOIT** appeler `resolve_indagis_home` uniquement pour la valeur, jamais pour l'effet de bord warning.

**Pattern obligatoire** (à appliquer tel quel dans `node-bootstrap.sh`) :

```bash
source "<path>/install_helpers.sh"
if [ -n "${HERMES_HOME:-}" ]; then
    _indagis_warn_legacy_alias_in_use_once "HERMES_HOME" "$HERMES_HOME"
elif [ -d "${HOME:-}/.hermes" ]; then
    _indagis_warn_legacy_alias_in_use_once "~/.hermes" "${HOME}/.hermes"
fi
INDAGIS_HOME="$(resolve_indagis_home)"
```

**Risque si non respecté** : régression du bug Draft 2.1 (warning qui spamme l'utilisateur à chaque `$(...)` capture). Le test "warning fires exactly once" pourrait être promu en test d'intégration partagé entre install.sh et node-bootstrap.sh si on veut le garantir cross-script.

**Action ouverte** : lorsque Draft 4 sera traité, ajouter un test dans `tests/scripts/` qui vérifie que **tous** les scripts qui source `install_helpers.sh` respectent ce contrat. Une approche simple : un test qui grep tous les `scripts/*.sh` pour des appels directs à `_indagis_warn_legacy_alias_in_use_once` en dehors des sources attendus (install.sh, node-bootstrap.sh futur), et échoue si un nouveau script appelle le warning en P3/P4 du résolveur. Cette check est grossière mais capture l'erreur de régression principale.

### Note CI

`scripts/run_tests.sh` est orienté pytest et ne collecte pas les fichiers `.sh`. Le test bash doit être câblé dans la cible `make test-scripts` (ou équivalent) — pas dans le runner pytest. **Action ouverte** : ajouter une cible `scripts/test_scripts.sh` qui itère sur `tests/scripts/*.sh` et exit sur le 1er fail. En attendant, le test est lancé manuellement avec `bash tests/scripts/test_install_helpers_home_resolution.sh`.
