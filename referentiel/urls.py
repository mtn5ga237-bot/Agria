from django.urls import path

from . import views

app_name = 'referentiel'

urlpatterns = [
    path('sols/', views.GestionTypesSolsView.as_view(), name='types_sols'),
    path('sols/nouveau/', views.CreerTypeSolView.as_view(), name='creer_type_sol'),
    path('sols/<int:pk>/modifier/', views.ModifierTypeSolView.as_view(), name='modifier_type_sol'),
    path('sols/<int:pk>/supprimer/', views.SupprimerTypeSolView.as_view(), name='supprimer_type_sol'),

    path('cultures/', views.GestionCulturesView.as_view(), name='cultures'),
    path('cultures/nouvelle/', views.CreerCultureView.as_view(), name='creer_culture'),
    path('cultures/<int:pk>/modifier/', views.ModifierCultureView.as_view(), name='modifier_culture'),
    path('cultures/<int:pk>/supprimer/', views.SupprimerCultureView.as_view(), name='supprimer_culture'),
]
