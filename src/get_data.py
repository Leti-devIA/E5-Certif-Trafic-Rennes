import pandas as pd
import requests
import logging


logger = logging.getLogger(__name__)

class GetData(object):

    def __init__(self, url) -> None:
        # URL de l'API publique de trafic
        self.url = url

        logger.info("Récupération des données trafic depuis l'URL fournie")

        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            self.data = response.json()
            logger.info("Données récupérées avec succès: %s enregistrements bruts", len(self.data))
        except Exception as e:
            logger.error(f"Échec de récupération des données trafic : {e}")
            raise

    def processing_one_point(self, data_dict: dict):

        logger.debug("Traitement d'un point de trafic")

        # Normalise un objet JSON en une ligne DataFrame
        temp = pd.DataFrame({key:[data_dict[key]] for key in ['datetime', 'trafficstatus', 'geo_point_2d', 'averagevehiclespeed', 'traveltime', 'trafficstatus']})
        temp['lat'] = data_dict['geo_point_2d']['lat']
        temp['lon'] = data_dict['geo_point_2d']['lon']
        temp['traffic'] = data_dict['trafficstatus']

        return temp

    def __call__(self):

        logger.info("Début de la construction du DataFrame trafic")

        # DataFrame final construit par concaténation
        res_df = pd.DataFrame({})

        for data_dict in self.data:
            temp_df = self.processing_one_point(data_dict)
            res_df = pd.concat([res_df, temp_df])

        # Supprime les statuts non exploitables par la carte
        res_df = res_df[res_df.traffic != 'unknown']

        logger.info("DataFrame final prêt: %s lignes après filtrage", len(res_df))

        return res_df