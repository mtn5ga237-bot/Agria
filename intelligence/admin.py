from django.contrib import admin

from .models import VersionModele


@admin.register(VersionModele)
class VersionModeleAdmin(admin.ModelAdmin):
    list_display = ['numero_version', 'algorithme', 'exactitude', 'score_f1', 'est_active', 'date_entrainement']
    list_filter = ['est_active']
    readonly_fields = [f.name for f in VersionModele._meta.fields]
    ordering = ['-numero_version']

    def has_add_permission(self, request):
        return False
