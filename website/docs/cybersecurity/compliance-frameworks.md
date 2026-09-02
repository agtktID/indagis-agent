---
id: compliance-frameworks
title: "Conformité et frameworks avec Indagis Agent"
sidebar_position: 8
description: "Comment Indagis Agent aide à préparer les éléments de conformité NIS2, ISO 27001, SOC 2 et RGPD, et quelles limites il a."
---

# Conformité et frameworks avec Indagis Agent

Cette page donne une vue d'ensemble des principaux frameworks de conformité applicables aux utilisateurs d'Indagis Agent dans un contexte professionnel : NIS2, ISO 27001, SOC 2 et RGPD. Elle explique comment Indagis peut aider à préparer certains éléments, et souligne ses limites.

:::warning Indagis n'est pas un consultant conformité certifié
Indagis Agent est un outil d'analyse, de documentation et d'automatisation. Il ne remplace pas un auditeur, un DPO ou un conseil juridique. Les livrables qu'il produit doivent être relus et validés par une personne compétente avant tout usage officiel.
:::

## Vue d'ensemble par framework

### NIS2

La directive NIS2 renforce la cybersécurité des entités essentielles et importantes dans l'Union européenne. Elle impose des obligations de gestion des risques, de reporting d'incidents, de chaîne d'approvisionnement et de gouvernance. Les organisations concernées doivent mettre en place une gestion des risques opérationnels, un reporting d'incident structuré et des mesures de sécurité proportionnées.

### ISO 27001

ISO/IEC 27001 définit un système de management de la sécurité de l'information (SMSI). Elle repose sur des clauses de contexte, de leadership, de planification, de support, d'opération, d'évaluation des performances et d'amélioration. Les contrôles de l'annexe A sont alignés avec les CIS Controls et couvrent l'accès, la cryptographie, les opérations, la sécurité des communications et la conformité.

### SOC 2

SOC 2 est un cadre américain d'audit du contrôle interne pour les prestataires de services technologiques. Il repose sur cinq critères de confiance : sécurité, disponibilité, intégrité du traitement, confidentialité et vie privée. Le type II évalue l'efficacité des contrôles sur une période.

### RGPD

Le Règlement Général sur la Protection des Données encadre la collecte, le traitement et la conservation des données personnelles dans l'UE. Il impose des principes de licéité, de minimisation, de limitation des finalités et de responsabilité. Le DPO, quand il est requis, joue un rôle central.

## Comment Indagis aide

Indagis Agent peut accélérer les tâches répétitives de préparation à la conformité :

- **Collecte et analyse de preuves** : lister les configurations, les logs ou les politiques existantes.
- **Rédaction assistée** : produire des brouillons de procédures, de rapports ou de fiches.
- **Cartographie des actifs** : inventorier les systèmes, les dépendances et les flux de données.
- **Vérification technique** : contrôler la présence de chiffrement, de sauvegardes ou de logs d'audit.
- **Suivi des actions correctives** : générer des tâches, des rappels et des tableaux de bord simples.

```bash
# Exemple : vérifier la présence de logs d'audit et de chiffrement sur un endpoint
ls -la /var/log/audit/
ausearch -ts recent -k user_logins
lsblk -f  # vérifier le chiffrement des volumes
```

## Limites d'Indagis

Indagis Agent n'est pas un outil de conformité certifié. Il ne peut pas :

- Décider seul de la conformité légale d'une organisation.
- Remplacer un audit externe.
- Garantir l'exactitude juridique d'un document.
- Se substituer au jugement d'un DPO ou d'un RSSI.

Tout livrable produit par l'agent doit être considéré comme une ébauche technique soumise à validation humaine.

## Tableau comparatif

| Framework | Obligatoire pour | Ce qu'Indagis couvre | Ce qui reste manuel |
|-----------|------------------|----------------------|---------------------|
| NIS2 | Entités essentielles et importantes en UE | Inventaire, analyse de logs, rédaction de procédures incident | Décision juridique, reporting aux autorités, gouvernance |
| ISO 27001 | Organisations souhaitant certifier un SMSI | Préparation des documents, preuves techniques, cartographie | Audit externe, management review, choix des contrôles |
| SOC 2 | Prestataires de services technologiques (surtout US) | Preuves de contrôles, rapports de configuration, chronologie | Audit par un CPA, définition des critères de confiance |
| RGPD | Toute entité traitant des données UE | Inventaire des données, rédaction de fiches, vérification logs | DPO, analyse juridique, consentement, registre des traitements |

