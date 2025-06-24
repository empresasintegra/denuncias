# Dockerfile para producción
FROM python:3.11-slim

# Variables de entorno para producción
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

# Copiar y instalar dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copiar código de la aplicación
COPY . /app/
RUN chown -R appuser:appuser /app

# Cambiar al usuario no-root
USER appuser

# Recopilar archivos estáticos
RUN python manage.py collectstatic --noinput

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 --access-logfile - --error-logfile - leykarin.wsgi:application"]