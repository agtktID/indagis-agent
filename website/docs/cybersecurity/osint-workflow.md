---
id: osint-workflow
title: "Workflow OSINT avec Indagis Agent"
sidebar_position: 3
description: "Investigation OSINT structurée : cadrage, sources ouvertes, recherche de personnes, domaines et entreprises, agrégation et chaîne de conservation des preuves."
---

# Workflow OSINT avec Indagis Agent

Cette page décrit une investigation en sources ouvertes (OSINT) menée avec Indagis Agent. Elle couvre le cadrage de la cible, la collecte sur les personnes, domaines et entreprises, l'agrégation des résultats et la conservation des preuves.

:::info Distinction éthique
L'OSINT se limite aux informations accessibles publiquement sans contournement de mesure de protection. L'utilisation de ces données doit respecter le RGPD, les droits à l'image et la législation locale. Indagis Agent est un outil de collecte et de synthèse, pas un moyen d'accès à des données protégées.
:::

## Cadrage de la cible

Une investigation OSINT commence par une question claire : qui, quoi, où, quand, pourquoi. Indagis Agent aide à formaliser le périmètre et à éviter le bruit informationnel. Le cadrage peut inclure :

- Identifiants : pseudonyme, adresse e-mail, numéro de téléphone, nom de domaine.
- Entités : entreprise, marque, infrastructure technique.
- Géographie : localisation, juridiction, langue.
- Temporalité : période d'intérêt, événements récents.

La mémoire persistante conserve les hypothèses de travail et les éléments à vérifier, ce qui permet de reprendre une investigation plusieurs jours plus tard sans perdre le fil.

## Sources ouvertes et techniques

Les sources OSINT couvrent les réseaux sociaux, les moteurs de recherche, les registres publics, les archives web, les certificats TLS et les services DNS. Indagis Agent peut orchestrer des recherches via :

- Recherche web et navigateur intégré.
- Skills spécialisés (Sherlock, holehe, Maigret, etc.).
- Outils de domain intelligence (WHOIS, DNS, recherche inverse).
- Bases de fuites de données autorisées (Have I Been Pwned).
- Archives web (Wayback Machine).
- Scripts Python personnalisés.

:::warning Sources fiables
Indagis peut collecter des données, mais la vérification reste humaine. Une information publique n'est pas forcément exacte, à jour ou contextuellement interprétable. Croisez toujours plusieurs sources.
:::

## Recherche de personnes

La recherche d'identités en OSINT suit une méthode par attribution : pseudonyme, e-mail, photo, réseaux sociaux, emplois, relations. Indagis Agent peut aider à :

- Dédupliquer les comptes trouvés sur plusieurs plateformes.
- Construire une timeline de publications.
- Identifier des liens entre comptes (adresses e-mail partagées, handles similaires).
- Documenter chaque source avec une URL et une date de capture.

```bash
# Exemple de workflow d'investigation sur un pseudonyme
indagis chat --skill security-sherlock \
  "Recherche le pseudonyme "cyberanalyst_fr" sur les principaux réseaux sociaux.
   Résume les comptes trouvés, les URLs et les indices de confiance dans un tableau markdown."
```

## Recherche de domaines et d'entreprises

L'investigation technique sur une entreprise passe par son infrastructure : noms de domaine, sous-domaines, adresses IP, certificats, MX, technologies détectées. Indagis Agent peut exécuter des outils comme `whois`, `dig`, `subfinder`, `amass`, `assetfinder`, `httpx`, `nmap`, Shodan ou Censys.

```bash
# Exemple de workflow d'investigation sur un nom de domaine
mkdir -p ~/osint/cible-exemple.com
subfinder -d cible-exemple.com -o ~/osint/cible-exemple.com/subdomains.txt
httpx -l ~/osint/cible-exemple.com/subdomains.txt -o ~/osint/cible-exemple.com/live_hosts.txt
cat ~/osint/cible-exemple.com/live_hosts.txt
```