## Préparation à un audit

Indagis Agent peut aider à préparer un audit en :

1. Listant les exigences du framework cible.
2. Collectant les preuves techniques disponibles.
3. Identifiant les lacunes.
4. Rédigeant un plan d'action.
5. Documentant les décisions et les écarts.

```bash
# Exemple de demande à Indagis pour préparer un audit ISO 27001
indagis chat --skill security-compliance \
  "À partir du dossier ~/compliance/iso27001/,
   liste les contrôles couverts par des preuves et identifie les lacunes.
   Génère un plan d'action priorisé en markdown."
```

## Mapping contrôles et frameworks

Les frameworks partagent de nombreux contrôles. Un mapping évite de dupliquer le travail et montre comment une même preuve sert plusieurs référentiels.

| Thème | NIS2 | ISO 27001:2022 | CIS Controls v8 | SOC 2 CC | RGPD |
|---|---|---|---|---|---|
| Inventaire d'actifs | Art. 21 | A.5.9, A.5.13 | CIS 1, CIS 2 | CC6.1, CC6.6 | Art. 32 |
| Gestion des accès | Art. 21 | A.5.15–A.5.18 | CIS 5, CIS 6 | CC6.2, CC6.3 | Art. 32 |
| Chiffrement | Art. 21 | A.8.24 | CIS 3.10 | CC6.7 | Art. 32 |
| Logging et monitoring | Art. 23 | A.8.15, A.8.16 | CIS 8 | CC7.2 | Art. 33 |
| Gestion des incidents | Art. 23 | A.5.24–A.5.26 | CIS 17 | CC7.3, CC7.4 | Art. 33, 34 |
| Continuité | Art. 21 | A.5.29, A.8.13 | CIS 11 | A1.2 | Art. 32 |

Indagis peut générer ce type de matrice à partir d'un fichier de contrôles existants et du répertoire de preuves. La commande suivante illustre la collecte des preuves techniques alignées sur CIS Controls v8 :

```bash
# Collecte des preuves pour CIS Controls v8
mkdir -p ~/compliance/cis-v8/{preuves,rapports}
# CIS 1 : inventaire
uname -a > ~/compliance/cis-v8/preuves/inventaire.txt
dpkg -l > ~/compliance/cis-v8/preuves/packages.txt
# CIS 2 : software inventory
which apt yum dnf > ~/compliance/cis-v8/preuves/gestionnaires.txt
# CIS 3 : data protection
mount | grep crypt > ~/compliance/cis-v8/preuves/chiffrement.txt
# CIS 8 : audit logging
systemctl status auditd > ~/compliance/cis-v8/preuves/auditd-status.txt 2>&1 || true
ausearch -ts this-month -k user_logins > ~/compliance/cis-v8/preuves/logins.txt 2>&1 || true
```

## Checklist opérationnelle de pré-audit

Avant l'arrivée d'un auditeur, Indagis peut piloter une checklist technique et documentaire.

- [ ] Inventaire des actifs à jour (serveurs, postes, comptes, API).
- [ ] Politiques de sécurité accessibles et datées.
- [ ] Logs d'audit conservés sur la durée exigée.
- [ ] Procédure d'incident testée dans les 12 derniers mois.
- [ ] Sauvegardes chiffrées et restaurées au moins une fois.
- [ ] Revue des accès privilégiés effectuée ce trimestre.
- [ ] Liste des correctifs critiques appliqués.
- [ ] Registre des traitements RGPD à jour (si applicable).

```bash
# Vérifications rapides pour une checklist RGPD / ISO 27001
find /etc -name "*.policy" -newer /var/log/btmp > ~/compliance/politiques_recentes.txt
lastlog | awk '$2 != "Never"' > ~/compliance/connexions_utilisateurs.txt
sudo find /var/log -type f -mtime -90 | wc -l > ~/compliance/logs_90j.txt
```

## Automatisation avec skills, mémoire et crons

