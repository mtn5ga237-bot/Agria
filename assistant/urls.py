from django.urls import path

from . import views

app_name = 'assistant'

urlpatterns = [
    path('discuter/', views.discuter_view, name='discuter'),
    path('reinitialiser/', views.reinitialiser_conversation_view, name='reinitialiser'),
]
