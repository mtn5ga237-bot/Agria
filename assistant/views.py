import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from . import services

CLE_SESSION = 'assistant_historique'
TAILLE_FENETRE = 12  # nombre de messages (utilisateur + assistant) conserves dans le contexte


@login_required
@require_POST
def discuter_view(request):
    try:
        donnees = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'erreur': 'Requete invalide.'}, status=400)

    message = (donnees.get('message') or '').strip()
    if not message:
        return JsonResponse({'erreur': 'Message vide.'}, status=400)
    if len(message) > 2000:
        return JsonResponse({'erreur': 'Message trop long (2000 caracteres maximum).'}, status=400)

    if services.limite_atteinte(request.user):
        return JsonResponse({
            'erreur': "Limite de messages atteinte pour cette heure. Reessayez plus tard ou "
                      "contactez un administrateur.",
        }, status=429)

    historique = request.session.get(CLE_SESSION, [])
    reponse = services.obtenir_reponse(request.user, message, historique)
    services.enregistrer_appel(request.user)

    historique = historique + [
        {'role': 'user', 'content': message},
        {'role': 'assistant', 'content': reponse},
    ]
    request.session[CLE_SESSION] = historique[-TAILLE_FENETRE:]

    return JsonResponse({'reponse': reponse})


@login_required
@require_POST
def reinitialiser_conversation_view(request):
    request.session.pop(CLE_SESSION, None)
    return JsonResponse({'ok': True})
