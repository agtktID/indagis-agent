---
id: dfir-triage
title: "DFIR Triage avec Indagis Agent"
sidebar_position: 4
description: "Réponse à incident et triage DFIR assistés par agent : préparation, identification, containment, éradication, recovery et lessons learned selon NIST SP 800-61."
---

# DFIR Triage avec Indagis Agent

Cette page décrit l'utilisation d'Indagis Agent pour le triage et la réponse à incident (DFIR : Digital Forensics and Incident Response). Elle suit la méthodologie de NIST SP 800-61 : préparation, identification, containment, éradication, recovery et lessons learned.

:::warning Timing critique
Les premières minutes d'un incident sont déterminantes. Indagis Agent peut accélérer les tâches répétitives, mais il ne remplace pas un analyste SOC ou un responder expérimenté. Gardez la main sur les actions destructrices.
:::

## Préparation

La préparation est la phase la plus importante et la moins visible. Elle comprend :

- L'inventaire des actifs critiques et des points de collecte de logs.
- La définition des rôles et des procédures d'escalade.
- La mise en place de playbooks de réponse.
- L'accès à des outils d'analyse et à des environnements isolés.

Indagis Agent peut contribuer à la préparation en générant des playbooks Markdown à partir de votre policy, en listant les sources de logs disponibles sur un endpoint, en vérifiant la présence et la configuration d'outils (Sysmon, Auditd, WEC), et en créant des tâches cron de vérification de la santé des collecteurs.

```bash
# Vérifier la collecte de logs sur un endpoint Linux
ls -la /var/log/
systemctl status rsyslog auditd
which sysmon
which auk
```

CIS Controls fournit une référence utile pour structurer cette phase, notamment les contrôles de logging, d'inventaire et de gestion des vulnérabilités.

## Identification

L'identification consiste à détecter qu'un incident est en cours, à qualifier sa sévérité et à rassembler les premiers indicateurs. Indagis Agent peut aider à parser des logs de pare-feu, proxy, endpoint ou cloud, appliquer des règles Sigma ou des patterns de détection, enrichir des IOC via des sources de threat intel, et générer une timeline des premiers événements suspects.

:::tip Analyse de logs suspects via Sigma
Un skill DFIR peut demander à Indagis de convertir une règle Sigma en requête pour votre SIEM, ou de l'appliquer directement sur un fichier de logs local.
:::

```bash
# Exemple : chaîne d'analyse de logs suspects via Sigma
mkdir -p ~/dfir/incident-2026-09/{logs,rules,output}
cp /var/log/auth.log ~/dfir/incident-2026-09/logs/
sigma convert -t splunk -c splunk-windows ~/dfir/incident-2026-09/rules/suspicious_login.yml
# ou exécuter une règle Sigma via un backend Python local
python3 -m sigma.cli convert -t sqlite ~/dfir/incident-2026-09/rules/
```

## Containment

Le containment vise à limiter l'impact de l'incident. Il peut être court-terme (isolation d'un endpoint) ou long-terme (segmentation réseau, blocage d'IOC). Indagis Agent peut générer des commandes de blocage (iptables, Windows firewall, route null), préparer des scripts de désactivation de comptes compromis, et documenter chaque action de containment avec un timestamp.

:::warning Privilèges et autorisation
Toute action de containment doit être validée avec l'équipe IT et la direction. Un blocage mal ciblé peut interrompre des services critiques.
:::

## Éradication

L'éradication consiste à retirer la menace : suppression de malware, correction des vulnérabilités exploitées, révocation des credentials, etc. Indagis Agent peut assister en identifiant les artefacts persistants (tâches cron, services, clés de registre), en générant des scripts de nettoyage et en vérifiant que les IOC connus ne sont plus présents.

L'agent ne doit pas exécuter seul des actions de suppression sur un système de production sans supervision humaine explicite.

## Recovery

La recovery remet les systèmes en service de manière contrôlée. Indagis Agent peut vérifier les prérequis avant réouverture (patchs, logs propres, monitoring renforcé), générer une checklist de validation et continuer la surveillance pendant une période de quarantaine.

