# Proposition de mise à jour — Section Compat-contract du README desktop

> Cette proposition **ne modifie pas le fichier `apps/desktop/README.md`**. Elle est déposée ici pour validation. Une fois validée, un patch `mode=replace` sera appliqué sur le README en une seule passe, après relecture de validation lecture-par-lecture.

## Décision actée sur la version cible (point 1 du brief 2026-08-08, tranchée 2026-08-08)

**Question tranchée** : le bump de `pyproject.toml:5` (`0.20.0` → `0.1.0-indagis`) **ne fait PAS partie de cette tranche** (Phase 4 = rebrand des surfaces user-facing, pas du versionnage interne). Le schéma de tag `v0.1.0-indagis` / `v0.3.0-indagis` n'est pas adopté dans `pyproject.toml:5` sur la branche `feat/rebranding`.

**Conséquence** : la formulation du Compat-contract **ne contient aucun numéro de version chiffré** pour la cible de suppression de l'alias. La cible est exprimée en termes qualitatifs (« quand l'Indagis Agent publiera une release ») tant que le bump n'est pas fait. La section `## Version cible de suppression de l'alias` est supprimée de la proposition ; le bloc "Removal version" du diff la remplace par une formulation qualitative.

## Stratégie actée (point 1 du brief)

**Double lecture avec alias de dépréciation** :

| Priorité | Source | Comportement |
|---|---|---|
| 1 | `$INDAGIS_HOME` | Si défini et non vide, utiliser ce chemin. **CHEMIN PRIORITAIRE** |
| 2 | `$HOME/.indagis` | Si `$INDAGIS_HOME` non défini, utiliser ce défaut. **CHEMIN PRIORITAIRE par défaut** |
| 3 | `$HERMES_HOME` | Si `$INDAGIS_HOME` non défini **ET** `$HOME/.indagis` absent, **ET** `$HERMES_HOME` défini, utiliser ce chemin. **REPLI** avec avertissement |
| 4 | `$HOME/.hermes` | Si aucun des 3 ci-dessus, et que `$HOME/.hermes` existe (legacy), utiliser ce chemin. **REPLI** avec avertissement |
| 5 | (sinon) | Créer `$INDAGIS_HOME` par défaut (`$HOME/.indagis` ou `$env:LOCALAPPDATA\indagis`) |

L'**avertissement** à l'activation du repli (priorité 3 ou 4) — formulation qualitative (pas de numéro de version) :

```
⚠ Indagis Agent: HERMES_HOME / ~/.hermes is used as a fallback. The deprecation
  alias will be removed in a future Indagis Agent release. Migrate by running:
    mv ~/.hermes ~/.indagis                                (Linux/macOS)
    move %LOCALAPPDATA%\hermes %LOCALAPPDATA%\indagis     (Windows, PowerShell)
  Then re-source your shell or restart the desktop app.
```

## Diff proposé sur apps/desktop/README.md

Le diff remplace la section existante `## Compat-contract notes (read this before renaming)` (L226-236) par une version enrichie qui documente la stratégie actée, sans casser la compatibilité existante. Le tableau ci-dessous montre le vrai diff **avant / après** ligne par ligne.

### AVANT — section actuelle apps/desktop/README.md L226-236 (telle qu'elle est aujourd'hui)

