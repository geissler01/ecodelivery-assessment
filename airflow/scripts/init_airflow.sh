#!/usr/bin/env bash
set -e

echo "=== Preparando directorios con permisos correctos ==="
mkdir -p /opt/airflow/logs/dag_processor \
         /opt/airflow/logs/scheduler \
         /opt/airflow/plugins
chown -R "${AIRFLOW_UID:-50000}:0" /opt/airflow/logs /opt/airflow/plugins
chmod -R 775 /opt/airflow/logs /opt/airflow/plugins

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
