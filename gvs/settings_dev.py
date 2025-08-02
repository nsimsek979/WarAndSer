"""
Development settings for Windows environment
"""

from .settings_base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-qvf(e!=kb_cn&uu0q33c*&unq!4#zjt5p8_v(or9y9$9bkzim-"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Database for development (SQLite)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Additional development settings
INTERNAL_IPS = [
    '127.0.0.1',
]
