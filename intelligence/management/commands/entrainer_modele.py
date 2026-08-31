from django.conf import settings
from django.core.management.base import BaseCommand

from intelligence.models import VersionModele
from intelligence.predictor import SoilPredictor
from intelligence.training import entrainer


class Command(BaseCommand):
    help = "Entraine le modele Random Forest d'AgriA et l'active si ses performances sont superieures."

    def add_arguments(self, parser):
        parser.add_argument('--dataset', default=str(settings.BASE_DIR / 'donnees' / 'Crop_recommendation.csv'))
        parser.add_argument('--forcer-activation', action='store_true')

    def handle(self, *args, **options):
        derniere = VersionModele.objects.order_by('-numero_version').first()
        numero = (derniere.numero_version if derniere else 0) + 1
        nom_fichier = f'agria_rf_v{numero}.joblib'
        chemin_sortie = settings.REPERTOIRE_MODELES / nom_fichier

        self.stdout.write(f'Entrainement du modele v{numero} sur {options["dataset"]} ...')
        metriques = entrainer(options['dataset'], chemin_sortie)

        version = VersionModele.objects.create(
            numero_version=numero,
            exactitude=metriques['exactitude'],
            precision_moy=metriques['precision'],
            rappel_moy=metriques['rappel'],
            score_f1=metriques['f1'],
            chemin_fichier=nom_fichier,
            nb_observations_entrainement=metriques['nb_observations'],
            hyperparametres={},
        )

        self.stdout.write(self.style.SUCCESS(
            f"Exactitude={metriques['exactitude']:.4f}  F1={metriques['f1']:.4f}  "
            f"Precision={metriques['precision']:.4f}  Rappel={metriques['rappel']:.4f}"
        ))
        self.stdout.write(metriques['rapport'])

        meilleure = (
            not derniere
            or options['forcer_activation']
            or metriques['exactitude'] >= derniere.exactitude
        )
        if meilleure:
            # Le modele courant est active en priorite ; le fichier de reference historique
            # (agria_rf.joblib) est egalement mis a jour pour le premier chargement du predicteur.
            version.activer()
            (settings.REPERTOIRE_MODELES / 'agria_rf.joblib').write_bytes(chemin_sortie.read_bytes())
            SoilPredictor.recharger()
            self.stdout.write(self.style.SUCCESS(f'Modele v{numero} active en production.'))
        else:
            self.stdout.write(self.style.WARNING(
                f"Modele v{numero} archive : exactitude inferieure a la version active "
                f"(v{derniere.numero_version}, {derniere.exactitude:.4f})."
            ))
