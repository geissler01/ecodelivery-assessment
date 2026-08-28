#!/usr/bin/env bash
set -e

echo "=== Ejecutando migración de DB de Airflow 3.0 ==="
airflow db migrate

echo "=== Creando usuario administrador ==="
airflow users create \
  --username "${AIRFLOW_ADMIN_USERNAME:-admin}" \
  --firstname "${AIRFLOW_ADMIN_FIRSTNAME:-Admin}" \
  --lastname "${AIRFLOW_ADMIN_LASTNAME:-User}" \
  --role Admin \
  --email "${AIRFLOW_ADMIN_EMAIL:-admin@ecodelivery.com}" \
  --password "${AIRFLOW_ADMIN_PASSWORD:-admin}" || true

echo "=== Inicialización de Airflow 3.0 completada ==="
