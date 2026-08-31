from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import JournalActivite, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    model = Utilisateur
    ordering = ['nom_complet']
    list_display = ['email', 'nom_complet', 'role', 'statut', 'is_staff', 'date_inscription']
    list_filter = ['role', 'is_active', 'est_banni', 'is_staff']
    search_fields = ['email', 'nom_complet']
    readonly_fields = ['date_inscription', 'last_login', 'tentatives_echouees', 'verrouille_jusqu_a']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom_complet', 'telephone', 'role', 'agent_vulgarisateur')}),
        ('Statut', {'fields': ('is_active', 'est_banni', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Securite', {'fields': ('tentatives_echouees', 'verrouille_jusqu_a', 'last_login', 'date_inscription')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom_complet', 'role', 'password1', 'password2', 'is_active', 'is_staff'),
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
