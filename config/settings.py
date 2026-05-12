from pathlib import Path
from datetime import timedelta
import sys
from decouple import config, Csv
# تقليل عدد العمال (workers) لخفض استهلاك الذاكرة
import os

# عدد العمال = 1 فقط للخطة المجانية
WEB_CONCURRENCY = os.environ.get('WEB_CONCURRENCY', 1)

# وقت المهلة (timeout)
GUNICORN_TIMEOUT = 60

# عدد الطلبات قبل إعادة تشغيل العامل
GUNICORN_MAX_REQUESTS = 200
GUNICORN_MAX_REQUESTS_JITTER = 50

# ─────────────────────────────────────────────────────
#  Paths + sys.path fix (Windows + Linux)
# ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


#  Security
# ─────────────────────────────────────────────────────
SECRET_KEY    = config('SECRET_KEY')
DEBUG         = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())


# ─────────────────────────────────────────────────────
#  Applications
# ─────────────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
] + (['django.contrib.admin'] if DEBUG else [])

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
] + (['django_extensions'] if DEBUG else [])

LOCAL_APPS = [
    'apps.users',
    'apps.wallets',
    'apps.transactions',
    'apps.comptes',
    'apps.abonnements',
    'apps.kyc',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ─────────────────────────────────────────────────────
#  Middleware
# ─────────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ─────────────────────────────────────────────────────
#  URLs & WSGI
# ─────────────────────────────────────────────────────
ROOT_URLCONF     = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'


# ─────────────────────────────────────────────────────
#  Templates
# ─────────────────────────────────────────────────────
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
            ],
        },
    },
]

# Email configuration
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL  = EMAIL_HOST_USER

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'trackpay-verif',
    }
}
# ─────────────────────────────────────────────────────
#  Database — PostgreSQL
# ─────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     config('DB_NAME'),
        'USER':     config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST':     config('DB_HOST', default='localhost'),
        'PORT':     config('DB_PORT', default='5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'sslmode': 'require' if not DEBUG else 'prefer',
            'connect_timeout': 10,
        },
    }
}


# ─────────────────────────────────────────────────────
#  Auth
# ─────────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─────────────────────────────────────────────────────
#  Internationalization
# ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Nouakchott'
USE_I18N      = True
USE_TZ        = True


# ─────────────────────────────────────────────────────
#  Static & Media
# ─────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─────────────────────────────────────────────────────
#  Django REST Framework
# ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}


# ─────────────────────────────────────────────────────
#  Simple JWT
# ─────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':    timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME':   timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':    True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN':        True,
    'AUTH_HEADER_TYPES':        ('Bearer',),
    'USER_ID_FIELD':            'id',
    'USER_ID_CLAIM':            'user_id',
    'TOKEN_OBTAIN_SERIALIZER':  'apps.users.serializers.CustomTokenObtainPairSerializer',
}


# ─────────────────────────────────────────────────────
#  CORS
# ─────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ORIGINS',
    default='http://localhost:3000',
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ── Windows Daesktop Flutter (pas de port fixe) ────────
CORS_ALLOW_ALL_ORIGINS = True   # ✅ en développement seulement


# ─────────────────────────────────────────────────────
#  KYC
# ─────────────────────────────────────────────────────
KYC_AI_URL = config('KYC_AI_URL', default='https://cheikhabdelkader.pythonanywhere.com/api/analyze')
