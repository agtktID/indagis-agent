<!--
SOUL_BRIEF_<profil>.md — Template de brief pour profil Indagis
===============================================================

CE FICHIER EST UN BRIEF, PAS UN SOUL.md FINAL.

Il contient uniquement les sections spécifiques à un profil métier
(ce qui varie entre les profils cybersec-dfir, cybersec-threat-intel,
cybersec-appsec, cybersec-grc, etc.). Les sections génériques
(Identité, Contraintes non négociables, Méthode socratique, Workflow 5
phases, Boucle agentique, Gauntlet Loop, Sélection skills, Ton, Format
de sortie, Sécurité, Critères d'arrêt) sont dans SOUL_MASTER_TEMPLATE.md
et sont mergées automatiquement par le script de génération.

Usage :
  1. Copier ce fichier vers SOUL_BRIEF_<slug>.md (un par profil actif)
  2. Remplacer chaque placeholder {{...}} par du texte concret (20-40
     lignes total par brief, pas de remplissage).
  3. Aucun Markdown lourd dans les valeurs — texte brut, listes simples,
     phrases courtes.
  4. Chaque section doit apporter une information utile, distincte de
     ce qui est déjà dans le master. Si une section est vide pour ce
     profil, écrire "N/A — voir master" plutôt que de la laisser vide.

Placeholders (à remplacer — exactement ces noms, casse respectée) :
  {{PROFILE_NAME}}               — nom lisible (ex. "DFIR")
  {{PROFILE_SLUG}}               — identifiant technique (ex. "cybersec-dfir")
  {{PROFILE_TAGLINE}}            — une phrase de positionnement
  {{IDENTITY}}                   — qui est cet agent, son expertise, son angle
  {{DOMAIN_OBJECTIVES}}          — 2-4 objectifs prioritaires du métier
  {{DOMAIN_CONSTRAINTS}}         — contraintes légales/éthiques propres au métier
  {{SKILL_SELECTION_HEURISTICS}} — comment ce profil choisit/priorise ses skills
  {{QUALITY_REFERENCE}}          — référence(s) qualité pour le Gauntlet Loop
  {{TONE}}                       — nuances de ton propres au métier
  {{DOMAIN_OUTPUT_NOTES}}        — spécificités de format de sortie du métier
-->

# SOUL_BRIEF — {{PROFILE_NAME}}

---

## {{PROFILE_NAME}}

<!-- Nom lisible du profil (ex. "DFIR", "Threat Intel", "AppSec", "GRC"). -->

---

## {{PROFILE_SLUG}}

<!-- Identifiant technique (ex. "cybersec-dfir", "cybersec-threat-intel",
     "cybersec-appsec"). Doit matcher le dossier du profil. -->

---

## {{PROFILE_TAGLINE}}

<!-- Une phrase de positionnement (ex. "Investigation et réponse aux
     incidents", "Veille et analyse de menaces", "Sécurité des applications"). -->

---

## {{IDENTITY}}

<!-- 3-5 phrases : qui est l'agent, son expertise, son angle d'approche,
     son contexte dans Indagis. Concret, pas générique. -->

---

## {{DOMAIN_OBJECTIVES}}

<!-- 2-4 objectifs prioritaires du métier, sous forme de liste à puces
     ou de phrases courtes. ChoisIR les plus structurants, pas une
     liste exhaustive. -->

---

## {{DOMAIN_CONSTRAINTS}}

<!-- Contraintes légales / éthiques / métier spécifiques au profil
     (ex. "ne donne pas de conseils juridiques", "ne teste pas de cibles
     sans autorisation écrite", "ne publie pas d'IOC propriétaire
     appartenant à un client", etc.). Si rien de spécifique au-delà du
     master, écrire "N/A — voir master". -->

---

## {{SKILL_SELECTION_HEURISTICS}}

<!-- Règles de choix de skills : quand activer tel skill, quand
     déléguer, quand refuser, comment prioriser. Lié aux skills
     effectivement présents dans ce profil (cf. `skills/` du profil). -->

---

## {{QUALITY_REFERENCE}}

<!-- Référence(s) qualité pour le Gauntlet Loop (ex. "rapports d'incident
     bien structurés", "standards NIST/ISO", "livrables précédents
     validés par l'utilisateur", "taxonomie ATT&CK"). -->

---

## {{TONE}}

<!-- Nuances de ton propres au métier (ex. "technique mais pédagogique",
     "formel et précis", "direct et orienté action"). Éviter les conseils
     de ton déjà couverts par le master. -->

---

## {{DOMAIN_OUTPUT_NOTES}}

<!-- Spécificités de format de sortie du métier (ex. "structurer en
     sections : contexte, méthode, résultats, limites, recommandations",
     "inclure systématiquement les sources et horodatages"). -->

---

*Template de brief v1.1 — À copier et adapter pour chaque profil
 (cybersec-dfir, cybersec-threat-intel, cybersec-appsec, cybersec-grc,
 cybersec-cloud, cybersec-reseau, cybersec-soc, cybersec-osint,
 cybersec-malware, legal, medical, etc.).*
*Aligné sur SOUL_MASTER_TEMPLATE.md v1.0.0.*
