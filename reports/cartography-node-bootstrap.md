# Cartographie scripts/lib/node-bootstrap.sh — occurrences liées à l'identité

- Date : 2026-08-08
- Commit de référence : a67b2bb98
- Fichier : scripts/lib/node-bootstrap.sh (437 lignes, 68 occurrences de tokens identité)
- Méthode : `rg -n -i 'hermes|HERMES|HERMES_HOME|HERMES_DESKTOP|HERMES_GIT_BASH|com\.nousresearch|\.hermes|~/\.hermes'` brut, puis classification ligne par ligne.
- Grille : USER_FACING / DOCSTRING USER_FACING / TECHNICAL critique / DEFER / ATTRIBUTION (identique à cartography-install-sh.md, cartography-install-ps1.md)
- Note préalable : ce fichier est une **librairie sourceable** (L17: `source scripts/lib/node-bootstrap.sh`), pas un script exécutable. Les fonctions qu'il expose (`ensure_node`, `heal_managed_node`, `_nb_*`) sont appelées par `install.sh` et d'autres scripts. La cartographie doit donc identifier les **points où les variables d'environnement sont lues ou écrites** plutôt que les chemins d'invocation utilisateur.

## Légende catégories

Voir cartography-install-sh.md pour la définition complète.

## Cartographie par section (ligne par ligne)

### 1. En-tête (L1-24)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1-3 | DOCSTRING | `#!/usr/bin/env bash` / `# scripts/lib/node-bootstrap.sh` | Préserver (technique) |
| 4-7 | DOCSTRING | `# Sourceable helper: ensure Node.js >= MIN_VERSION is available for the TUI (React + Ink), browser tools, and the WhatsApp bridge.` | DOCSTRING (neutre) |
| 8-13 | DOCSTRING+USER_FACING | `# Strategy (first hit wins — respects the user's existing tooling):` / `1. modern node already on PATH` / `2. ~/.hermes/node/ from a prior Hermes-managed install` / `3. fnm, proto, nvm (in that order) if the user already uses a version manager` / `4. Termux pkg, macOS Homebrew` / `5. pinned nodejs.org tarball into ~/.hermes/node/ (always works, zero shell rc edits)` | DOCSTRING USER_FACING : 2 références au chemin `~/.hermes/node/` (USER_FACING) + 1 référence "Hermes-managed install" (USER_FACING) |
| 14-17 | DOCSTRING | `# Usage: source scripts/lib/node-bootstrap.sh` / `#   ensure_node   # returns 0 on success, non-zero on failure` / `#   if [ "$HERMES_NODE_AVAILABLE" = true ]; then ...; fi` | DOCSTRING (neutre + référence env var technique) |
| 18-23 | DOCSTRING+TECHNICAL | `# Env inputs (set before sourcing to override defaults):` / `#   HERMES_NODE_MIN_VERSION   (default: 20)   — accepted on PATH` / `#   HERMES_NODE_TARGET_MAJOR  (default: 22)   — installed when we install` / `#   HERMES_HOME               (default: $HOME/.hermes)` | DOCSTRING+USER_FACING : chemin par défaut `$HOME/.hermes` (USER_FACING) + 2 env vars techniques (préserver) |

→ 3 DOCSTRING USER_FACING (références `~/.hermes/node/` ×2 + "Hermes-managed install" ×1) + 1 USER_FACING (chemin `$HOME/.hermes`).

### 2. Configuration / Variables globales (L26-29)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 26 | TECHNICAL | `HERMES_NODE_MIN_VERSION="${HERMES_NODE_MIN_VERSION:-20}"` | **Cible critique** : env var `HERMES_NODE_MIN_VERSION`, préfixe `HERMES_NODE_*` (pas `HERMES_HOME`). À préserver (nom d'env var technique) — l'extension vers `INDAGIS_NODE_MIN_VERSION` peut attendre la migration des env vars. |
| 27 | TECHNICAL | `HERMES_NODE_TARGET_MAJOR="${HERMES_NODE_TARGET_MAJOR:-22}"` | **Cible critique** : env var `HERMES_NODE_TARGET_MAJOR`, préserver. |
| 28 | TECHNICAL | `HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"` | **Cible critique majeure** : initialisation, exactement la même que install.sh L48. À étendre avec `INDAGIS_HOME` en priorité. |
| 29 | TECHNICAL | `HERMES_NODE_AVAILABLE=false` | **Cible critique** : variable de sortie, préserver le nom. |

