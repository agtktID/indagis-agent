---
id: threat-intel
title: "Threat Intelligence avec Indagis Agent"
sidebar_position: 2
description: "Agréger, enrichir et diffuser des indicateurs de compromission depuis MISP, OTX, VirusBay et d'autres sources de threat intel."
---

# Threat Intelligence avec Indagis Agent

Cette page présente comment Indagis Agent peut être utilisé pour collecter, enrichir, corréler et diffuser des informations de threat intelligence. Elle couvre les sources de feeds, les formats STIX/TAXII, l'enrichissement d'IOC, la corrélation avec les logs internes et la diffusion vers les équipes opérationnelles.

## Sources de feeds et formats

Les analystes CTI s'appuient sur des sources internes et externes. Indagis Agent peut interfacer avec les formats et API courants : MISP, AlienVault OTX, VirusBay, RSS de blogs de sécurité, et flux STIX/TAXII. Les formats de partage standardisés permettent d'échanger des indicateurs de manière interopérable :

- **STIX** : format structuré pour les objets d'intelligence (indicateurs, malware, campagnes, acteurs).
- **TAXII** : protocole de transport de données STIX entre organisations.
- **MISP JSON** : format événement/attribut utilisé par les communautés MISP.
- **OpenIOC / YARA / Sigma** : formats d'indicateurs plus spécialisés.

Indagis ne remplace pas un serveur MISP ou une plateforme TIP, mais il peut automatiser la récupération, le parsing et l'enrichissement de ces données.

## Collecte automatisée

Un skill peut orchestrer la collecte périodique de feeds. Par exemple, un skill peut demander à Indagis de :

1. Poll l'API AlienVault OTX toutes les heures.
2. Parser la réponse JSON.
3. Filtrer les IOC pertinents (IP, domaine, hash).
4. Stocker les résultats dans une base SQLite locale.
5. Lever une alerte si un nouvel IOC correspond au périmètre de veille défini.

```python
# Exemple de skill Python simplifié pour poll OTX
import requests, sqlite3, os, datetime

API_KEY = os.environ.get("OTX_API_KEY")
HEADERS = {"X-OTX-API-KEY": API_KEY}
URL = "https://otx.alienvault.com/api/v1/pulses/subscribed"

conn = sqlite3.connect("/tmp/indagis_threat_intel.db")
conn.execute("""CREATE TABLE IF NOT EXISTS iocs (
    id INTEGER PRIMARY KEY,
    type TEXT,
    value TEXT,
    source TEXT,
    seen_at TEXT,
    UNIQUE(type, value, source)
)""")

resp = requests.get(URL, headers=HEADERS, timeout=30)
resp.raise_for_status()
for pulse in resp.json().get("results", []):
    for ioc in pulse.get("indicators", []):
        try:
            conn.execute(
                "INSERT INTO iocs (type, value, source, seen_at) VALUES (?, ?, ?, ?)",
                (ioc["type"], ioc["indicator"], "otx", datetime.datetime.now().isoformat())
            )
        except sqlite3.IntegrityError:
            pass
conn.commit()
print("IOC stockés:", conn.execute("SELECT COUNT(*) FROM iocs").fetchone()[0])
```

:::tip Planification
Utilisez les crons d'Indagis pour exécuter ce skill à intervalle régulier. La sortie peut être envoyée à un canal configuré via la gateway.
:::

## Enrichissement des IOC

Un indicateur brut gagne en valeur quand il est enrichi : pays d'origine, ASN, résolutions passées, détections antivirus, campagnes connues. Indagis Agent peut chaîner des appels à différentes sources : VirusTotal, AlienVault OTX, URLhaus, Abuse.ch, CIRCL, Shodan ou Censys. Un skill d'enrichissement peut lire un IOC depuis la base SQLite, interroger plusieurs sources, puis mettre à jour l'entrée avec les métadonnées collectées.

```bash
# Enrichir un hash SHA256 depuis le terminal Indagis
indagis chat --skill security-threat-enrichment \
  "Enrichis le hash 5fd6...d42a avec VirusTotal et OTX, puis résume en markdown."
```

## Corrélation et détection

La corrélation consiste à croiser les IOC externes avec les logs internes ou la cartographie d'actifs. Indagis peut aider à parser des logs SIEM exportés (CSV, JSON, parquet), rechercher des correspondances d'IP, domaine, hash ou URL, générer des règles Sigma ou YARA à partir d'un pattern observé, et produire une timeline d'activité suspecte.

:::warning Vie des indicateurs
Un IOC peut devenir obsolète rapidement. Un skill doit gérer la date de première vue, la date de dernière vue, et une logique de retraitement périodique pour éviter les faux positifs.
:::

