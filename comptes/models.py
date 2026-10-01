import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


def chemin_document_justificatif(instance, nom_fichier):
    """Regenere un nom de fichier aleatoire pour le document justificatif televerse par un
    agent vulgarisateur ou un expert pedologue a l'inscription, afin de ne jamais exposer ni
    reutiliser le nom fourni par l'utilisateur (meme principe que Analyse.chemin_photo_sol)."""
    extension = nom_fichier.rsplit('.', 1)[-1].lower() if '.' in nom_fichier else 'pdf'
    return f'documents_justificatifs/{uuid.uuid4().hex}.{extension}'


class GestionnaireUtilisateur(BaseUserManager):
    """Gestionnaire du modele Utilisateur, l'authentification se faisant par adresse email."""

    def create_user(self, email, nom_complet, password=None, role='agriculteur', **extra):
        if not email:
            raise ValueError("L'adresse electronique est obligatoire.")
        email = self.normalize_email(email)
        utilisateur = self.model(email=email, nom_complet=nom_complet, role=role, **extra)
        utilisateur.set_password(password)
        utilisateur.save(using=self._db)
        return utilisateur

    def create_superuser(self, email, nom_complet, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('is_active', True)
        extra.setdefault('role', Utilisateur.Role.ADMINISTRATEUR)
        if extra.get('is_staff') is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra.get('is_superuser') is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")
        return self.create_user(email, nom_complet, password, **extra)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    """Represente tout utilisateur de la plateforme, quel que soit son role (Tableau 14)."""

    class Role(models.TextChoices):
        AGRICULTEUR = 'agriculteur', 'Agriculteur'
        AGENT = 'agent', 'Agent Vulgarisateur'
        EXPERT = 'expert', 'Expert Pedologue'
        ADMINISTRATEUR = 'admin', 'Administrateur'

    email = models.EmailField('adresse electronique', unique=True)
    nom_complet = models.CharField('nom complet', max_length=150)
    telephone = models.CharField('telephone', max_length=20, blank=True)
    role = models.CharField('role', max_length=20, choices=Role.choices, default=Role.AGRICULTEUR)

    # Localite declaree par l'utilisateur : zone d'intervention pour un agent vulgarisateur,
    # lieu de residence pour un agriculteur (permet de lui proposer les agents les plus proches
    # avant meme qu'il n'ait enregistre une parcelle). Texte libre, a l'image de Parcelle.localite.
    localite = models.CharField('localite / zone d\'intervention', max_length=100, blank=True)

    # Document officiel (carte professionnelle, attestation...) justifiant le role declare par
    # un agent vulgarisateur ou un expert pedologue a l'inscription : n'importe qui peut cocher
    # « agent » ou « expert » dans le formulaire, ce document permet a l'administrateur de le
    # verifier avant d'activer le compte (Dossier VII, 2.1). Seul l'administrateur peut le
    # consulter (voir comptes.views.DocumentJustificatifView) ; non requis pour un agriculteur.
    document_justificatif = models.FileField(
        'document justificatif', upload_to=chemin_document_justificatif, null=True, blank=True,
    )

    # Le champ agent_vulgarisateur permet a un agent de suivre les producteurs de son secteur.
    agent_vulgarisateur = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='producteurs_suivis', limit_choices_to={'role': Role.AGENT},
        verbose_name="agent vulgarisateur rattache",
    )

    is_active = models.BooleanField('actif', default=False)
    est_banni = models.BooleanField('banni', default=False)
    is_staff = models.BooleanField('acces admin Django', default=False)
    date_inscription = models.DateTimeField('date d\'inscription', default=timezone.now)

    tentatives_echouees = models.PositiveSmallIntegerField(default=0)
    verrouille_jusqu_a = models.DateTimeField(null=True, blank=True)

    objects = GestionnaireUtilisateur()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom_complet']

    class Meta:
        verbose_name = 'utilisateur'
        verbose_name_plural = 'utilisateurs'
        ordering = ['nom_complet']

    def __str__(self):
        return f'{self.nom_complet} ({self.get_role_display()})'

    @property
    def statut(self):
        """Traduit les booleens is_active/est_banni dans les trois etats du diagramme d'etat-transition."""
        if self.est_banni:
            return 'banni'
        if self.is_active:
            return 'actif'
        return 'inactif'

    def a_le_role(self, *roles):
        return self.role in roles

    def localite_effective(self):
        """Localite a utiliser pour la mise en relation avec un agent vulgarisateur : le champ
        declare par l'utilisateur en priorite, sinon la localite de sa parcelle la plus recente."""
        if self.localite:
            return self.localite
        parcelle = self.parcelles.exclude(localite='').order_by('-date_creation').first()
        return parcelle.localite if parcelle else ''

    def activer(self):
        self.is_active = True
        self.est_banni = False
        self.save(update_fields=['is_active', 'est_banni'])

    def desactiver(self):
        self.is_active = False
        self.est_banni = False
        self.save(update_fields=['is_active', 'est_banni'])

    def bannir(self):
        self.is_active = False
        self.est_banni = True
        self.save(update_fields=['is_active', 'est_banni'])


class JournalActivite(models.Model):
    """Journal d'audit des operations sensibles (Tableau 17, Annexe 9)."""

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='journaux',
    )
    action = models.CharField(max_length=255)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    horodatage = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    class Meta:
        verbose_name = "entree du journal d'activite"
        verbose_name_plural = "journal d'activite"
        ordering = ['-horodatage']

    def __str__(self):
        return f'[{self.horodatage:%Y-%m-%d %H:%M}] {self.utilisateur} - {self.action}'