→ 4 TECHNICAL critiques.

### 3. Logging helpers (L31-37)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 31-37 | TECHNICAL | `_nb_log` / `_nb_ok` / `_nb_warn` : préfèrent `log_info` / `log_success` / `log_warn` du host script, sinon fallback sur `printf` | Préserver (technique) |

→ 0 migration.

### 4. Platform + version helpers (L39-77)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 43-45 | TECHNICAL | `_nb_is_termux` : `[ -n "${TERMUX_VERSION:-}" ] || [[ "${PREFIX:-}" == *"com.termux/files/usr"* ]]` | **Cible critique mineure** : match sur le chemin `com.termux/files/usr` (littéral, pas un nom de produit) — préserver. |
| 47-49 | DOCSTRING+USER_FACING | `# Where to symlink node/npm/npx so they land on PATH.` / `# Mirrors get_command_link_dir() from install.sh: root FHS → /usr/local/bin,` / `# Termux → $PREFIX/bin, otherwise ~/.local/bin.` | DOCSTRING (neutre) |
| 50-58 | TECHNICAL | `_nb_get_link_dir` : retourne `$PREFIX/bin` / `/usr/local/bin` / `$HOME/.local/bin` | **Cible critique** : équivalent de `get_command_link_dir()` install.sh L450-458. |
| 60-64 | DOCSTRING+USER_FACING | `# Redirect a Hermes-managed Node's `npm install -g` to the command link dir` | DOCSTRING USER_FACING (référence "Hermes-managed Node") |
| 65-71 | DOCSTRING+TECHNICAL | `_nb_configure_npm_prefix` : teste `$HERMES_HOME/node/bin/npm`, crée `$HERMES_HOME/node/etc/npmrc` | **Cible critique** : 2 chemins en dur `$HERMES_HOME/node/bin/npm` et `$HERMES_HOME/node/etc/npmrc` |
| 73-77 | TECHNICAL | `_nb_node_major` | Préserver (technique) |

→ 1 USER_FACING (commentaire "Hermes-managed Node"), 3 TECHNICAL critiques (`_nb_get_link_dir`, `$HERMES_HOME/node/bin/npm`, `$HERMES_HOME/node/etc/npmrc`).

### 5. _nb_npm_range (L79-102)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 79-82 | DOCSTRING | `# The npm range the checkout's root package.json demands. Read from the manifest rather than duplicated here so the two can never drift; falls back to the current floor when the manifest is unreadable (vendored copy of this script, stripped install tree).` | DOCSTRING (neutre) |
| 84-86 | TECHNICAL | `HERMES_NPM_TARGET_RANGE="${HERMES_NPM_TARGET_RANGE:-}"` (test) | **Cible critique** : env var `HERMES_NPM_TARGET_RANGE`, préserver. |
| 88-101 | TECHNICAL | parse package.json via `sed` (sans node car pas encore installé) | Préserver (technique) |
| 101 | TECHNICAL | `printf '>=12.0.0\n'` (fallback) | Préserver |

→ 1 TECHNICAL critique (env var).