Indagis transforme la conformité en tâches récurrentes exécutées par des skills et planifiées par des crons.

- **`security-compliance`** : génère les livrables de conformité (matrices, rapports, plans d'action).
- **`documentation-and-adrs`** : produit les procédures et les traces de décision.
- **`cron`** : exécute les vérifications périodiques et les rappels.
- **`memory`** : conserve l'état de l'inventaire, des écarts et des actions en cours d'une session à l'autre.

```bash
# Exemple de cron Indagis pour une revue mensuelle de conformité
indagis chat \
  "Planifie une tâche mensuelle qui vérifie les logs d'audit,
   les sauvegardes et les politiques, puis génère un rapport dans ~/compliance/monthly/"
```

## Anti-patterns et faux amis

| Faux ami | Réalité | Bonne pratique |
|---|---|---|
| "Indagis certifie ISO 27001" | L'agent ne peut pas signer d'attestation | Valider les livrables avec un auditeur accrédité. |
| "Un scan vert = conforme" | La conformité englobe processus et gouvernance | Coupler les preuves techniques aux procédures et aux revues de management. |
| "Générer des procédures sans les relire" | Les modèles de langage inventent parfois | Chaque procédure doit être relue par le RSSI ou le DPO. |
| "Stocker les preuves n'importe où" | Les preuves doivent être traçables | Utiliser une arborescence datée et un fichier de traçabilité. |

## Liens vers les autorités et ressources

Les liens vers les textes officiels sont génériques et vérifiables :

- [NIS2 sur le site de l'UE](https://eur-lex.europa.eu)
- [ISO 27001 sur iso.org](https://www.iso.org)
- [RGPD sur cnil.fr](https://www.cnil.fr)
- [NIST SP 800-61 sur nist.gov](https://www.nist.gov)

## Rapport d'écart et plan d'action

Un audit génère des écarts. Indagis peut structurer chaque écart sous forme de fiche actionnable.

```markdown
## Écart E01 - Gestion des accès privilégiés
- **Référentiel** : ISO 27001 A.5.18, CIS Controls v8 5.4
- **Constat** : 12 comptes administrateurs n'ont pas été révisés depuis 9 mois.
- **Risque** : Compromission persistante difficile à détecter.
- **Action corrective** : Révision trimestrielle + MFA sur tous les comptes privilégiés.
- **Responsable** : RSSI
- **Échéance** : 2026-10-15
- **Preuve attendue** : Extraction IAM datée et liste des comptes nettoyés.
```

Indagis peut générer ce type de fiche à partir d'un répertoire de preuves et d'une liste de contrôles, puis produire un plan d'action global priorisé.

```bash
# Génération d'un plan d'action à partir des preuves
indagis chat --skill security-compliance \
  "Analyse ~/compliance/iso27001/preuves/ contre la liste des contrôles A.5.
   Identifie les écarts et génère un plan d'action avec échéances et responsables."
```

## Ressources pour aller plus loin

- [CIS Controls v8](https://www.cisecurity.org/controls)
- [ISO 27001/27002](https://www.iso.org)
- [Directive NIS2](https://eur-lex.europa.eu)
- [RGPD](https://www.cnil.fr)
- [SOC 2 Trust Services Criteria](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2)

## Skills Indagis recommandés

| Skill | Rôle dans la conformité |
|-------|-------------------------|
| `security-compliance` | Orchestration des tâches de conformité |
| `documentation-and-adrs` | Rédaction de procédures et de traces |
| `security-vuln-management` | Gestion des vulnérabilités et preuves techniques |
| `security-dfir-triage` | Préparation au reporting d'incidents |
| `cron` | Planification des vérifications périodiques |

## Pour aller plus loin

- [Skills Indagis](/docs/user-guide/features/skills)
- [MCP servers](/docs/user-guide/features/mcp)
- [Mémoire persistante](/docs/user-guide/features/memory)
- [Gestion des secrets](/docs/user-guide/secrets)
- [DFIR Triage](/docs/cybersecurity/dfir-triage)
- [Vulnérabilités et remédiation](/docs/cybersecurity/vulnerability-remediation)
- [Commandes CLI](/docs/reference/cli-commands)

