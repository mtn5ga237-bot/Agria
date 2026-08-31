from django import forms
from django.db.models import Q

from parcelles.models import Parcelle

from .models import Analyse


class ChampParcelle(forms.ModelChoiceField):
    """Affiche le nom du proprietaire pour les parcelles suivies par un agent, afin de
    distinguer ses propres parcelles de celles des producteurs qu'il accompagne."""

    def label_from_instance(self, parcelle):
        if parcelle.proprietaire_id != self.utilisateur_courant_id:
            return f'{parcelle.nom} — {parcelle.proprietaire.nom_complet}'
        return parcelle.nom


class FormulaireAnalyse(forms.ModelForm):
    """Formulaire de saisie des parametres du sol (Dossier VII, 2.3 ; test T07).

    Un agent vulgarisateur peut realiser une analyse pour le compte d'un producteur qu'il
    suit (Tableau 4) : la liste des parcelles inclut alors aussi celles de ses producteurs.
    """

    parcelle = ChampParcelle(queryset=Parcelle.objects.none(), label='Parcelle')

    class Meta:
        model = Analyse
        fields = [
            'parcelle', 'ph', 'azote', 'phosphore', 'potassium',
            'temperature', 'humidite', 'pluviometrie',
            'matiere_organique', 'argile', 'limon', 'sable', 'photo_sol',
        ]
        widgets = {
            'photo_sol': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'ph': forms.NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 14}),
            'azote': forms.NumberInput(attrs={'step': '0.1', 'min': 0}),
            'phosphore': forms.NumberInput(attrs={'step': '0.1', 'min': 0}),
            'potassium': forms.NumberInput(attrs={'step': '0.1', 'min': 0}),
            'temperature': forms.NumberInput(attrs={'step': '0.1'}),
            'humidite': forms.NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 100}),
            'pluviometrie': forms.NumberInput(attrs={'step': '0.1', 'min': 0}),
            'matiere_organique': forms.NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 20}),
            'argile': forms.NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 100}),
            'limon': forms.NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 100}),
            'sable': forms.NumberInput(attrs={'step': '0.1', 'min': 0, 'max': 100}),
        }

    def __init__(self, utilisateur, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if utilisateur.a_le_role('agent'):
            queryset = Parcelle.objects.filter(
                Q(proprietaire=utilisateur) | Q(proprietaire__agent_vulgarisateur=utilisateur),
            ).select_related('proprietaire')
        else:
            queryset = Parcelle.objects.filter(proprietaire=utilisateur)
        self.fields['parcelle'].queryset = queryset
        self.fields['parcelle'].utilisateur_courant_id = utilisateur.pk
        for nom in ['matiere_organique', 'argile', 'limon', 'sable', 'photo_sol']:
            self.fields[nom].required = False

    def clean_photo_sol(self):
        """Controle du type MIME et de la taille du fichier televerse (Tableau 17 : risque de
        televersement malveillant). Le format est deja verifie par ImageField (decodage Pillow) ;
        seule la taille maximale doit etre imposee explicitement."""
        photo = self.cleaned_data.get('photo_sol')
        if photo and hasattr(photo, 'size') and photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("L'image du sol ne doit pas depasser 5 Mo.")
        return photo

    def clean_ph(self):
        valeur = self.cleaned_data['ph']
        if not 0 <= valeur <= 14:
            raise forms.ValidationError('Le pH doit etre compris entre 0 et 14.')
        return valeur

    def clean_humidite(self):
        valeur = self.cleaned_data['humidite']
        if not 0 <= valeur <= 100:
            raise forms.ValidationError("L'humidite doit etre comprise entre 0 et 100 %.")
        return valeur

    def clean(self):
        cleaned = super().clean()
        argile, limon, sable = cleaned.get('argile'), cleaned.get('limon'), cleaned.get('sable')
        if argile is not None and limon is not None and sable is not None:
            somme = argile + limon + sable
            if abs(somme - 100) > 2:
                raise forms.ValidationError(
                    f"La somme des trois fractions texturales (argile + limon + sable = {somme:.1f} %) "
                    "doit avoisiner 100 %."
                )
        for champ in ('azote', 'phosphore', 'potassium'):
            valeur = cleaned.get(champ)
            if valeur is not None and valeur < 0:
                raise forms.ValidationError(f'La teneur {champ} ne peut pas etre negative.')
        return cleaned