### 6. _nb_ensure_bundled_npm_range (L104-164)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 104-124 | DOCSTRING | commentaire expliquant que le tarball nodejs.org ship un npm trop vieux, EBADENGINE sur `npm ci` | DOCSTRING (neutre) |
| 110-111 | DOCSTRING+USER_FACING | `# The Python side recovers through hermes_cli/npm_engine.py; the installer path had no such rung, so provision the right npm here instead of reacting later.` | DOCSTRING USER_FACING (référence `hermes_cli/npm_engine.py` = module Python interne) → **DEFER** (nom de module Python) |
| 117-120 | DOCSTRING+USER_FACING | `#   an explicit --prefix at the managed tree, because` / `#   _nb_configure_npm_prefix wrote prefix=~/.local into its etc/npmrc, and` | DOCSTRING (neutre) |
| 126 | TECHNICAL | `local npm_bin="$HERMES_HOME/node/bin/npm"` | **Cible critique** : chemin du npm managé |
| 144 | USER_FACING | `_nb_log "Upgrading bundled npm to satisfy $range..."` | USER_FACING (neutre) |
| 147-153 | TECHNICAL | `(cd "$tmp_cwd" || exit 1; CI=1 npm_config_min_release_age=0 "$npm_bin" install --global --prefix "$HERMES_HOME/node" "npm@$range" ...)` | **Cible critique** : `--prefix "$HERMES_HOME/node"` |
| 155-163 | USER_FACING | `_nb_ok "npm $(\"$npm_bin\" --version 2>/dev/null) installed"` / `_nb_warn "Could not upgrade bundled npm to $range — \`npm ci\` may fail with EBADENGINE."` / `_nb_warn "Fix manually: npm install -g --prefix \"$HERMES_HOME/node\" npm@\"$range\""` | USER_FACING (3×) |

→ 1 DOCSTRING USER_FACING (DEFER), 2 TECHNICAL critiques (`$HERMES_HOME/node/bin/npm`, `--prefix`), 3 USER_FACING.

### 7. _nb_have_modern_node / _nb_try_fnm / _nb_try_proto / _nb_try_nvm (L166-206)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 166-169 | TECHNICAL | `_nb_have_modern_node` | Préserver (technique) |
| 171-173 | DOCSTRING | `# Version-manager paths — respect what the user already uses` | DOCSTRING (neutre) |
| 175-184 | USER_FACING+TECHNICAL | `_nb_try_fnm` + `_nb_log "fnm detected — installing Node $HERMES_NODE_TARGET_MAJOR..."` + `_nb_ok "Node $(node --version) activated via fnm"` | USER_FACING (3×) |
| 186-193 | USER_FACING+TECHNICAL | `_nb_try_proto` + similaires | USER_FACING (2×) |
| 195-206 | USER_FACING+TECHNICAL | `_nb_try_nvm` + similaires | USER_FACING (2×) |

→ 7 USER_FACING (messages de log).

### 8. Platform package managers (L208-232)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 208-210 | DOCSTRING | `# Platform package managers` | DOCSTRING (neutre) |
| 212-219 | USER_FACING+TECHNICAL | `_nb_try_termux_pkg` + `_nb_log "Installing Node.js via pkg..."` + `_nb_ok "Node $(node --version) installed via pkg"` | USER_FACING (2×) |
| 221-232 | USER_FACING+TECHNICAL | `_nb_try_brew` + similaires | USER_FACING (2×) |

→ 4 USER_FACING (messages de log).

### 9. _nb_install_bundled_node (L234-326)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 234-236 | DOCSTRING+USER_FACING | `# Bundled binary fallback — always works, no shell rc edits` | DOCSTRING (neutre) |
| 238-249 | TECHNICAL | architecture detection | Préserver (technique) |
| 251-260 | TECHNICAL | OS detection | Préserver (technique) |
| 261 | TECHNICAL | `local index_url="https://nodejs.org/dist/latest-v${HERMES_NODE_TARGET_MAJOR}.x/"` | **Cible critique** : référence env var dans URL |
| 262-274 | TECHNICAL | tarball name resolution | Préserver (technique) |
| 276-281 | USER_FACING+TECHNICAL | `_nb_log "Downloading $tarball..."` + curl | USER_FACING (1×) |
| 283 | USER_FACING+TECHNICAL | `_nb_log "Extracting to $HERMES_HOME/node/..."` | USER_FACING (chemin en dur `$HERMES_HOME/node/`) + TECHNICAL critique |
| 284-301 | TECHNICAL | tar xf / mv vers `$HERMES_HOME/node` | **Cible critique** : `rm -rf "$HERMES_HOME/node"` + `mv "$extracted" "$HERMES_HOME/node"` |
| 303-316 | DOCSTRING+TECHNICAL | `_nb_get_link_dir` + ln -sf + `HERMES_NODE_SKIP_LINKS=1` | **Cible critique** : 3 symlinks `node`, `npm`, `npx` vers `$HERMES_HOME/node/bin/` |
| 318 | TECHNICAL | `export PATH="$HERMES_HOME/node/bin:$PATH"` | **Cible critique** : export PATH (équivalent L1855-1863 install.sh) |
| 320-321 | USER_FACING+TECHNICAL | `_nb_have_modern_node || return 1` + `_nb_ok "Node $(node --version) installed to $HERMES_HOME/node/"` | USER_FACING (chemin en dur) |
| 322-323 | DOCSTRING | `# The tarball's bundled npm is usually below the repo's engines.npm floor. Best-effort: an old npm still beats no Node.` | DOCSTRING (neutre) |
| 324 | TECHNICAL | `_nb_ensure_bundled_npm_range || true` | Préserver |

