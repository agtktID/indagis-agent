# Cartographie scripts/install.sh — occurrences liées à l'identité

- Date : 2026-08-08
- Commit de référence : a67b2bb98
- Fichier : scripts/install.sh (3370 lignes, 208 occurrences de tokens identité)
- Méthode : `rg -n -i 'hermes|HERMES|HERMES_HOME|HERMES_DESKTOP|com\.nousresearch|\.hermes|~/\.hermes'` brut, puis classification ligne par ligne.
- Grille : USER_FACING (à migrer) / DOCSTRING (commentaire de fonction) / COMMENT (commentaire de section) / TECHNICAL (variable d'environnement, chemin en dur, fonction de résolution) / ATTRIBUTION (mention upstream préservée) / DEFER (hors tranche 5)
- Note préalable : la méthode « même grille que install.ps1 et node-bootstrap.sh » invoquée par le brief n'a pas été déposée dans `reports/` (vérifié : 5 fichiers seulement, aucun ne cartographie ces scripts). Je pose donc le format ici ; à confirmer en ouverture de la prochaine itération.

## Légende catégories

- **USER_FACING** : chaîne visible de l'utilisateur final dans un message de log, banner, help, message d'erreur, success, .env.example généré. Doit migrer vers Indagis.
- **DOCSTRING** : commentaire d'en-tête de fonction bash qui documente le contrat. Nom propre dans le commentaire = usage descriptif, migrer.
- **COMMENT** : commentaire libre / section banner. Migrer si le nom est projet-spécifique (ex. "Hermes installer") mais préserver les références techniques (ex. "Hermes-managed Node" devient "Indagis-managed Node" ou reste neutre).
- **TECHNICAL** : nom de variable d'environnement (HERMES_HOME), nom de fonction (get_hermes_home), chemin répertoire (`.hermes/`), config Windows (`com.nousresearch.hermes` si on l'aborde). Ces points sont précisément ceux que la tranche va ensuite déplacer en repli.
- **ATTRIBUTION** : "by Nous Research", URL upstream, mentions de fork. Préservées.
- **DEFER** : explicitement hors tranche 5 — bundle ID macOS, branding identité produit, etc.

## Cartographie par section (ligne par ligne)

### 1. En-tête (L1-14)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1-3 | DOCSTRING | `#!/bin/bash` / `# Hermes Agent Installer` | USER_FACING → « Indagis Agent Installer » |
| 4-6 | DOCSTRING | `# Installation script for Linux, macOS, and Android/Termux.` | Préserver (technique) |
| 7 | COMMENT | `# Uses uv for desktop/server installs...` | Préserver (technique) |
| 8-13 | DOCSTRING | `# Usage: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash` | DEFER (migration future vers infra Indagis) : l'URL upstream et le nom de fichier restent attachés au domaine `hermes-agent.nousresearch.com`. Quand l'infra Indagis aura son propre domaine et son propre hébergement de bootstrap (par exemple `indagis-agent.indagis.fr/install.sh`), les 2 installateurs basculeront. |
| 14-15 | COMMENT | séparateurs de section | neutre |

→ 2 occurrences USER_FACING (titre + URL), 1 DOCSTRING fonction d'usage.

### 2. Garde env leakage (L18-29)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 18-21 | DOCSTRING | "Guard against environment leakage when the installer is launched from another Python-driven tool session (e.g. Hermes terminal tool)" | USER_FACING (référence projet) → « Indagis terminal tool » |
| 22-24 | TECHNICAL | `unset PYTHONPATH` après garde | Préserver (technique) |
| 25-28 | TECHNICAL | `unset PYTHONHOME` après garde | Préserver (technique) |

→ 1 USER_FACING (« Hermes terminal tool »), 2 TECHNICAL (garde env).

### 3. Config uv + couleurs (L31-44)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 31-33 | DOCSTRING | "Prevent uv from discovering config files (uv.toml, pyproject.toml) from the wrong user's home directory when running under sudo -u <user>. See #21269." | Préserver (commentaire technique) |
| 35-44 | TECHNICAL | Constantes couleurs ANSI (`RED`, `GREEN`, etc.) | Préserver (technique) |

→ 0 migration.

