# Dockerfile (versión minimalista)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=leykarin.settings.production

# Instalar dependencias
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiar aplicación
COPY . .

# Script de inicio inline
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Iniciando aplicación Django..."\n\
while ! nc -z $DB_HOST $DB_PORT; do sleep 2; done\n\
echo "✅ Base de datos lista!"\n\
python manage.py migrate --noinput\n\
python manage.py collectstatic --noinput\n\
echo "🎉 ¡Aplicación lista!"\n\
exec gunicorn --bind 0.0.0.0:8000 --workers 3 leykarin.wsgi:application' > /app/start.sh

RUN chmod +x /app/start.sh

EXPOSE 8000
CMD ["/app/start.sh"]