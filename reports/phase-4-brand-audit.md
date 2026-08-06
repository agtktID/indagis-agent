# Phase 4 — Brand audit (G14 livrable)

**Date :** 2026-08-06
**Commit analysé :** `0b597586cb` (Phase 3 + CHANGELOG)
**Branche :** `feat/rebranding`
**Working tree de référence :** clean
**Phase 3 :** validée (G2/G6/G7/G9 clos, web + TUI builds + tests verts)

---

## Inventaire initial (audit-only, aucune modification effectuée)

Commande : `rg -n -i 'Hermes Agent|Hermes|hermes-agent|Nous Research|\.hermes' hermes_cli web ui-tui README.md website assets package.json pyproject.toml CHANGELOG.md` (avec exclusions `.git/**`, `node_modules/**`, `dist/**`, `build/**`, `*.lock`).

**Total : 24 808 occurrences** sur le périmètre G14.

### Distribution top-30 par fichier

| Fichier | Occurrences | Catégorie dominante (estimation) |
|---|---:|---|
| `hermes_cli/main.py` | 847 | CLI user-facing (G1 cible) + technique (parser CLI, docstrings) |
| `hermes_cli/web_server.py` | 481 | Backend labels + thèmes catalogue (G2 partiellement fermé) |
| `website/docs/reference/cli-commands.md` | 429 | Doc produit (G5 cible) |
| `hermes_cli/gateway.py` | 365 | Technique (noms d'événements, modules internes) |
| `website/i18n/zh-Hans/.../cli-commands.md` | 302 | Doc produit traduite (G5 cible) |
| `hermes_cli/update_cmd.py` | 277 | CLI user-facing (G1) |
| `hermes_cli/setup.py` | 235 | CLI user-facing (G1) |
| `website/docs/integrations/providers.md` | 234 | Doc produit (G5) |
| `hermes_cli/config.py` | 232 | Technique (noms de clés de config) |
| `hermes_cli/auth.py` | 224 | Technique (noms de clients OAuth, scopes) |
| `website/.../autonomous-ai-agents-hermes-agent.md` | 210 | Doc produit (G5) |
| `website/docs/user-guide/configuration.md` | 205 | Doc produit (G5) |
| `website/docs/user-guide/docker.md` | 187 | Doc produit (G5) |
| `hermes_cli/kanban_db.py` | 182 | Technique (noms de tables SQLite) |
| `website/docs/reference/environment-variables.md` | 177 | Doc produit (G5) — référence env vars |
| `website/docs/getting-started/nix-setup.md` | 171 | Doc produit (G5) |
| `hermes_cli/doctor.py` | 165 | CLI user-facing (G1) |
| `hermes_cli/model_switch.py` | 157 | CLI user-facing (G1) |
| `hermes_cli/config_defaults.py` | 150 | Technique (défauts de config) |
| `website/docs/user-guide/features/web-dashboard.md` | 142 | Doc produit (G5) |
| `hermes_cli/uninstall.py` | 134 | CLI user-facing (G1) |
| `hermes_cli/tools_config.py` | 133 | Technique |
| `hermes_cli/tips.py` | 129 | CLI user-facing (G1) |
| (autres `hermes_cli/*.py`) | ~3500 | Mix technique / user-facing |
| `web/src/i18n/*.ts` (17 fichiers) | 2 par fichier = **34** | i18n user-facing (G3) |
| `README.md` | 11 | README rebrand (G4) |
| `website/` (reste, ~250 fichiers) | ~16 000 | Doc produit (G5) |

### Catégorisation par type (cahier §4)

| Catégorie | Volume estimé | Action |
|---|---:|---|
| Texte produit visible (CLI help, i18n, README) | ~2 000 | **À remplacer** (G1, G3, G4) |
| Doc technique site web | ~16 000 | **Traiter par lots** (G5) |
| Nom de module interne (`hermes_cli`, `hermes_constants.py`) | technique | **Conserver** (cahier §3.2) |
| Import Python interne (`from hermes_cli import …`) | technique | **Conserver** |
| Attribution / licence (MIT, NousResearch fork) | ~150 (mentions) | **Conserver** (cahier §3.3) |
| Référence historique (issue #1234 upstream, etc.) | ~50 | **Conserver ou annoter** |
| Exemple de commande upstream (`hermes setup`) | ~200 | **Adapter si contexte Indagis, sinon conserver avec note** |
| URL upstream (`github.com/NousResearch/hermes-agent`) | ~300 | **Conserver si upstream**, reformuler label |
| Compatibilité / migration | ~50 | **Conserver et documenter** |
| Test technique (vérifie branding) | quelques-uns | **Adapter seulement si test vise branding** |

---

## Périmètre G8 spécifique — assets visuels

### Assets existants (étape 1 G8)

```
assets/banner.png                                # 1145×196 PNG — banner README, à remplacer
apps/desktop/assets/icon.png                     # 1024×1024 PNG — Electron icon, à rebrand
apps/desktop/assets/icon.ico                     # Windows multi-res ICO — à rebrand (travail design)
apps/desktop/public/apple-touch-icon.png         # 180×180 — mobile favicon
apps/desktop/public/hermes.png                    # sprite source (probable)
apps/desktop/public/hermes-sprite.png            # sprite compilé
apps/desktop/public/hermes-frames/                # 8 frames d'animation
apps/bootstrap-installer/src-tauri/icons/        # 32×32, 128×128, 128×128@2x, icon.icns, icon.ico (Tauri)
hermes_cli/web_dist/                              # build output (gitignored)
.github/pr-screenshots/                            # historique (NE PAS toucher)
```

### Classification G8

| Type | Action | Effort |
|---|---|---|
| **A** — `assets/banner.png` (README) | **À remplacer** | Faible (1 SVG → PNG) |
| **B** — `apps/desktop/assets/icon.png` | **À rebrand** | Moyen (design icon 1024×1024) |
| **C** — `apps/desktop/assets/icon.ico` | **À rebrand** | Élevé (multi-résolutions Windows) |
| **D** — `apps/desktop/public/apple-touch-icon.png` | **À rebrand** | Moyen |
| **E** — `apps/desktop/public/hermes-frames/` (8 frames) | **À rebrand** | Élevé (régénération sprite cohérent) |
| **F** — `apps/desktop/public/hermes-sprite.png` | **À rebrand** | Élevé |
| **G** — `apps/bootstrap-installer/src-tauri/icons/` | **À rebrand** | Moyen (multi-tailles) |
| **H** — `hermes_cli/web_dist/` | **Gitignored**, non touché | 0 |
| **I** — `.github/pr-screenshots/` | **Historique**, non touché | 0 |

**Découpage proposé :**

- **G8-A** (Phase 4) : créer `assets/branding/{indagis-logo,indagis-mark,indagis-avatar,favicon}.svg` + `assets/branding/README.md` + `web/public/branding/{indagis-mark,favicon}.svg` + `web/src/components/branding/IndagisAvatar.tsx`. **~6 fichiers SVG simples dérivés du cyan diamond déjà créé en Phase 3** (favicon). Effort : 1 commit.
- **G8-B/C/D/E/F/G** (Phase 5, hors Phase 4) : régénération des icônes Electron/Tauri/sprites demande un travail design (sketch → PNG/ICO multi-résolution). Ces assets sont visuels, pas du code. Effort estimé : 1-2 sessions design.

---

## Risques identifiés

- **Volume G5** : ~16 000 occurrences dans `website/docs/`. Répartition par lots nécessaire pour éviter un commit illisible. Le cahier §10.3 prévoit explicitement des lots avec `git diff --stat` entre chaque lot.
- **Sprite frames** : 8 PNG d'animation cohérente (hermes-frames/). Les remplacer individuellement casse la cohérence visuelle. À traiter en bloc ou pas du tout en Phase 4.
- **i18n traductions humaines** : 17 langues × 2 chaînes = 34 modifications. Les langues non-anglophones utilisent `Hermes` comme nom propre (ex. `更新 Hermes`, `Hermes aktualisieren`). Je peux remplacer par `Indagis` partout (mot propre), mais vérifier qu'aucune traduction existante n'utilise une variante longue.
- **Tests qui vérifient le branding** : rare mais possible. À inspecter avant tout remplacement (chercher `expect(... "Hermes Agent")` dans les `.test.ts`).
- **Compatibilité alias `hermes` CLI** : si un alias de compatibilité existe (cf. cahier §3.2 mentionne "commande de compatibilité : hermes"), il doit rester fonctionnel.

---

## Décision requise avant de commencer les modifications

Le cahier §13 demande l'autorisation avant tout commit/push. Je propose :

1. **G1** (hermes_cli/{main,banner,completion,update_cmd,setup,doctor,uninstall}.py) : exécution mécanique, ~100 chaînes user-facing. Risque : faible (docstrings argparse).
2. **G3** (web/src/i18n/*.ts, 34 chaînes) : exécution mécanique. Risque : faible (clé i18n conservée).
3. **G4** (README.md, 11 occurrences) : modif manuelle soignée pour la section attribution. Risque : moyen (badges, structure).
4. **G8-A** (assets/branding/) : création de SVG dérivés du cyan diamond Phase 3. Risque : faible.
5. **G5** (website/, ~16 000 occurrences) : **par lots de 10-20 fichiers maximum par commit** avec rapport intermédiaire. Risque : élevé en volume.
6. **G14** (rapport final) : ce document + rapport de fin.

**Question pour Hermes Agent** : (a) confirmer l'ordre G1→G3→G4→G8-A→G5→G14 ; (b) confirmer la limite de 10-20 fichiers par lot pour G5 ; (c) confirmer que G8-B à G8-G (icons Electron/Tauri/sprites) sont hors Phase 4.

---

**Critères G8 révisés (2026-08-06, post-feedback) :**

| Sous-tâche | Périmètre | Phase |
|---|---|---|
| **G8-A** | Kit de branding Indagis : `assets/branding/{indagis-logo,indagis-mark,favicon}.svg`, `assets/branding/README.md` | **Phase 4** |
| **G8-B** | `apps/desktop/public/hermes-frames/` (sprite animations) | Phase 5 |
| **G8-C** | `apps/desktop/public/hermes.png` | Phase 5 |
| **G8-D** | `apps/desktop/public/hermes-sprite.png` | Phase 5 |
| **G8-E** | `apps/desktop/assets/icon.{png,ico}` (Electron) + `apps/bootstrap-installer/src-tauri/icons/` | Phase 5 |
| **G8-F** | `apps/desktop/src/components/pet/pet-egg-sheet.png` | Phase 5 |
| **G8-G** | `.github/pr-screenshots/*` (historique) | Hors scope (jamais) |

**Deferred assets (Phase 5) :**

Les assets upstream suivants sont **intentionnellement reportés** parce que
leur usage runtime Indagis n'a pas été établi par cet audit :

- `apps/desktop/public/hermes-frames/` (8 frames sprite)
- `apps/desktop/public/hermes.png`
- `apps/desktop/public/hermes-sprite.png`
- `apps/desktop/assets/icon.{png,ico}`
- `apps/bootstrap-installer/src-tauri/icons/`
- `apps/desktop/src/components/pet/pet-egg-sheet.png`
- `.github/pr-screenshots/*`

Règle de décision appliquée :

- Asset chargé par le runtime actif (web, TUI, Electron, Tauri) → traiter
- Asset utilisé uniquement dans une doc historique → conserver
- Asset non référencé → ne pas toucher

Les sprite frames (`hermes-frames/`) **ne sont pas remplacés en masse** :
c'est une animation cohérente qui doit être régénérée d'un bloc ou pas du
tout. Hors Phase 4.

---

## Critères de sortie Phase 4 (post-feedback)

La Phase 4 sera acceptée si :

1. `reports/phase-4-brand-audit.md` est commité séparément (immuable)
2. G1 ne modifie aucun import ni nom de module interne
3. Les 34 chaînes i18n sont traitées (G3)
4. Les 11 occurrences README sont classifiées et traitées (G4)
5. Le kit G8-A est créé
6. G8-B à G8-G sont documentés comme reportés en Phase 5
7. G5 est traité par lots thématiques (G5-01 à G5-09)
8. G14 final classe toutes les occurrences restantes
9. Tests web et TUI passent
10. `git diff --check` passe
11. Attribution Hermes/MIT reste présente
12. Working tree propre
13. **Aucun push final sans revue du diff**

---

## Plan d'exécution par lots G5 (organisation recommandée)

Avec ~16 000 occurrences / ~250 fichiers, organisation thématique :

| Lot | Périmètre | Critère |
|---|---|---|
| **G5-01** | guides installation (`getting-started/`) | commandes `indagis` + retrait Hermes dans les URLs publiques |
| **G5-02** | guides CLI (`reference/cli-commands.md`) | doc des commandes `indagis` |
| **G5-03** | guides dashboard (`user-guide/features/web-dashboard.md`, `kanban.md`, `skills.md`) | mentions produit |
| **G5-04** | guides plugins (`plugins/`) | label `indagis-plugins` |
| **G5-05** | guides skills (`user-guide/skills/`) | titre + corps |
| **G5-06** | guides providers (`integrations/providers.md`) | endpoints LLM externes (URLs upstream conservées) |
| **G5-07** | guides desktop (`integrations/desktop.md`, `docker.md`) | paths `~/.indagis/` |
| **G5-08** | guides sécurité (`security.md`, `permission.md`) | texte conceptuel |
| **G5-09** | relecture finale + commits résiduels | `git diff --stat`, `git diff --check` |

**Règle G5** (cahier §10.3) : ne jamais remplacer en bloc les blocs Python /
JavaScript / JSON / shell dans les guides — ces chaînes peuvent représenter
des noms d'API internes. Adapter au cas par cas.

---

## Validation post-Phase-3 (rappel)

Tous les checks Phase 3 étaient verts (commit `f6faecae4f`) :

- `python3 -c "import ast; ast.parse(...)"` sur `hermes_cli/web_server.py` : **PASS**
- Web typecheck (`bunx tsc --noEmit`) : **PASS**
- Web tests (`bunx vitest run`) : **27 fichiers, 191/191 tests**
- Web build (`bunx vite build`) : **PASS**
- TUI build (`bun run build` dans packages/hermes-ink/) : **PASS**
- TUI typecheck (`bunx tsc --noEmit -p tsconfig.json`) : **PASS**
- TUI theme tests (`bunx vitest run src/__tests__/theme.test.ts`) : **49/49 tests**
- `_normalise_theme_definition` extraite par AST + appliquée au YAML utilisateur : **PASS**
- `grep "Hermes Teal"` : **0 résidu**
- Push `origin/feat/rebranding` : SHA `0b597586cb`

**Aucun changement de Phase 3 n'a été annulé.**
