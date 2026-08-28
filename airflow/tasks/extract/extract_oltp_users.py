"""
Tarea de Extracción: Usuarios OLTP -> Bronze.raw_users
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

def extract_oltp_users():
    logger.info(">>> [BRONZE] Iniciando extracción de usuarios desde OLTP...")
    
    # 1. Intentar extracción desde la base de datos PostgreSQL transaccional
    df_users = None
    try:
        engine_oltp = create_engine(OLTP_URI)
        with engine_oltp.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    id::text, email, full_name, role::text,
                    COALESCE(telefono, '') as telefono,
                    COALESCE(zona_principal, '') as zona_principal,
                    COALESCE(tipo_vehiculo_predilecto, '') as tipo_vehiculo_predilecto,
                    is_active::text, is_verified::text,
                    created_at::text, updated_at::text
                FROM users
            """))
            df_users = pd.DataFrame(result.fetchall(), columns=result.keys())
            logger.info(f">>> [BRONZE] {len(df_users)} usuarios extraídos directamente de ecodelivery_db.users.")
    except Exception as e:
        logger.warning(f">>> [BRONZE] No se pudo extraer de la BD OLTP ({e}). Usando dataset semilla como respaldo...")
        csv_path = os.path.join(os.getcwd(), "data", "users_db_ready.csv")
        if not os.path.exists(csv_path):
            csv_path = "/opt/airflow/dwh/../data/users_db_ready.csv"
        if os.path.exists(csv_path):
            df_users = pd.read_csv(csv_path, dtype=str)
            for col in ["telefono", "zona_principal", "tipo_vehiculo_predilecto"]:
                if col not in df_users.columns:
                    df_users[col] = ""
            logger.info(f">>> [BRONZE] {len(df_users)} usuarios cargados desde archivo CSV semilla.")
        else:
            raise FileNotFoundError(f"No se encontró dataset semilla en {csv_path}")

    # 2. Asegurar esquema y tabla en DWH
    engine_dwh = create_engine(DWH_URI)
    with engine_dwh.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bronze.raw_users (
                id VARCHAR(100),
                email VARCHAR(255),
                full_name VARCHAR(100),
                role VARCHAR(50),
                telefono VARCHAR(50),
                zona_principal VARCHAR(50),
                tipo_vehiculo_predilecto VARCHAR(50),
                is_active VARCHAR(10),
                is_verified VARCHAR(10),
                created_at VARCHAR(50),
                updated_at VARCHAR(50),
                ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

    # 3. Limpieza de Bronze y Carga Masiva
    records = df_users.fillna("").to_dict(orient="records")
    with engine_dwh.begin() as conn:
        conn.execute(text("TRUNCATE TABLE bronze.raw_users;"))
        conn.execute(text("""
            INSERT INTO bronze.raw_users (
                id, email, full_name, role, telefono, zona_principal, tipo_vehiculo_predilecto,
                is_active, is_verified, created_at, updated_at, ingestion_timestamp
            ) VALUES (
                :id, :email, :full_name, :role, :telefono, :zona_principal, :tipo_vehiculo_predilecto,
                :is_active, :is_verified, :created_at, :updated_at, CURRENT_TIMESTAMP
            )
        """), records)

    logger.info(f">>> [BRONZE] Ingesta exitosa: {len(records)} usuarios almacenados en bronze.raw_users.")
    return len(records)
