from django.core.management.base import BaseCommand

from comptes.models import Utilisateur

COMPTES = [
    ('admin@agria.local', 'Administrateur AgriA', Utilisateur.Role.ADMINISTRATEUR, True),
    ('expert@agria.local', 'Fatima Expert Pedologue', Utilisateur.Role.EXPERT, False),
    ('agent@agria.local', 'Ibrahim Agent Vulgarisateur', Utilisateur.Role.AGENT, False),
    ('agriculteur@agria.local', 'Moussa Agriculteur', Utilisateur.Role.AGRICULTEUR, False),
]


class Command(BaseCommand):
    help = 'Cree un compte de demonstration par role, mot de passe AgriA2026!'

    def handle(self, *args, **options):
        for email, nom, role, staff in COMPTES:
            if Utilisateur.objects.filter(email=email).exists():
                self.stdout.write(f'{email} existe deja, ignore.')
                continue
            utilisateur = Utilisateur.objects.create_user(
                email=email, nom_complet=nom, password='AgriA2026!', role=role,
            )
            utilisateur.is_active = True
            utilisateur.is_staff = staff
            utilisateur.is_superuser = staff
            utilisateur.save()
            self.stdout.write(self.style.SUCCESS(f'Cree : {email} / AgriA2026! ({role})'))
