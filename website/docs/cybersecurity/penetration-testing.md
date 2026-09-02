---
id: penetration-testing
title: "Tests d'intrusion avec Indagis Agent"
sidebar_position: 1
description: "Workflow end-to-end de pentest assisté par agent : reconnaissance, énumération, exploitation, post-exploitation et reporting."
---

# Tests d'intrusion avec Indagis Agent

Cette page décrit un workflow de test d'intrusion complet piloté par Indagis Agent. Elle couvre la reconnaissance passive, l'énumération technique, l'exploitation, la post-exploitation et la production d'un rapport structuré. L'objectif n'est pas de remplacer l'expertise du pentester, mais d'automatiser les tâches répétitives et de maintenir une trace cohérente tout au long de l'engagement.

:::warning Cadre légal
Un test d'intrusion ne doit être réalisé que sur des systèmes pour lesquels vous disposez d'une autorisation écrite explicite. Indagis Agent exécute des commandes réelles dans un terminal ; toute action est de votre responsabilité.
:::

## Reconnaissance et cadrage de l'engagement

La phase de reconnaissance détermine le périmètre, les règles d'engagement et les objectifs métier. Avant de toucher à la cible, le pentester collecte des informations publiques : noms de domaine, adresses IP, employés, technologies, annonces de recrutement, certificats TLS. Cette collecte se fait sans interaction directe avec les systèmes cibles.

Indagis Agent aide à structurer cette phase en croisant plusieurs sources ouvertes via des skills OSINT et des outils de recherche de domaines. La mémoire persistante conserve le périmètre, les exclusions et les contacts d'urgence, ce qui évite de les rappeler à chaque prompt. L'agent peut également générer un fichier de règles d'engagement à partir du brief initial.

:::tip Formaliser le périmètre
Demandez à Indagis de produire un fichier Markdown reprenant le périmètre IP, les domaines autorisés, les exclusions, les horaires de test et les points de contact. Ce document peut être relu à chaque étape par l'agent.
:::

## Énumération technique

L'énumération transforme les indicateurs de surface en un inventaire exploitable. Indagis Agent peut orchestrer Nmap, Masscan, ffuf, nikto, gobuster, ou tout outil installé dans le terminal, guidé par un skill de sécurité. Le workflow typique comprend :

1. Scan SYN rapide sur le périmètre défini.
2. Identification des services et versions.
3. Exécution de scripts NSE ciblés (`http-title`, `ssl-cert`, `vuln`).
4. Stockage des résultats dans un dossier de preuves daté.
5. Comparaison avec une baseline si elle existe.

```bash
# Exemple de workflow d'énumération dans le terminal Indagis
mkdir -p ~/pentest/target-2026-09/{nmap,web,proofs}
nmap -sS -T4 -p- -oA ~/pentest/target-2026-09/nmap/allports 10.0.0.0/24
nmap -sV -sC -p 22,80,443,8080 -oA ~/pentest/target-2026-09/nmap/services 10.0.0.12
ffuf -w /usr/share/wordlists/dirb/common.txt -u http://10.0.0.12/FUZZ \
  -o ~/pentest/target-2026-09/web/ffuf.json
```

L'agent peut parser les sorties, identifier les services intéressants et proposer la suite : fuzzing de répertoires, test de credentials par défaut, ou analyse des certificats SSL.

## Exploitation assistée

L'exploitation ne doit pas être aveugle. Indagis Agent aide à trier les vulnérabilités potentielles, chercher des preuves d'exploitabilité et rédiger des commandes contrôlées. L'agent peut interroger des bases de vulnérabilités, générer des commandes Metasploit ou des scripts Python ciblés, et documenter chaque preuve.

:::warning Preuve minimale
Le but d'un pentest est de démontrer l'impact, pas d'endommager la cible. Indagis peut aider à capturer un screenshot, un flag ou un hash, mais la décision d'arrêt reste humaine.
:::

```python
# Exemple de script généré par Indagis pour capturer une preuve
import requests, hashlib, datetime
url = "http://10.0.0.12/admin"
r = requests.get(url, timeout=10)
print(datetime.datetime.now(), r.status_code, len(r.text))
with open("~/pentest/target-2026-09/proofs/admin-access.html", "w") as f:
    f.write(r.text)
print("hash:", hashlib.sha256(r.text.encode()).hexdigest()[:16])
```