### 4. Variables d'installation (L46-67)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 46-47 | ATTRIBUTION | `REPO_URL_SSH="git@github.com:NousResearch/hermes-agent.git"` / `REPO_URL_HTTPS="https://github.com/NousResearch/hermes-agent.git"` | **ATTRIBUTION permanent** : URL upstream préservée. La migration du repo (renommer `hermes-agent` → `indagis-agent` côté GitHub) est une tranche distincte hors Phase 5. |
| 48 | TECHNICAL | `HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"` | **Cible du rebrand** : à remplacer par `INDAGIS_HOME="${INDAGIS_HOME:-$HOME/.indagis}"` (CHEMIN PRIORITAIRE) + `HERMES_HOME` conservé en fallback |
| 49-58 | DOCSTRING+COMMENT | "INSTALL_DIR is resolved AFTER arg parsing..." | Préserver (technique) |
| 62-65 | DOCSTRING | "FHS-style root install layout (set by resolve_install_layout when applicable): code at /usr/local/lib/hermes-agent, command at /usr/local/bin/hermes, data still at /root/.hermes (HERMES_HOME)." | USER_FACING : les chemins `/usr/local/lib/hermes-agent`, `/usr/local/bin/hermes` → à migrer vers `/usr/local/lib/indagis-agent` + `/usr/local/bin/indagis`. Le commentaire explicite le contrat. |
| 66-67 | TECHNICAL | `ROOT_FHS_LAYOUT=false` | Préserver (technique) |

→ 1 TECHNICAL critique (HERMES_HOME) — point central de la future fonction de résolution, 1 DOCSTRING USER_FACING (chemins FHS).

### 5. Options CLI (L69-204)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 69-92 | TECHNICAL | options (`USE_VENV`, `RUN_SETUP`, etc.) | Préserver |
| 95-149 | TECHNICAL | boucle `case` argument parser | Préserver |
| 150-153 | USER_FACING | option `--hermes-home PATH` | Migrer : ajouter `--indagis-home` (prioritaire), garder `--hermes-home` (fallback) |
| 160-198 | USER_FACING | bloc `echo "Hermes Agent Installer"` du `--help` | Migrer le titre + toutes les références dans le help text vers Indagis |
| 181-183 | USER_FACING | "default (non-root): ~/.hermes/hermes-agent" / "default (root, Linux): /usr/local/lib/hermes-agent" / "Data directory (default: ~/.hermes, or \$HERMES_HOME)" | USER_FACING — migrer vers `~/.indagis/indagis-agent` etc. |

→ 1 option flag (--hermes-home), 1 bloc --help (titre + 3 lignes de default path).

### 6. Fonctions utilitaires (L207-498)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 211-220 | USER_FACING | `print_banner()` : "Hermes Agent Installer" / "An open source AI agent by Nous Research." | USER_FACING : migrer le titre + tagline. Conserver "Nous Research" comme ATTRIBUTION explicite sauf décision contraire. |
| 222-244 | TECHNICAL | log_info / log_success / log_warn / log_error / json_escape | Préserver |
| 246-261 | DOCSTRING | restore_dirty_lockfiles — commentaire | Préserver |
| 251-261 | TECHNICAL | restore_dirty_lockfiles — corps | Préserver |
| 263-313 | DOCSTRING+TECHNICAL | discard_update_lockfile_churn | Préserver |
| 315-327 | USER_FACING | `emit_manifest()` : stages JSON avec titres "System prerequisites", "Download Hermes Agent", "Create Python virtual environment", "Install Python dependencies", "Install browser-tool dependencies", "Install hermes command", "Prepare config and skills", "Configure API keys and settings", "Configure gateway service", "Finish install" / si desktop : "Build desktop app" | USER_FACING : "Download Hermes Agent" → "Download Indagis Agent". "Install hermes command" → "Install indagis command". |
| 329-334 | TECHNICAL | stage_needs_user_input | Préserver |
| 336-348 | TECHNICAL | emit_stage_json | Préserver |
| 350-387 | TECHNICAL | prompt_yes_no | Préserver |
| 389-391 | TECHNICAL | is_termux | Préserver |
| 393-448 | DOCSTRING+TECHNICAL | resolve_install_layout | Docstring mentionne `$HERMES_HOME/hermes-agent` → USER_FACING (chemin en dur), à migrer |
| 450-458 | TECHNICAL | get_command_link_dir | Préserver |
| 460-468 | USER_FACING | get_command_link_display_dir : retourne `'$PREFIX/bin'` / `'/usr/local/bin'` / `'~/.local/bin'` | USER_FACING : c'est du chemin en dur, à migrer en cohérence avec install.sh L62-65 |
| 470-487 | DOCSTRING+TECHNICAL | configure_managed_node_npm_prefix | Docstring parle de "Hermes-managed Node" → USER_FACING, migrer vers "Indagis-managed Node" |
| 489-497 | TECHNICAL | get_hermes_command_path : retourne `hermes` en fallback | **Cible future résolution** : à remplacer par get_indagis_command_path qui résout `indagis` puis `hermes` en repli |

→ 3 USER_FACING (banner, manifest stages, command_link_display_dir), 1 DOCSTRING USER_FACING (resolve_install_layout), 1 DOCSTRING USER_FACING (configure_managed_node_npm_prefix), 1 TECHNICAL critique (get_hermes_command_path).

