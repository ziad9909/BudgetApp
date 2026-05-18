from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

_env_path = BASE_DIR / '.env'
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        pass

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure--@1y&=f8!lwe6#^lm%rpcuiv2_%ufkx-%d-+-vl)byvzo#@4x$')

_ON_RAILWAY = bool(
    os.environ.get('RAILWAY_ENVIRONMENT')
    or os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    or os.environ.get('RAILWAY_PROJECT_ID')
)
_ON_PAAS = _ON_RAILWAY or bool(os.environ.get('PORT'))

# Default DEBUG off on Railway/PaaS unless explicitly enabled.
_debug_default = 'False' if _ON_PAAS else 'True'
DEBUG = os.environ.get('DEBUG', _debug_default) == 'True'

ALLOWED_HOSTS = ['*']


def _https_origin(value: str) -> str:
    value = (value or '').strip().rstrip('/')
    if not value:
        return ''
    if value.startswith('http://'):
        return 'https://' + value[7:]
    if value.startswith('https://'):
        return value
    return f'https://{value}'


def _build_csrf_trusted_origins() -> list[str]:
    origins: list[str] = []
    for part in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(','):
        origin = _https_origin(part)
        if origin and origin not in origins:
            origins.append(origin)
    for env_name in (
        'RAILWAY_PUBLIC_DOMAIN',
        'RAILWAY_STATIC_URL',
        'PUBLIC_URL',
        'WEB_URL',
        'APP_URL',
    ):
        origin = _https_origin(os.environ.get(env_name, ''))
        if origin and origin not in origins:
            origins.append(origin)
    return origins


CSRF_TRUSTED_ORIGINS = _build_csrf_trusted_origins()

if _ON_PAAS:
    # Railway terminates TLS at the edge; gunicorn sees HTTP without this header.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SAMESITE = 'Lax'
    if not DEBUG:
        CSRF_COOKIE_SECURE = True
        SESSION_COOKIE_SECURE = True


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'budget',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'budget.middleware.NoCacheAuthenticatedMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'budgeting_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'budget.context_processors.user_profile',
            ],
        },
    },
]

WSGI_APPLICATION = 'budgeting_project.wsgi.application'


          
                                                               

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


                     
                                                                              

AUTH_PASSWORD_VALIDATORS = []

                                                            
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'


                      
                                                    

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Cairo'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
