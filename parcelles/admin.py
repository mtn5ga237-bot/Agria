from django.contrib import admin

from .models import Parcelle


@admin.register(Parcelle)
class ParcelleAdmin(admin.ModelAdmin):
    list_display = ['nom', 'proprietaire', 'localite', 'superficie_ha', 'date_creation']
    search_fields = ['nom', 'localite', 'proprietaire__nom_complet']
    list_filter = ['localite']
