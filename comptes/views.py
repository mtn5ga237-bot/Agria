import csv
import logging

from django.contrib import messages
from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Max, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from .forms import (
    FormulaireChangementMotDePasse, FormulaireConnexion, FormulaireCreerProducteur, FormulaireInscription,
    FormulaireProfil, FormulaireRattacherProducteur,
)
from .middleware import adresse_ip_client
from .mixins import AdministrateurRequisMixin, AgentRequisMixin
from .models import JournalActivite, Utilisateur

logger = logging.getLogger('agria.securite')


class InscriptionView(CreateView):
    form_class = FormulaireInscription
    template_name = 'comptes/inscription.html'
    success_url = reverse_lazy('comptes:connexion')

    def form_valid(self, form):
        reponse = super().form_valid(form)
        JournalActivite.objects.create(
            utilisateur=self.object,
            action='Inscription',
            adresse_ip=adresse_ip_client(self.request),
            details=f"Nouveau compte {self.object.get_role_display()}",
        )
        messages.success(
            self.request,
            "Votre compte a ete cree. Il doit etre active par un administrateur avant la premiere connexion.",
        )
        return reponse


class ConnexionView(LoginView):
    form_class = FormulaireConnexion
    template_name = 'comptes/connexion.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        # Regeneration de l'identifiant de session a la connexion (Tableau 17)
        self.request.session.cycle_key()
        reponse = super().form_valid(form)
        JournalActivite.objects.create(
            utilisateur=self.request.user,
            action='Connexion reussie',
            adresse_ip=adresse_ip_client(self.request),
        )
        return reponse

    def form_invalid(self, form):
        email = form.data.get('username', '')
        logger.info('Tentative de connexion echouee pour %s depuis %s', email, adresse_ip_client(self.request))
        return super().form_invalid(form)


@login_required
def deconnexion_view(request):
    JournalActivite.objects.create(
        utilisateur=request.user, action='Deconnexion', adresse_ip=adresse_ip_client(request),
    )
    django_logout(request)
    messages.info(request, 'Vous avez ete deconnecte.')
    return redirect('comptes:connexion')


class ProfilView(UpdateView):
    model = Utilisateur
    form_class = FormulaireProfil
    template_name = 'comptes/profil.html'
    success_url = reverse_lazy('comptes:profil')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profil mis a jour.')
        return super().form_valid(form)


@login_required
def changer_mot_de_passe_view(request):
    if request.method == 'POST':
        form = FormulaireChangementMotDePasse(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['nouveau_mot_de_passe'])
            request.user.save(update_fields=['password'])
            django_login(request, request.user, backend='comptes.backends.AuthentificationParEmail')
            JournalActivite.objects.create(
                utilisateur=request.user, action='Changement de mot de passe',
                adresse_ip=adresse_ip_client(request),
            )
            messages.success(request, 'Mot de passe modifie avec succes.')
            return redirect('comptes:profil')
    else:
        form = FormulaireChangementMotDePasse(request.user)
    return render(request, 'comptes/changer_mot_de_passe.html', {'form': form})


class GestionUtilisateursView(AdministrateurRequisMixin, ListView):
    """Liste des comptes et actions d'activation/desactivation/bannissement (Tableau 4, profil Administrateur)."""

    model = Utilisateur
    template_name = 'comptes/gestion_utilisateurs.html'
    context_object_name = 'utilisateurs'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        recherche = self.request.GET.get('q', '').strip()
        if recherche:
            qs = qs.filter(Q(nom_complet__icontains=recherche) | Q(email__icontains=recherche))
        role = self.request.GET.get('role', '').strip()
        if role:
            qs = qs.filter(role=role)
        return qs


class JournalActiviteView(AdministrateurRequisMixin, ListView):
    """Consultation du journal d'activite et de securite par l'administrateur (Tableau 4)."""

    model = JournalActivite
    template_name = 'comptes/journal_activite.html'
    context_object_name = 'entrees'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related('utilisateur')
        recherche = self.request.GET.get('q', '').strip()
        if recherche:
            qs = qs.filter(
                Q(action__icontains=recherche)
                | Q(utilisateur__email__icontains=recherche)
                | Q(adresse_ip__icontains=recherche),
            )
        return qs


@login_required
@require_POST
def changer_statut_utilisateur_view(request, pk):
    if not request.user.a_le_role('admin'):
        raise PermissionDenied("Seul l'administrateur peut modifier le statut d'un compte.")

    cible = get_object_or_404(Utilisateur, pk=pk)
    action = request.POST.get('action')
    actions = {'activer': cible.activer, 'desactiver': cible.desactiver, 'bannir': cible.bannir}
    if action not in actions:
        messages.error(request, 'Action inconnue.')
        return redirect('comptes:gestion_utilisateurs')

    actions[action]()
    JournalActivite.objects.create(
        utilisateur=request.user,
        action=f'Changement de statut du compte {cible.email} : {action}',
        adresse_ip=adresse_ip_client(request),
    )
    messages.success(request, f'Le compte de {cible.nom_complet} a ete mis a jour ({cible.statut}).')
    return redirect('comptes:gestion_utilisateurs')


