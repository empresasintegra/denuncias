# leykarin/settings/__init__.py

import os
from django.core.exceptions import ImproperlyConfigured

# Determinar qué configuración usar basado en DJANGO_SETTINGS_MODULE
def get_settings_module():
    """
    Determina automáticamente qué configuración usar si no se especifica
    """
    # Si ya está definido, usar ese
    settings_module = os.getenv('DJANGO_SETTINGS_MODULE')
    if settings_module:
        return settings_module
    
    # Si no está definido, usar desarrollo por defecto
    debug = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes', 'on')
    
    if debug:
        return 'leykarin.settings.development'
    else:
        return 'leykarin.settings.production'

# Configurar el módulo de settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', get_settings_module())