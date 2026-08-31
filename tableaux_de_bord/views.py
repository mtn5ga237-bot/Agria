from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from analyses.models import Analyse
from comptes.models import Utilisateur
from parcelles.models import Parcelle
from referentiel.models import Culture


@login_required
def accueil_view(request):
    utilisateur = request.user

    if utilisateur.a_le_role('admin'):
        return _tableau_administrateur(request)
    if utilisateur.a_le_role('expert'):
        return _tableau_expert(request)
    if utilisateur.a_le_role('agent'):
        return _tableau_agent(request)
    return _tableau_agriculteur(request)


def _tableau_agriculteur(request):
    utilisateur = request.user
    analyses = Analyse.objects.filter(parcelle__proprietaire=utilisateur)
    contexte = {
        'nb_analyses': analyses.count(),
        'nb_parcelles': Parcelle.objects.filter(proprietaire=utilisateur).count(),
        'nb_cultures_recommandees': analyses.filter(recommandations__isnull=False).distinct().count(),
        'analyses_recentes': analyses.select_related('parcelle', 'type_sol').order_by('-date_analyse')[:5],
    }
    return render(request, 'tableaux_de_bord/agriculteur.html', contexte)


def _tableau_agent(request):
    utilisateur = request.user
    producteurs = Utilisateur.objects.filter(agent_vulgarisateur=utilisateur)
    analyses = Analyse.objects.filter(operateur=utilisateur)
    contexte = {
        'nb_producteurs': producteurs.count(),
        'nb_analyses': analyses.count(),
        'producteurs': producteurs[:10],
        'analyses_recentes': analyses.select_related('parcelle', 'type_sol').order_by('-date_analyse')[:5],
    }
    return render(request, 'tableaux_de_bord/agent.html', contexte)


def _tableau_expert(request):
    analyses_a_valider = Analyse.objects.filter(validee=False, statut=Analyse.Statut.TERMINEE)
    contexte = {
        'nb_analyses_a_valider': analyses_a_valider.count(),
        'nb_types_sols': Culture.objects.count(),
        'analyses_a_valider': analyses_a_valider.select_related('parcelle', 'type_sol').order_by('-date_analyse')[:10],
    }
    return render(request, 'tableaux_de_bord/expert.html', contexte)


def _tableau_administrateur(request):
    contexte = {
        'nb_utilisateurs': Utilisateur.objects.count(),
        'nb_comptes_inactifs': Utilisateur.objects.filter(is_active=False, est_banni=False).count(),
        'nb_analyses': Analyse.objects.count(),
        'nb_cultures': Culture.objects.count(),
        'repartition_roles': Utilisateur.objects.values('role').annotate(total=Count('id')),
    }
    return render(request, 'tableaux_de_bord/administrateur.html', contexte)
