"""
Production settings for IIS (Windows Server) with PostgreSQL
"""

import os
from pathlib import Path
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
DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# PostgreSQL Database Configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get('DB_NAME', 'warandser_db'),
        "USER": os.environ.get('DB_USER', 'postgres'),
        "PASSWORD": os.environ.get('DB_PASSWORD', ''),
        "HOST": os.environ.get('DB_HOST', 'localhost'),
        "PORT": os.environ.get('DB_PORT', '5432'),
        "OPTIONS": {
            'client_encoding': 'UTF8',
        },
    }
}

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Session and CSRF cookies
# Note: Set these to True only if using HTTPS
SESSION_COOKIE_SECURE = os.environ.get('USE_HTTPS', 'False') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('USE_HTTPS', 'False') == 'True'
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "warandser_session"
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds

# Static files for IIS production
# These paths should be absolute Windows paths
STATIC_ROOT = os.environ.get('STATIC_ROOT', r'C:\inetpub\wwwroot\warandser\static')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', r'C:\inetpub\wwwroot\warandser\media')

# Static and media URLs
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Email settings for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'shipstore.app@gmail.com'  # Your Gmail address
EMAIL_HOST_PASSWORD = 'jstz iios mkao qxes'  # Use App Password if 2FA is enabled
DEFAULT_FROM_EMAIL = 'shipstore.app@gmail.com'  # Your Gmail address

# Logging for Windows
LOG_DIR = os.environ.get('LOG_DIR', r'C:\inetpub\wwwroot\warandser\logs')
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except:
        pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Cache configuration (optional - for better performance)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),
    }
}

# CORS settings if API is being used
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if os.environ.get('CORS_ALLOWED_ORIGINS') else []

# Celery Configuration (Windows-compatible)
# Note: For Windows, you might want to use APScheduler instead of Celery
# Or run Celery with gevent/solo pool
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Template settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'builtins': ['django.templatetags.i18n'],
            'autoescape': True,
            'file_charset': 'utf-8'
        },
    },
]
