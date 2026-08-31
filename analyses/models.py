import uuid

from django.conf import settings
from django.db import models


def chemin_photo_sol(instance, nom_fichier):
    """Regenere un nom de fichier aleatoire pour la photo televersee (Tableau 17 : « noms de
    fichiers regeneres »), afin de ne jamais exposer ni reutiliser le nom fourni par l'utilisateur."""
    extension = nom_fichier.rsplit('.', 1)[-1].lower() if '.' in nom_fichier else 'jpg'
    return f'analyses/photos/{uuid.uuid4().hex}.{extension}'


class Analyse(models.Model):
    """Materialise une analyse de sol : parametres mesures, prediction et indice de confiance
    (Tableau 14, Figure 13 : diagramme d'etat-transition d'une analyse)."""

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        EN_COURS = 'en_cours', 'En cours'
        TERMINEE = 'terminee', 'Terminee'
        ERREUR = 'erreur', 'Erreur'

    parcelle = models.ForeignKey(
        'parcelles.Parcelle', on_delete=models.CASCADE, related_name='analyses',
    )
    operateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='analyses_realisees',
    )

    # Parametres physico-chimiques mesures (Dossier VII, 2.3 ; Annexe 8)
    ph = models.FloatField('pH du sol')
    azote = models.FloatField('azote N (mg/kg)')
    phosphore = models.FloatField('phosphore P (mg/kg)')
    potassium = models.FloatField('potassium K (mg/kg)')
    temperature = models.FloatField('temperature (degres C)')
    humidite = models.FloatField('humidite relative (%)')
    pluviometrie = models.FloatField('pluviometrie (mm/an)')

    # Parametres pedologiques complementaires, utilises par le moteur de recommandation
    # (Tableau 16) et par la validation de coherence de la saisie (somme des textures = 100 %).
    matiere_organique = models.FloatField('matiere organique (%)', null=True, blank=True)
    argile = models.FloatField('argile (%)', null=True, blank=True)
    limon = models.FloatField('limon (%)', null=True, blank=True)
    sable = models.FloatField('sable (%)', null=True, blank=True)

    # Prediction du modele de recommandation (Random Forest entraine sur le Crop Recommendation
    # Dataset) : la culture la mieux adaptee aux parametres physico-chimiques et climatiques saisis.
    culture_predite = models.ForeignKey(
        'referentiel.Culture', on_delete=models.PROTECT, null=True, blank=True,
        related_name='analyses_predites', verbose_name='culture recommandee par le modele',
    )
    confiance_culture = models.FloatField('indice de confiance (culture)', null=True, blank=True)
    importances_variables = models.JSONField(null=True, blank=True)

    # Classification du type de sol reel (Alluvial, Aride, Noir...), par photographie ou saisie
    # manuelle d'un expert pedologue ; alimente le bareme de recommandation (Tableau 16).
    photo_sol = models.ImageField('photo du sol', upload_to=chemin_photo_sol, null=True, blank=True)
    type_sol = models.ForeignKey(
        'referentiel.TypeSol', on_delete=models.PROTECT, null=True, blank=True, related_name='analyses',
        verbose_name='type de sol identifie',
    )
    confiance_sol = models.FloatField('indice de confiance (type de sol)', null=True, blank=True)

    statut = models.CharField(max_length=15, choices=Statut.choices, default=Statut.EN_ATTENTE)
    validee = models.BooleanField(default=False)
    date_analyse = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'analyse de sol'
        verbose_name_plural = 'analyses de sol'
        ordering = ['-date_analyse']

    def __str__(self):
        return f'Analyse {self.pk} - {self.parcelle.nom}'

    def parametres(self) -> dict:
        return {
            'ph': self.ph, 'azote': self.azote, 'phosphore': self.phosphore, 'potassium': self.potassium,
            'temperature': self.temperature, 'humidite': self.humidite, 'pluviometrie': self.pluviometrie,
            'matiere_organique': self.matiere_organique or 0,
        }


class Recommandation(models.Model):
    """Table d'association portant le score de compatibilite entre une analyse et une culture."""

    analyse = models.ForeignKey(Analyse, on_delete=models.CASCADE, related_name='recommandations')
    culture = models.ForeignKey('referentiel.Culture', on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField()
    rang = models.PositiveSmallIntegerField()
    commentaire = models.TextField(blank=True)

    class Meta:
        verbose_name = 'recommandation de culture'
        verbose_name_plural = 'recommandations de cultures'
        ordering = ['rang']
        unique_together = ['analyse', 'culture']

    def __str__(self):
        return f'{self.culture.nom} - score {self.score} (analyse {self.analyse_id})'