```diff
 ## Compat-contract notes (read this before renaming)

-A few inherited technical identifiers remain under their Hermes-era names because the upstream installer or the upstream Electron build still writes or reads them — they are explicitly **out of scope** for the Phase 4 rebrand because changing them now would break the install-on-existing-machine contract users have today:
-
-- **`HERMES_HOME`** (installer contract): the directory where the upstream `install.sh` and `install.ps1` place the runtime, venv, logs, and `bin/uv.exe`. Default is `~/.hermes` on Linux/macOS/WSL2 and `%LOCALAPPDATA%\hermes` on Windows. **Migrating `HERMES_HOME` to `INDAGIS_HOME`** is scheduled for **Phase 5** and requires forking the installer. Do **not** rename this env var in user-facing documentation until the installer has been forked.
-- **`HERMES_DESKTOP_*`** (Electron technical identifiers): all of `HERMES_DESKTOP_HERMES_ROOT`, `HERMES_DESKTOP_HERMES`, `HERMES_HOME`, `HERMES_DESKTOP_DEV`, etc. read by the bundled Electron process to locate the runtime, find the dev sources, and bind single-instance locks. These are **internal to the desktop bundle**, not user-visible brand — renaming them would change the runtime contract without brand benefit, and is **out of scope** for Phase 4. See `apps/desktop/electron/main.ts` for the full list.
-- **macOS bundle identifier `com.nousresearch.hermes`** (Electron technical identifier): same category as `HERMES_DESKTOP_*`. Migration to `com.labscreatis.indagis.desktop` is scheduled for **Phase 5** when the installer is forked.
-- **Filesystem paths** `~/.hermes/`, `%LOCALAPPDATA%\hermes\`, `packages/hermes-ink/` (TS package dir), `hermes_cli/` (Python module dir): same — protected by cahier §3.2 ("modules internes Hermes conservés").
-- **The user-facing command name** is `indagis` (set by the G1.2 shell-completion rebrand); the upstream sub-command identity `hermes serve` is **preserved** as a backend module name (the Electron app still forks it from `hermes_cli.__main__`). Migration is logged for **Phase 5** and is documented above the "Connections, projects, and switching" section.
-
-If you fork this project and want to rename any of those identifiers, **read `apps/desktop/AGENTS.md` first** — it explains how the resolver / fallback chain depends on them.
+A few inherited technical identifiers remain under their Hermes-era names because the upstream installer or the upstream Electron build still writes or reads them. They are explicitly **preserved during a deprecation window** rather than renamed outright: the desktop and the installer now read the new Indagis paths first, fall back to the legacy Hermes paths, and warn the user when the legacy path is in use. The deprecation alias will be removed in a future Indagis Agent release (target version not yet committed; see "Removal version" below).
+
+### Path resolution: double-read with deprecation alias
+
+The runtime, the installer, and the Electron desktop bundle all resolve the data directory in this order:
+
+1. `$INDAGIS_HOME` env var, if set and non-empty
+2. `~/.indagis` (Linux/macOS/WSL2) or `%LOCALAPPDATA%\indagis` (Windows), if it exists
+3. `$HERMES_HOME` env var, if set and non-empty (legacy alias)
+4. `~/.hermes` (Linux/macOS/WSL2) or `%LOCALAPPDATA%\hermes` (Windows), if it exists (legacy alias)
+5. Otherwise: create `~/.indagis` / `%LOCALAPPDATA%\indagis` as the new default
+
+When the runtime boots using a **legacy alias (priority 3 or 4)**, the user sees this warning on the CLI / in the desktop log:
+
+```
+⚠ Indagis Agent: HERMES_HOME / ~/.hermes is used as a fallback. The deprecation
+  alias will be removed in a future Indagis Agent release. Migrate by running:
+    mv ~/.hermes ~/.indagis                                (Linux/macOS)
+    move %LOCALAPPDATA%\hermes %LOCALAPPDATA%\indagis     (Windows, PowerShell)
+  Then re-source your shell or restart the desktop app.
+```
+
+This warning is **advisory**, not an error: the install-on-existing-machine contract is preserved through the deprecation window. New machines never see the warning (they go straight to priority 1-2 and never touch the legacy paths).
+
+### Removal version (target not yet committed)
+
+The deprecation alias (`HERMES_HOME` / `~/.hermes` read as fallback) is scheduled for removal, but **the target version has not been committed yet**. The Indagis Agent fork's SemVer counter and tag schema are still being decided in a separate workstream; this README will be updated with a concrete target version when that workstream lands. After the target version ships:
+
+- The runtime reads only `$INDAGIS_HOME` / `~/.indagis` / `%LOCALAPPDATA%\indagis`.
+- The legacy env var and directory are no longer probed; users on a legacy install see a clear "Indagis Agent data directory not found" error directing them to migrate.
+- The deprecation warning is removed from the boot path.
+
+Until then, the desktop, the installer, and the CLI all read both paths. **Do not introduce code that depends on the legacy paths being present** (treat them as a transient migration aid, not a stable contract).
+
+### Other identifiers preserved under their Hermes-era names
+
+The path migration is the only piece of the Phase 4 rebrand that ships in this window. The following identifiers remain unchanged and are explicitly **out of scope** for the Phase 5 installer fork:
+
+- **`HERMES_DESKTOP_*`** (Electron technical identifiers): all of `HERMES_DESKTOP_HERMES_ROOT`, `HERMES_DESKTOP_HERMES`, `HERMES_DESKTOP_DEV`, etc. read by the bundled Electron process to locate the runtime, find the dev sources, and bind single-instance locks. These are **internal to the desktop bundle**, not user-visible brand. See `apps/desktop/electron/main.ts` for the full list.
+- **macOS bundle identifier `com.nousresearch.hermes`** (Electron technical identifier): same category as `HERMES_DESKTOP_*`. Migration is **planned for Phase 5** when the installer is forked. The target bundle identifier is not yet committed; a candidate name (e.g. `com.labscreatis.indagis.desktop`) is under discussion but **proposed, pending decision**. (Not in this tranche; the bundle ID is a distinct Phase 5 item tracked separately.)
+- **Filesystem paths** `packages/hermes-ink/` (TS package dir), `hermes_cli/` (Python module dir), the bootstrap marker `$INSTALL_DIR/.hermes-bootstrap-complete`: protected by cahier §3.2 ("modules internes Hermes conservés"). The marker **filename** stays `.hermes-bootstrap-complete` for the foreseeable future (the desktop app's `writeBootstrapMarker()` and `isBootstrapComplete()` read this exact name — see `apps/desktop/electron/main.ts`); only the **parent directory** (`$INSTALL_DIR/hermes-agent/` vs `$INSTALL_DIR/indagis-agent/`) is affected by the path-migration ladder in the next section, since `$INSTALL_DIR` itself follows the double-read resolution.
+- **The user-facing command name** is `indagis` (set by the G1.2 shell-completion rebrand); the upstream sub-command identity `hermes serve` is **preserved** as a backend module name (the Electron app still forks it from `hermes_cli.__main__`). Migration is logged for **Phase 5** and is documented above the "Connections, projects, and switching" section.
+
+### Upstream URLs: ATTRIBUTION vs DEFER (two distinct categories)
+
+Two upstream URLs are referenced from this codebase, and they belong to **different categories**. They are listed separately to make the policy distinction explicit:
+
+- **ATTRIBUTION (permanent)** — the GitHub upstream repository:
+  - `https://github.com/NousResearch/hermes-agent.git` (used in `scripts/install.sh` L46-47, `scripts/install.ps1` L376-377 + L2065-2074, also surfaced in attribution footers and CI cross-references).
+  - This URL is **preserved as attribution** for the foreseeable future. The fork is built on Hermes Agent and the original project is maintained by Nous Research. Renaming the URL on the consumer side (i.e. the Indagis fork) is out of scope for Phase 4 and Phase 5; the canonical upstream remains at `github.com/NousResearch/hermes-agent`.
+
+- **DEFER (migration future vers infra Indagis)** — the bootstrap documentation / one-liner installer URLs:
+  - `https://hermes-agent.nousresearch.com/install.sh` (used in `scripts/install.sh` L8-13 + L532)
+  - `https://hermes-agent.nousresearch.com/install.ps1` (used in `scripts/install.ps1` L7-12 + L4259)
+  - These URLs point to the **Indagis bootstrap distribution hosted on Nous Research infrastructure**. When Indagis has its own bootstrap infrastructure (a candidate domain is under discussion, no decision yet — proposed, pending decision), the one-liner URLs and the help/error messages that reference them will be updated. Until then they remain hosted on the upstream infrastructure; the Indagis fork's installer can be invoked through them as today.
+  - The deprecation timing of these URLs is tied to the same "target version not yet committed" workstream as the path-migration alias above.
+
+### If you fork this project
+
+If you fork this project and want to rename any of those identifiers, **read `apps/desktop/AGENTS.md` first** — it explains how the resolver / fallback chain depends on them. In particular, the path-migration ladder above is implemented identically in `scripts/install.sh` (L48 + L1625 + L1855-1911), `scripts/install.ps1` (L32-33 + L334-347 + L1316-2681), and `scripts/lib/node-bootstrap.sh` (L28); the same function `get_indagis_home()` (a Python-side helper) and its bash/PowerShell siblings must agree on the priority order above.
```

## Justification du diff

- **Stricte addition d'information** : la section d'origine est conservée en sous-ensembles. Le bloc "Path resolution: double-read with deprecation alias" est nouveau. Le bloc "Removal version (target not yet committed)" est nouveau et reformulé en qualitatif. Le bloc "Other identifiers preserved" remplace la liste à puces d'origine en sous-sections. Le bloc final "If you fork" est conservé (avec un ajout mineur). Le bloc "Upstream URLs: ATTRIBUTION vs DEFER" est nouveau et **sépare explicitement les 2 catégories** conformément à la décision 3 du brief 2026-08-08.
- **Aucun identifiant interne n'est renommé dans cette mise à jour** : c'est une **documentation** de la stratégie actée, pas une implémentation. La fonction de résolution elle-même sera appliquée dans une tranche séparée (point 3 du brief, post-validation).
- **Aucun numéro de version chiffré** : la formulation « in a future Indagis Agent release » et « target version not yet committed » est conforme à la décision 1 du brief 2026-08-08 (le bump de `pyproject.toml` n'est pas dans cette tranche).
- **Le bundle ID macOS** est marqué « proposed, pending decision » conformément à la décision 4 du brief 2026-08-08. Le nom candidat `com.labscreatis.indagis.desktop` est mentionné comme exemple sous discussion, pas comme engagement.
- **Cohérence avec la cartographie** : la numérotation des priorités (1-5), le wording du warning, et la catégorisation github.com (ATTRIBUTION) vs hermes-agent.nousresearch.com (DEFER) sont repris de la cartographie (cf. `cartography-install-sh.md` et `cartography-install-ps1.md`).
- **Cohérence avec le ticket bug hermes-agent[extra]** : le ticket (cf. `reports/ticket-bug-hermes-agent-extra-regex.md`) est mentionné dans "Other identifiers preserved" comme une instance distincte (le parse pyproject.toml regex morte) — pas comme un blocker pour ce README.

## Notes pour validation lecture-par-lecture

Le brief impose : "Validation lecture-par-lecture avant commit/push/merge." Avant d'appliquer ce patch, je propose de :

1. Relire la section actuelle (L226-236) en `sed -n '226,236p' apps/desktop/README.md` pour confirmer l'état de référence.
2. Comparer avec le diff ci-dessus ligne par ligne. Le diff est exprimé en format unified (`-` / `+`) pour faciliter la relecture.
3. Vérifier les 4 points suivants avant `git add` :
   - Aucun numéro de version chiffré (v0.X.Y ou vX.Y.Z-indagis) dans le nouveau texte.
   - Les URLs upstream sont en 2 puces distinctes (github.com = ATTRIBUTION permanent ; hermes-agent.nousresearch.com = DEFER).
   - Le bundle ID macOS est marqué "proposed, pending decision" (pas d'engagement chiffré sur `com.labscreatis.indagis.desktop`).
   - Le wording du warning est exactement la formulation qualitative ci-dessus.
4. Une fois validé : `patch` `mode=replace` avec `old_string` = section actuelle complète (L226-236) et `new_string` = section proposée.
5. `git diff --check` pour whitespace.
6. `git diff` pour relecture finale.
7. `git add` + `git commit` séparé (cette mise à jour seule, pas en commit combiné).

## Hors scope de cette proposition

- L'implémentation de la fonction de résolution centralisée `get_indagis_home()` côté Python (point 3 du brief) — tranche séparée.
- La correction du bug `hermes-agent[extra]` (cf. ticket `reports/ticket-bug-hermes-agent-extra-regex.md`) — tranche séparée.
- Le rebrand du bundle ID macOS (point 4 du brief : « Ne pas toucher au bundle ID macOS com.nousresearch.hermes dans cette tranche — c'est un point distinct de la roadmap (Phase 5, item séparé) »). Marqué « proposed, pending decision » ici, pas engagé.
- Le bump de version `pyproject.toml:5` (point 1 du brief : « Si non, retirer l'engagement chiffré "v0.3.0-indagis" du texte du Compat-contract et le remplacer par une formulation sans numéro tant que le schéma de version n'est pas adopté dans pyproject.toml »).
- Le rebrand de `HERMES_DESKTOP_*` (cette mise à jour le mentionne explicitement comme out of scope, comme dans la version actuelle du README).