→ 3 USER_FACING (log messages avec chemin `$HERMES_HOME/node/`), 4 TECHNICAL critiques (rm, mv, symlinks, export PATH).

### 10. Heal broken managed Node (L328-387)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 328-330 | DOCSTRING+USER_FACING | `# Heal a broken Hermes-managed Node tree (partial upgrade / missing lib/)` | DOCSTRING USER_FACING (référence "Hermes-managed Node") |
| 332-346 | TECHNICAL | `_nb_managed_tool_broken` : teste `$HERMES_HOME/node/bin/$tool` / `$HERMES_HOME/node/${tool}.exe` / `$HERMES_HOME/node/$tool` | **Cible critique** : 3 chemins en dur |
| 348-352 | DOCSTRING+USER_FACING | `# The managed node runs but is below HERMES_NODE_TARGET_MAJOR — an old tree from a previous install (e.g. 22). Outdated heals the same way broken does, so existing users get upgraded on the next heal probe, not just on a full installer re-run. Mirrors _managed_node_tree_outdated() in hermes_constants.py.` | DOCSTRING USER_FACING (référence `hermes_constants.py` = module Python interne) → **DEFER** (nom de module Python) |
| 353-364 | TECHNICAL | `_nb_managed_node_outdated` : teste `$HERMES_HOME/node/bin/node` / `$HERMES_HOME/node/node` | **Cible critique** : 2 chemins en dur |
| 366-374 | TECHNICAL | `_nb_managed_node_needs_heal` | Préserver (technique) |
| 376-379 | DOCSTRING+USER_FACING | `# Redownload the pinned nodejs.org tarball when a managed tree exists but node/npm/npx fail a --version probe. No-op when the tree is healthy or absent. Used by hermes_constants.find_hermes_node_executable() and safe to call from install reruns.` | DOCSTRING USER_FACING (référence `hermes_constants.find_hermes_node_executable()`) → **DEFER** (nom de module Python) |
| 380-387 | DOCSTRING+USER_FACING+TECHNICAL | `heal_managed_node` + `_nb_log "Hermes-managed Node is broken — redownloading to $HERMES_HOME/node/..."` | USER_FACING (référence "Hermes-managed Node" + chemin en dur `$HERMES_HOME/node/`) + TECHNICAL critique |

→ 3 DOCSTRING USER_FACING (3 DEFER), 4 USER_FACING, 4 TECHNICAL critiques (3 chemins + 1 log message).

