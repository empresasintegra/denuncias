from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Hosts permitidos - incluye tu dominio de DigitalOcean
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'tu-dominio.com',  # Tu dominio personalizado
    'www.tu-dominio.com',
    'tu-app-12345.ondigitalocean.app',  # Si usas App Platform
    # Agrega la IP de tu droplet si es necesario
]

# Base de datos externa de DigitalOcean
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

# Configuración de seguridad
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

# Configuración para proxy SSL de DigitalOcean
# DigitalOcean maneja SSL, nosotros recibimos HTTP
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # DigitalOcean maneja la redirección
SESSION_COOKIE_SECURE = True  # Las cookies deben ser seguras
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Configuración para Load Balancer de DigitalOcean
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Archivos estáticos para producción
STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# Configuración de WhiteNoise para archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración de logging para producción
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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email para producción
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@tu-dominio.com')

# Configuraciones adicionales para DigitalOcean
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://tu-dominio.com",
    "https://www.tu-dominio.com",
]

# Configuración de cache (opcional)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}