L'agent peut ensuite parser les résultats, identifier les technologies par page et suggérer des angles d'investigation supplémentaires (fuite d'informations, endpoints exposés, certificats).

## Agrégation et structuration

Une investigation OSINT génère rapidement des centaines de données brutes. Indagis Agent aide à structurer les résultats dans un format exploitable :

- Tableau des sources avec URL, date, type et fiabilité.
- Graphe des relations entre entités (peut être exporté en Markdown ou DOT).
- Timeline chronologique des événements observés.
- Synthèse des hypothèses validées et non validées.

```markdown
| Entité | Type | Source | Date | Fiabilité | Note |
|--------|------|--------|------|-----------|------|
| cyberanalyst_fr | Pseudonyme | Sherlock | 2026-09-02 | Moyenne | Compte actif, bio technique |
| cible-exemple.com | Domaine | WHOIS | 2026-09-02 | Haute | Enregistré via Gandi, DNS Cloudflare |
```

## Preuves et chaîne de conservation

La valeur d'une investigation OSINT dépend de la qualité de ses preuves. Chaque élément collecté doit être tracé : source, date de collecte, méthode, hash de fichier et contexte. Indagis Agent peut automatiser :

- La capture de pages via le navigateur intégré ou des outils comme `waybackpy`.
- Le calcul d'empreintes de fichiers.
- La génération d'un dossier de preuves avec métadonnées.
- La rédaction d'un rapport de synthèse.

:::warning Conservation des preuves
Ne modifiez jamais un fichier de preuve après capture. Renommez et datez les exports, conservez les URLs originales et documentez la méthode de collecte. Indagis peut vous aider à organiser le dossier, mais ne garantit pas la valeur juridique des preuves.
:::

## Outils dédiés et skills Indagis

L'OSINT repose sur un écosystème d'outils que skills d'Indagis pilotent directement.

| Outil / Skill | Fonction | Exemple d'usage |
|---|---|---|
| `security-sherlock` | Recherche de pseudonymes | `indagis chat --skill security-sherlock "cherche le pseudo target123"` |
| `research-osint-investigation` | Investigation structurée | Cadrage, collecte, synthèse et rapport. |
| `research-domain-intel` | Infrastructure technique | WHOIS, DNS, sous-domaines, certificats. |
| `research-gitnexus-explorer` | Sources et fuites code | Recherche dans les commits et dépôts publics. |
| `browser-testing-with-devtools` | Capture et inspection | Screenshot, DOM, réseau d'une page. |

```bash
# Workflow complet d'investigation d'un e-mail
indagis chat --skill research-osint-investigation \
  "Enquête sur l'e-mail cible@exemple.com : recherche de fuites,
   profiles publics, domaines associés. Résume dans un rapport markdown."
```

## Recherche d'e-mails et de fuites de données

Les adresses e-mail et pseudonymes apparaissent souvent dans des fuites publiques. Indagis peut interroger Have I Been Pwned ou des index de fuites autorisés, en respectant les conditions d'utilisation.

```bash
# Vérifier une adresse via l'API HIBP (clé requise)
curl -s -H "hibp-api-key: $HIBP_API_KEY" \
  "https://haveibeenpwned.com/api/v3/breachedaccount/cible@exemple.com" \
  | jq '.[] | {name: .Name, date: .BreachDate}'
```

L'agent peut ensuite croiser les résultats avec d'autres sources, identifier les mots de passe compromis si le contexte l'autorise, et proposer des actions de remédiation.

:::warning Fuites de données
La consultation de bases de fuites peut être illégale ou contraire aux CGU selon la juridiction. N'utilisez que des sources légales et autorisées.
:::

## Visualisation des relations et timeline

Une investigation complexe génère un graphe d'entités. Indagis peut produire un fichier DOT ou Mermaid pour visualiser les liens entre personnes, domaines, entreprises et infrastructure.

```markdown
```mermaid
graph LR
    A[cible@exemple.com] -->|HIBP| B[Fuites 2021]
    A -->|WHOIS| C[exemple.com]
    C -->|Subfinder| D[api.exemple.com]
    C -->|Certificat| E[*.exemple.com]
```
```

Indagis peut aussi structurer une timeline des publications, des enregistrements de domaine et des changements d'infrastructure.

## Checklist OSINT

- [ ] Objectif de l'investigation formalisé.
- [ ] Cible clairement identifiée (pseudo, e-mail, domaine, entreprise).
- [ ] Sources collectées avec URL et date de capture.
- [ ] Informations croisées entre au moins deux sources indépendantes.
- [ ] Preuves sauvegardées et hashées.
- [ ] Rapport de synthèse rédigé avec niveaux de confiance.
- [ ] Respect du RGPD et des droits à l'image vérifié.

## Automatisation et mémoire

Indagis transforme l'OSINT en workflow récurrent :

- **`memory`** : conserve les hypothèses, les sources et les écarts entre sessions.
- **`cron`** : planifie la veille régulière d'une marque ou d'une infrastructure.
- **`hooks`** : déclenche une investigation quand un nom de domaine suspect apparaît dans les alertes.
- **`subagent-driven-development`** : délègue des sous-tâches (recherche de domaine, recherche de pseudo) à des subagents spécialisés.

```bash
# Veille planifiée d'un nom de domaine
indagis chat \
  "Crée un cron hebdomadaire qui surveille les changements WHOIS et DNS
   de cible-exemple.com et m'alerte par e-mail des différences."
```

## Anti-patterns OSINT

| Anti-pattern | Risque | Bonne pratique |
|---|---|---|
| Croire une source unique sans vérification | Information fausse | Croiser au moins deux sources indépendantes. |
| Stocker les données personnelles sans fondement juridique | Violation RGPD | Documenter la base légale et la durée de conservation. |
| Contourner une mesure de protection | Acte illégal | S'arrêter aux données publiquement accessibles. |
| Oublier de capturer la source avant qu'elle ne disparaisse | Perte de preuve | Archiver via Wayback Machine ou screenshot. |

## OSINT sur les entreprises et registres publics

Les registres publics enrichissent l'investigation d'entreprise : registre du commerce, annonces légales, brevets, litiges et sanctions. Indagis peut structurer ces recherches.

| Source | Type d'information | Usage |
|---|---|---|
| Registre du commerce | Dirigeants, capital, siège | Cartographie légale |
| Annonces légales | Créations, fusions, dissolution | Timeline d'événements |
| Brevets et marques | Technologies, produits | Identification d'actifs |
| Sanctions et listes | Conformité, risque tierce partie | Due diligence |
| Recrutement | Stack technique, croissance | Angle technique |

```bash
# Recherche d'annonces légales françaises via un moteur public
indagis chat --skill research-osint-investigation \
  "Recherche les annonces légales de la société EXEMPLE SAS sur les 24 derniers mois.
   Résume les changements de dirigeants et de capital en tableau."
```

## Géolocalisation et analyse d'images

Les images publiées en ligne peuvent contenir des métadonnées ou des indices de localisation. Indagis peut guider l'analyse sans accéder à des données privées.

```bash
# Extraction de métadonnées EXIF avec exiftool (sur une image publique)
exiftool photo.jpg | grep -E "GPS|Date|Camera|Software"
```

Les éléments à noter sont : objets identifiables, enseignes, plaques d'immatriculation, langues sur les panneaux, architecture et végétation.

:::warning Données sensibles
Ne publiez pas les métadonnées EXIF brutes d'autrui sans autorisation. L'analyse OSINT se limite à ce qui est déjà public.
:::

## Ressources pour aller plus loin

- [OSINT Framework](https://osintframework.com)
- [Wayback Machine](https://archive.org)
- [Have I Been Pwned](https://haveibeenpwned.com)
- [Shodan](https://www.shodan.io)
- [Censys](https://search.censys.io)

## Skills Indagis recommandés

| Skill | Rôle dans l'OSINT |
|-------|-------------------|
| `research-osint-investigation` | Investigation générale et structuration |
| `research-domain-intel` | Recherche technique de domaines et IPs |
| `security-sherlock` | Recherche de pseudonymes sur réseaux sociaux |
| `browser-testing-with-devtools` | Capture et inspection de pages web |
| `documentation-and-adrs` | Rédaction de rapports et traces de décision |

## Pour aller plus loin

- [Installation et configuration](/docs/getting-started/installation)
- [Skills Indagis](/docs/user-guide/features/skills)
- [MCP servers](/docs/user-guide/features/mcp)
- [Mémoire persistante](/docs/user-guide/features/memory)
- [Tests d'intrusion](/docs/cybersecurity/penetration-testing)
- [Threat Intelligence](/docs/cybersecurity/threat-intel)
- [Commandes CLI](/docs/reference/cli-commands)

