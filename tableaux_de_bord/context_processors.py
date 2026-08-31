from django.conf import settings


def indicateurs_navigation(request):
    """Met a disposition de tous les gabarits le role courant, utilise pour adapter le menu lateral
    (Dossier VII, 2.2 : « le menu lateral gauche donne acces aux fonctionnalites disponibles pour
    le role de l'utilisateur ») ainsi que les coordonnees par defaut de la carte (Garoua)."""
    contexte = {'centre': settings.COORDONNEES_GAROUA}
    utilisateur = getattr(request, 'user', None)
    if not utilisateur or not utilisateur.is_authenticated:
        return contexte
    contexte.update({
        'role_courant': utilisateur.role,
        'est_agriculteur': utilisateur.a_le_role('agriculteur'),
        'est_agent': utilisateur.a_le_role('agent'),
        'est_expert': utilisateur.a_le_role('expert'),
        'est_administrateur': utilisateur.a_le_role('admin'),
    })
    return contexte