### 11. Public entry point ensure_node (L389-437)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 389-391 | DOCSTRING | `# Public entry point` | DOCSTRING (neutre) |
| 393-420 | DOCSTRING+TECHNICAL | `ensure_node` + commentaire "Repair pre-existing managed installs where `npm install -g` lands off PATH. No-op when there's no managed Node, so it's safe to run first." + `_nb_configure_npm_prefix` + `[ -x "$HERMES_HOME/node/bin/node" ]` | **Cible critique** : test existence binaire + commentaire |
| 401-403 | USER_FACING | `_nb_ok "Node $(node --version) found"` | USER_FACING (neutre) |
| 409 | USER_FACING | `_nb_ok "Node $(node --version) found (Hermes-managed)"` | USER_FACING (référence "Hermes-managed") |
| 416-417 | DOCSTRING+USER_FACING | `# The npm upgrade in _nb_install_bundled_node is best-effort — one offline install leaves an at-target tree stranded below engines.npm forever, since heal only fires for a *broken* tree. Mirrors Update-ManagedNpm's reuse-path call in install.ps1. No-ops on a probe when the npm is already in range.` | DOCSTRING USER_FACING (référence `Update-ManagedNpm` = fonction install.ps1) → cross-script ref |
| 418 | TECHNICAL | `_nb_ensure_bundled_npm_range || true` | Préserver (technique) |
| 421-432 | TECHNICAL+USER_FACING | `_nb_try_fnm && ...` / `_nb_try_proto && ...` / etc. | TECHNIQUE |
| 434-435 | USER_FACING | `_nb_warn "Node.js install failed — TUI and browser tools will be unavailable."` / `_nb_warn "Install manually: https://nodejs.org/en/download/  (or: \`brew install node\`, \`fnm install $HERMES_NODE_TARGET_MAJOR\`, etc.)"` | USER_FACING (2×) |

