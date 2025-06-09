# Usamos como base una imagen oficial y liviana de Python 3.12
FROM python:3.12-slim

# Configuramos algunas variables de entorno para:
# - evitar que Python genere archivos .pyc innecesarios
# - hacer que los logs salgan directo a la consola (sin buffer)
# - que las instalaciones no pidan confirmación
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Este es el directorio donde va a vivir nuestra app dentro del contenedor
WORKDIR /app

# Instalamos herramientas básicas necesarias para compilar algunas dependencias (aunque para SQLite no siempre hace falta)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el archivo que lista nuestras dependencias de Python
COPY requirements.txt .

# Instalamos las dependencias listadas en requirements.txt sin guardar caché (así la imagen es más liviana)
RUN pip install --no-cache-dir -r requirements.txt

# Ahora copiamos todo el código fuente del proyecto a la carpeta de trabajo dentro del contenedor
COPY . .

# Copiamos un pequeño script que usaremos como entrada (entrypoint) para automatizar tareas como migraciones
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Le damos permisos de ejecución al script de entrypoint
RUN chmod +x /docker-entrypoint.sh

# Indicamos qué puerto expone la aplicación (el que usa Django por defecto)
EXPOSE 8000

# Este será el comando inicial que se ejecuta cuando arranca el contenedor.
# El script se encargará de correr migraciones y luego levantar el servidor.
ENTRYPOINT ["/docker-entrypoint.sh"]
