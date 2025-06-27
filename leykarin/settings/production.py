# leykarin/settings/production.py
from .base import *
import os

# SECURITY
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

# HOSTS
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# DATABASE EXTERNA DE DIGITALOCEAN
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '25060'),
        'OPTIONS': {
            'sslmode': 'require',  # DigitalOcean requiere SSL
        },
    }
}

# STATIC FILES con WhiteNoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# SECURITY HEADERS (opcionales)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# CSRF Configuration para tus dominios
CSRF_TRUSTED_ORIGINS = [
    'https://denunciasenlinea.cl',
    'https://www.denunciasenlinea.cl',
    'http://134.209.46.183',
    'http://138.197.63.32',
    'cloud.digitalocean.com',
]

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}