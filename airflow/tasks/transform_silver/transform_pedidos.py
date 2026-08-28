"""
Transformación Silver: Limpieza, Validación y Conciliación de Pedidos (Silver.pedidos)
"""
import os
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DWH_URI = os.getenv(
    "AIRFLOW_DWH_URI",
    "postgresql+psycopg2://ecodelivery_user:ecodelivery_user_01**@postgres:5432/ecodelivery_dwh"
)

ZONE_CENTROIDS = {
    "Sur": (6.1649, -75.5953),
    "Occidente": (6.2566, -75.6045),
    "Centro": (6.2502, -75.5594),
    "Chapinero": (6.2649, -75.5497),
    "Norte": (6.2839, -75.5654),
}

def parse_iso_datetime(dt_str):
    if not dt_str or str(dt_str).strip() in ["", "None", "nan", "NaT"]:
        return None
    try:
        # Reemplazar espacios y formato
        clean_str = str(dt_str).strip().replace(" ", "T")
        if not clean_str.endswith("Z") and "+" not in clean_str and "-" not in clean_str[10:]:
            clean_str += "+00:00"
        return pd.to_datetime(clean_str).to_pydatetime()
    except Exception:
        return None

def transform_pedidos():
    logger.info(">>> [SILVER] Procesando y conciliando pedidos...")
    engine_dwh = create_engine(DWH_URI)

    # 1. Asegurar esquema y tabla silver.pedidos
    with engine_dwh.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver.pedidos (
                id_pedido UUID PRIMARY KEY,
                cliente_id UUID NOT NULL,
                repartidor_id UUID,
                zona VARCHAR(50) NOT NULL,
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
                fecha_asignacion TIMESTAMP WITH TIME ZONE,
                fecha_entrega TIMESTAMP WITH TIME ZONE,
                silver_processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

    # 2. Leer Bronze raw_pedidos
    with engine_dwh.connect() as conn:
        res = conn.execute(text("""
            SELECT id_pedido, cliente_id, zona, fecha_creacion, fecha_asignacion, fecha_entrega,
                   estado, repartidor_id, metodo_pago, monto, tipo_vehiculo, costo_operacion,
                   latitud, longitud
            FROM bronze.raw_pedidos
        """))
        df_raw = pd.DataFrame(res.fetchall(), columns=res.keys())

    if df_raw.empty:
        logger.warning(">>> [SILVER] bronze.raw_pedidos está vacío.")
        return 0

    silver_pedidos = []
    for _, row in df_raw.iterrows():
        # Parsing de Fechas
        dt_creacion = parse_iso_datetime(row["fecha_creacion"])
        if not dt_creacion:
            dt_creacion = datetime.now()

        dt_asignacion = parse_iso_datetime(row["fecha_asignacion"])
        dt_entrega = parse_iso_datetime(row["fecha_entrega"])

        # Estado y Zona Normalizados
        estado = str(row["estado"]).strip().lower()
        if estado not in ["pendiente", "en_camino", "entregado", "cancelado"]:
            estado = "pendiente"

        zona = str(row["zona"]).strip().capitalize()
        if zona not in ZONE_CENTROIDS:
            zona = "Centro"

        metodo_pago = str(row["metodo_pago"]).strip().lower()
        if metodo_pago not in ["efectivo", "tarjeta", "app"]:
            metodo_pago = "app"

        # Monto y Costo Operativo
        try:
            monto = round(float(row["monto"]), 2)
        except (ValueError, TypeError):
            monto = 25000.00

        tipo_vehiculo = str(row["tipo_vehiculo"]).strip().lower() if row["tipo_vehiculo"] else "bicicleta"
        if tipo_vehiculo not in ["bicicleta", "moto_electrica"]:
            tipo_vehiculo = "bicicleta"

        try:
            costo_op = round(float(row["costo_operacion"]), 2)
            if costo_op <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            pct = 0.10 if tipo_vehiculo == "bicicleta" else 0.15
            costo_op = round(monto * pct, 2)

        margen_bruto = round(monto - costo_op, 2)

        # Cálculo de Tiempo de Entrega en Minutos (Solo para entregados)
        tiempo_entrega_min = None
        if estado == "entregado" and dt_entrega and dt_creacion:
            diff_secs = (dt_entrega - dt_creacion).total_seconds()
            if diff_secs > 0:
                tiempo_entrega_min = int(round(diff_secs / 60.0))

        # Coordenadas geográficas
        try:
            lat = round(float(row["latitud"]), 6)
            lon = round(float(row["longitud"]), 6)
        except (ValueError, TypeError):
            lat, lon = ZONE_CENTROIDS[zona]

        repartidor_id = str(row["repartidor_id"]).strip() if row["repartidor_id"] and str(row["repartidor_id"]).strip() not in ["", "None", "nan"] else None

        silver_pedidos.append({
            "id_pedido": row["id_pedido"],
            "cliente_id": row["cliente_id"],
            "repartidor_id": repartidor_id,
            "zona": zona,
            "estado": estado,
            "metodo_pago": metodo_pago,
            "tipo_vehiculo": tipo_vehiculo,
            "monto": monto,
            "costo_operacion": costo_op,
            "margen_bruto": margen_bruto,
            "tiempo_entrega_minutos": tiempo_entrega_min,
            "latitud": lat,
            "longitud": lon,
            "fecha_creacion": dt_creacion,
            "fecha_asignacion": dt_asignacion,
            "fecha_entrega": dt_entrega,
        })

    # 3. UPSERT Idempotente en silver.pedidos
    with engine_dwh.begin() as conn:
        for rec in silver_pedidos:
            conn.execute(text("""
                INSERT INTO silver.pedidos (
                    id_pedido, cliente_id, repartidor_id, zona, estado, metodo_pago,
                    tipo_vehiculo, monto, costo_operacion, margen_bruto, tiempo_entrega_minutos,
                    latitud, longitud, fecha_creacion, fecha_asignacion, fecha_entrega,
                    silver_processed_at
                ) VALUES (
                    :id_pedido, :cliente_id, :repartidor_id, :zona, :estado, :metodo_pago,
                    :tipo_vehiculo, :monto, :costo_operacion, :margen_bruto, :tiempo_entrega_minutos,
                    :latitud, :longitud, :fecha_creacion, :fecha_asignacion, :fecha_entrega,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT (id_pedido) DO UPDATE SET
                    repartidor_id = EXCLUDED.repartidor_id,
                    zona = EXCLUDED.zona,
                    estado = EXCLUDED.estado,
                    metodo_pago = EXCLUDED.metodo_pago,
                    tipo_vehiculo = EXCLUDED.tipo_vehiculo,
                    monto = EXCLUDED.monto,
                    costo_operacion = EXCLUDED.costo_operacion,
                    margen_bruto = EXCLUDED.margen_bruto,
                    tiempo_entrega_minutos = EXCLUDED.tiempo_entrega_minutos,
                    latitud = EXCLUDED.latitud,
                    longitud = EXCLUDED.longitud,
                    fecha_asignacion = EXCLUDED.fecha_asignacion,
                    fecha_entrega = EXCLUDED.fecha_entrega,
                    silver_processed_at = CURRENT_TIMESTAMP;
            """), rec)

    logger.info(f">>> [SILVER] {len(silver_pedidos)} pedidos transformados y conciliados en silver.pedidos.")
    return len(silver_pedidos)
