#!/bin/bash
# docker-entrypoint.sh

set -e

echo "🚀 Iniciando aplicación Django..."

# Esperar a la base de datos externa de DigitalOcean
echo "⏳ Esperando a la base de datos DigitalOcean..."
while ! nc -z $DB_HOST $DB_PORT; do
  echo "Intentando conectar a $DB_HOST:$DB_PORT..."
  sleep 2
done
echo "✅ Base de datos DigitalOcean lista!"

# Migraciones
echo "🗄️ Ejecutando migraciones..."
python manage.py migrate --noinput

# Archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Crear superuser automáticamente
echo "👤 Verificando superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
    print("✅ Superuser creado: admin/admin123")
else:
    print("✅ Superuser ya existe")
EOF

echo "🎉 ¡Aplicación lista!"

# Iniciar Gunicorn
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    leykarin.wsgi:application "$@"