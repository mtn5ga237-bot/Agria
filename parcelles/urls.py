from django.urls import path

from . import views

app_name = 'parcelles'

urlpatterns = [
    path('', views.MesParcellesView.as_view(), name='liste'),
    path('nouvelle/', views.CreerParcelleView.as_view(), name='creer'),
    path('<int:pk>/', views.ParcelleDetailView.as_view(), name='detail'),
    path('<int:pk>/supprimer/', views.SupprimerParcelleView.as_view(), name='supprimer'),
]