→ 2 USER_FACING (1 référence "Hermes-managed" + 1 message d'erreur), 1 DOCSTRING USER_FACING (cross-script ref), 1 TECHNICAL critique (test existence binaire).

## Récapitulatif

### Par catégorie

| Catégorie | Total occurrences | Sites principaux |
|---|---|---|
| USER_FACING (à migrer) | ~25 | Commentaires en-tête `~/.hermes/node/` (L10, L13), référence `$HOME/.hermes` (L23), "Hermes-managed Node" commentaires (L60, L110, L328-330, L385), log messages "Node ... installed to $HERMES_HOME/node/" (L321, L385), log message "Node found (Hermes-managed)" (L409), warn message final (L434) |
| DOCSTRING USER_FACING | ~7 | Référence `hermes_cli/npm_engine.py` (L110-111), `hermes_constants.py` (L348-352, L376-379), `Update-ManagedNpm's reuse-path call in install.ps1` (L416-417), 2 références "Hermes-managed Node" (L60, L328-330) |
| TECHNICAL critique (cible de la fonction de résolution) | ~22 | `HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"` (L28), `$HERMES_HOME/node/bin/npm` (L66, L126), `$HERMES_HOME/node/etc/npmrc` (L69-70), `_nb_get_link_dir` (L50-58), `--prefix "$HERMES_HOME/node"` (L151), `$HERMES_HOME/node/bin/node` (L226, L355), `rm -rf "$HERMES_HOME/node"` (L299), `mv "$extracted" "$HERMES_HOME/node"` (L300), symlinks (L311-313), `export PATH="$HERMES_HOME/node/bin:$PATH"` (L318), 3 chemins dans `_nb_managed_tool_broken` (L336-338), 2 chemins dans `_nb_managed_node_outdated` (L355) |
| DEFER (hors tranche 5) | ~4 | `hermes_cli/npm_engine.py` (L110-111), `hermes_constants.find_hermes_node_executable()` (L376-379), `hermes_constants.py` (L348-352), `Update-ManagedNpm` (L416-417) — tous des modules/fonctions Python internes |
| ATTRIBUTION | 0 | (Aucune URL upstream dans ce fichier) |

### Sites critiques pour la fonction de résolution centralisée (point 3 du brief)

Ce sont les **points où HERMES_HOME est lu** dans cette lib sourceable :

1. **L28** : `HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"` — initialisation, à étendre avec `INDAGIS_HOME` en priorité.
2. **L66, L126** : `$HERMES_HOME/node/bin/npm` — test existence + chemin du npm managé.
3. **L69-70** : `$HERMES_HOME/node/etc/npmrc` — création du fichier de config npm.
4. **L151** : `--prefix "$HERMES_HOME/node"` — installation upgrade npm.
5. **L226, L355** : `$HERMES_HOME/node/bin/node` — test existence du binaire node managé.
6. **L299-300** : `rm -rf "$HERMES_HOME/node"` + `mv "$extracted" "$HERMES_HOME/node"` — suppression et recréation de l'arbre node.
7. **L311-313** : `ln -sf "$HERMES_HOME/node/bin/{node,npm,npx}" "$_link_dir/{node,npm,npx}"` — 3 symlinks vers le binaire managé.
8. **L318** : `export PATH="$HERMES_HOME/node/bin:$PATH"` — export PATH (équivalent L1855-1863 install.sh).
9. **L336-338** : 3 chemins dans `_nb_managed_tool_broken` : `$HERMES_HOME/node/bin/$tool` / `$HERMES_HOME/node/${tool}.exe` / `$HERMES_HOME/node/$tool`.
10. **L385** : log "redownloading to $HERMES_HOME/node/" — chemin en dur.

### Sites équivalents aux écritures .zshrc / .bashrc / .profile install.sh (L1855-1863)

Côte node-bootstrap.sh, **il n'y a pas d'écriture persistante de PATH dans un fichier rc**. Les exports de PATH sont session-only (`export PATH=...` dans le process courant). C'est cohérent avec le fait que ce script est sourceable et n'est pas un installateur persistant — l'écriture du PATH est faite par install.sh (qui écrit dans .zshrc/.bashrc).

La coordination entre `install.sh` (qui persiste) et `node-bootstrap.sh` (qui export en session) doit être explicite : la fonction de résolution centralisée doit être appelée **avant** le `source scripts/lib/node-bootstrap.sh` dans install.sh.

### DEFER explicitement hors tranche 5

- `hermes_cli/npm_engine.py` (L110-111) — module Python interne
- `hermes_constants.find_hermes_node_executable()` (L376-379) — fonction Python interne
- `hermes_constants.py` (L348-352) — module Python interne
- `Update-ManagedNpm` (L416-417) — fonction install.ps1 (cross-script ref)
- `HERMES_NODE_*` env vars (L26-27) — préfixe `HERMES_NODE_*` distinct de `HERMES_HOME`, à traiter avec la migration des env vars

### Hypothèses de la tranche 5

- La fonction de résolution centralisée doit être appelée **avant** `source scripts/lib/node-bootstrap.sh` dans install.sh (sinon `HERMES_HOME` est figé au moment du source).
- Le fallback `HERMES_HOME` doit rester en place pour ne pas casser les installations existantes.

## Décision requise

- Validation de la grille de classification (identique aux 2 autres) ;
- Validation de la liste des sites critiques (10 points) ;
- Validation de l'hypothèse de coordination avec install.sh (la fonction de résolution doit être appelée avant le source) ;
- Validation du périmètre de la cartographie (node-bootstrap.sh seul) avant alignement avec install.sh / install.ps1.

## Note de cohérence inter-rapports

Les 3 cartographies (install.sh, install.ps1, node-bootstrap.sh) utilisent la même grille et le même format. Les sites critiques sont :
- **install.sh** : 9 points HERMES_HOME (cf. rapport)
- **install.ps1** : 16 points HERMES_HOME + 7 points SetEnvironmentVariable (cf. rapport)
- **node-bootstrap.sh** : 10 points HERMES_HOME (cf. ce rapport)

La fonction de résolution centralisée `get_indagis_home()` doit être appliquée de manière cohérente à ces **35 points** au total (avec recouvrement : `install.sh:48`, `node-bootstrap.sh:28` lisent la même variable, `install.ps1:32-33` initialise la même chose côté PowerShell).

### BUG FONCTIONNEL isolé — parité install.sh / install.ps1 / tests

Les deux installateurs parsent `pyproject.toml` pour extraire la liste des extras via :
- `install.sh:1625` : `m = re.search(r"hermes-agent\[([\w-]+)\]", s)` (Python heredoc, L1617-1632)
- `install.ps1:2487` : `m = re.search(r'hermes-agent\[([\w-]+)\]', s)` (Python heredoc, L2479-2492) — **strictement le seul site** contenant la regex `hermes-agent\[...\]` dans install.ps1. Les 4 lignes voisines citées dans les cartographies précédentes (L1693, L2247, L2476, L2625) ne contiennent **PAS** le mot `hermes-agent` :
  - L1693 : `$output = winget install --exact --id $pkg --source winget --silent --force` (commande winget)
  - L2247 : `Where-Object { $_.TaskName -like '*Hermes_Gateway*' }` (pattern de nom de Scheduled Task Windows)
  - L2476 : `$pythonExeForParse = if (-not $NoVenv) { "$InstallDir\venv\Scripts\python.exe" } else { (& $UvCmd python find $PythonVersion) }` (résolution de l'interpréteur Python)
  - L2625 : `& $pythonExe -m py_compile "$InstallDir\hermes_cli\web_server.py" 2>&1 | Out-Null` (le mot présent est `hermes_cli`, pas `hermes-agent`)

**Périmètre strict : 2 sites** dans 2 fichiers, **0 doublon** ailleurs.

`pyproject.toml:4` dit `name = "indagis-agent"`, donc les deux regex sont **mortes** sur cette branche : `_ALL_EXTRAS_CSV=""` toujours, le filtrage `_BROKEN_EXTRAS` ne s'exécute jamais. Le tier 2 du fallback pip n'est jamais appelé ; seul `".[all]"` (tier 1) est utilisé en permanence. Pas un crash, mais un chemin mort.

**Preuve par les tests (citation littérale)** :

`tests/test_project_metadata.py:80-82` :
```
        offending = [
            spec for spec in all_extra_specs
            if f"hermes-agent[{extra}]" in spec
        ]
```
Ce test itère sur les extras `LAZY_DEPS` (cf. L70-77) et assertit qu'aucune spec `[all]` ne référence `hermes-agent[extra]` (le nom upstream). Le test est **vert** sur cette branche, ce qui prouve que `pyproject.toml` ne contient plus `hermes-agent[extra]`.

`tests/test_termux_all_extra_compat.py:14-16` :
```
    assert '"indagis-agent[termux]"' in text
    assert '"hermes-agent[matrix]"' not in text.split("termux-all = [", 1)[1].split("]", 1)[0]
    assert '"hermes-agent[voice]"' not in text.split("termux-all = [", 1)[1].split("]", 1)[0]
```
Ce test vérifie que les specs `[termux-all]` dans pyproject.toml utilisent bien `indagis-agent[termux]` et ne contiennent plus `hermes-agent[matrix]` ni `hermes-agent[voice]`. Le test est **vert** sur cette branche, ce qui confirme que pyproject.toml est déjà migré.

**Parité cassée en 4 endroits** : `install.sh:1625` ↔ `install.ps1:2487` ↔ `tests/test_project_metadata.py:80-82` ↔ `tests/test_termux_all_extra_compat.py:14-16`. Les 2 installateurs cherchent encore l'ancien nom que les 2 tests bloquent. **À corriger en tranche séparée** : changer la regex en `indagis-agent\[...\]` dans **les deux fichiers** pour préserver la parité.

### Structure de l'env var prioritaire

```bash
# bash
INDAGIS_HOME="${INDAGIS_HOME:-$HOME/.indagis}"
HERMES_HOME="${HERMES_HOME:-${INDAGIS_HOME:-$HOME/.hermes}}"
```

```powershell
# PowerShell
[string]$IndagisHome = $(if ($env:INDAGIS_HOME) { $env:INDAGIS_HOME } else { "$env:LOCALAPPDATA\indagis" })
[string]$HermesHome = $(if ($env:HERMES_HOME) { $env:HERMES_HOME } elseif ($env:INDagisHome) { $env:IndagisHome } else { "$env:LOCALAPPDATA\hermes" })
```

(équivalent de install.sh L48 + install.ps1 L32-33)
