"""
Tarea de Extracción: Pedidos OLTP -> Bronze.raw_pedidos
"""
import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

OLTP_URI = os.getenv(
    "AIRFLOW_OLTP_URI",
    "postgresql+psycopg2://ecodelivery_user:ecodelivery_user_01**@postgres:5432/ecodelivery_db"
)
DWH_URI = os.getenv(
    "AIRFLOW_DWH_URI",
    "postgresql+psycopg2://ecodelivery_user:ecodelivery_user_01**@postgres:5432/ecodelivery_dwh"
)

def extract_oltp_pedidos():
    logger.info(">>> [BRONZE] Iniciando extracción de pedidos desde OLTP...")
    
    # 1. Intentar extracción desde la base de datos PostgreSQL transaccional
    df_pedidos = None
    try:
        engine_oltp = create_engine(OLTP_URI)
        with engine_oltp.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    id_pedido::text, cliente_id::text, zona, 
                    fecha_creacion::text, fecha_asignacion::text, fecha_entrega::text,
                    estado::text, repartidor_id::text, metodo_pago, monto::text,
                    tipo_vehiculo, costo_operacion::text, latitud::text, longitud::text
                FROM pedidos
            """))
            df_pedidos = pd.DataFrame(result.fetchall(), columns=result.keys())
            logger.info(f">>> [BRONZE] {len(df_pedidos)} pedidos extraídos directamente de ecodelivery_db.pedidos.")
    except Exception as e:
        logger.warning(f">>> [BRONZE] No se pudo extraer de la BD OLTP ({e}). Usando dataset semilla como respaldo...")
        csv_path = os.path.join(os.getcwd(), "data", "pedidos_db_ready.csv")
        if not os.path.exists(csv_path):
            csv_path = "/opt/airflow/dwh/../data/pedidos_db_ready.csv"
        if os.path.exists(csv_path):
            df_pedidos = pd.read_csv(csv_path, dtype=str)
            logger.info(f">>> [BRONZE] {len(df_pedidos)} pedidos cargados desde archivo CSV semilla.")
        else:
            raise FileNotFoundError(f"No se encontró dataset semilla en {csv_path}")

    # 2. Asegurar esquema y tabla en DWH
    engine_dwh = create_engine(DWH_URI)
    with engine_dwh.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bronze.raw_pedidos (
                id_pedido VARCHAR(100),
                cliente_id VARCHAR(100),
                zona VARCHAR(50),
                fecha_creacion VARCHAR(50),
                fecha_asignacion VARCHAR(50),
                fecha_entrega VARCHAR(50),
                estado VARCHAR(50),
                repartidor_id VARCHAR(100),
                metodo_pago VARCHAR(50),
                monto VARCHAR(50),
                tipo_vehiculo VARCHAR(50),
                costo_operacion VARCHAR(50),
                latitud VARCHAR(50),
                longitud VARCHAR(50),
                ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

    # 3. Limpieza de Bronze y Carga Masiva
    records = df_pedidos.fillna("").to_dict(orient="records")
    with engine_dwh.begin() as conn:
        conn.execute(text("TRUNCATE TABLE bronze.raw_pedidos;"))
        conn.execute(text("""
            INSERT INTO bronze.raw_pedidos (
                id_pedido, cliente_id, zona, fecha_creacion, fecha_asignacion, fecha_entrega,
                estado, repartidor_id, metodo_pago, monto, tipo_vehiculo, costo_operacion,
                latitud, longitud, ingestion_timestamp
            ) VALUES (
                :id_pedido, :cliente_id, :zona, :fecha_creacion, :fecha_asignacion, :fecha_entrega,
                :estado, :repartidor_id, :metodo_pago, :monto, :tipo_vehiculo, :costo_operacion,
                :latitud, :longitud, CURRENT_TIMESTAMP
            )
        """), records)

    logger.info(f">>> [BRONZE] Ingesta exitosa: {len(records)} pedidos almacenados en bronze.raw_pedidos.")
    return len(records)
