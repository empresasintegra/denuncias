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

# URL de admin
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')

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
            'sslmode': 'require',
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

# ✅ CONFIGURACIÓN PARA SSL MANEJADO POR DIGITALOCEAN
# Django confía en el proxy de DigitalOcean para HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# CSRF Configuration
CSRF_TRUSTED_ORIGINS = [
    'https://denunciasenlinea.cl',
    'https://www.denunciasenlinea.cl',
    'http://denunciasenlinea.cl',        # Fallback HTTP
    'http://www.denunciasenlinea.cl',    # Fallback HTTP
    'http://134.209.46.183',
    'http://138.197.63.32',
    'https://cloud.digitalocean.com',
    'http://cloud.digitalocean.com',
]

# ✅ SSL SETTINGS PARA PROXY
CSRF_COOKIE_SECURE = True      # DigitalOcean maneja SSL
SESSION_COOKIE_SECURE = True   # DigitalOcean maneja SSL
SECURE_SSL_REDIRECT = False    # DigitalOcean maneja la redirección

# SECURITY HEADERS
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

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