## Diffusion et action

Une fois les IOC enrichis et corrélés, ils doivent être actionnés : blocage DNS, règles IDS, alertes SIEM, brief interne. Indagis Agent peut formater les IOC en règles iptables, Suricata, ou Windows Defender, générer un brief Markdown pour l'équipe SOC, pousser les indicateurs vers un webhook ou une API interne, et créer un ticket via un MCP server de gestion de projet.

## Sources de threat intelligence et Diamond Model

Le modèle **Diamond Model of Intrusion Analysis** structure l'analyse d'un incident autour de quatre sommets : adversaire, infrastructure, victime et capacité. Indagis peut aider à documenter chaque sommet à partir des IOC collectés.

| Sommet | Questions clés | Sources typiques |
|---|---|---|
| Adversaire | Qui mène l'attaque ? Quels sont ses objectifs ? | Rapports sectoriels, OSINT, attribution technique |
| Infrastructure | Quels C2, domaines, IPs, outils sont utilisés ? | MISP, VirusTotal, passive DNS |
| Capacité | Quelles techniques et malwares ? | MITRE ATT&CK, YARA, capa |
| Victime | Quelle cible, quels secteurs, quelles géographies ? | Logs internes, threat feeds sectoriels |

## Gestion du cycle de vie des IOC

Un IOC suit un cycle de vie. Indagis peut automatiser chaque étape.

| État | Action | Exemple |
|---|---|---|
| Collecte | Poll de feeds | OTX, MISP, RSS sécurité |
| Enrichissement | Ajout de contexte | VirusTotal, Shodan, Whois |
| Corrélation | Croisement avec logs | Recherche dans SIEM export |
| Action | Blocage ou détection | Suricata, iptables, EDR |
| Rétrogradation | Retrait si faux positif | Mettre à jour la base SQLite |

```python
# Marquer un IOC comme obsolète ou faux positif
import sqlite3
conn = sqlite3.connect("/tmp/indagis_threat_intel.db")
conn.execute("UPDATE iocs SET status='false_positive' WHERE value=?", ("198.51.100.4",))
conn.commit()
print("IOC mis à jour.")
```

## Production de CTI interne

L'intelligence de menace interne transforme les incidents et IOC en connaissance actionnable pour la Blue Team.

```bash
# Générer un brief CTI hebdomadaire avec Indagis
indagis chat --skill security-threat-enrichment \
  "À partir de /tmp/indagis_threat_intel.db et des logs de la semaine,
   génère un brief CTI avec les nouveaux IOC, les techniques MITRE ATT&CK observées
   et les recommandations de détection pour le SOC."
```

Le brief doit contenir :
- Résumé exécutif en 3 points.
- Liste des IOC priorisés avec contexte.
- Mapping MITRE ATT&CK.
- Règles de détection proposées (Sigma, Suricata, YARA).
- Actions recommandées et responsables.

## Pyramid of Pain et qualité des indicateurs

La Pyramid of Pain de David Bianco classe les indicateurs par valeur défensive. Les IOC basiques (hash, IP, domaine) sont faciles à changer pour l'attaquant ; les TTP sont les plus difficiles à modifier.

| Niveau | Indicateur | Difficulté pour l'attaquant | Valeur défensive |
|---|---|---|---|
| 1 | Hash | Très faible | Signature immédiate mais volatile |
| 2 | IP / Domaine | Faible | Blocage rapide, vie courte |
| 3 | Artefact réseau (JA3, User-Agent) | Moyenne | Détection de pattern |
| 4 | Outils et armes | Moyenne-élevée | Détection de comportement |
| 5 | TTP | Élevée | Stratégie défensive durable |

Indagis peut aider à remonter la pyramide : au lieu de bloquer une IP, générer une règle Sigma sur le comportement observé.

## Checklist CTI

- [ ] Sources de feeds identifiées et fiables.
- [ ] Formats standardisés (STIX, MISP, Sigma, YARA).
- [ ] Pipeline de collecte testé et résilient.
- [ ] Enrichissement automatisé ou semi-automatisé.
- [ ] Corrélation avec les logs internes.
- [ ] Actionnabilité vérifiée (blocage, détection, brief).
- [ ] Gestion des faux positifs et obsolescence.
- [ ] Diffusion régulière au SOC et à la direction.

## Automatisation avec crons, hooks et mémoire

Indagis transforme la CTI en programme continu :

- **`security-threat-enrichment`** : enrichissement des IOC.
- **`research-osint-investigation`** : veille sources ouvertes.
- **`cron`** : planifie les collectes et les briefs.
- **`memory`** : garde l'historique des campagnes observées.
- **`mcp`** : interroge des plateformes TIP via des MCP servers.