### 7. Détection OS (L503-543)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 503-543 | TECHNICAL | detect_os | Préserver sauf L532 : `log_info "  iex (irm https://hermes-agent.nousresearch.com/install.ps1)"` — DEFER (migration future vers infra Indagis), bascule en même temps que L8-13. |

→ 1 DEFER (URL install.ps1, cohérent avec L9 — bascule conjointe vers infra Indagis).

### 8. install_uv (L549-610)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 549-610 | DOCSTRING+TECHNICAL | install_uv | Docstring mentionne "Hermes owns its own uv at $HERMES_HOME/bin/uv" → USER_FACING, migrer vers "Indagis owns its own uv at $INDAGIS_HOME/bin/uv". Le reste est technique. |

→ 1 DOCSTRING USER_FACING.

### 9. check_python / attempt_install_git / check_git (L612-781)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 612-653 | TECHNICAL | check_python | Préserver |
| 655-720 | DOCSTRING+TECHNICAL | attempt_install_git, mentionne "mirroring install.ps1's Install-Git" | Préserver (référence croisée technique) |
| 722-781 | USER_FACING+TECHNICAL | check_git — la plupart technique, mais "Install manually: Use your package manager to install git" → préservée | Préserver globalement |

→ 0 migration.

### 10. node_satisfies_build / npm_supports_npmrc / check_node (L783-860)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 783-860 | DOCSTRING+TECHNICAL | "Hermes requires Node >=26" L853 → USER_FACING (message log_warn), migrer vers "Indagis requires Node >=26" | 1 USER_FACING (L853) |

