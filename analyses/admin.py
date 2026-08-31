from django.contrib import admin

from .models import Analyse, Recommandation


class RecommandationInline(admin.TabularInline):
    model = Recommandation
    extra = 0
    readonly_fields = ['culture', 'score', 'rang']
    can_delete = False


@admin.register(Analyse)
class AnalyseAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'parcelle', 'operateur', 'culture_predite', 'confiance_culture',
        'type_sol', 'statut', 'validee', 'date_analyse',
    ]
    list_filter = ['statut', 'validee', 'type_sol', 'culture_predite']
    search_fields = ['parcelle__nom', 'operateur__email']
    inlines = [RecommandationInline]
    date_hierarchy = 'date_analyse'