OWASP Testing Guide et le framework MITRE ATT&CK fournissent des références pour structurer cette phase et documenter les techniques utilisées.

## Post-exploitation et latéralisation

Après compromission initiale, l'agent assiste la cartographie du réseau interne, l'élévation de privilèges et la latéralisation. Il peut lire des fichiers, exécuter des commandes via un shell obtenu, ou analyser des logs locaux. Chaque action doit être documentée en temps réel : fichiers consultés, comptes utilisés, commandes exécutées, artefacts de persistance testés et retirés.

Indagis peut produire un fichier `post-exploitation.md` chronologique à partir des commandes passées dans la session, en s'appuyant sur la mémoire et le terminal.

## Production du rapport

Le rapport est souvent le livrable le plus important. Indagis Agent compile les notes de session en un document structuré : executive summary, périmètre, méthodologie, findings avec criticité, preuves, recommandations et annexes techniques. Le classement par criticité peut s'appuyer sur le score CVSS et sur l'exposition réelle du service.

| ID | Vulnérabilité | Sévérité | Preuve | Recommandation |
|---|---|---|---|---|
| F01 | SSH avec authentification par mot de passe | Haute | Capture Nmap + Hydra | Clés SSH uniquement, fail2ban |
| F02 | Divulgation de version Apache | Moyenne | Bannière HTTP 2.4.41 | Masquer la bannière, patcher |
| F03 | Endpoint admin sans authentification | Critique | preuve-admin-access.html | Authentification forte, ACL |

```bash
# Générer le rapport à partir des notes de session
indagis chat --skill security-web-pentest \
  "Génère un rapport de pentest à partir de ~/pentest/target-2026-09/notes/"
```

## Méthodologies de pentest et mapping MITRE ATT&CK

Un pentest structuré suit une méthodologie reconnue. OWASP Testing Guide v4 structure les tests applicatifs ; MITRE ATT&CK fournit le mapping des techniques adverses.

| Phase | Référence | Objectif |
|---|---|---|
| Reconnaissance | OSINT Framework | Cartographier la surface d'attaque sans toucher la cible. |
| Énumération | OWASP OTG-INFO | Identifier les services, versions, endpoints et technologies. |
| Exploitation | OWASP OTG-CONF, OTG-INPV | Démontrer l'impact avec une preuve minimale. |
| Post-exploitation | MITRE ATT&CK | Latéralisation, persistance, élévation de privilèges. |
| Reporting | CVSS v3.1 | Documenter et prioriser les findings. |

```bash
# Lister les techniques MITRE ATT&CK couvertes par un engagement
indagis chat --skill security-web-pentest \
  "Analyse les notes de ~/pentest/target-2026-09/notes/
   et mappe chaque finding aux techniques MITRE ATT&CK correspondantes."
```

## Tests web spécifiques

OWASP Top 10 2021 guide les tests applicatifs les plus courants. Indagis peut orchestrer des outils spécialisés pour chaque famille de faille.

| Catégorie OWASP | Outil d'exemple | Commande indicatif |
|---|---|---|
| Injection SQL | sqlmap | `sqlmap -u "http://10.0.0.12/search?q=test" --batch` |
| IDOR | Burp Suite / ffuf | `ffuf -w ids.txt -u http://10.0.0.12/api/user/FUZZ` |
| XSS | dalfox | `dalfox url http://10.0.0.12/?q=test` |
| Sécurité des APIs | Postman + ffuf | `ffuf -w endpoints.txt -u http://10.0.0.12/api/FUZZ` |
| SSRF | curl custom | `curl http://10.0.0.12/fetch?url=http://169.254.169.254/` |

:::warning Preuve minimale
Le but n'est pas d'extraire des données clients. Capturez un screenshot, un hash ou un flag fictif pour prouver l'impact.
:::

## Fuzzing et wordlists

Le fuzzing découvre des endpoints, fichiers et paramètres cachés. Les wordlists courantes incluent SecLists, dirb et fuzzdb.

```bash
# Installation rapide de SecLists sur la machine d'attaque
git clone --depth 1 https://github.com/danielmiessler/SecLists.git /opt/SecLists

# Fuzzing de répertoires web
ffuf -w /opt/SecLists/Discovery/Web-Content/raft-medium-directories.txt \
     -u http://10.0.0.12/FUZZ -mc 200,301,302,403

# Fuzzing de paramètres GET
ffuf -w /opt/SecLists/Discovery/Web-Content/burp-parameter-names.txt \
     -u 'http://10.0.0.12/search?FUZZ=value' -fs 0
```

