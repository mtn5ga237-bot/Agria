from django.db import models


class VersionModele(models.Model):
    """Trace chaque version du modele entraine et ses metriques de performance (Tableau 14)."""

    numero_version = models.PositiveIntegerField(unique=True)
    algorithme = models.CharField(max_length=100, default='RandomForestClassifier')
    exactitude = models.FloatField()
    precision_moy = models.FloatField()
    rappel_moy = models.FloatField()
    score_f1 = models.FloatField()
    chemin_fichier = models.CharField(max_length=255)
    est_active = models.BooleanField(default=False)
    date_entrainement = models.DateTimeField(auto_now_add=True)
    nb_observations_entrainement = models.PositiveIntegerField(default=0)
    hyperparametres = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'version du modele'
        verbose_name_plural = 'versions du modele'
        ordering = ['-numero_version']

    def __str__(self):
        etat = 'active' if self.est_active else 'archivee'
        return f'Modele v{self.numero_version} ({etat}, exactitude={self.exactitude:.2%})'

    def activer(self):
        VersionModele.objects.exclude(pk=self.pk).update(est_active=False)
        self.est_active = True
        self.save(update_fields=['est_active'])
