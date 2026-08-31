from django.db import models


class TypeSol(models.Model):
    """Referentiel des types de sols reconnus par le modele (Tableau 14).

    Chaque type de sol correspond a l'une des classes predites par le moteur de classification
    (cf. Annexe 8, dictionnaire des donnees : le champ soilType prend pour valeur l'une des
    cultures du referentiel). Le profil colorimetrique sert a la restitution cartographique
    (marqueurs colores, Dossier VII 2.4).
    """

    code = models.SlugField('code', max_length=40, unique=True)
    libelle = models.CharField('libelle', max_length=100)
    description = models.TextField('description', blank=True)
    ph_min = models.FloatField('pH minimal observe')
    ph_max = models.FloatField('pH maximal observe')
    couleur_hex = models.CharField('couleur du marqueur', max_length=7, default='#3388ff')

    class Meta:
        verbose_name = 'type de sol'
        verbose_name_plural = 'referentiel des types de sols'
        ordering = ['libelle']

    def __str__(self):
        return self.libelle


class Culture(models.Model):
    """Decrit une culture et ses exigences agronomiques (Tableau 14, Tableau 16)."""

    code = models.SlugField(
        'code', max_length=40, unique=True, default='',
        help_text="Etiquette anglaise du jeu de donnees Kaggle (ex. 'cotton'), utilisee pour relier "
                  'la prediction brute du modele a cette fiche.',
    )
    nom = models.CharField('nom', max_length=100, unique=True)
    nom_scientifique = models.CharField('nom scientifique', max_length=150, blank=True)
    ph_min = models.FloatField('pH minimal tolere')
    ph_max = models.FloatField('pH maximal tolere')
    cycle_jours = models.PositiveSmallIntegerField('duree du cycle (jours)')
    besoin_azote = models.FloatField('besoin en azote (mg/kg)', help_text='Seuil utilise par le bareme de score')
    besoin_phosphore = models.FloatField('besoin en phosphore (mg/kg)', default=30)
    besoin_potassium = models.FloatField('besoin en potassium (mg/kg)', default=100)
    couleur_hex = models.CharField('couleur du marqueur', max_length=7, default='#22c55e')
    description = models.TextField('conseils culturaux', blank=True)
    sols_favorables = models.ManyToManyField(
        TypeSol, related_name='cultures_favorables', verbose_name='types de sols favorables', blank=True,
    )

    class Meta:
        verbose_name = 'culture'
        verbose_name_plural = 'referentiel des cultures'
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def calculer_score(self, type_sol, parametres):
        """Barème de compatibilite (Tableau 16) : type de sol 40, pH 30, MO 15, N/P/K 5 chacun."""
        score = 0
        if type_sol and self.sols_favorables.filter(pk=type_sol.pk).exists():
            score += 40
        if self.ph_min <= parametres.get('ph', 0) <= self.ph_max:
            score += 30
        if parametres.get('matiere_organique', 0) >= 2:
            score += 15
        if parametres.get('azote', 0) >= self.besoin_azote:
            score += 5
        if parametres.get('phosphore', 0) >= self.besoin_phosphore:
            score += 5
        if parametres.get('potassium', 0) >= self.besoin_potassium:
            score += 5
        return min(100, score)
