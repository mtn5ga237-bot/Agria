from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.utils import timezone


class AuthentificationParEmail(ModelBackend):
    """Authentifie par adresse email et applique le verrouillage anti force-brute (Tableau 17, test T05)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        Utilisateur = get_user_model()
        email = username or kwargs.get('email')
        if email is None or password is None:
            return None
        try:
            utilisateur = Utilisateur.objects.get(email__iexact=email)
        except Utilisateur.DoesNotExist:
            Utilisateur().set_password(password)  # temps constant : evite l'enumeration de comptes
            return None

        if utilisateur.verrouille_jusqu_a and utilisateur.verrouille_jusqu_a > timezone.now():
            return None

        if utilisateur.check_password(password):
            if utilisateur.tentatives_echouees:
                utilisateur.tentatives_echouees = 0
                utilisateur.verrouille_jusqu_a = None
                utilisateur.save(update_fields=['tentatives_echouees', 'verrouille_jusqu_a'])
            # is_active n'est pas verifie ici : AuthenticationForm.confirm_login_allowed()
            # s'en charge et restitue le message "compte inactif" distinct (Dossier VII, 2.1).
            return utilisateur

        self._enregistrer_echec(utilisateur)
        return None

    def _enregistrer_echec(self, utilisateur):
        from django.conf import settings
        from datetime import timedelta

        utilisateur.tentatives_echouees += 1
        if utilisateur.tentatives_echouees >= getattr(settings, 'TENTATIVES_MAX_CONNEXION', 5):
            duree = getattr(settings, 'DUREE_VERROUILLAGE_MINUTES', 15)
            utilisateur.verrouille_jusqu_a = timezone.now() + timedelta(minutes=duree)
        utilisateur.save(update_fields=['tentatives_echouees', 'verrouille_jusqu_a'])
