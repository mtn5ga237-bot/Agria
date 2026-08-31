"""
Configuration Django du projet AgriA.

Plateforme d'analyse et de classification des sols assistee par IA,
developpee dans le cadre du stage IAI-Cameroun, centre de Garoua (2025-2026).
"""

import os
from pathlib import Path

import dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

dotenv.load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


# ---------------------------------------------------------------------------
# Securite generale
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-cle-de-developpement-a-remplacer')

DEBUG = env_bool('DEBUG', True)

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',

    # Authentification sociale (connexion via Google)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Applications du projet AgriA
    'comptes',
    'referentiel',
    'parcelles',
    'analyses',
    'intelligence',
    'cartographie',
    'tableaux_de_bord',
    'assistant',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'comptes.middleware.JournalActiviteMiddleware',
    'comptes.securite_middleware.EnTetesSecuriteMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tableaux_de_bord.context_processors.indicateurs_navigation',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ---------------------------------------------------------------------------
# Base de donnees : SQLite en developpement, PostgreSQL en production
# ---------------------------------------------------------------------------

if os.environ.get('DATABASE_URL', '').startswith('postgres'):
    import urllib.parse as _urlparse

    _url = _urlparse.urlparse(os.environ['DATABASE_URL'])
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _url.path.lstrip('/'),
            'USER': _url.username,
            'PASSWORD': _url.password,
            'HOST': _url.hostname,
            'PORT': _url.port or 5432,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = 'comptes.Utilisateur'

AUTHENTICATION_BACKENDS = [
    'comptes.backends.AuthentificationParEmail',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# --- django-allauth : connexion via Google (Dossier VII, securite des comptes) ---
ACCOUNT_ADAPTER = 'comptes.adapters.AdaptateurCompte'
SOCIALACCOUNT_ADAPTER = 'comptes.adapters.AdaptateurSocial'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'  # l'activation manuelle par un administrateur fait deja office de controle
ACCOUNT_RATE_LIMITS = {'login_failed': '5/5m/ip,key'}
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_OAUTH_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}

LOGIN_URL = 'comptes:connexion'
LOGIN_REDIRECT_URL = 'tableaux_de_bord:accueil'
LOGOUT_REDIRECT_URL = 'comptes:connexion'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# PBKDF2-SHA256 natif de Django, 600 000 iterations (Tableau 17 du rapport)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
from django.contrib.auth.hashers import PBKDF2PasswordHasher as _PBKDF2  # noqa: E402
_PBKDF2.iterations = 600_000


# ---------------------------------------------------------------------------
# Securite des sessions et des cookies (Tableau 17)
# ---------------------------------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 30 * 60  # 30 minutes d'inactivite
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_HTTPONLY = False  # doit rester lisible par le JS pour l'en-tete X-CSRFToken

SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', not DEBUG)
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', False)
SECURE_HSTS_SECONDS = 0 if DEBUG else 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Protection contre la force brute (Tableau 17 : 5 tentatives puis verrouillage)
AXES_ENABLED = True
TENTATIVES_MAX_CONNEXION = 5
DUREE_VERROUILLAGE_MINUTES = 15


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Douala'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Fichiers statiques et medias
# ---------------------------------------------------------------------------

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Parametres propres a AgriA
# ---------------------------------------------------------------------------

# Repertoire de stockage des modeles entraines (Annexe 6 : intelligence/modeles/)
REPERTOIRE_MODELES = BASE_DIR / 'intelligence' / 'modeles'
SEUIL_CONFIANCE_VALIDATION_EXPERT = 70.0  # en pourcentage (Dossier V, 6.3)
COORDONNEES_GAROUA = {'lat': 9.3017, 'lng': 13.3921}  # centre par defaut de la carte

# Journalisation (JournalActivite)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{asctime} {levelname} {name} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
        'fichier': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'agria.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 7,
            'formatter': 'verbose',
        },
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'agria.securite': {'handlers': ['console', 'fichier'], 'level': 'INFO', 'propagate': False},
    },
}
(BASE_DIR / 'logs').mkdir(exist_ok=True)

if not DEBUG:
    ADMINS = [('Administrateur AgriA', os.environ.get('ADMIN_EMAIL', 'admin@agria.local'))]


# ---------------------------------------------------------------------------
# Assistant IA (Claude) - cle lue uniquement cote serveur, jamais transmise
# au navigateur. Le widget de discussion n'appelle que notre propre endpoint.
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-opus-5')
ASSISTANT_MAX_MESSAGES_PAR_HEURE = int(os.environ.get('ASSISTANT_MAX_MESSAGES_PAR_HEURE', 30))


# ---------------------------------------------------------------------------
# Envoi d'emails (reinitialisation de mot de passe, Dossier VII)
# ---------------------------------------------------------------------------

EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
else:
    # Aucun serveur SMTP configure : les emails sont ecrits dans logs/emails.log
    # (mode developpement), ce qui permet de tester le flux de bout en bout
    # sans dependre d'un fournisseur externe.
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = BASE_DIR / 'logs' / 'emails'
    EMAIL_FILE_PATH.mkdir(parents=True, exist_ok=True)

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'AgriA <noreply@agria.local>')
PASSWORD_RESET_TIMEOUT = 60 * 60 * 2  # 2 heures de validite du lien (Tableau 17 : conditions de reinitialisation)
