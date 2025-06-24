import os
from django.core.wsgi import get_wsgi_application

# Cambiar esta línea:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'leykarin.settings.production')

application = get_wsgi_application()