from django.urls import path

from . import views

app_name = 'tableaux_de_bord'

urlpatterns = [
    path('', views.accueil_view, name='accueil'),
]
