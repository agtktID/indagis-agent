# Ticket — Bug fonctionnel : regex `hermes-agent\[...\]` morte dans install.sh:1625 et install.ps1:2487

## Statut

- **Type** : Bug fonctionnel isolé (signalé en tâche 3 du brief 2026-08-08)
- **Sévérité** : MINEURE (pas de crash, mais chemin mort dans le tier 2 du fallback pip)
- **Tranche** : À traiter en tranche séparée, **PAS** dans la cartographie actuelle
- **Commit de référence** : a67b2bb98
- **Branche** : feat/rebranding
- **Fichiers concernés** :
  - `scripts/install.sh` ligne 1625 (regex `hermes-agent\[...\]` morte)
  - `scripts/install.ps1` ligne 2487 (même regex, dans un heredoc Python)
- **Fichiers de preuve (verts)** :
  - `tests/test_project_metadata.py:80-82`
  - `tests/test_termux_all_extra_compat.py:14-16`
- **Référence** : `pyproject.toml:4` (où `name = "indagis-agent"` est défini)

## Symptôme

Les deux installateurs extraient la liste des extras `[all]` de `pyproject.toml` via un regex qui cherche le nom de package upstream `hermes-agent`. Or `pyproject.toml:4` a déjà été migré vers `name = "indagis-agent"` sur la branche `feat/rebranding`.

Résultat à l'exécution : `_ALL_EXTRAS_CSV=""` (variable vide). Le code entre dans la branche `Write-Warn "Could not parse [all] from pyproject.toml; Tier 2 will be a no-op."` et `install_tier` n'est jamais appelé avec la liste filtrée. Le tier 2 du fallback pip (`install_tier "all minus known-broken"` + `".[$safeAll]"`) est mort. Seul le tier 1 (`install_tier "all" ".[all]"`) est utilisé en permanence.

## Impact opérationnel

- **Pas de crash** : le tier 1 fonctionne, l'installation aboutit.
- **Filtrage cassé** : si un jour un extra PyPI est cassé et `_BROKEN_EXTRAS` est populé, le tier 2 ne pourra pas filtrer dynamiquement. L'utilisateur recevra `".[all]"` complet, et l'install échouera.
- **Désynchronisation** : les 2 installateurs (bash + PowerShell) ont exactement le même bug, mais les 2 tests qui valident la migration de `pyproject.toml` sont verts. La parité est rompue.

## Citation littérale des sites

### install.sh:1625 (à l'intérieur du heredoc Python L1617-1632)

```
m = re.search(r"hermes-agent\[([\w-]+)\]", s)
```

### install.ps1:2487 (à l'intérieur du heredoc Python L2479-2492)

```
m = re.search(r'hermes-agent\[([\w-]+)\]', s)
```

**Périmètre strict** : L2487 est le **seul** site contenant la regex `hermes-agent\[...\]` dans `install.ps1`. Vérification faite par lecture littérale des 4 lignes voisines citées dans les cartographies précédentes (L1693, L2247, L2476, L2625) : aucune ne contient le mot `hermes-agent`. Le seul autre site contenant exactement le même regex est `install.sh:1625`. **2 sites au total**, **0 doublon**.

### tests/test_project_metadata.py:80-82

```
        offending = [
            spec for spec in all_extra_specs
            if f"hermes-agent[{extra}]" in spec
        ]
```

### tests/test_termux_all_extra_compat.py:14-16

```
    assert '"indagis-agent[termux]"' in text
    assert '"hermes-agent[matrix]"' not in text.split("termux-all = [", 1)[1].split("]", 1)[0]
    assert '"hermes-agent[voice]"' not in text.split("termux-all = [", 1)[1].split("]", 1)[0]
```

### pyproject.toml:4

```
name = "indagis-agent"
```

## Correction proposée

**2 sites à patcher, en parité stricte** :

1. `scripts/install.sh:1625` :
   - **Avant** : `m = re.search(r"hermes-agent\[([\w-]+)\]", s)`
   - **Après** : `m = re.search(r"indagis-agent\[([\w-]+)\]", s)`

2. `scripts/install.ps1:2487` :
   - **Avant** : `m = re.search(r'hermes-agent\[([\w-]+)\]', s)`
   - **Après** : `m = re.search(r'indagis-agent\[([\w-]+)\]', s)`

**Aucun changement dans les tests** : les 2 tests sont déjà verts et valident la migration.

## Test de non-régression

Après correction, exécuter :
```bash
source .venv/bin/activate && pytest tests/test_project_metadata.py tests/test_termux_all_extra_compat.py -v
```

Attendu : les 2 tests restent verts. (Ils ne testent pas les installateurs, ils testent `pyproject.toml`.)

**Test E2E** : après la correction, exécuter `bash scripts/install.sh --no-venv --skip-setup` (ou un sous-stage) sur un checkout propre, et vérifier que `_ALL_EXTRAS_CSV` n'est plus vide :
```bash
bash -c 'source .venv/bin/activate && python -c "import tomllib; data = tomllib.load(open(\"pyproject.toml\",\"rb\")); import re; specs = data[\"project\"][\"optional-dependencies\"][\"all\"]; extras = []; 
[extras.append(m.group(1)) for s in specs if (m := re.search(r\"indagis-agent\\[(?:[\\w-]+)\\]\", s))]; print(\",\".join(extras))"'
```

Attendu : CSV non vide listant les extras `[all]`.

## Hors scope de ce ticket

- Le rebrand de `name = "hermes-agent"` (impossible : déjà migré, ticket vide)
- Le rebrand du bundle ID macOS `com.nousresearch.hermes` (Phase 5 item séparé)
- Le rebrand du repo GitHub `NousResearch/hermes-agent` → `NousResearch/indagis-agent` (DEFER tranche migration repo)
- La migration de l'URL `hermes-agent.nousresearch.com` (DEFER tranche migration infra)

## Statut d'ouverture

**OUVERT** — à programmer en tranche dédiée après validation des cartographies et de la section Compat-contract du README desktop.
