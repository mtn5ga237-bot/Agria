"""Sauvegarde automatisee de la base de donnees, avec conservation des sept dernieres
versions (Tableau 17 : « Perte de donnees » ; section 6.5 du rapport).

Independant du moteur de base de donnees (SQLite en developpement, PostgreSQL en
production) : s'appuie sur `dumpdata` plutot que sur une copie de fichier, l'ORM assurant
l'abstraction du SGBD comme le reste de la plateforme.

A planifier quotidiennement par le systeme d'exploitation cible (tache planifiee Windows en
developpement, cron en production) :
    python manage.py sauvegarder_base
"""

from datetime import datetime, timezone

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings

NB_VERSIONS_CONSERVEES = 7


class Command(BaseCommand):
    help = "Sauvegarde la base de donnees et ne conserve que les sept versions les plus recentes."

    def handle(self, *args, **options):
        repertoire = settings.BASE_DIR / 'sauvegardes'
        repertoire.mkdir(exist_ok=True)

        horodatage = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        fichier = repertoire / f'agria_sauvegarde_{horodatage}.json'

        with open(fichier, 'w', encoding='utf-8') as sortie:
            call_command(
                'dumpdata',
                exclude=['contenttypes', 'auth.permission', 'sessions.session', 'admin.logentry'],
                indent=2,
                stdout=sortie,
            )
        self.stdout.write(self.style.SUCCESS(f'Sauvegarde creee : {fichier.name}'))

        sauvegardes = sorted(repertoire.glob('agria_sauvegarde_*.json'), key=lambda p: p.name)
        excedent = sauvegardes[:-NB_VERSIONS_CONSERVEES] if len(sauvegardes) > NB_VERSIONS_CONSERVEES else []
        for ancienne in excedent:
            ancienne.unlink()
            self.stdout.write(f'Ancienne sauvegarde supprimee : {ancienne.name}')

        self.stdout.write(f'{min(len(sauvegardes), NB_VERSIONS_CONSERVEES)} version(s) conservee(s).')
