# Rennes Traffic KO

Application pédagogique de prédiction et de monitoring autour des données de trafic de Rennes.

Le projet combine :
- une application Flask pour afficher la carte et lancer une prédiction,
- un modèle Keras déjà entraîné (`model.h5`),
- un suivi de l'activité dans une base SQLite,
- un tableau de bord Streamlit pour visualiser les métriques de monitoring.

## Avertissement

Ce projet est fourni dans un cadre pédagogique.

- Il n'est pas destiné à un usage industriel ou commercial.
- Il peut contenir des bugs volontaires.
- Le modèle est volontairement simplifié et sous-optimisé.

## Fonctionnalités

- Chargement des données trafic depuis l'API de Rennes Métropole.
- Affichage d'une carte interactive avec Plotly.
- Prédiction d'un état de trafic à partir d'une heure sélectionnée.
- Journalisation applicative avec identifiant de requête.
- Endpoint de santé pour vérifier l'état de l'application.
- Enregistrement des inférences dans SQLite.
- Visualisation du monitoring dans Streamlit.
- Intégration d'un tableau de bord technique Flask Monitoring Dashboard.

## Structure du projet

```text
rennes_traffic_ko-main/
├── app.py
├── model.h5
├── monitoring.db
├── flask_monitoringdashboard.db
├── streamlit_monitoring.py
├── templates/
│   └── index.html
└── src/
	├── get_data.py
	├── monitoring.py
	└── utils.py
```

## Rôle des fichiers

- `app.py` : application Flask principale, chargement du modèle, routes HTTP, logs et monitoring.
- `src/get_data.py` : récupération et transformation des données trafic en `DataFrame`.
- `src/utils.py` : génération de la carte Plotly et appel au modèle de prédiction.
- `src/monitoring.py` : création de la base SQLite et enregistrement des événements d'inférence.
- `streamlit_monitoring.py` : tableau de bord de monitoring lisant la base `monitoring.db`.
- `templates/index.html` : interface web Flask.
- `model.h5` : modèle Keras utilisé pour la prédiction.

## Prérequis

- Python 3.10+ recommandé
- `pip`
- Connexion Internet pour récupérer les données trafic

## Dépendances Python

Le projet utilise notamment :

- `flask`
- `flask-monitoringdashboard`
- `tensorflow` ou `keras` selon l'environnement
- `pandas`
- `numpy`
- `requests`
- `plotly`
- `streamlit`

## Installation

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd rennes_traffic_ko-main
```

### 2. Créer un environnement virtuel

Sous Windows :

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install flask flask-monitoringdashboard pandas numpy requests plotly streamlit tensorflow keras
```

> Selon votre installation, `tensorflow` suffit souvent à fournir `keras`.

## Lancer l'application Flask

```bash
python app.py
```

Par défaut, l'application est accessible sur :

- `http://127.0.0.1:5000`

### Endpoints utiles

- `/` : interface principale avec carte et formulaire de prédiction
- `/health` : état applicatif et métriques simplifiées

## Lancer le tableau de bord Streamlit

Dans un second terminal :

```bash
streamlit run streamlit_monitoring.py
```

Le tableau de bord est généralement accessible sur :

- `http://localhost:8501`

## Monitoring disponible

Le projet met en place plusieurs niveaux de suivi.

### 1. Monitoring métier

Chaque prédiction enregistre :

- l'heure demandée,
- la classe prédite,
- le libellé affiché,
- la latence du modèle,
- l'identifiant de requête,
- le statut de l'événement.

Ces données sont stockées dans `monitoring.db`, table `inference_events`.

### 2. Monitoring applicatif

L'endpoint `/health` renvoie notamment :

- si les données ont bien été chargées,
- si le modèle est bien chargé,
- le nombre total de prédictions,
- la latence moyenne récente,
- le nombre d'erreurs enregistrées.

### 3. Monitoring technique Flask

Le projet utilise aussi `flask_monitoringdashboard`, branché directement sur l'application Flask.

La base associée est :

- `flask_monitoringdashboard.db`

## Journaux

Les logs sont écrits :

- dans la console,
- dans le fichier `app.log`.

Le format inclut un `request_id` pour relier les événements entre eux.

## Fonctionnement général

1. L'application Flask démarre.
2. Les données trafic sont téléchargées depuis l'API Rennes.
3. Le modèle `model.h5` est chargé.
4. L'utilisateur choisit une heure dans l'interface.
5. Une prédiction est calculée.
6. Le résultat est affiché avec une couleur associée.
7. L'événement est enregistré dans SQLite pour le monitoring.
8. Streamlit permet ensuite de visualiser les événements récents et les métriques.

## Base de données SQLite

### `monitoring.db`

Contient la table `inference_events` avec les colonnes principales suivantes :

- `id`
- `ts_utc`
- `request_id`
- `selected_hour`
- `predicted_class`
- `predicted_label`
- `latency_ms`
- `status`

## Dépannage

### `Import "flask" could not be resolved`

Le paquet Flask n'est pas installé dans l'environnement Python actif.

Solution :

```bash
pip install flask
```

### `Import "flask_monitoringdashboard" could not be resolved`

Le paquet du dashboard n'est pas installé.

Solution :

```bash
pip install flask-monitoringdashboard
```

### `streamlit run streamlit_monitoring.py` échoue

Vérifier que :

- `streamlit` est installé,
- `monitoring.db` existe,
- l'application Flask a déjà été lancée au moins une fois.

### Le tableau de bord est vide

Cela signifie généralement qu'aucune inférence n'a encore été enregistrée.

Solution :

1. lancer Flask,
2. ouvrir l'interface web,
3. effectuer une ou plusieurs prédictions,
4. relancer ou actualiser Streamlit.

## Limites du projet

- Projet conçu pour l'apprentissage, pas pour la production.
- Modèle simple, non optimisé.
- Dépendance à une API externe pour les données.
- Faible gestion avancée des erreurs et de la sécurité.

## Pistes d'amélioration

- Ajouter un fichier `requirements.txt`.
- Mettre en place des tests unitaires.
- Gérer les erreurs de manière plus fine.
- Ajouter une vraie configuration par variables d'environnement.
- Déployer l'application avec un serveur de production.
- Enrichir le dashboard avec davantage d'indicateurs.

## Auteur

Projet utilisé dans le cadre d'un travail pédagogique autour de Flask, du monitoring et de la visualisation de données.
