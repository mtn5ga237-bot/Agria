from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from comptes.mixins import ExpertRequisMixin

from .forms import FormulaireCulture, FormulaireTypeSol
from .models import Culture, TypeSol


class GestionTypesSolsView(ExpertRequisMixin, ListView):
    """Gestion du referentiel des types de sols, reservee a l'expert pedologue (Tableau 4)."""

    model = TypeSol
    template_name = 'referentiel/types_sols.html'
    context_object_name = 'types_sols'


class CreerTypeSolView(ExpertRequisMixin, CreateView):
    model = TypeSol
    form_class = FormulaireTypeSol
    template_name = 'referentiel/typesol_formulaire.html'
    success_url = reverse_lazy('referentiel:types_sols')

    def form_valid(self, form):
        messages.success(self.request, f'Type de sol « {form.instance.libelle} » ajoute.')
        return super().form_valid(form)


class ModifierTypeSolView(ExpertRequisMixin, UpdateView):
    model = TypeSol
    form_class = FormulaireTypeSol
    template_name = 'referentiel/typesol_formulaire.html'
    success_url = reverse_lazy('referentiel:types_sols')


class SupprimerTypeSolView(ExpertRequisMixin, DeleteView):
    model = TypeSol
    template_name = 'referentiel/confirmer_suppression.html'
    success_url = reverse_lazy('referentiel:types_sols')


class GestionCulturesView(ExpertRequisMixin, ListView):
    """Gestion du referentiel des cultures, reservee a l'expert pedologue (Tableau 4)."""

    model = Culture
    template_name = 'referentiel/cultures.html'
    context_object_name = 'cultures'


class CreerCultureView(ExpertRequisMixin, CreateView):
    model = Culture
    form_class = FormulaireCulture
    template_name = 'referentiel/culture_formulaire.html'
    success_url = reverse_lazy('referentiel:cultures')

    def form_valid(self, form):
        messages.success(self.request, f'Culture « {form.instance.nom} » ajoutee.')
        return super().form_valid(form)


class ModifierCultureView(ExpertRequisMixin, UpdateView):
    model = Culture
    form_class = FormulaireCulture
    template_name = 'referentiel/culture_formulaire.html'
    success_url = reverse_lazy('referentiel:cultures')


class SupprimerCultureView(ExpertRequisMixin, DeleteView):
    model = Culture
    template_name = 'referentiel/confirmer_suppression.html'
    success_url = reverse_lazy('referentiel:cultures')
