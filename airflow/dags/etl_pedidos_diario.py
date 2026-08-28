"""
DAG Principal: EcoDelivery Medallion Pipeline (ETL Diario)
Orquesta las capas:
  1. Bronze (Extracción cruda de OLTP y RandomUser API)
  2. Silver (Limpieza, Validación, Conciliación y Enriquecimiento)
  3. Gold (Modelo Estrella Dimensional, KPIs de Negocio y Exportación CSV)
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

# 1. Tareas de Extracción (Bronze)
from tasks.extract import (
    extract_oltp_pedidos,
    extract_oltp_users,
    extract_randomuser,
)

# 2. Tareas de Transformación (Silver)
from tasks.transform_silver import (
    transform_users,
    transform_pedidos,
)

# 3. Tareas de Modelado Estrella y Reportes (Gold)
from tasks.load_gold import (
    load_gold_star_schema,
    export_kpi_reports,
)

default_args = {
    "owner": "ecodelivery_data_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="etl_pedidos_diario",
    default_args=default_args,
    description="Pipeline ETL Diario EcoDelivery: OLTP + RandomUser -> Bronze -> Silver -> Gold (Star Schema)",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ecodelivery", "medallion", "star_schema", "powerbi", "fastapi"],
) as dag:

    # --------------------------------------------------------------------------
    # FASE 1: BRONZE (Extracción Cruda)
    # --------------------------------------------------------------------------
    with TaskGroup("bronze_ingestion_group", tooltip="Ingesta cruda desde OLTP y API RandomUser") as bronze_group:
        task_extract_pedidos = PythonOperator(
            task_id="extract_oltp_pedidos",
            python_callable=extract_oltp_pedidos,
        )
        task_extract_users = PythonOperator(
            task_id="extract_oltp_users",
            python_callable=extract_oltp_users,
        )
        task_extract_randomuser = PythonOperator(
            task_id="extract_randomuser",
            python_callable=extract_randomuser,
        )

    # --------------------------------------------------------------------------
    # FASE 2: SILVER (Limpieza, Enriquecimiento y Conciliación)
    # --------------------------------------------------------------------------
    with TaskGroup("silver_transformation_group", tooltip="Transformación y enriquecimiento controlado") as silver_group:
        task_transform_users = PythonOperator(
            task_id="transform_users",
            python_callable=transform_users,
        )
        task_transform_pedidos = PythonOperator(
            task_id="transform_pedidos",
            python_callable=transform_pedidos,
        )

        # Orden secuencial: Usuarios enriquecidos primero, luego pedidos
        task_transform_users >> task_transform_pedidos

    # --------------------------------------------------------------------------
    # FASE 3: GOLD (Star Schema Dimensional & Reportes de Rúbrica)
    # --------------------------------------------------------------------------
    with TaskGroup("gold_star_schema_group", tooltip="Carga de dimensiones, hechos y exportación CSV") as gold_group:
        task_load_star = PythonOperator(
            task_id="load_gold_star_schema",
            python_callable=load_gold_star_schema,
        )
        task_export_kpi = PythonOperator(
            task_id="export_kpi_reports",
            python_callable=export_kpi_reports,
        )

        # Carga del modelo estrella seguida de la generación del reporte
        task_load_star >> task_export_kpi

    # --------------------------------------------------------------------------
    # FLUJO END-TO-END MEDALLÓN
    # --------------------------------------------------------------------------
    bronze_group >> silver_group >> gold_group