→ 1 USER_FACING (message d'erreur Node).

### 11. install_node (L862-975)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 935 | USER_FACING | `log_info "Extracting to ~/.hermes/node/..."` | USER_FACING (chemin en dur) — migrer vers `~/.indagis/node/...` |
| 952-954 | DOCSTRING | "Place into ~/.hermes/node/ and symlink binaries into the same bin dir the hermes command uses" | USER_FACING, migrer |
| 963-965 | TECHNICAL | ln -sf vers $HERMES_HOME/node/bin | Préserver (technique) |
| 969 | TECHNICAL | export PATH | Préserver |
| 973 | USER_FACING | `log_success "Node.js $installed_ver installed to ~/.hermes/node/"` | USER_FACING (chemin en dur), migrer |

→ 3 USER_FACING (chemin `~/.hermes/node/` cité 3 fois : log_info, docstring, log_success).

### 12. check_network_prerequisites (L977-1031)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1028 | USER_FACING | `log_warn "Network checks failed. Hermes install may complete..."` | USER_FACING, migrer |

→ 1 USER_FACING.

### 13. install_system_packages (L1033-1222)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1152, 1168 | USER_FACING | `log_info "Hermes Agent itself does not require or retain root access."` cité 2× | USER_FACING, migrer vers "Indagis Agent itself does not require or retain root access." |

→ 1 USER_FACING (×2 occurrences du même message).

### 14. clone_repo (L1228-1398)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1258 | COMMENT | "Mirrors the `hermes update` path" | USER_FACING (référence produit), migrer vers "Mirrors the `indagis update` path" |
| 1280 | DOCSTRING | "mirror ``hermes update`` and reset" | USER_FACING, migrer |
| 1315 | USER_FACING | "Review git diff / git status if Hermes behaves unexpectedly." | USER_FACING, migrer |
| 1348 | COMMENT | "Try SSH first (for private repo access), fall back to HTTPS" | Préserver |
| 1350-1351 | DOCSTRING | GIT_SSH_COMMAND disables interactive prompts... | Préserver |

→ 3 USER_FACING (références `hermes update` dans 2 commentaires + 1 message d'erreur).

### 15. setup_venv (L1400-1441)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1400-1441 | TECHNICAL | setup_venv | Préserver |

→ 0 migration.

### 16. install_deps (L1443-1695)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1625 | TECHNICAL | regex parse `hermes-agent\[([\w-]+)\]` dans pyproject.toml — **PKG NAME** | **BUG FONCTIONNEL ISOLÉ — périmètre strict 2 sites** : `pyproject.toml:4` dit `name = "indagis-agent"`. Le regex `hermes-agent\[...\]` ne matche aucune des specs de `[all]` (qui référencent `indagis-agent[extra]`). Résultat : `_ALL_EXTRAS_CSV=""` toujours, le filtrage `_BROKEN_EXTRAS` est mort, et `install_tier` n'est appelé qu'avec `".[all]"` au lieu de la liste filtrée. **Périmètre strict** : `install.sh:1625` (1 site) + `install.ps1:2487` (1 site) = **2 sites au total**, **0 doublon** ailleurs. Vérification faite par recherche large dans le repo (cf. `rg '\[([\\w-]+)\]'` filtré sur `pyproject.toml`) : aucun autre fichier ne parse les extras avec un regex similaire. **Tests impactés (citation littérale)** : `tests/test_project_metadata.py:80-82` dit littéralement : `offending = [\n    spec for spec in all_extra_specs\n    if f"hermes-agent[{extra}]" in spec\n]` (itère sur les extras lazy_install et assertit qu'aucune spec `[all]` ne référence `hermes-agent[extra]`). `tests/test_termux_all_extra_compat.py:14-16` dit littéralement : `assert '"indagis-agent[termux]"' in text\nassert '"hermes-agent[matrix]"' not in text.split("termux-all = [", 1)[1].split("]", 1)[0]\nassert '"hermes-agent[voice]"' not in text.split("termux-all = [", 1)[1].split("]", 1)[0]` (vérifie que les specs `[termux-all]` dans pyproject.toml utilisent bien `indagis-agent[termux]`). Les deux tests bloquent les références upstream `hermes-agent[extra]` dans pyproject.toml — donc la **parité install.sh:1625 ↔ install.ps1:2487 ↔ tests/test_project_metadata.py:80-82 ↔ tests/test_termux_all_extra_compat.py:14-16** est cassée en 4 endroits. À corriger dans une tranche séparée : changer la regex en `indagis-agent\[...\]` côté install.sh **ET** install.ps1 (L2487, qui est le seul site contenant le regex dans install.ps1) en cohérence. |

→ 1 BUG FONCTIONNEL (point 3 du brief, à corriger en tranche séparée, pas dans cette cartographie).

### 17. setup_path (L1697-1918)

C'est la section la plus dense en identité. Inventaire ligne par ligne :

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1697-1755 | USER_FACING | `setup_path()` — nom de fonction, `$INSTALL_DIR/venv/bin/python`, `$INSTALL_DIR/hermes` (entrypoint) | **Nom de la fonction de résolution** : `setup_path` est neutre ; le **chemin en dur `$INSTALL_DIR/hermes`** est USER_FACING → migrer vers `$INSTALL_DIR/indagis` |
| 1697, 1755-1804 | USER_FACING | Bloc shim : `cat > "$command_link_dir/hermes"`, `cat > "$command_link_dir/hermes-agent"`, `cat > "$command_link_dir/hermes-acp"` — **3 launchers** | USER_FACING : créer les launchers `indagis`, `indagis-agent`, `indagis-acp` comme cibles prioritaires, garder `hermes`/`hermes-agent`/`hermes-acp` en alias de repli |
| 1756 | USER_FACING | `log_success "Installed hermes launcher → $command_link_display_dir/hermes"` | USER_FACING, migrer vers "Installed indagis launcher → .../indagis" |
| 1758-1779 | USER_FACING | Bloc `hermes-agent` launcher : commentaire "`hermes-agent` console script declared in pyproject.toml's [project.scripts]" | USER_FACING (commentaire référence), migrer |
| 1779 | USER_FACING | `log_success "Installed hermes-agent launcher → ..."` | USER_FACING, migrer |
| 1781-1804 | USER_FACING | Bloc `hermes-acp` : commentaire "ACP hosts (Zed, JetBrains, Buzz) resolve the agent by command name..." | USER_FACING (commentaire + nom), migrer |
| 1804 | USER_FACING | `log_success "Installed hermes-acp launcher → ..."` | USER_FACING, migrer |
| 1809 | USER_FACING | `log_success "hermes command ready"` | USER_FACING, migrer vers "indagis command ready" |
| 1815-1818 | DOCSTRING | "FHS layout: /usr/local/bin is normally on PATH..." + "/usr/local/bin is normally on PATH for login shells" | DOCSTRING (référence `/usr/local/bin/hermes`) → migrer chemin dans le commentaire |
| 1826-1841 | USER_FACING | "hermes not on PATH in non-login shells" + "Added /usr/local/bin to PATH in $SHELL_CONFIG" + commentaire `# Hermes Agent — ensure /usr/local/bin is on PATH` | USER_FACING, migrer vers "# Indagis Agent — ensure /usr/local/bin is on PATH" et "indagis not on PATH" |
| 1848-1912 | USER_FACING | Bloc "Check if ~/.local/bin is on PATH" + commentaires "# Hermes Agent — ensure ~/.local/bin is on PATH" + fish config | USER_FACING, migrer vers "# Indagis Agent — ensure ~/.local/bin is on PATH" |
| 1906-1907 | USER_FACING | "Could not detect shell config file to add ~/.local/bin to PATH" | Préserver (neutre) |
| 1911 | USER_FACING | `log_info "~/.local/bin already on PATH"` | Préserver (neutre) |
| 1917 | USER_FACING | `log_success "hermes command ready"` (2e occurrence) | USER_FACING, migrer |

→ Section lourde : 18+ USER_FACING (3 launchers, 5 commentaires, 6 messages de log). **Cible principale de la fonction de résolution centralisée** : get_indagis_command_path() doit résoudre le bon binaire, et les 3 shims doivent être écrits avec le nom indagis en tête de liste.

### 18. copy_config_templates (L1920-1991)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 1923-1924 | USER_FACING+TECHNICAL | `mkdir -p "$HERMES_HOME"/{cron,sessions,logs,pairing,hooks,image_cache,audio_cache,memories,skills}` | **Cible critique** : à migrer vers `$INDAGIS_HOME` (prioritaire) puis `$HERMES_HOME` (fallback). Toute la structure de répertoires est ancrée sur HERMES_HOME. |
| 1927-1942 | USER_FACING | bloc "Create .env at ~/.hermes/.env" + log_success "Created ~/.hermes/.env from template" + log_info "~/.hermes/.env already exists" + chmod 600 | USER_FACING (chemin en dur 4×), migrer |
| 1944-1952 | USER_FACING | "Create config.yaml at ~/.hermes/config.yaml" + log_success "Created ~/.hermes/config.yaml from template" + log_info "~/.hermes/config.yaml already exists" | USER_FACING, migrer |
| 1954-1963 | USER_FACING | "Create SOUL.md" + contenu SOUL.md "You are Hermes Agent, an intelligent AI assistant created by Nous Research." + log_success | **DEFER tranche 5+** : SOUL.md est de la persona utilisateur, à traiter séparément. Conservé en l'état. |
| 1966 | USER_FACING | `log_success "Configuration directory ready: ~/.hermes/"` | USER_FACING, migrer |
| 1968-1990 | USER_FACING | Bloc skills : `~/.hermes/skills/`, `~/.hermes/.no-bundled-skills`, `'hermes update'`, ".no-bundled-skills (installed with --no-skills)" | USER_FACING (chemins en dur 6× + 1 référence `hermes update`), migrer |

→ Section lourde : ~14 USER_FACING (création config + skills). Toute cette section doit basculer sur la fonction de résolution.

### 19. strip_snap_browser_override (L2027-2052)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 2027-2052 | DOCSTRING+USER_FACING | "Existing installs created before the system-browser fallback was dropped" + `Hermes will use the bundled Chromium instead.` | USER_FACING (×2), migrer |

→ 2 USER_FACING.

### 20. install_node_deps (L2273-2401)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 2394 | USER_FACING | `log_warn "TUI npm install failed or timed out (hermes --tui may not work)"` | USER_FACING, migrer vers "indagis --tui" |
| 2399-2400 | COMMENT | "Keep the checkout clean so `hermes update` doesn't autostash every run" + `restore_dirty_lockfiles` | USER_FACING (référence), migrer vers "`indagis update`" |

→ 2 USER_FACING (références `hermes --tui`, `hermes update`).

### 21. run_setup_wizard / maybe_start_gateway (L2403-2532)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 2418 | USER_FACING | `log_info "Setup wizard skipped (no terminal available). Run 'hermes setup' after install."` | USER_FACING, migrer vers "indagis setup" |
| 2428-2433 | DOCSTRING+USER_FACING | "Run hermes setup using the venv Python directly..." + `python -m hermes_cli.main setup` | USER_FACING (référence `hermes setup`, `hermes_cli.main` est interne), migrer `hermes setup` vers `indagis setup` ; `hermes_cli.main` est **TECHNICAL/DEFER** (nom de package Python) |
| 2459 | USER_FACING | `log_info "The gateway needs to be running for Hermes to send/receive messages."` | USER_FACING, migrer |
| 2462-2475 | USER_FACING+TECHNICAL | `$HERMES_HOME/whatsapp/session/creds.json` + "WhatsApp is enabled but not yet paired" + "Running 'hermes whatsapp' to pair via QR code..." | USER_FACING (chemin + référence `hermes whatsapp`), migrer |
| 2483 | USER_FACING | "Run 'hermes gateway install' later." | USER_FACING, migrer |
| 2494-2524 | USER_FACING | "Install the gateway as a background service" + `hermes gateway install` + `hermes gateway start` + `hermes gateway` + "Gateway started! Your bot is now online." + "Try: hermes gateway start" + "You can start manually: hermes gateway" | USER_FACING (6×), migrer |
| 2516-2527 | USER_FACING | `log_info "Termux detected — starting gateway in best-effort background mode..."` + `nohup $HERMES_CMD gateway` + "Gateway started (PID $GATEWAY_PID). Logs: ~/.hermes/logs/gateway.log" + "To stop: kill $GATEWAY_PID" + "To restart later: hermes gateway" | USER_FACING (chemin + commandes), migrer |

→ Section lourde : 15+ USER_FACING (références `hermes gateway`, `hermes whatsapp`, `hermes setup`, `~/.hermes/logs/gateway.log`).

### 22. write_bootstrap_marker (L2534-2574)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 2535-2544 | DOCSTRING | "Writes $INSTALL_DIR/.hermes-bootstrap-complete, which tells the Hermes desktop app (apps/desktop/electron/main.ts) and the macOS launcher fast path (apps/bootstrap-installer) "a real install finished here..." | DOCSTRING : nom de fichier `.hermes-bootstrap-complete` → **DEFER ou migration** ; nom de fonction write_bootstrap_marker reste ; "Hermes desktop app" → "Indagis desktop app" |
| 2564-2573 | TECHNICAL | `local marker_path="$INSTALL_DIR/.hermes-bootstrap-complete"` | **Cible critique** : nom de fichier marqueur, à renommer `.indagis-bootstrap-complete` **avec compatibilité lecture** du nom legacy (le desktop lit ce fichier) |
| 2569-2572 | TECHNICAL | JSON `schemaVersion: 1, pinnedCommit, pinnedBranch, completedAt` | Préserver (contrat JSON interne) |

→ 1 DOCSTRING USER_FACING, 1 TECHNICAL critique (nom du marker).

### 23. print_success (L2576-2655)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 2577-2582 | USER_FACING | "Installation Complete!" | USER_FACING (neutre) |
| 2588-2591 | USER_FACING | `Config: $HERMES_HOME/config.yaml` / `API Keys: $HERMES_HOME/.env` / `Data: $HERMES_HOME/cron/, sessions/, logs/` / `Code: $INSTALL_DIR` | USER_FACING (chemin), migrer |
| 2598-2603 | USER_FACING | `hermes` / `hermes setup` / `hermes config` / `hermes config edit` / `hermes gateway install` / `hermes update` | USER_FACING (6 commandes), migrer vers `indagis` etc. |
| 2609-2612 | USER_FACING | "'hermes' was linked into $(get_command_link_display_dir)..." + "'hermes' was linked into /usr/local/bin and is ready to use" | USER_FACING, migrer |
| 2630-2641 | USER_FACING | "Node.js could not be installed automatically..." + "Browser tools need Node.js. Install manually" | Préserver (neutre) |
| 2643-2653 | USER_FACING | "ripgrep (rg) was not found. File search will use grep as a fallback..." | Préserver (neutre) |

→ 12+ USER_FACING (1 chemin + 6 commandes + 2 messages de succès).

### 24. ensure_browser (L2657-2725)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 2659-2660 | TECHNICAL | `local node_bin="$HERMES_HOME/node/bin/node"` | **Cible** : migrer vers `$INDAGIS_HOME/node/bin/node` (prioritaire), `$HERMES_HOME/node/bin/node` (repli) |
| 2669 | TECHNICAL | `npm_bin="$(command -v npm 2>/dev/null || echo "$HERMES_HOME/node/bin/npm")"` | Idem |
| 2690 | TECHNICAL | `export PATH="$HERMES_HOME/node/bin:$PATH"` | Idem |
| 2692-2700 | USER_FACING | "Explicit browser override set -- skipping bundled Chromium download" | USER_FACING, migrer vers "Indagis will use" / neutre |

→ 1 USER_FACING, 3 TECHNICAL critiques (chemins $HERMES_HOME/node).

### 25. clear_electron_build_cache (L2765-2824)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 2765-2773 | DOCSTRING | "the next `npm run pack` re-downloads and re-stages from scratch. A corrupt zip in the per-user Electron download cache - most often a partial/resumed download that leaves concatenated junk - makes electron-builder's `unpack-electron` extract a tree MISSING the electron binary, so the `electron`->`Hermes` rename" | DOCSTRING référence la chaîne de renommage `electron`→`Hermes` (produit de build Electron-builder). **À traiter avec le rename macOS** : le bundle s'appelle `Hermes.app` car c'est le productName electron-builder, qui sera migré vers `Indagis.app` lors de la migration du productName. **DEFER tranche 5+** : ce nom est le résultat du build, pas de install.sh directement. |
| 2775-2824 | TECHNICAL | reste du code | Préserver |

→ 1 DOCSTRING critique (référence à `Hermes.app` qui est un DEFER).

### 26. install_desktop_voice_deps (L2921-2950)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 2921-2928 | DOCSTRING | "Desktop ships with working voice out of the box: eagerly install the wake-word + local-STT stacks ([wake] + [voice] extras) instead of leaving them to lazy first-use install. Policy change (Teknium, July 2026, #70509 testing)" | DOCSTRING (neutre) |
| 2940-2945 | USER_FACING+TECHNICAL | "Installing voice + wake-word dependencies (onnxruntime, faster-whisper — 1-3min)..." + "Voice + wake-word dependencies installed" + "Voice/wake dependency install failed — they will lazy-install at first use" | USER_FACING, neutre (pas de nom projet) |

→ 0 migration.

### 27. install_desktop (L2952-3165)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 2961-2963 | DOCSTRING | "more importantly check_node now enforces the build floor (Node >=26) and prepends the Hermes-managed Node to PATH" | DOCSTRING USER_FACING (référence "Hermes-managed Node"), migrer vers "Indagis-managed Node" |
| 3077-3093 | USER_FACING+TECHNICAL | test app built : `$desktop_dir/release/linux-unpacked/Hermes` puis `hermes` en repli, et `$desktop_dir/release/mac-arm64/Hermes.app` / `$desktop_dir/release/mac/Hermes.app` | **Cible critique** : `Hermes.app` est le productName electron-builder. **DEFER tranche 5+** (migration productName distincte). Le `linux-unpacked/Hermes` est aussi le résultat du build — **DEFER**. La branche fallback `hermes` (L3082) est une préservation d'ancien nom binaire, à garder comme repli. |
| 3125-3136 | DOCSTRING | "macOS: route through the same config-aware signing fixup as `hermes desktop`, so install/repair and self-update agree about the app's identity" | DOCSTRING USER_FACING (référence `hermes desktop`), migrer vers `indagis desktop` |
| 3137-3160 | USER_FACING | codesign + `hermes_cli.main import _desktop_macos_relaunchable_fixup` | **DEFER tranche 5+** : `hermes_cli.main` est le nom du package Python. Cible distincte. |

→ 2 DOCSTRING USER_FACING, 4 DEFER (Hermes.app, linux-unpacked/Hermes, hermes_cli.main).

### 28. run_stage_body / run_stage_protocol (L3180-3318)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 3180-3278 | TECHNICAL | switch case sur stage | Préserver (noms de stages sont déjà neutres : prerequisites, repository, venv, python-deps, node-deps, path, config, setup, gateway, desktop, complete) |
| 3255-3257 | DOCSTRING | "the Hermes-managed Node provisioned during prerequisites/node-deps (at $HERMES_HOME/node/bin) isn't on PATH here" | DOCSTRING USER_FACING (référence "Hermes-managed Node", "$HERMES_HOME/node/bin"), migrer vers "Indagis-managed Node" et "$INDAGIS_HOME/node/bin" |
| 3267-3272 | DOCSTRING | "Code-scoped stamp: write next to the install tree, not into $HERMES_HOME. $HERMES_HOME is a shared data dir (it can be bind-mounted into a Docker gateway too), so a stamp there gets clobbered by the container's 'docker' stamp and wrongly blocks 'hermes update' on this host install. See detect_install_method()." | DOCSTRING USER_FACING (référence `hermes update` + commentaire), migrer vers "indagis update" |
| 3295-3297 | TECHNICAL | Skipping $stage (non-interactive bootstrap) | Préserver |

→ 2 DOCSTRING USER_FACING.

### 29. main (L3324-3360)

| Lignes | Catégorie | Contenu | Décision par défaut |
|---|---|---|---|
| 3324-3359 | TECHNICAL | orchestration main(), détecte_os, install_uv, etc. | Préserver |
| 3354-3359 | DOCSTRING | "Code-scoped stamp: write next to the install tree, not into $HERMES_HOME..." (reprise L3267) | DOCSTRING USER_FACING, migrer `hermes update` → `indagis update` |
| 3370 | TECHNICAL | dispatch MANIFEST_MODE/STAGE_NAME/ENSURE_DEPS/main | Préserver |

→ 1 DOCSTRING USER_FACING (référence `hermes update`).

## Récapitulatif

### Par catégorie

| Catégorie | Total occurrences | Sites principaux |
|---|---|---|
| USER_FACING (à migrer) | ~95 | banner (L211-220), --help (L160-198), 3 launchers (L1736-1804), copy_config_templates (L1923-1990), setup_path shims, print_success (L2576-2655), maybe_start_gateway (L2459-2532), 3 références à "Hermes Agent" / "hermes update" / "hermes --tui" / "hermes gateway" / "hermes setup" / "hermes whatsapp" dans les logs |
| DOCSTRING USER_FACING | ~12 | configure_managed_node_npm_prefix, install_uv, resolve_install_layout, attempt_install_git, write_bootstrap_marker, run_stage_body, main |
| TECHNICAL critique (cible de la fonction de résolution) | ~22 | `HERMES_HOME` (L48, L560, L846, L954, L963-965, L969, L1924, L2036, L2244, L2255, L2259, L2309, L2330, L2441, L2463, L2520, L2540, L2556, L2564, L2659, L2669, L2690), `$INSTALL_DIR/hermes` (L1702), `linux-unpacked/Hermes` (L3079-3082) |
| DEFER (hors tranche 5) | ~7 | `Hermes.app` (macOS bundle), `linux-unpacked/Hermes` (Linux unpacked binary), `hermes_cli.main` (Python package), `hermes-agent[extra]` (parse pyproject.toml), SOUL.md content (L1961) |
| ATTRIBUTION | ~5 | URLs `https://github.com/NousResearch/hermes-agent.git` (L46-47), "by Nous Research" (L218) |

### Sites critiques pour la fonction de résolution centralisée (point 3 du brief)

Ce sont les **points où HERMES_HOME est lu comme valeur par défaut** et où un script shell doit basculer vers INDAGIS_HOME en priorité tout en gardant HERMES_HOME en repli :

1. **L48** : `HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"` — initialisation, à étendre avec INDAGIS_HOME.
2. **L1924** : `mkdir -p "$HERMES_HOME"/{cron,sessions,...}` — création des sous-répertoires.
3. **L2036, L2244, L2255, L2259, L2441, L2520** : chemins vers `.env` et `logs/gateway.log` (USER_FACING).
4. **L560, L846, L954, L963-965, L969** : chemins vers `bin/uv`, `node/bin/node`, etc. (variable technique critique).
5. **L2659, L2669, L2690** : `HERMES_HOME/node/bin/...` (ensure_browser).
6. **L1702, L1704, L1712, L1725, L1745, L1752, L1755, L1762** : résolution du binaire `hermes` à lancer (USER_FACING, devient `indagis`).
7. **L2564-2573** : `$INSTALL_DIR/.hermes-bootstrap-complete` — marker (DEFER ou migration de nom avec repli).
8. **L3079-3093** : `$desktop_dir/release/.../Hermes(.app|)` — binaire produit (DEFER).
9. **L1625** : regex parse `hermes-agent\[...\]` dans pyproject.toml — **BUG FONCTIONNEL** (cf. §16, à corriger en tranche séparée).

### Sites équivalents aux écritures .zshrc / .bashrc / .profile (L1855-1863 et équivalents)

C'est ici que `install.sh` persiste le PATH dans les fichiers rc de l'utilisateur. La fonction de résolution doit aussi être consciente de ces sites pour que les PATH_LINE écrits contiennent bien le chemin `INDAGIS_HOME` (prioritaire) avec repli.

| Lignes | Fichier rc | Contenu |
|---|---|---|
| **L1855-1863** | `~/.zshrc` (et `~/.zprofile` si existe) | `PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'` + commentaire `# Hermes Agent — ensure ~/.local/bin is on PATH` + `echo "$PATH_LINE" >> "$SHELL_CONFIG"` |
| **L1865-1868** | `~/.bashrc` + `~/.bash_profile` | `SHELL_CONFIGS+=("$HOME/.bashrc")` / `SHELL_CONFIGS+=("$HOME/.bash_profile")` |
| **L1869-1875** | `~/.config/fish/config.fish` | `IS_FISH=true` + `FISH_CONFIG="$HOME/.config/fish/config.fish"` + `fish_add_path "$HOME/.local/bin"` |
| **L1877-1879** | `~/.bashrc` + `~/.zshrc` (fallback autres shells) | `[ -f "$HOME/.bashrc" ] && SHELL_CONFIGS+=("$HOME/.bashrc")` |
| **L1883** | `~/.profile` | `[ "$IS_FISH" = "false" ] && [ -f "$HOME/.profile" ] && SHELL_CONFIGS+=("$HOME/.profile")` |
| **L1885-1894** | tous les fichiers rc détectés | `PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'` + `echo "$PATH_LINE" >> "$SHELL_CONFIG"` |
| **L1896-1904** | `~/.config/fish/config.fish` | `fish_add_path "$HOME/.local/bin"` |
| **L1906-1909** | tous | log warning + PATH_LINE manual fallback |
| **L1911** | tous | `log_info "~/.local/bin already on PATH"` |

C'est l'équivalent PowerShell des `SetEnvironmentVariable("Path", ..., "User")` côté install.ps1 (L1316, L1336, L1412, L1502, L1509, L2662-2681). Les deux faces (bash + PowerShell) doivent être traitées ensemble par la fonction de résolution centralisée pour garantir la cohérence du PATH_LINE écrit.

### Hypothèses de la tranche 5

- La fonction de résolution centralisée s'appellera `get_indagis_home()` (équivalent Python de `get_hermes_home` côté `hermes_constants.py`).
- **Priorité** : `INDAGIS_HOME` env > `$HOME/.indagis` > `HERMES_HOME` env > `$HOME/.hermes`.
- **Version cible de suppression de l'alias** : à proposer dans le rapport — les sessions profil sont déjà HOME-anchored (cf. AGENTS.md "Profile operations are HOME-anchored"), donc la migration de l'alias est cadrée par la sortie de la Phase 5.

## Décision requise

- Validation de la grille de classification (5 catégories + DEFER) ;
- Validation de la liste des sites critiques (8 points pour la fonction de résolution) ;
- Validation du périmètre de la cartographie (install.sh seul) avant que je passe à la section Compat-contract du README desktop (point 2).
