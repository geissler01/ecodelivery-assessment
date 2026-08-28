"""
Carga Gold: Construcción del Star Schema Dimensional (Gold.dim_* y Gold.fact_pedidos)
"""
import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DWH_URI = os.getenv(
    "AIRFLOW_DWH_URI",
    "postgresql+psycopg2://ecodelivery_user:ecodelivery_user_01**@postgres:5432/ecodelivery_dwh"
)

ZONES_DATA = [
    {"nombre_zona": "Sur", "lat": 6.1649, "lon": -75.5953, "region": "Valle de Aburrá - Sur"},
    {"nombre_zona": "Occidente", "lat": 6.2566, "lon": -75.6045, "region": "Valle de Aburrá - Occidente"},
    {"nombre_zona": "Centro", "lat": 6.2502, "lon": -75.5594, "region": "Valle de Aburrá - Centro"},
    {"nombre_zona": "Chapinero", "lat": 6.2649, "lon": -75.5497, "region": "Valle de Aburrá - Nororiente"},
    {"nombre_zona": "Norte", "lat": 6.2839, "lon": -75.5654, "region": "Valle de Aburrá - Norte"},
]

def load_gold_star_schema():
    logger.info(">>> [GOLD] Construyendo Modelo Estrella Dimensional...")
    engine_dwh = create_engine(DWH_URI)

    # 1. Asegurar DDL de la Capa Gold
    with engine_dwh.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold.dim_cliente (
                cliente_sk BIGSERIAL PRIMARY KEY,
                user_id UUID UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                gender VARCHAR(20),
                age INT,
                age_group VARCHAR(50),
                phone VARCHAR(50),
                zona_principal VARCHAR(50),
                avatar_url VARCHAR(500)
            );
            CREATE TABLE IF NOT EXISTS gold.dim_repartidor (
                repartidor_sk BIGSERIAL PRIMARY KEY,
                user_id UUID UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                gender VARCHAR(20),
                age INT,
                phone VARCHAR(50),
                tipo_vehiculo_predilecto VARCHAR(50),
                zona_principal VARCHAR(50),
                avatar_url VARCHAR(500)
            );
            CREATE TABLE IF NOT EXISTS gold.dim_zona (
                zona_sk BIGSERIAL PRIMARY KEY,
                nombre_zona VARCHAR(50) UNIQUE NOT NULL,
                latitud_centro NUMERIC(10,6),
                longitud_centro NUMERIC(10,6),
                region VARCHAR(50) DEFAULT 'Valle de Aburrá'
            );
            CREATE TABLE IF NOT EXISTS gold.dim_date (
                date_sk INT PRIMARY KEY,
                full_date DATE UNIQUE NOT NULL,
                year INT NOT NULL,
                quarter INT NOT NULL,
                month_number INT NOT NULL,
                month_name VARCHAR(20) NOT NULL,
                day_of_month INT NOT NULL,
                day_of_week VARCHAR(20) NOT NULL,
                is_weekend BOOLEAN NOT NULL
            );
            CREATE TABLE IF NOT EXISTS gold.fact_pedidos (
                pedido_sk BIGSERIAL PRIMARY KEY,
                id_pedido UUID UNIQUE NOT NULL,
                cliente_sk BIGINT NOT NULL REFERENCES gold.dim_cliente(cliente_sk),
                repartidor_sk BIGINT REFERENCES gold.dim_repartidor(repartidor_sk),
                zona_sk BIGINT NOT NULL REFERENCES gold.dim_zona(zona_sk),
                date_sk INT NOT NULL REFERENCES gold.dim_date(date_sk),
                estado VARCHAR(50) NOT NULL,
                metodo_pago VARCHAR(50) NOT NULL,
                tipo_vehiculo VARCHAR(50),
                monto NUMERIC(12,2) NOT NULL,
                costo_operacion NUMERIC(12,2) NOT NULL,
                margen_bruto NUMERIC(12,2) NOT NULL,
                tiempo_entrega_minutos INT,
                latitud NUMERIC(10,6),
                longitud NUMERIC(10,6),
                fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL,
                fecha_entrega TIMESTAMP WITH TIME ZONE
            );
            CREATE INDEX IF NOT EXISTS idx_fact_pedidos_cliente ON gold.fact_pedidos(cliente_sk);
            CREATE INDEX IF NOT EXISTS idx_fact_pedidos_repartidor ON gold.fact_pedidos(repartidor_sk);
            CREATE INDEX IF NOT EXISTS idx_fact_pedidos_zona ON gold.fact_pedidos(zona_sk);
            CREATE INDEX IF NOT EXISTS idx_fact_pedidos_date ON gold.fact_pedidos(date_sk);
            CREATE INDEX IF NOT EXISTS idx_fact_pedidos_estado ON gold.fact_pedidos(estado);
        """))

    # 2. Poblar Dimensiones
    with engine_dwh.begin() as conn:
        # A. Dimensión Zonas
        for z in ZONES_DATA:
            conn.execute(text("""
                INSERT INTO gold.dim_zona (nombre_zona, latitud_centro, longitud_centro, region)
                VALUES (:nombre_zona, :lat, :lon, :region)
                ON CONFLICT (nombre_zona) DO UPDATE SET
                    latitud_centro = EXCLUDED.latitud_centro,
                    longitud_centro = EXCLUDED.longitud_centro,
                    region = EXCLUDED.region;
            """), z)

        # B. Dimensión Clientes
        conn.execute(text("""
            INSERT INTO gold.dim_cliente (
                user_id, full_name, email, gender, age, age_group, phone, zona_principal, avatar_url
            )
            SELECT DISTINCT
                user_id, full_name, email, gender, age, age_group, phone, zona_principal, avatar_url
            FROM silver.users
            WHERE role = 'cliente' OR user_id IN (SELECT DISTINCT cliente_id FROM silver.pedidos)
            ON CONFLICT (user_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                email = EXCLUDED.email,
                gender = EXCLUDED.gender,
                age = EXCLUDED.age,
                age_group = EXCLUDED.age_group,
                phone = EXCLUDED.phone,
                zona_principal = EXCLUDED.zona_principal,
                avatar_url = EXCLUDED.avatar_url;
        """))

        # C. Dimensión Repartidores
        conn.execute(text("""
            INSERT INTO gold.dim_repartidor (
                user_id, full_name, email, gender, age, phone, tipo_vehiculo_predilecto, zona_principal, avatar_url
            )
            SELECT DISTINCT
                user_id, full_name, email, gender, age, phone, tipo_vehiculo_predilecto, zona_principal, avatar_url
            FROM silver.users
            WHERE role = 'repartidor' OR user_id IN (SELECT DISTINCT repartidor_id FROM silver.pedidos WHERE repartidor_id IS NOT NULL)
            ON CONFLICT (user_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                email = EXCLUDED.email,
                gender = EXCLUDED.gender,
                age = EXCLUDED.age,
                phone = EXCLUDED.phone,
                tipo_vehiculo_predilecto = EXCLUDED.tipo_vehiculo_predilecto,
                zona_principal = EXCLUDED.zona_principal,
                avatar_url = EXCLUDED.avatar_url;
        """))

    # 3. Generar y Poblar Dimensión Calendario (dim_date)
    with engine_dwh.connect() as conn:
        res = conn.execute(text("SELECT MIN(fecha_creacion) as min_dt, MAX(fecha_creacion) as max_dt FROM silver.pedidos"))
        row_dt = res.fetchone()
        
    start_date = pd.to_datetime(row_dt[0]).date() if row_dt and row_dt[0] else pd.to_datetime("2026-01-01").date()
    end_date = pd.to_datetime(row_dt[1]).date() if row_dt and row_dt[1] else pd.to_datetime("2026-12-31").date()
    
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    date_records = []
    month_names_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    day_names_es = {
        0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"
    }

    for dt in date_range:
        date_sk = int(dt.strftime("%Y%m%d"))
        date_records.append({
            "date_sk": date_sk,
            "full_date": dt.date(),
            "year": dt.year,
            "quarter": dt.quarter,
            "month_number": dt.month,
            "month_name": month_names_es[dt.month],
            "day_of_month": dt.day,
            "day_of_week": day_names_es[dt.weekday()],
            "is_weekend": dt.weekday() >= 5
        })

    with engine_dwh.begin() as conn:
        for d in date_records:
            conn.execute(text("""
                INSERT INTO gold.dim_date (
                    date_sk, full_date, year, quarter, month_number, month_name,
                    day_of_month, day_of_week, is_weekend
                ) VALUES (
                    :date_sk, :full_date, :year, :quarter, :month_number, :month_name,
                    :day_of_month, :day_of_week, :is_weekend
                ) ON CONFLICT (date_sk) DO NOTHING;
            """), d)

    logger.info(f">>> [GOLD] {len(date_records)} días sincronizados en gold.dim_date.")

    # 4. Poblar Tabla de Hechos (fact_pedidos)
    with engine_dwh.begin() as conn:
        conn.execute(text("""
            INSERT INTO gold.fact_pedidos (
                id_pedido, cliente_sk, repartidor_sk, zona_sk, date_sk,
                estado, metodo_pago, tipo_vehiculo, monto, costo_operacion,
                margen_bruto, tiempo_entrega_minutos, latitud, longitud,
                fecha_creacion, fecha_entrega
            )
            SELECT 
                p.id_pedido,
                dc.cliente_sk,
                dr.repartidor_sk,
                dz.zona_sk,
                CAST(TO_CHAR(p.fecha_creacion, 'YYYYMMDD') AS INT) as date_sk,
                p.estado,
                p.metodo_pago,
                p.tipo_vehiculo,
                p.monto,
                p.costo_operacion,
                p.margen_bruto,
                p.tiempo_entrega_minutos,
                p.latitud,
                p.longitud,
                p.fecha_creacion,
                p.fecha_entrega
            FROM silver.pedidos p
            JOIN gold.dim_cliente dc ON p.cliente_id = dc.user_id
            LEFT JOIN gold.dim_repartidor dr ON p.repartidor_id = dr.user_id
            JOIN gold.dim_zona dz ON p.zona = dz.nombre_zona
            JOIN gold.dim_date dd ON CAST(TO_CHAR(p.fecha_creacion, 'YYYYMMDD') AS INT) = dd.date_sk
            ON CONFLICT (id_pedido) DO UPDATE SET
                repartidor_sk = EXCLUDED.repartidor_sk,
                zona_sk = EXCLUDED.zona_sk,
                date_sk = EXCLUDED.date_sk,
                estado = EXCLUDED.estado,
                metodo_pago = EXCLUDED.metodo_pago,
                tipo_vehiculo = EXCLUDED.tipo_vehiculo,
                monto = EXCLUDED.monto,
                costo_operacion = EXCLUDED.costo_operacion,
                margen_bruto = EXCLUDED.margen_bruto,
                tiempo_entrega_minutos = EXCLUDED.tiempo_entrega_minutos,
                latitud = EXCLUDED.latitud,
                longitud = EXCLUDED.longitud,
                fecha_entrega = EXCLUDED.fecha_entrega;
        """))

    logger.info(">>> [GOLD] Modelo Estrella poblado exitosamente en gold.fact_pedidos.")
