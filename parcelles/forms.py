from django import forms
from django.db.models import Q

from comptes.models import Utilisateur

from .models import Parcelle


class FormulaireParcelle(forms.ModelForm):
    """Un agent vulgarisateur peut creer une parcelle pour lui-meme ou pour l'un de ses
    producteurs (Tableau 4) ; les autres profils ne voient pas ce choix."""

    proprietaire = forms.ModelChoiceField(queryset=Utilisateur.objects.none(), label='Pour', required=False)

    class Meta:
        model = Parcelle
        fields = ['proprietaire', 'nom', 'superficie_ha', 'localite', 'latitude', 'longitude']
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def __init__(self, utilisateur, *args, **kwargs):
        self.utilisateur = utilisateur
        super().__init__(*args, **kwargs)
        if utilisateur.a_le_role('agent'):
            self.fields['proprietaire'].queryset = Utilisateur.objects.filter(
                Q(pk=utilisateur.pk) | Q(agent_vulgarisateur=utilisateur),
            )
            self.fields['proprietaire'].initial = utilisateur.pk
            self.fields['proprietaire'].required = True
        else:
            del self.fields['proprietaire']

    def save(self, commit=True):
        parcelle = super().save(commit=False)
        parcelle.proprietaire = self.cleaned_data.get('proprietaire') or self.utilisateur
        if commit:
            parcelle.save()
        return parcelle

    def clean_latitude(self):
        valeur = self.cleaned_data['latitude']
        if not -90 <= valeur <= 90:
            raise forms.ValidationError('La latitude doit etre comprise entre -90 et 90.')
        return valeur

    def clean_longitude(self):
        valeur = self.cleaned_data['longitude']
        if not -180 <= valeur <= 180:
            raise forms.ValidationError('La longitude doit etre comprise entre -180 et 180.')
        return valeur
