from django.conf import settings
from django.core.management.base import BaseCommand

from intelligence.image_training import entrainer

CHEMIN_PAR_DEFAUT = r"C:\Users\MAJOR\Downloads\DATASET KAGGLE\archive(5)\CyAUG-Dataset"


class Command(BaseCommand):
    help = "Entraine le classificateur de type de sol par photographie (7 classes)."

    def add_arguments(self, parser):
        parser.add_argument('--dataset', default=CHEMIN_PAR_DEFAUT)

    def handle(self, *args, **options):
        chemin_sortie = settings.REPERTOIRE_MODELES / 'agria_sol_image.joblib'
        self.stdout.write(f'Extraction des caracteristiques depuis {options["dataset"]} ...')
        metriques = entrainer(options['dataset'], chemin_sortie)

        self.stdout.write(self.style.SUCCESS(
            f"Exactitude={metriques['exactitude']:.4f}  F1={metriques['f1']:.4f}  "
            f"({metriques['nb_observations']} images, {metriques['nb_test']} en test)"
        ))
        self.stdout.write(metriques['rapport'])
        self.stdout.write(self.style.SUCCESS(f'Modele enregistre dans {chemin_sortie}'))
