<div align="center">

# ComplAI Sales Auto-SDR

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-Fast%20Python-blueviolet.svg)](https://docs.astral.sh/uv/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com/)
[![Gemini](https://img.shields.io/badge/Google-Gemini--2.5--flash-orange.svg)](https://deepmind.google/technologies/gemini/)
[![Mailtrap](https://img.shields.io/badge/Mailtrap-SMTP-purple.svg)](https://mailtrap.io/)

*Une architecture multi-agents sécurisée pour l'automatisation de la prospection commerciale avec des LLMs hétérogènes.*
</div>

## Introduction

Ce projet implémente un système d'agents IA (SDR - *Sales Development Representative*) visant à automatiser la création, l'évaluation, le formatage et l'envoi d'e-mails de démarchage pour le produit **ComplAI** (un outil SaaS B2B de conformité SOC2 propulsé par l'IA). 

L'approche repose sur un **manager d'agents avec garde-fous (Guardrails)** qui coordonne plusieurs sous-agents spécialisés (des rédacteurs, un évaluateur, un formateur HTML et un expéditeur) propulsés par différents modèles (OpenAI et Google Gemini) afin de garantir les meilleurs taux de conversion tout en sécurisant les opérations et en évitant les dérives.

## Concepts Clés & Logique

### 1. Agents Hétérogènes (Multi-Modèles)
Le projet tire parti des forces de différents LLMs dans un même workflow :
- **Google Gemini (2.5 Flash Lite)** est utilisé en tant qu'outils de génération rapide pour écrire les brouillons d'e-mails sous différents tons (sérieux, plein d'esprit, concis).
- **OpenAI (GPT-4o-mini)** est utilisé pour le raisonnement de haut niveau (le Sales Manager) et pour des tâches techniques spécifiques de formatage (Génération d'objet, conversion HTML).

### 2. Le Modèle "Evaluator-Optimizer" 
Le `Sales Manager` (Directeur des ventes) ne rédige pas lui-même les e-mails. La logique repose sur une évaluation comparative où il :
1. *Sollicite* la rédaction auprès de trois agents distincts.
2. *Évalue* les trois brouillons de manière critique selon le contexte.
3. *Sélectionne* le meilleur e-mail à envoyer.

### 3. Agent Handoffs (Transfert de tâches)
Une fois le meilleur e-mail sélectionné, le Sales Manager utilise le concept de **Handoff** (Passage de relais) pour transférer l'e-mail gagnant à l'agent `Email Manager`. Ce dernier a son propre scope d'outils et prend la responsabilité finale de la mise en forme et de la transmission.

### 4. Guardrails (Garde-fous de Sécurité)
Le `Sales Manager` est instancié en tant que `GuardrailAgent`. Il est configuré pour détecter et bloquer les requêtes potentiellement dangereuses ou illégitimes (via les exceptions `InputGuardrailTripwireTriggered`). Par exemple, bloquer l'envoi d'e-mails se faisant passer indûment pour le PDG de l'entreprise, protégeant ainsi la réputation de ComplAI.

### 5. Utilisation d'Outils (Tool Calling)
L'agent intègre des fonctions Python natives ("outils") qu'il est capable d'appeler de manière autonome :
- `subject_writer` : Sous-agent transformé en outil pour générer un objet d'e-mail accrocheur.
- `html_converter` : Sous-agent transformé en outil pour coder le texte en structure HTML stylisée.
- `send_html_email` : Fonction standard interagissant avec l'API SMTP de **Mailtrap** pour envoyer l'e-mail dans une sandbox sécurisée.

### 6. Observabilité et Tracing (`trace`)
Afin de suivre en profondeur la prise de décision, l'orchestration multi-agents et les appels d'outils, le workflow est encapsulé dans un bloc `with trace(...)`. Ce système de **tracing** permet d'enregistrer et de visualiser l'ensemble du cheminement logique, des itérations et des transferts de tâches ("handoffs") directement depuis le tableau de bord de la plateforme **OpenAI**. Cela garantit un debug facilité et une transparence totale sur les choix effectués par le *Sales Manager* lors de ses évaluations.


## Architecture du Flux (Workflow)

1. **Input utilisateur** : Une demande d'envoi de prospection parvient au `Sales Manager`.
2. **Contrôle Guardrail** : Inspection de la légitimité contextuelle de la requête.
3. **Drafting Multi-Agent** : Le Sales Manager sollicite successivement ou en parallèle les agents sous-jacents (`sales_agent1`, `sales_agent2`, `sales_agent3`).
4. **Sélection & Tri** : Choix du e-mail "Winner" parmi les propositions.
5. **Handoff** : Transfert exclusif de l'e-mail au `Email Manager`.
6. **Polissage & Envoi** : L'Email Manager écrit l'objet via un premier outil, génère le HTML via le second, et active l'envoi SMTP via le troisième.

## Installation & Utilisation

### Prérequis
- Python 3.12+
- Clés API : `OPENAI_API_KEY`, `GOOGLE_API_KEY`
- Identifiants SMTP Sandbox : `MAILTRAP_USERNAME`, `MAILTRAP_PASSWORD`

### Configuration
*Ce projet est configuré pour utiliser **[uv](https://docs.astral.sh/uv/)**, un gestionnaire de packages ultra-rapide.*

1. Clonez le dépôt et naviguez dans le répertoire.
2. Synchronisez l'environnement et installez les dépendances avec `uv` :
   ```bash
   uv sync
   ```
3. Copiez le fichier d'exemple pour créer votre configuration locale :
   ```bash
   cp .env.example .env
   ```
   *Puis, éditez le fichier `.env` pour y renseigner vos propres clés API (`OPENAI_API_KEY`, `GOOGLE_API_KEY`, etc.).*
4. Assurez-vous d'avoir le fichier de règles `guardrails_config.json` présent.

### Exécution
Démarrez la macro-séquence automatisée via `uv` :
```bash
uv run main.py
```
*Le script initie les boucles de prospection. Consultez la console pour vérifier le raisonnement des agents, et votre boîte de réception Mailtrap Sandbox pour lire les résultats.*

---

## Statut du Projet (POC)

**Ce projet est un Proof of Concept (POC).** 
L'entreprise **"ComplAI"** mentionnée dans les instructions de système (`instructions`) est purement fictive et est utilisée uniquement à des fins de démonstration du comportement des agents dans un cadre B2B réaliste.

### Pistes d'Amélioration
Cette architecture de base modulaire a vocation à être étendue. Voici quelques pistes pour une mise en production :
- **Observabilité Avancée** : Connexion à un gestionnaire de logs ou de monitoring LLM professionnel (LangSmith, Datadog, etc.) pour stocker l'historique des traces et analyser les coûts.
- **Intégration CRM** : Remplacer les données de test codées en dur par des appels API directs vers un CRM (HubSpot, Salesforce) pour dynamiser l'envoi.
- **Agents d'enrichissement** : Ajouter des agents capables de naviguer sur le web (scraping LinkedIn ou site cible) pour hyper-personnaliser le contenu de l'e-mail avec une pertinence maximale avant rédaction.
- **Mailing en Production** : Basculer de la Sandbox Mailtrap à un environnement de production via SendGrid ou Amazon SES.
