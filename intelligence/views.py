from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView

from comptes.middleware import adresse_ip_client
from comptes.mixins import ExpertRequisMixin
from comptes.models import JournalActivite

from .models import VersionModele


class HistoriqueVersionsView(ExpertRequisMixin, ListView):
    """Espace expert : suivi des versions du modele et de leurs metriques (Tableau 4)."""

    model = VersionModele
    template_name = 'intelligence/historique_versions.html'
    context_object_name = 'versions'


class ReentrainerModeleView(ExpertRequisMixin, ListView):
    model = VersionModele
    template_name = 'intelligence/reentrainer.html'
    context_object_name = 'versions'

    def post(self, request, *args, **kwargs):
        # Import differe : pandas n'est utilise que par le reentrainement (reserve a
        # l'expert), pas par le reste de l'application - inutile de l'exiger au demarrage
        # du serveur sur un hebergement au stockage limite.
        import pandas as pd

        from analyses.models import Analyse

        analyses_validees = Analyse.objects.filter(validee=True, culture_predite__isnull=False)
        observations = pd.DataFrame([{
            'N': a.azote, 'P': a.phosphore, 'K': a.potassium,
            'temperature': a.temperature, 'humidity': a.humidite,
            'ph': a.ph, 'rainfall': a.pluviometrie, 'label': a.culture_predite.code,
        } for a in analyses_validees])

        from .training import entrainer

        derniere = VersionModele.objects.order_by('-numero_version').first()
        numero = (derniere.numero_version if derniere else 0) + 1
        nom_fichier = f'agria_rf_v{numero}.joblib'
        chemin_sortie = settings.REPERTOIRE_MODELES / nom_fichier

        metriques = entrainer(
            settings.BASE_DIR / 'donnees' / 'Crop_recommendation.csv',
            chemin_sortie,
            observations_supplementaires=observations if not observations.empty else None,
        )
        version = VersionModele.objects.create(
            numero_version=numero,
            exactitude=metriques['exactitude'], precision_moy=metriques['precision'],
            rappel_moy=metriques['rappel'], score_f1=metriques['f1'],
            chemin_fichier=nom_fichier, nb_observations_entrainement=metriques['nb_observations'],
        )

        if not derniere or metriques['exactitude'] >= derniere.exactitude:
            version.activer()
            (settings.REPERTOIRE_MODELES / 'agria_rf.joblib').write_bytes(chemin_sortie.read_bytes())
            from .predictor import SoilPredictor
            SoilPredictor.recharger()
            messages.success(
                request,
                f"Nouveau modele v{numero} entraine et active (exactitude {metriques['exactitude']:.2%}, "
                f"{len(observations)} observation(s) de terrain integree(s)).",
            )
        else:
            messages.warning(
                request,
                f"Nouveau modele v{numero} entraine mais archive : exactitude "
                f"({metriques['exactitude']:.2%}) inferieure a la version active "
                f"({derniere.exactitude:.2%}).",
            )

        JournalActivite.objects.create(
            utilisateur=request.user,
            action=f'Reentrainement du modele (v{numero})',
            adresse_ip=adresse_ip_client(request),
            details=f"Exactitude={metriques['exactitude']:.4f}",
        )
        return redirect('intelligence:historique_versions')
