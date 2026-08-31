from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView

from .forms import FormulaireParcelle
from .models import Parcelle


class MesParcellesView(LoginRequiredMixin, ListView):
    template_name = 'parcelles/liste.html'
    context_object_name = 'parcelles'

    def get_queryset(self):
        return Parcelle.objects.filter(proprietaire=self.request.user)


class ParcelleDetailView(LoginRequiredMixin, DetailView):
    model = Parcelle
    template_name = 'parcelles/detail.html'
    context_object_name = 'parcelle'

    def get_queryset(self):
        utilisateur = self.request.user
        if utilisateur.a_le_role('agent'):
            return Parcelle.objects.filter(
                Q(proprietaire=utilisateur) | Q(proprietaire__agent_vulgarisateur=utilisateur),
            )
        if utilisateur.a_le_role('expert', 'admin'):
            return Parcelle.objects.all()
        return Parcelle.objects.filter(proprietaire=utilisateur)


class CreerParcelleView(LoginRequiredMixin, CreateView):
    """Depuis la carte, un clic sur une zone vierge pre-remplit les coordonnees de la
    nouvelle parcelle via les parametres `lat`/`lng` de l'URL (Dossier VII, 2.4)."""

    model = Parcelle
    form_class = FormulaireParcelle
    template_name = 'parcelles/formulaire.html'
    success_url = reverse_lazy('parcelles:liste')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['utilisateur'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        lat, lng = self.request.GET.get('lat'), self.request.GET.get('lng')
        if lat and lng:
            try:
                initial['latitude'] = float(lat)
                initial['longitude'] = float(lng)
            except ValueError:
                pass
        return initial

    def get_context_data(self, **kwargs):
        contexte = super().get_context_data(**kwargs)
        lat, lng = self.request.GET.get('lat'), self.request.GET.get('lng')
        if lat and lng:
            try:
                contexte['centre'] = {'lat': float(lat), 'lng': float(lng)}
                contexte['point_initial'] = True
            except ValueError:
                pass
        return contexte

    def form_valid(self, form):
        messages.success(self.request, f'Parcelle « {form.instance.nom} » enregistree.')
        return super().form_valid(form)


class SupprimerParcelleView(LoginRequiredMixin, DeleteView):
    model = Parcelle
    template_name = 'parcelles/confirmer_suppression.html'
    success_url = reverse_lazy('parcelles:liste')

    def get_queryset(self):
        return Parcelle.objects.filter(proprietaire=self.request.user)
