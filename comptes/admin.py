from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import JournalActivite, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    model = Utilisateur
    ordering = ['nom_complet']
    list_display = ['email', 'nom_complet', 'role', 'statut', 'document_present', 'is_staff', 'date_inscription']
    list_filter = ['role', 'is_active', 'est_banni', 'is_staff']
    search_fields = ['email', 'nom_complet']
    readonly_fields = ['date_inscription', 'last_login', 'tentatives_echouees', 'verrouille_jusqu_a']

    @admin.display(description='Document', boolean=True)
    def document_present(self, utilisateur):
        if utilisateur.role not in (Utilisateur.Role.AGENT, Utilisateur.Role.EXPERT):
            return None
        return bool(utilisateur.document_justificatif)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom_complet', 'telephone', 'role', 'localite', 'agent_vulgarisateur')}),
        (
            'Document justificatif (agent / expert)',
            {'fields': ('document_justificatif',), 'description':
                "Carte professionnelle ou attestation televersee a l'inscription. Absent pour un "
                "compte cree directement ici (interface d'administration) plutot que par le "
                'formulaire d\'inscription public, qui l\'exige pour un agent ou un expert.'},
        ),
        ('Statut', {'fields': ('is_active', 'est_banni', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Securite', {'fields': ('tentatives_echouees', 'verrouille_jusqu_a', 'last_login', 'date_inscription')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'nom_complet', 'role', 'localite', 'document_justificatif',
                'password1', 'password2', 'is_active', 'is_staff',
            ),
            'description':
                "Un compte agent ou expert cree ici n'est pas soumis a la verification du "
                'formulaire d\'inscription public : televersez vous-meme le document justificatif '
                "si vous en disposez, ou laissez le champ vide si vous creez le compte sur la foi "
                "d'une autre preuve (connaissance personnelle de l'agent, etc.).",
        }),
    )


@admin.register(JournalActivite)
class JournalActiviteAdmin(admin.ModelAdmin):
    list_display = ['horodatage', 'utilisateur', 'action', 'adresse_ip']
    list_filter = ['horodatage']
    search_fields = ['action', 'utilisateur__email', 'details']
    readonly_fields = [f.name for f in JournalActivite._meta.fields]
    date_hierarchy = 'horodatage'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
