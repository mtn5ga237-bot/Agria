import logging

logger = logging.getLogger('agria.securite')

CHEMINS_SENSIBLES = {
    '/comptes/connexion/': 'Connexion',
    '/comptes/inscription/': 'Inscription',
    '/comptes/deconnexion/': 'Deconnexion',
}


def adresse_ip_client(request):
    en_tete = request.META.get('HTTP_X_FORWARDED_FOR')
    if en_tete:
        return en_tete.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class JournalActiviteMiddleware:
    """Journalise les operations sensibles (connexions, actions d'administration) dans JournalActivite.

    Implemente en middleware plutot qu'en signal pour disposer systematiquement de l'adresse IP
    et du contexte de la requete, conformement au Tableau 17 (« journalisation des operations sensibles »).
    """

    METHODES_SENSIBLES = {'POST', 'PUT', 'PATCH', 'DELETE'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._journaliser_si_pertinent(request, response)
        return response

    def _journaliser_si_pertinent(self, request, response):
        if request.method not in self.METHODES_SENSIBLES:
            return
        if not request.path.startswith(('/comptes/', '/referentiel/gerer/', '/intelligence/reentrainer')):
            return
        if response.status_code >= 500:
            return

        from .models import JournalActivite

        utilisateur = getattr(request, 'user', None)
        utilisateur = utilisateur if utilisateur and utilisateur.is_authenticated else None

        JournalActivite.objects.create(
            utilisateur=utilisateur,
            action=f'{request.method} {request.path}',
            adresse_ip=adresse_ip_client(request),
            details=f'Statut de reponse : {response.status_code}',
        )
