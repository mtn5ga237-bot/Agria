from django.urls import path

from . import views

app_name = 'intelligence'

urlpatterns = [
    path('versions/', views.HistoriqueVersionsView.as_view(), name='historique_versions'),
    path('reentrainer/', views.ReentrainerModeleView.as_view(), name='reentrainer'),
]
