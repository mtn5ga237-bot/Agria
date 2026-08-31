from django import forms

from .models import Culture, TypeSol


class FormulaireTypeSol(forms.ModelForm):
    class Meta:
        model = TypeSol
        fields = ['code', 'libelle', 'description', 'ph_min', 'ph_max', 'couleur_hex']
        widgets = {'couleur_hex': forms.TextInput(attrs={'type': 'color'})}


class FormulaireCulture(forms.ModelForm):
    class Meta:
        model = Culture
        fields = [
            'nom', 'nom_scientifique', 'ph_min', 'ph_max', 'cycle_jours',
            'besoin_azote', 'besoin_phosphore', 'besoin_potassium', 'sols_favorables', 'description',
        ]
        widgets = {'sols_favorables': forms.CheckboxSelectMultiple()}
