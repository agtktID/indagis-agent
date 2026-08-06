# Indagis Agent — Audit des couches UI (Étape 0 du design system)

Date : 2026-08-06
Périmètre : `ui-tui/`, `web/`, `apps/`
Parent : `a712ac409a` (rebrand Phase 1+2)

## État actuel

| Couche | Stack | Système de thème | Fichiers de style clés |
|---|---|---|---|
| `ui-tui/` | Ink 6 + React 19 + TypeScript | skin via `@hermes/shared/skin` + `theme.ts` local | `src/theme.ts` (480+ lignes), `src/lib/color.ts`, `packages/hermes-ink/` |
| `web/` | Vite + React 19 + Tailwind 4 + `@nous-research/ui` 0.18 | token CSS dans `index.css` + `src/themes/{fonts,presets,context,types,index}.ts` | `src/index.css` (variables `--foreground/--midground/--background`, palette LENS_0 = Hermes teal), `src/themes/` |
| `apps/desktop/` | Electron 36 + Vite + React 19 + TypeScript | design system dédié, `DESIGN.md` de 4 Ko | `src/themes/` (data-driven), `DESIGN.md`, `AGENTS.md` |
| `apps/shared/` | TS pur, partagé TUI/desktop | types `SkinBranding`, `SkinColors` | `src/skin.ts` |
| `apps/bootstrap-installer/` | Tauri (Rust + React 19) | `theme.ts` local | `src/styles.css`, `src/theme.ts` |
| `ui-tui/packages/hermes-ink/` | sous-package Ink 6 | `theme.ts` miroir | `src/theme.ts` |

## Palette déjà embarquée (référence LENS_0)

`web/src/index.css` charge `@nous-research/ui/styles/globals.css` qui expose la palette LENS_0 (« Hermes teal »). L’examen des valeurs trouve notamment `#041c1c` (midground), `#ffe6cb` (foreground), `#ffffff`. Aucun lien direct avec l’Indagis palette (#0B0F14, #37D5D6). Le rebadge visuel est donc à faire sur **toutes** les couches.

## Tokens de thème actuellement déclarés

- `ui-tui/src/theme.ts` : 480+ lignes, identité de marque explicite `name: 'Hermes Agent'`, `icon: '⚕'`, brand = Hermes. Polarity-aware, ANSI 256 normalisé. Très dense : pas une simple palette, un vrai moteur de thème.
- `web/src/index.css` : variables CSS `--foreground/--midground/--background` avec LENS_0 figé. Indagis tokens devront remplacer ces variables.
- `apps/desktop/src/themes/` : data-driven, palette déjà séparée de la logique (équivalent mature de ce que le brief demande).
- `apps/bootstrap-installer/src/theme.ts` : simple `theme.ts` qui mérite d’être aligné.

## Bannière ASCII

`ui-tui/src/banner.ts` est la bannière Ink de lancement. Elle est référencée par `app.tsx` et embarque probablement le `⚕` et le `Hermes Agent`. Le brief demande un bloc ASCII en Cyber Cyan. Le binaire `INDAGIS` proposé dans le brief n’est pas adapté à un terminal moderne qui supporte Unicode. Je propose plutôt un bloc ASCII 7 lignes basé sur des caractères `█` (BLOC PLEIN) qui s’imprime dans tous les terminaux, y compris en CP-1252.

## Fichiers marqués « à modifier sans toucher à la logique »

- `ui-tui/src/theme.ts` : remplacer `BRAND.name` et `BRAND.icon`. Ne pas toucher à `DARK_SEEDS`/`LIGHT_SEEDS` ni au moteur de contraste (pixel-sampling + lift canon).
- `ui-tui/src/banner.ts` : remplacer le bloc ASCII. Ne pas toucher au code Ink de rendu.
- `web/src/index.css` : remplacer les variables `--foreground/--midground/--background/--midground-base` par les tokens Indagis.
- `web/src/themes/presets.ts` : si un preset `LENS_0` existe, créer un preset `LENS_INDAGIS` plutôt que d’écraser.
- `apps/desktop/src/styles.css` (ou équivalent) : introduire les tokens Indagis dans la couche theme-sdk.
- `apps/bootstrap-installer/src/styles.css` + `theme.ts` : aligner sur la même palette.
- `apps/shared/src/skin.ts` : aucun changement de schéma requis. La palette est transmise via le réseau ; seul le défaut côté serveur change.

## Périmètre interdit confirmé

Aucune logique de palette, ANSI, contraste, lift, ou font-loading ne doit être modifiée. Le rebrand visuel est un remplacement de valeurs, pas un refactor de moteur.

## Volume estimé

| Fichier | Estimation |
|---|---|
| `ui-tui/src/theme.ts` | 5 à 10 lignes (BRAND) |
| `ui-tui/src/banner.ts` | 20 à 40 lignes (bloc ASCII) |
| `web/src/index.css` | 20 à 40 lignes (remplacement variables) |
| `web/src/themes/presets.ts` | 30 à 60 lignes (nouveau preset) |
| `apps/desktop/src/styles.css` | 40 à 80 lignes (tokens) |
| `apps/bootstrap-installer/src/styles.css` | 10 à 20 lignes |
| `apps/bootstrap-installer/src/theme.ts` | 5 à 10 lignes |

Total : 130 à 280 lignes modifiées sur 7 fichiers, plus 2 nouveaux assets SVG (logo, bannière). Aucun impact sur les 28 000+ lignes du moteur Python.

## Validation

Aucun fichier modifié. Cette étape est strictement un audit.

## Risques identifiés

1. Le moteur `ui-tui/src/theme.ts` est testé (chemin `__tests__/`). Toute modification de `DARK_SEEDS` casserait des tests. Je propose de ne modifier que `BRAND`, jamais `DARK_SEEDS` ni `LIGHT_SEEDS`.
2. `apps/desktop/DESIGN.md` (4 Ko) décrit des principes de design encore valides. Le rebrand n’a pas besoin d’y toucher sauf si je veux référencer la nouvelle palette.
3. Le rebrand de `@nous-research/ui` n’est pas applicable : c’est une dépendance externe. On s’aligne sur ce qu’elle expose, on ne la modifie pas.
4. Le site web contient un `favicon` et des assets `pr-assets/` que je n’ai pas audités. La validation les couvre en vrac.

## Décisions à prendre avant de toucher au code

1. Le brief fournit un bloc ASCII `INDAGIS` (7 lignes) construit avec des caractères `█`. Souhaitez-vous ce bloc exact, ou un bloc Indagis plus lisible en ASCII (par exemple `INDiGis` ou un blason sans caractères non-ASCII) ?
2. Pour la bannière, le brief indique `Agent Platform v0.1  |  Built on Hermes Agent (NousResearch, MIT)`. Voulez-vous conserver la mention « Built on Hermes Agent » ou la retirer pour un rebrand plus radical ?
3. Pour la web, le brief propose deux pistes : `tokens.css` (variables) ou `indagis.css` (Tailwind 4 `@theme inline`). Le projet utilise Tailwind 4 via `@import 'tailwindcss'`. Je recommande la piste `@theme` dans un nouveau fichier `web/src/styles/indagis.css` importé en plus de l’existant, pour ne pas casser LENS_0 utilisé par d’autres pages.
4. Le brief interdit « Matrix, vert-sur-noir, glitches ». La palette fournie est respectueuse. Je la copie à l’identique.

Sans ta confirmation sur les 4 points ci-dessus, je n’édite aucun fichier UI.