# ---------------------------------------------------------------------------
# Portefeuille de producteurs de l'Agent Vulgarisateur (Tableau 4)
# ---------------------------------------------------------------------------

class MesProducteursView(AgentRequisMixin, ListView):
    """Liste des producteurs suivis par l'agent, avec statistiques par producteur et par zone."""

    template_name = 'comptes/mes_producteurs.html'
    context_object_name = 'producteurs'

    def get_queryset(self):
        return Utilisateur.objects.filter(agent_vulgarisateur=self.request.user).annotate(
            nb_parcelles=Count('parcelles', distinct=True),
            nb_analyses=Count('parcelles__analyses', distinct=True),
            derniere_analyse=Max('parcelles__analyses__date_analyse'),
        ).order_by('nom_complet')

    def get_context_data(self, **kwargs):
        contexte = super().get_context_data(**kwargs)
        zones = (
            self.get_queryset()
            .filter(parcelles__isnull=False)
            .exclude(parcelles__localite='')
            .values('parcelles__localite')
            .annotate(total=Count('parcelles', distinct=True))
            .order_by('-total')
        )
        contexte['zones'] = zones
        contexte['form_creer'] = FormulaireCreerProducteur()
        contexte['form_rattacher'] = FormulaireRattacherProducteur()
        return contexte


class CreerProducteurView(AgentRequisMixin, CreateView):
    form_class = FormulaireCreerProducteur
    template_name = 'comptes/creer_producteur.html'
    success_url = reverse_lazy('comptes:mes_producteurs')

    def form_valid(self, form):
        producteur = form.save(agent=self.request.user)
        self.object = producteur
        JournalActivite.objects.create(
            utilisateur=self.request.user,
            action=f'Producteur enregistre : {producteur.email}',
            adresse_ip=adresse_ip_client(self.request),
        )
        messages.success(self.request, f'Producteur « {producteur.nom_complet} » enregistre et rattache.')
        return redirect(self.success_url)


class RattacherProducteurView(AgentRequisMixin, View):
    def post(self, request):
        form = FormulaireRattacherProducteur(request.POST)
        if form.is_valid():
            producteur = form.producteur
            producteur.agent_vulgarisateur = request.user
            producteur.save(update_fields=['agent_vulgarisateur'])
            JournalActivite.objects.create(
                utilisateur=request.user,
                action=f'Producteur rattache : {producteur.email}',
                adresse_ip=adresse_ip_client(request),
            )
            messages.success(request, f'Producteur « {producteur.nom_complet} » rattache a votre portefeuille.')
        else:
            for erreurs in form.errors.values():
                for erreur in erreurs:
                    messages.error(request, erreur)
        return redirect('comptes:mes_producteurs')


class DetailProducteurView(AgentRequisMixin, DetailView):
    template_name = 'comptes/detail_producteur.html'
    context_object_name = 'producteur'

    def get_queryset(self):
        return Utilisateur.objects.filter(agent_vulgarisateur=self.request.user)

    def get_context_data(self, **kwargs):
        from analyses.models import Analyse

        contexte = super().get_context_data(**kwargs)
        contexte['analyses'] = Analyse.objects.filter(
            parcelle__proprietaire=self.object,
        ).select_related('parcelle', 'culture_predite').order_by('-date_analyse')[:20]
        return contexte


def exporter_producteurs_view(request):
    if not request.user.is_authenticated or not request.user.a_le_role('agent'):
        raise PermissionDenied

    producteurs = Utilisateur.objects.filter(agent_vulgarisateur=request.user).annotate(
        nb_parcelles=Count('parcelles', distinct=True),
        nb_analyses=Count('parcelles__analyses', distinct=True),
        derniere_analyse=Max('parcelles__analyses__date_analyse'),
    )

    reponse = HttpResponse(content_type='text/csv')
    reponse['Content-Disposition'] = 'attachment; filename="rapport_producteurs_agria.csv"'
    ecrivain = csv.writer(reponse)
    ecrivain.writerow(['Producteur', 'Email', 'Telephone', 'Parcelles', 'Analyses', 'Derniere analyse'])
    for p in producteurs:
        ecrivain.writerow([
            p.nom_complet, p.email, p.telephone, p.nb_parcelles, p.nb_analyses,
            p.derniere_analyse.strftime('%d/%m/%Y') if p.derniere_analyse else '',
        ])
    return reponse
