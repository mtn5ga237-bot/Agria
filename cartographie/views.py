from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from analyses.models import Analyse


@login_required
def carte_view(request):
    return render(request, 'cartographie/carte.html', {'centre': settings.COORDONNEES_GAROUA})


@login_required
def marqueurs_json_view(request):
    """Restitue les analyses de l'utilisateur sous forme de marqueurs (Dossier VII, 2.4).

    Le marqueur est colore selon la culture recommandee par le modele (toujours disponible),
    et precise en complement le type de sol reel lorsque celui-ci a ete identifie par photo.
    """
    qs = Analyse.objects.select_related('parcelle', 'type_sol', 'culture_predite').exclude(
        culture_predite__isnull=True,
    )
    if request.user.a_le_role('agent'):
        qs = qs.filter(operateur=request.user)
    elif not request.user.a_le_role('expert', 'admin'):
        qs = qs.filter(parcelle__proprietaire=request.user)

    marqueurs = [{
        'id': a.pk,
        'lat': a.parcelle.latitude,
        'lng': a.parcelle.longitude,
        'parcelle': a.parcelle.nom,
        'culture': a.culture_predite.nom,
        'type_sol': a.type_sol.libelle if a.type_sol else None,
        'couleur': a.culture_predite.couleur_hex,
        'date': a.date_analyse.strftime('%d/%m/%Y'),
        'confiance': a.confiance_culture,
        'cultures': [r.culture.nom for r in a.recommandations.select_related('culture').order_by('rang')[:3]],
    } for a in qs]
    return JsonResponse({'marqueurs': marqueurs})
