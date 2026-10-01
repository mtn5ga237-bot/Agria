from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = 'comptes'

urlpatterns = [
    path('inscription/', views.InscriptionView.as_view(), name='inscription'),
    path('connexion/', views.ConnexionView.as_view(), name='connexion'),
    path('deconnexion/', views.deconnexion_view, name='deconnexion'),
    path('profil/', views.ProfilView.as_view(), name='profil'),
    path('profil/mot-de-passe/', views.changer_mot_de_passe_view, name='changer_mot_de_passe'),
    path('utilisateurs/', views.GestionUtilisateursView.as_view(), name='gestion_utilisateurs'),
    path('utilisateurs/<int:pk>/statut/', views.changer_statut_utilisateur_view, name='changer_statut'),
    path('utilisateurs/<int:pk>/document/', views.document_justificatif_view, name='document_justificatif'),
    path('journal/', views.JournalActiviteView.as_view(), name='journal_activite'),

    # Portefeuille de producteurs de l'agent vulgarisateur
    path('producteurs/', views.MesProducteursView.as_view(), name='mes_producteurs'),
    path('producteurs/nouveau/', views.CreerProducteurView.as_view(), name='creer_producteur'),
    path('producteurs/rattacher/', views.RattacherProducteurView.as_view(), name='rattacher_producteur'),
    path('producteurs/<int:pk>/', views.DetailProducteurView.as_view(), name='detail_producteur'),
    path('producteurs/export/', views.exporter_producteurs_view, name='exporter_producteurs'),

    # Mise en relation agriculteur <-> agent vulgarisateur de sa region
    path('trouver-un-agent/', views.TrouverAgentView.as_view(), name='trouver_agent'),
    path('trouver-un-agent/choisir/', views.ChoisirAgentView.as_view(), name='choisir_agent'),

    # Reinitialisation de mot de passe oublie (Dossier VII / securite des comptes).
    # Conditions requises : l'adresse doit correspondre a un compte actif disposant d'un mot de
    # passe utilisable (PasswordResetForm.get_users filtre is_active=True) ; le lien envoye par
    # email est a usage unique et expire au bout de 2 heures (PASSWORD_RESET_TIMEOUT).
    path(
        'mot-de-passe-oublie/',
        auth_views.PasswordResetView.as_view(
            template_name='comptes/reinitialisation_mdp.html',
            email_template_name='comptes/email_reinitialisation_mdp.txt',
            subject_template_name='comptes/email_reinitialisation_mdp_objet.txt',
            success_url=reverse_lazy('comptes:reinitialisation_mdp_envoyee'),
        ),
        name='reinitialisation_mdp',
    ),
    path(
        'mot-de-passe-oublie/envoye/',
        auth_views.PasswordResetDoneView.as_view(template_name='comptes/reinitialisation_mdp_envoyee.html'),
        name='reinitialisation_mdp_envoyee',
    ),
    path(
        'mot-de-passe-oublie/confirmer/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='comptes/reinitialisation_mdp_confirmer.html',
            success_url=reverse_lazy('comptes:reinitialisation_mdp_terminee'),
        ),
        name='reinitialisation_mdp_confirmer',
    ),
    path(
        'mot-de-passe-oublie/termine/',
        auth_views.PasswordResetCompleteView.as_view(template_name='comptes/reinitialisation_mdp_terminee.html'),
        name='reinitialisation_mdp_terminee',
    ),
]