```markdown
## Checklist de recovery
- [ ] Patchs de sécurité appliqués
- [ ] Mots de passe des comptes critiques réinitialisés
- [ ] Règles de détection mises à jour
- [ ] Monitoring renforcé activé 7 jours
- [ ] Rapport d'incident rédigé
```

## Lessons learned

La dernière phase formalise les enseignements de l'incident : ce qui a fonctionné, ce qui a pris du temps, ce qui doit être amélioré. Indagis Agent peut aider à rédiger le post-mortem, extraire les actions correctives et les transformer en tickets ou en tâches planifiées.

## Acquisition et chaîne de conservation

Avant analyse, les artefacts doivent être collectés sans altération. La chaîne de conservation garantit que les preuves resteront exploitables en cas d'enquête interne ou judiciaire.

- **Identifier l'artefact** : processus, fichier mémoire, disque, logs réseau.
- **Bloquer l'accès** : isoler la machine ou le compte concerné.
- **Collecter de manière forensiquement saine** : utiliser des outils comme `dcfldd`, `dd`, `FTK Imager`, `velociraptor`.
- **Calculer et stocker les empreintes** : SHA256 du dump et du rapport.
- **Documenter** : qui, quand, quoi, pourquoi, comment.

```bash
# Exemple de collecte d'un dump mémoire Linux avec LiME
mkdir -p ~/dfir/evidence/mem
sudo insmod /opt/lime/src/lime-$(uname -r).ko "path=/home/$(whoami)/dfir/evidence/mem/mem.lime format=lime"
sha256sum ~/dfir/evidence/mem/mem.lime > ~/dfir/evidence/mem/mem.lime.sha256
```

```bash
# Collecte de logs et d'artefacts sur un endpoint Linux
mkdir -p ~/dfir/evidence/host-{hostname}
sudo cp /var/log/auth.log ~/dfir/evidence/host-{hostname}/
sudo cp /var/log/syslog ~/dfir/evidence/host-{hostname}/
sudo last -f /var/log/wtmp > ~/dfir/evidence/host-{hostname}/wtmp.txt
sudo netstat -tulpn > ~/dfir/evidence/host-{hostname}/listeners.txt 2>&1 || true
sha256sum ~/dfir/evidence/host-{hostname}/* > ~/dfir/evidence/host-{hostname}/manifest.sha256
```

## Timeline et corrélation

Une timeline reconstruit la chronologie des événements. Elle permet de relier les artefacts entre eux et de qualifier l'ampleur de l'incident.

```bash
# Générer une timeline avec plaso/log2timeline (si installé)
log2timeline.py --status_view linear \
  ~/dfir/incident-2026-09/timeline.plaso \
  ~/dfir/evidence/host-{hostname}/
psort.py -o l2tcsv -w ~/dfir/incident-2026-09/timeline.csv \
  ~/dfir/incident-2026-09/timeline.plaso
```

Indagis peut parser le CSV et proposer une timeline synthétique :

| Heure | Source | Événement | Impact |
|---|---|---|---|
| 2026-09-02T08:12:00Z | auth.log | Connexion SSH réussie depuis 198.51.100.4 | Accès initial potentiel |
| 2026-09-02T08:14:22Z | auditd | Exécution de `curl | bash` | Téléchargement suspect |
| 2026-09-02T08:15:01Z | cron | Tâche planifiée ajoutée | Persistance |
| 2026-09-02T09:03:11Z | netstat | Connexion sortante vers 203.0.113.7:443 | C2 possible |

## Commandes de containment courantes

Le containment rapide limite la propagation. Les commandes suivantes servent d'exemples opérationnels, à adapter au contexte.

```bash
# Isoler une VM via null route (Linux)
sudo ip route add blackhole 203.0.113.0/24

# Bloquer une adresse IP avec iptables
sudo iptables -I INPUT -s 198.51.100.4 -j DROP
sudo iptables -I OUTPUT -d 203.0.113.7 -j DROP

# Désactiver un compte utilisateur compromis
sudo usermod -L compte_compromis
sudo pkill -u compte_compromis

# Supprimer une tâche cron malveillante
sudo crontab -u compte_compromis -l > ~/dfir/evidence/cron-backup.txt
sudo crontab -u compte_compromis -r
```

