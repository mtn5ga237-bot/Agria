"""Service de prediction (SoilPredictor, Annexe 6b). Charge le modele une seule fois en
memoire au demarrage du serveur applicatif (exigence de performance, Tableau 5)."""

import threading

import joblib
import numpy as np
from django.conf import settings

from .training import VARIABLES


class SoilPredictor:
    """Singleton thread-safe exposant la prediction a partir des parametres d'une analyse."""

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
            from .models import VersionModele

            version = VersionModele.objects.filter(est_active=True).order_by('-numero_version').first()
            chemin = settings.REPERTOIRE_MODELES / (version.chemin_fichier if version else 'agria_rf.joblib')
            if not chemin.exists():
                raise FileNotFoundError(
                    f"Aucun modele entraine trouve a l'emplacement {chemin}. "
                    "Executez `python manage.py entrainer_modele`."
                )
            artefact = joblib.load(chemin)
            self.modele = artefact['modele']
            self.encodeur = artefact['encodeur']
            self.classes = artefact['classes']
            self.variables = artefact.get('variables', VARIABLES)
            self.version_numero = version.numero_version if version else 0
            self._charge = True

    def predire(self, parametres: dict) -> dict:
        """parametres attendu : azote, phosphore, potassium, ph, temperature, humidite, pluviometrie."""
        self._charger_si_necessaire()
        vecteur = self._construire_vecteur(parametres)
        classe = self.modele.predict(vecteur)[0]
        probabilites = self.modele.predict_proba(vecteur)[0]
        confiance = float(np.max(probabilites) * 100)
        importances = dict(sorted(
            zip(self.variables, self.modele.feature_importances_.tolist()),
            key=lambda item: item[1], reverse=True,
        ))
        return {
            'nom_culture': self.encodeur.inverse_transform([classe])[0],
            'confiance': round(confiance, 2),
            'importances': importances,
            'version_modele': self.version_numero,
            'fiable': confiance >= settings.SEUIL_CONFIANCE_VALIDATION_EXPERT,
        }

    def _construire_vecteur(self, p: dict):
        n, ph_ = p['azote'], p['ph']
        phosphore, k = p['phosphore'], p['potassium']
        temperature, humidite, pluviometrie = p['temperature'], p['humidite'], p['pluviometrie']
        ratio_nk = n / max(k, 1)
        indice_fertilite = (n + phosphore + k) / 3
        base = {
            'N': n, 'P': phosphore, 'K': k, 'temperature': temperature,
            'humidity': humidite, 'ph': ph_, 'rainfall': pluviometrie,
            'ratio_NK': ratio_nk, 'indice_fertilite': indice_fertilite,
        }
        return np.array([[base[v] for v in self.variables]])

    @classmethod
    def recharger(cls):
        """Force le rechargement du modele actif (appele apres un reentrainement reussi)."""
        if cls._instance is not None:
            cls._instance._charge = False
