import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

if not os.environ.get('RENDER'):
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / '.env')
        load_dotenv(BASE_DIR.parent / '.env', override=False)
    except ImportError:
        pass


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return str(env(key, str(default))).strip().lower() in {'1', 'true', 'yes', 'on'}


def env_list(key: str, default: str = '') -> list[str]:
    value = env(key, default)
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


SECRET_KEY = env('SECRET_KEY', 'change-me-in-production')
DEBUG = env_bool('DEBUG', True)
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '127.0.0.1,localhost')

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'channels',
]

LOCAL_APPS = [
    'common',
    'apps.accounts',
    'apps.ingestion',
    'apps.dashboards',
    'apps.alerts',
    'apps.websockets',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.middleware.CorrelationIDMiddleware',
    'common.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'realtime_platform.urls'

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

WSGI_APPLICATION = 'realtime_platform.wsgi.application'
ASGI_APPLICATION = 'realtime_platform.asgi.application'

# ── Database ──────────────────────────────────────────────────────────────────
# Render provides DATABASE_URL; local dev uses DB_ENGINE / DB_* vars.
DATABASE_URL = env('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(env('DB_CONN_MAX_AGE', '60')),
            ssl_require=not DEBUG,
        )
    }
else:
    DB_ENGINE = env('DB_ENGINE', 'sqlite').lower()
    if DB_ENGINE == 'postgres':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('DB_NAME', 'realtime_platform'),
                'HOST': env('DB_HOST', 'localhost'),
                'PORT': int(env('DB_PORT', '5432')),
                'USER': env('DB_USER', 'postgres'),
                'PASSWORD': env('DB_PASSWORD', 'postgres'),
                'OPTIONS': {
                    'connect_timeout': int(env('DB_CONNECT_TIMEOUT', '10')),
                    'sslmode': env('DB_SSLMODE', 'prefer'),
                },
                'CONN_MAX_AGE': int(env('DB_CONN_MAX_AGE', '60')),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': env('SQLITE_PATH', str(BASE_DIR / 'db.sqlite3')),
            }
        }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

JWT_SECRET = env('JWT_SECRET', SECRET_KEY)
JWT_ALGORITHM = env('JWT_ALGORITHM', 'HS256')
JWT_ACCESS_EXP_MINUTES = int(env('JWT_ACCESS_EXP_MINUTES', '60'))
JWT_REFRESH_EXP_DAYS = int(env('JWT_REFRESH_EXP_DAYS', '30'))

REDIS_URL = env('REDIS_URL', 'redis://127.0.0.1:6379/0')

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = env('CELERY_TIMEZONE', 'UTC')
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = int(env('CELERY_TASK_TIME_LIMIT', '300'))
CELERY_TASK_SOFT_TIME_LIMIT = int(env('CELERY_TASK_SOFT_TIME_LIMIT', '240'))
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
            'capacity': int(env('CHANNEL_CAPACITY', '1500')),
            'expiry': int(env('CHANNEL_EXPIRY_SECONDS', '10')),
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'TIMEOUT': int(env('CACHE_TIMEOUT_SECONDS', '300')),
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
    'DEFAULT_PAGINATION_CLASS': 'common.boilerplate.custom_pagination.CustomPagination',
    'PAGE_SIZE': 20,
}

CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS', 'http://localhost:3000')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-api-key',
    'x-correlation-id',
    'x-org-slug',
    'x-webhook-secret',
]

EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(env('EMAIL_PORT', '587'))
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'noreply@realtimeplatform.com')

RATE_LIMIT_PER_ORG = int(env('RATE_LIMIT_PER_ORG', '1000'))
RATE_LIMIT_PER_API_KEY = int(env('RATE_LIMIT_PER_API_KEY', '500'))

FRONTEND_URL = env('FRONTEND_URL', 'http://localhost:3000')
GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', '')
PUBLIC_API_BASE_URL = env('PUBLIC_API_BASE_URL', 'http://localhost:8000')

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', not DEBUG)
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', False)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': env('LOG_LEVEL', 'INFO'),
    },
}
