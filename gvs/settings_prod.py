"""
Production settings for Ubuntu server
"""

import os
from .settings_base import *

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-production-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Change back after fixing
ALLOWED_HOSTS = ['*']  # Temporarily allow all hosts
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Third party apps
    "import_export",

    # Local apps
    "core",
    "dashboard",
    "item_master",
    "customer",
    "custom_user",
    "warranty_and_services",
    "rest_framework",
    "rest_framework_simplejwt",
    "api",
]

# Database for production (PostgreSQL or MySQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_ENGINE = "django.contrib.sessions.backends.db"  # Explicitly set
SESSION_COOKIE_NAME = "warandser_session"  # Unique name
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds

# Session and CSRF cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

# Static files for production
STATIC_ROOT = '/var/www/warandser/static/'
MEDIA_ROOT = '/var/www/warandser/media/'

# Email settings for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@your-domain.com')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/warandser/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # ... diger processor'lar
            ],
            'libraries': {
                # ... özel template tag'ler
            },
            'builtins': ['django.templatetags.i18n'],  # Bu satiri ekleyin
            'debug': True,  # DEBUG=False olsa bile template hatalarini göster
            'string_if_invalid': 'INVALID_EXPRESSION',  # Hatalari daha görünür yapar
            'autoescape': True,
            'file_charset': 'utf-8'  # Bu kritik öneme sahip
        },
    },
]