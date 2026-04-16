import plotly.express as px
import numpy as np
import logging


logger = logging.getLogger(__name__)


def create_figure(data):
    # Construit la carte interactive des points trafic
    logger.debug("Création de la figure mapbox avec %s lignes", len(data))

    fig_map = px.scatter_mapbox(
            data,
            title="Traffic en temps réel",
            color="traffic",
            lat="lat",
            lon="lon",
            color_discrete_map={'freeFlow':'green', 'heavy':'orange', 'congested':'red'},
            zoom=10,
            height=500,
            mapbox_style="carto-positron"
    )

    logger.debug("Figure mapbox créée avec succès")

    return fig_map

def prediction_from_model(model, hour_to_predict):
    # Encode l'heure en one-hot puis prédit la classe
    logger.debug("Lancement de la prédiction pour l'heure=%s", hour_to_predict)

    input_pred = np.array([0]*24)
    input_pred[int(hour_to_predict)] = 1

    cat_predict = np.argmax(model.predict(np.array([input_pred])))

    logger.debug("Prédiction terminée: catégorie=%s", cat_predict)

    return cat_predict