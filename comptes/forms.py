from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm

from .models import Utilisateur


class FormulaireInscription(forms.ModelForm):
    """Inscription (test T01/T02/T03) : role limite aux trois profils auto-inscriptibles,
    l'administrateur etant reserve et attribue manuellement (Dossier VII, 2.1)."""

    ROLES_AUTORISES = [
        (Utilisateur.Role.AGRICULTEUR, Utilisateur.Role.AGRICULTEUR.label),
        (Utilisateur.Role.AGENT, Utilisateur.Role.AGENT.label),
        (Utilisateur.Role.EXPERT, Utilisateur.Role.EXPERT.label),
    ]

    role = forms.ChoiceField(choices=ROLES_AUTORISES, label='Vous etes')
    mot_de_passe = forms.CharField(label='Mot de passe', widget=forms.PasswordInput, strip=False)
    confirmation = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput, strip=False)

    class Meta:
        model = Utilisateur
        fields = ['nom_complet', 'email', 'telephone', 'role']
        widgets = {
            'nom_complet': forms.TextInput(attrs={'autofocus': True}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Cette adresse electronique est deja utilisee.')
        return email

    def clean(self):
        cleaned = super().clean()
        mot_de_passe = cleaned.get('mot_de_passe')
        confirmation = cleaned.get('confirmation')
        if mot_de_passe and confirmation and mot_de_passe != confirmation:
            raise forms.ValidationError('Les deux mots de passe ne correspondent pas.')
        if mot_de_passe:
            password_validation.validate_password(mot_de_passe)
        return cleaned

    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.set_password(self.cleaned_data['mot_de_passe'])
        # Inscrit a l'etat "Inactif" (diagramme d'etat-transition) ; l'administrateur active le compte.
        utilisateur.is_active = False
        if commit:
            utilisateur.save()
        return utilisateur


class FormulaireConnexion(AuthenticationForm):
    username = forms.EmailField(label='Adresse electronique', widget=forms.EmailInput(attrs={'autofocus': True}))

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': "Adresse electronique ou mot de passe incorrect, ou compte verrouille apres "
                          "plusieurs echecs. Reessayez dans quelques minutes.",
        'inactive': "Ce compte n'est pas encore actif. Contactez un administrateur.",
    }


class FormulaireProfil(forms.ModelForm):
    """Le role et l'adresse electronique ne sont pas modifiables par l'utilisateur (Dossier VII, 2.6)."""

    class Meta:
        model = Utilisateur
        fields = ['nom_complet', 'telephone']


class FormulaireCreerProducteur(forms.ModelForm):
    """Permet a un agent vulgarisateur d'enregistrer un producteur de son secteur (Tableau 4).

    Le compte est active immediatement : contrairement a une auto-inscription, l'agent qui
    accompagne le producteur sur le terrain se porte garant de l'identite de celui-ci.
    """

    mot_de_passe = forms.CharField(
        label='Mot de passe initial', widget=forms.PasswordInput, strip=False,
        help_text='A communiquer au producteur ; il pourra le modifier depuis son profil.',
    )

    class Meta:
        model = Utilisateur
        fields = ['nom_complet', 'email', 'telephone']

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Cette adresse electronique est deja utilisee.')
        return email

    def clean_mot_de_passe(self):
        valeur = self.cleaned_data['mot_de_passe']
        password_validation.validate_password(valeur)
        return valeur

    def save(self, agent, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.role = Utilisateur.Role.AGRICULTEUR
        utilisateur.agent_vulgarisateur = agent
        utilisateur.is_active = True
        utilisateur.set_password(self.cleaned_data['mot_de_passe'])
        if commit:
            utilisateur.save()
        return utilisateur


class FormulaireRattacherProducteur(forms.Form):
    """Rattache un compte agriculteur existant, non encore suivi par un agent, a l'agent courant."""

    email = forms.EmailField(label="Adresse electronique du producteur")

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        try:
            producteur = Utilisateur.objects.get(email__iexact=email, role=Utilisateur.Role.AGRICULTEUR)
        except Utilisateur.DoesNotExist:
            raise forms.ValidationError("Aucun compte agriculteur ne correspond a cette adresse.")
        if producteur.agent_vulgarisateur_id:
            raise forms.ValidationError('Ce producteur est deja suivi par un autre agent.')
        self.producteur = producteur
        return email


class FormulaireChangementMotDePasse(forms.Form):
    ancien_mot_de_passe = forms.CharField(widget=forms.PasswordInput, label='Mot de passe actuel')
    nouveau_mot_de_passe = forms.CharField(widget=forms.PasswordInput, label='Nouveau mot de passe')
    confirmation = forms.CharField(widget=forms.PasswordInput, label='Confirmer le nouveau mot de passe')

    def __init__(self, utilisateur, *args, **kwargs):
        self.utilisateur = utilisateur
        super().__init__(*args, **kwargs)

    def clean_ancien_mot_de_passe(self):
        valeur = self.cleaned_data['ancien_mot_de_passe']
        if not self.utilisateur.check_password(valeur):
            raise forms.ValidationError('Mot de passe actuel incorrect.')
        return valeur

    def clean(self):
        cleaned = super().clean()
        nouveau = cleaned.get('nouveau_mot_de_passe')
        confirmation = cleaned.get('confirmation')
        if nouveau and confirmation and nouveau != confirmation:
            raise forms.ValidationError('Les deux mots de passe ne correspondent pas.')
        if nouveau:
            password_validation.validate_password(nouveau, user=self.utilisateur)
        return cleaned
