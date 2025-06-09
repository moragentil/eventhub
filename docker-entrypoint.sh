#!/bin/bash

# Salimos del script si algún comando falla
set -e

# Cargar variables del .env si existe
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi


# Aplicamos las migraciones (por si hay modelos nuevos o modificados)
echo "Aplicando migraciones"
python manage.py migrate --noinput


echo "Creando directorios de archivos estaticos y media si no existen"
mkdir -p staticfiles media


echo "Recolectando archivos estáticos"
python manage.py collectstatic --noinput --clear

# Finalmente, ejecutamos el comando que viene después en el Dockerfile
echo "Iniciando servidor de desarrollo"
exec "$@"
