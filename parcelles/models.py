from django.conf import settings
from django.db import models


class Parcelle(models.Model):
    """Represente une parcelle agricole geolocalisee appartenant a un producteur (Tableau 14)."""

    proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parcelles',
    )
    nom = models.CharField('nom de la parcelle', max_length=100)
    superficie_ha = models.FloatField('superficie (hectares)', null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    localite = models.CharField('localite', max_length=100, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'parcelle'
        verbose_name_plural = 'parcelles'
        ordering = ['-date_creation']

    def __str__(self):
        return f'{self.nom} ({self.proprietaire.nom_complet})'

    def analyses_recentes(self, limite=5):
        return self.analyses.order_by('-date_analyse')[:limite]
