from django.urls import path

from . import views

app_name = 'analyses'

urlpatterns = [
    path('nouvelle/', views.LancerAnalyseView.as_view(), name='nouvelle'),
    path('<int:pk>/resultat/', views.ResultatAnalyseView.as_view(), name='resultat'),
    path('a-valider/', views.AnalysesAValiderView.as_view(), name='a_valider'),
    path('<int:pk>/valider/', views.ValiderAnalyseView.as_view(), name='valider'),
    path('<int:pk>/ecart/', views.EcartCultureView.as_view(), name='ecart'),
    path('historique/', views.HistoriqueAnalysesView.as_view(), name='historique'),
    path('historique/export/<str:format_export>/', views.exporter_historique_view, name='exporter'),
]
