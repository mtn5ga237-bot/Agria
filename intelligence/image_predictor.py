"""Service de prediction du type de sol a partir d'une photographie (SoilImagePredictor).

Meme principe que SoilPredictor : chargement unique du modele en memoire, exposition
d'une methode de prediction simple. Modele entraine sur des caracteristiques classiques
de couleur et de texture (voir image_features.py et image_training.py)."""

import threading

from django.conf import settings

from .image_features import extraire_caracteristiques


class SoilImagePredictor:
    _instance = None
    _verrou = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._verrou:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._charge = False
                    cls._instance = instance
        return cls._instance

    def _charger_si_necessaire(self):
        if self._charge:
            return
        with self._verrou:
            if self._charge:
                return
            import joblib

            chemin = settings.REPERTOIRE_MODELES / 'agria_sol_image.joblib'
            if not chemin.exists():
                raise FileNotFoundError(
                    f"Aucun classificateur d'image de sol trouve a {chemin}. "
                    "Executez `python manage.py entrainer_classificateur_sol`."
                )
            artefact = joblib.load(chemin)
            self.modele = artefact['modele']
            self.encodeur = artefact['encodeur']
            self._charge = True

    def predire(self, fichier_image) -> dict:
        import numpy as np

        self._charger_si_necessaire()
        caracteristiques = extraire_caracteristiques(fichier_image).reshape(1, -1)
        classe = self.modele.predict(caracteristiques)[0]
        probabilites = self.modele.predict_proba(caracteristiques)[0]
        confiance = float(np.max(probabilites) * 100)
        return {
            'code_type_sol': self.encodeur.inverse_transform([classe])[0],
            'confiance': round(confiance, 2),
        }

    @classmethod
    def recharger(cls):
        if cls._instance is not None:
            cls._instance._charge = False