## Checklist pentest

- [ ] Autorisation écrite obtenue et archivée.
- [ ] Périmètre, exclusions et contacts d'urgence formalisés.
- [ ] Environnement de test ou d'attaque isolé.
- [ ] Reconnaissance passive effectuée sans impact.
- [ ] Scans et énumération documentés avec des preuves datées.
- [ ] Exploitation limitée au minimum démontrable.
- [ ] Post-exploitation traçée et nettoyée.
- [ ] Rapport structuré avec CVSS et recommandations.
- [ ] Réunion de restitution préparée.

## Automatisation, mémoire et delegation

Indagis optimise le pentest via ses fonctionnalités natives :

- **`security-web-pentest`** : orchestre Nmap, ffuf, sqlmap, Burp, etc.
- **`security-godmode`** : automatise des scans à grande échelle et de la post-exploitation.
- **`research-osint-investigation`** : prépare la reconnaissance passive.
- **`memory`** : conserve le périmètre, les credentials de test et les findings.
- **`delegation`** : distribue les phases (reconnaissance, web, infra, reporting) à des subagents.

```bash
# Exemple de commande de delegation : un subagent dédié au reporting
indagis chat \
  "Délègue la rédaction du rapport de pentest de ~/pentest/target-2026-09/
   à un subagent spécialisé documentation-and-adrs."
```

## Anti-patterns pentest

| Anti-pattern | Risque | Bonne pratique |
|---|---|---|
| Lancer un scan sans autorisation | Activité illégale | Toujours disposer d'un scope signé. |
| Exploiter à l'aveugle | Indisponibilité du service | Privilégier la preuve minimale. |
| Négliger le nettoyage | Artefacts laissés en production | Documenter et retirer comptes, fichiers et tâches. |
| Reporter sans CVSS ni preuve | Rapport inactionnable | Attribuer un score et une preuve à chaque finding. |

## Restitution et suivi des recommandations

Le rapport n'a de valeur que s'il est compris et suivi. Indagis peut aider à préparer la restitution et le suivi des actions correctives.

```markdown
## Plan de suivi des recommandations
| ID | Action | Responsable | Échéance | Statut |
|---|---|---|---|---|
| F01 | Clés SSH + fail2ban | Admin sys | 2026-09-15 | En cours |
| F02 | Masquer bannière Apache | Admin web | 2026-09-10 | À faire |
| F03 | Authentification admin | DevSecOps | 2026-09-20 | À faire |
```

Indagis peut relire les preuves, vérifier que chaque finding a une action assignée, et planifier des rappels de validation.

```bash
# Suivi des actions correctives
indagis chat --skill security-web-pentest \
  "À partir du rapport ~/pentest/target-2026-09/report.md,
   vérifie que chaque finding a une action, un responsable et une échéance.
   Génère un fichier de suivi dans ~/pentest/target-2026-09/actions.md"
```

## Ressources pour aller plus loin

- [OWASP Testing Guide v4](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [MITRE ATT&CK](https://attack.mitre.org)
- [CVSS v3.1 Calculator](https://www.first.org/cvss/calculator/3.1)
- [Pentest Reporting Standard](https://pentestreports.com/)

## Skills Indagis recommandés

| Skill | Rôle dans le pentest |
|-------|----------------------|
| `research-osint-investigation` | Reconnaissance passive et cadrage |
| `security-web-pentest` | Énumération web, fuzzing, exploitation |
| `security-godmode` | Automatisation avancée de scans et post-exploitation |
| `security-sherlock` | Recherche d'identités et de comptes publics |
| `systematic-debugging` | Analyse d'échecs et triage d'exploits |

## Pour aller plus loin

- [Installation et configuration](/docs/getting-started/installation)
- [Skills Indagis](/docs/user-guide/features/skills)
- [MCP servers](/docs/user-guide/features/mcp)
- [Mémoire persistante](/docs/user-guide/features/memory)
- [Gestion des secrets](/docs/user-guide/secrets)
- [Commandes CLI](/docs/reference/cli-commands)