```bash
# Exemple de cron pour un brief CTI hebdomadaire
indagis chat \
  "Crée un cron chaque lundi à 08:00 qui génère un brief CTI
   à partir de /tmp/indagis_threat_intel.db et l'envoie sur #soc."
```

## Anti-patterns CTI

| Anti-pattern | Risque | Bonne pratique |
|---|---|---|
| Accumuler des IOC sans les actionner | Bruit et fatigue | Chaque IOC doit avoir un destinataire (SOC, EDR, DNS). |
| Croire un feed sans vérification | Faux positifs | Croiser avec au moins une source interne. |
| Rester au niveau hash/IP | Contournement rapide | Remonter vers les TTP et comportements. |
| Ignorer la vie des indicateurs | Blocages obsolètes | Planifier des revues et retraits périodiques. |

## Cas d'usage réel : campagne de phishing ciblée

Supposons qu'une campagne de phishing cible votre secteur. Le workflow CTI avec Indagis suit les étapes suivantes.

1. **Collecte** : un skill surveille les RSS de blogs de sécurité et les communautés MISP pour les mots-clés du secteur.
2. **Extraction d'IOC** : domaines d'hameçonnage, hashes de pièces jointes, URLs de landing page.
3. **Enrichissement** : VirusTotal pour les URLs, Whois pour les domaines, Shodan pour les IPs.
4. **Corrélation** : recherche dans les logs proxy et mail des 30 derniers jours.
5. **Action** : blocage DNS des domaines, règles YARA sur les pièces jointes, brief SOC.

```bash
# Exemple de corrélation d'IOC dans des logs proxy
zgrep -E "phishing-example\.com|malicious\.net" /var/log/proxy/access.log*.gz \
  > ~/cti/correlation-$(date +%Y%m%d).txt
```

## Intégration MISP et export STIX

MISP reste la plateforme de référence pour le partage communautaire. Indagis peut préparer des événements MISP sans remplacer le serveur.

```python
# Squelette d'événement MISP généré par Indagis
misp_event = {
    "info": "Campagne phishing secteur - septembre 2026",
    "threat_level_id": 2,
    "distribution": 1,
    "tags": [{"name": "phishing"}, {"name": "sectoriel"}],
    "Attribute": [
        {"type": "domain", "value": "phishing-example.com", "to_ids": True},
        {"type": "sha256", "value": "aabbccdd...", "to_ids": True},
    ]
}
```

L'agent peut ensuite générer un bundle STIX équivalent pour intégration dans un TIP ou un SIEM moderne.

## Intégration SIEM et EDR

Les IOC enrichis doivent atteindre les outils opérationnels. Indagis peut formater les indicateurs pour différentes plates-formes.

```yaml
# Exemple de règle Sigma générée à partir d'un IOC
title: Suspicious DNS query to phishing domain
logsource:
  product: windows
  category: dns_query
detection:
  selection:
    query|endswith: '.phishing-example.com'
  condition: selection
level: high
```

| Plate-forme | Format | Usage |
|---|---|---|
| SIEM | Sigma, Splunk SPL, KQL | Recherche et alertes |
| EDR | IOC list, YARA | Blocage et hunting |
| DNS | RPZ, Pi-hole | Blocage de résolution |
| Firewall | iptables, Palo Alto | Blocage réseau |

```bash
# Générer des règles iptables à partir d'une liste d'IP
while read ip; do
  echo "iptables -A INPUT -s $ip -j DROP"
done < ~/cti/malicious-ips.txt > ~/cti/iptables-rules.sh
```

## Ressources pour aller plus loin

- [MISP Project](https://www.misp-project.org)
- [STIX/TAXII](https://oasis-open.github.io/cti-documentation/)
- [MITRE ATT&CK](https://attack.mitre.org)
- [VirusTotal](https://www.virustotal.com)
- [AlienVault OTX](https://otx.alienvault.com)

## Skills Indagis recommandés

| Skill | Rôle dans la CTI |
|-------|------------------|
| `research-osint-investigation` | Veille sources ouvertes et blogs |
| `research-domain-intel` | Enrichissement de noms de domaine |
| `security-threat-enrichment` | Enrichissement automatique d'IOC |
| `security-yara-rules` | Génération et maintenance de signatures YARA |
| `cron` | Planification des collectes périodiques |

## Pour aller plus loin

- [Skills Indagis](/docs/user-guide/features/skills)
- [MCP servers](/docs/user-guide/features/mcp)
- [Crons et tâches planifiées](/docs/user-guide/features/cron)
- [Mémoire persistante](/docs/user-guide/features/memory)
- [Gestion des secrets](/docs/user-guide/secrets)
- [Commandes CLI](/docs/reference/cli-commands)

