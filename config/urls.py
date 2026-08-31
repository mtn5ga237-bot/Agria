from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='accueil.html'), name='accueil_public'),
    path('comptes/', include('comptes.urls')),
    path('accounts/', include('allauth.urls')),
    path('tableau-de-bord/', include('tableaux_de_bord.urls')),
    path('parcelles/', include('parcelles.urls')),
    path('analyses/', include('analyses.urls')),
    path('intelligence/', include('intelligence.urls')),
    path('referentiel/', include('referentiel.urls')),
    path('carte/', include('cartographie.urls')),
    path('assistant/', include('assistant.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
