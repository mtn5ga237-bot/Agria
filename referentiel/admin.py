from django.contrib import admin

from .models import Culture, TypeSol


@admin.register(TypeSol)
class TypeSolAdmin(admin.ModelAdmin):
    list_display = ['libelle', 'code', 'ph_min', 'ph_max', 'couleur_hex']
    search_fields = ['libelle', 'code']
    prepopulated_fields = {'code': ('libelle',)}


@admin.register(Culture)
class CultureAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'nom_scientifique', 'ph_min', 'ph_max', 'cycle_jours', 'couleur_hex']
    search_fields = ['nom', 'code', 'nom_scientifique']
    filter_horizontal = ['sols_favorables']
