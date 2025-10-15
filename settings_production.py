"""
Production settings for Ubuntu server
Bu dosyayı settings_production.py olarak kaydedin
"""

from .settings import *
import os

# Production settings
DEBUG = False

# Allowed hosts - Domain adresinizi buraya ekleyin
ALLOWED_HOSTS = [
    'your-domain.com',
    'www.your-domain.com',
    'your-server-ip',  # Server IP adresinizi buraya yazın
    'localhost',
    '127.0.0.1',
]

# Database - PostgreSQL production config
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'garantiveservis_db',
        'USER': 'garantiveservis_user',
        'PASSWORD': 'your-strong-password',  # Güçlü bir şifre kullanın
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files for production
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/garantiveservis/staticfiles/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files for production
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/garantiveservis/media/'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/garantiveservis/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Veya mail server adresiniz
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'

# Secret key - Production'da environment variable kullanın
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', SECRET_KEY)
