"""Adaptateurs django-allauth pour la connexion via Google.

Deux regles metier specifiques a AgriA :
1. Si l'adresse Google correspond a un compte deja existant (inscrit classiquement),
   on relie le compte Google a ce compte plutot que de lever une erreur de doublon.
2. Un compte cree via Google reste soumis a la meme politique d'activation manuelle
   par un administrateur que les inscriptions classiques (Tableau 4, Dossier V) : la
   connexion sociale est un mode d'authentification alternatif, pas un contournement
   du controle d'acces.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from comptes.models import Utilisateur


class AdaptateurCompte(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return True


class AdaptateurSocial(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('email', '').lower()
        if not email or sociallogin.is_existing:
            return
        try:
            utilisateur_existant = Utilisateur.objects.get(email__iexact=email)
        except Utilisateur.DoesNotExist:
            return
        sociallogin.connect(request, utilisateur_existant)

    def populate_user(self, request, sociallogin, data):
        utilisateur = super().populate_user(request, sociallogin, data)
        utilisateur.nom_complet = data.get('name') or utilisateur.email.split('@')[0]
        utilisateur.role = Utilisateur.Role.AGRICULTEUR
        utilisateur.is_active = False
        return utilisateur

    def save_user(self, request, sociallogin, form=None):
        utilisateur = super().save_user(request, sociallogin, form)
        from comptes.middleware import adresse_ip_client
        from comptes.models import JournalActivite

        JournalActivite.objects.create(
            utilisateur=utilisateur,
            action='Inscription via Google',
            adresse_ip=adresse_ip_client(request),
        )
        return utilisateur
