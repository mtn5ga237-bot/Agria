from django.urls import path

from . import views

app_name = 'cartographie'

urlpatterns = [
    path('', views.carte_view, name='carte'),
    path('marqueurs.json', views.marqueurs_json_view, name='marqueurs_json'),
]