Sous Windows, les équivalents passent par `netsh advfirewall`, `Disable-LocalUser`, `Get-ScheduledTask`, et `Remove-Item` sur les clés de registre de persistance.

## Checklist DFIR 24 premières heures

- [ ] Identifier les systèmes concernés et leur criticité.
- [ ] Sauvegarder les artefacts avant toute modification.
- [ ] Couper l'accès réseau des machines compromises si autorisé.
- [ ] Révoquer les credentials exposés ou compromis.
- [ ] Rechercher les IOC dans l'ensemble du périmètre.
- [ ] Notifier les équipes IT, juridique et communication.
- [ ] Documenter chaque action avec un timestamp et un opérateur.
- [ ] Rédiger un premier rapport de situation.

## Automatisation via skills, hooks et mémoire

Indagis transforme le DFIR en workflow répétable :

- **`security-dfir-triage`** : orchestration des phases de réponse.
- **`security-sigma-rules`** : génération et conversion de détections.
- **`security-threat-enrichment`** : enrichissement automatique des IOC.
- **`memory`** : conservation du contexte d'un incident d'une session à l'autre.
- **`hooks`** : déclenchement d'actions à l'arrivée d'une alerte ou d'un fichier de logs.

```bash
# Exemple de hook : déclencher un triage DFIR à l'arrivée d'une alerte
indagis chat \
  "Crée un hook qui, quand un fichier ~/alerts/*.json arrive,
   exécute le skill security-dfir-triage et génère un rapport dans ~/dfir/auto/"
```

## Anti-patterns DFIR

| Anti-pattern | Risque | Bonne pratique |
|---|---|---|
| Exécuter un malware sur la machine d'analyse | Compromission de l'enquête | Analyse dans une VM isolée sans réseau. |
| Supprimer des artefacts avant capture | Perte de preuves | Toujours collecter avant de nettoyer. |
| Bloquer un C2 sans étudier le comportement | Empêche l'analyse du TTP | Isoler et observer si possible. |
| Ignorer les comptes de service | Latéralisation silencieuse | Auditer les credentials API, IAM et service. |

## Intégration avec Velociraptor

Velociraptor est un outil de forensics et de threat hunting à grande échelle. Indagis peut aider à rédiger des artefacts VQL (Velociraptor Query Language) et à parser les résultats.

```vql
// Lister les connexions réseau actives sur les endpoints
SELECT Timestamp, ProcessName, SrcIP, DstIP, DstPort
FROM source()
WHERE Artifact = "Windows.Network.Netstat"
```

Un skill DFIR peut demander à Indagis de générer un artefact VQL pour rechercher un IOC, de l'exécuter via Velociraptor, et d'analyser les résultats collectés.

```bash
# Exemple de collecte Velociraptor via Indagis
indagis chat --skill security-dfir-triage \
  "Génère un artefact VQL qui recherche le hash sha256
   5fd6...d42a sur tous les endpoints du périmètre,
   puis analyse les résultats dans ~/dfir/velociraptor/."
```

## Ressources pour aller plus loin

- [NIST SP 800-61 rev2](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final)
- [CIS Controls v8](https://www.cisecurity.org/controls)
- [Velociraptor](https://docs.velociraptor.app)
- [Sigma](https://sigmahq.io)
- [Plaso / log2timeline](https://plaso.readthedocs.io)

## Skills Indagis recommandés

| Skill | Rôle dans le DFIR |
|-------|-------------------|
| `security-dfir-triage` | Orchestration du triage incident |
| `security-sigma-rules` | Détection et conversion de règles Sigma |
| `security-threat-enrichment` | Enrichissement des IOC observés |
| `security-yara-rules` | Analyse de fichiers suspects |
| `systematic-debugging` | Triage des erreurs et anomalies |

## Pour aller plus loin

- [Skills Indagis](/docs/user-guide/features/skills)
- [MCP servers](/docs/user-guide/features/mcp)
- [Mémoire persistante](/docs/user-guide/features/memory)
- [Gestion des secrets](/docs/user-guide/secrets)
- [Threat Intelligence](/docs/cybersecurity/threat-intel)
- [Malware Analysis](/docs/cybersecurity/malware-analysis)
- [Commandes CLI](/docs/reference/cli-commands)

