# Dockerfile
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=leykarin.settings.production

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        git \
        curl \
        libreoffice \
        gettext \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN adduser --disabled-password --gecos '' appuser

# Crear directorios de trabajo
WORKDIR /app
RUN mkdir -p /app/staticfiles /app/media
RUN chown -R appuser:appuser /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copiar código de la aplicación
COPY . /app/
RUN chown -R appuser:appuser /app

# Cambiar al usuario no-root
USER appuser

# Script de entrada
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Exponer puerto
EXPOSE 8000

# Comando por defecto
ENTRYPOINT ["/app/docker-entrypoint.sh"]