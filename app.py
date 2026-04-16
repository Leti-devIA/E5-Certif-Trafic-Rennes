from flask import Flask, g, jsonify, render_template, request, has_request_context
import flask_monitoringdashboard as dashboard
import logging
import time
import uuid
from logging.handlers import RotatingFileHandler

from keras.models import load_model
from src.get_data import GetData
from src.utils import create_figure, prediction_from_model
from src.monitoring import get_health_snapshot, init_monitoring_db, record_inference_event

# Application Flask principale
app = Flask(__name__)


# Dashboard technique externe branché sur Flask
dashboard.bind(app)
dashboard.config.database_name = "monitoring.db"


class RequestIdFilter(logging.Filter):
    # Injecte un identifiant de requête dans chaque log
    def filter(self, record):
        if has_request_context() and hasattr(g, "request_id"):
            record.request_id = g.request_id
        else:
            record.request_id = "-"
        return True


def configure_logging() -> logging.Logger:
    # Format commun pour corréler facilement les événements
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [request_id=%(request_id)s] - %(message)s"
    )

    request_filter = RequestIdFilter()

    # Fichier rotatif pour éviter un log infini
    file_handler = RotatingFileHandler("app.log", maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(request_filter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(request_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    return logging.getLogger(__name__)


logger = configure_logging()
# Crée la base SQLite de monitoring si elle n'existe pas
init_monitoring_db()


@app.before_request
def add_request_id():
    # Reprend l'ID client si fourni, sinon en génère un
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


@app.after_request
def inject_request_id_header(response):
    # Renvoie l'ID au client pour faciliter le traçage
    response.headers["X-Request-ID"] = g.request_id
    return response

# Source de données trafic (API Rennes Métropole)
data_retriever = GetData(url="https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets/etat-du-trafic-en-temps-reel/exports/json?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B")
data_cache = None

def get_cached_data(retriever):
    # Évite de recharger les données à chaque requête
    global data_cache
    if data_cache is None:
        logger.info("Chargement des données depuis l'API...")
        try:
            data_cache = retriever()
            logger.info(f"Données chargées : {len(data_cache)} points | Statuts : {data_cache['traffic'].unique().tolist()}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données : {e}")
            raise
    else:
        logger.debug("Utilisation des données en cache")
    return data_cache

try:
    data = get_cached_data(data_retriever)
except Exception as e:
    logger.error(f"Impossible de charger les données : {e}")
    raise

try:
    model = load_model('model.h5')
    logger.info("Modèle Keras chargé avec succès")
except Exception as e:
    logger.error(f"Erreur lors du chargement du modèle : {e}")
    raise


@app.route('/health', methods=['GET'])
def health():
    # Vérifications minimales de disponibilité
    data_ok = data is not None and len(data) > 0
    model_ok = model is not None

    health_snapshot = get_health_snapshot()
    payload = {
        "status": "ok" if data_ok and model_ok else "degraded",
        "checks": {
            "data_loaded": data_ok,
            "model_loaded": model_ok,
        },
        "metrics": health_snapshot,
    }
    return jsonify(payload), 200 if payload["status"] == "ok" else 503


@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':
        logger.info("Requête POST reçue")

        # Regénère la carte à afficher
        fig_map = create_figure(data)
        graph_json = fig_map.to_json()

        # Heure choisie par l'utilisateur pour la prédiction
        selected_hour = request.form['hour']

        # ── Monitoring : mesure de la latence du modèle ──────────────────
        start = time.time()
        cat_predict = prediction_from_model(model, selected_hour)
        latency = time.time() - start
        latency_ms = latency * 1000
        # ─────────────────────────────────────────────────────────────────

        color_pred_map = {
            0: ["Prédiction : Libre", "green"],
            1: ["Prédiction : Dense", "orange"],
            2: ["Prédiction : Bloqué", "red"]
        }

        if cat_predict not in color_pred_map:
            logger.error(f"ALERTE prédiction : classe inattendue {cat_predict}")
            label = "Prédiction : Inconnue"
            color = "gray"
        else:
            label = color_pred_map[cat_predict][0]
            color = color_pred_map[cat_predict][1]

        # ── Logging métier ────────────────────────────────────────────────
        logger.info(f"Heure sélectionnée : {selected_hour}h | Prédiction : {label} | Latence modèle : {latency:.3f}s")

        try:
            # Persiste l'événement pour le suivi dans le temps
            record_inference_event(
                request_id=g.request_id,
                selected_hour=int(selected_hour),
                predicted_class=cat_predict,
                predicted_label=label,
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.error(f"Erreur enregistrement monitoring : {e}")

        # ── Alerte automatique si latence trop élevée ─────────────────────
        if latency > 2.0:
            logger.warning(f"ALERTE latence : {latency:.3f}s > seuil de 2.0s")

        # ── Alerte si prédiction bloquée (possible dérive du modèle) ──────
        if cat_predict == 2:
            logger.warning(f"ALERTE prédiction : trafic BLOQUÉ prédit pour {selected_hour}h")
        # ─────────────────────────────────────────────────────────────────

        return render_template('index.html', graph_json=graph_json, text_pred=label, color_pred=color)

    else:
        logger.info("Requête GET reçue")
        # Première vue: carte sans prédiction sélectionnée
        fig_map = create_figure(data)
        graph_json = fig_map.to_json()
        return render_template('index.html', graph_json=graph_json)


if __name__ == '__main__':
    logger.info("Démarrage de l'application Flask")
    app.run(debug=True, use_reloader=False)