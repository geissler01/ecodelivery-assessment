"""
Carga Gold: Cálculo de KPIs del Assessment y Exportación de reporte_pedidos.csv
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

def export_kpi_reports():
    logger.info(">>> [GOLD] Calculando métricas de negocio y exportando reporte...")
    engine_dwh = create_engine(DWH_URI)

    # 1. Asegurar tabla de KPIs en Gold para Power BI
    with engine_dwh.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold.kpi_reporte_zona (
                zona VARCHAR(50) PRIMARY KEY,
                pedidos_totales INT NOT NULL,
                pedidos_entregados INT NOT NULL,
                tiempo_promedio_entrega_min NUMERIC(10,2),
                ingresos_totales NUMERIC(14,2) NOT NULL,
                costo_total NUMERIC(14,2) NOT NULL,
                margen_total NUMERIC(14,2) NOT NULL,
                ticket_promedio NUMERIC(12,2) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

    # 2. Consultar Métricas de Negocio requeridas por la Rúbrica
    # KPI 1: Tiempo promedio de entrega por zona (solo entregados)
    # KPI 2: Cantidad de pedidos por estado
    # KPI 3: Ingresos totales por zona
    with engine_dwh.connect() as conn:
        # A. Métricas por Zona
        query_zonas = text("""
            SELECT 
                dz.nombre_zona as zona,
                COUNT(fp.pedido_sk) as pedidos_totales,
                COUNT(CASE WHEN fp.estado = 'entregado' THEN 1 END) as pedidos_entregados,
                ROUND(AVG(CASE WHEN fp.estado = 'entregado' THEN fp.tiempo_entrega_minutos END)::numeric, 2) as tiempo_promedio_entrega_min,
                ROUND(SUM(fp.monto)::numeric, 2) as ingresos_totales,
                ROUND(SUM(fp.costo_operacion)::numeric, 2) as costo_total,
                ROUND(SUM(fp.margen_bruto)::numeric, 2) as margen_total,
                ROUND(AVG(fp.monto)::numeric, 2) as ticket_promedio
            FROM gold.fact_pedidos fp
            JOIN gold.dim_zona dz ON fp.zona_sk = dz.zona_sk
            GROUP BY dz.nombre_zona
            ORDER BY ingresos_totales DESC;
        """)
        res_zonas = conn.execute(query_zonas)
        df_kpi_zonas = pd.DataFrame(res_zonas.fetchall(), columns=res_zonas.keys())

        # B. Métricas por Estado
        query_estados = text("""
            SELECT 
                estado,
                COUNT(pedido_sk) as total_pedidos,
                ROUND(SUM(monto)::numeric, 2) as monto_total
            FROM gold.fact_pedidos
            GROUP BY estado
            ORDER BY total_pedidos DESC;
        """)
        res_estados = conn.execute(query_estados)
        df_kpi_estados = pd.DataFrame(res_estados.fetchall(), columns=res_estados.keys())

        # C. Dataset completo enriquecido para Power BI
        query_full_report = text("""
            SELECT 
                fp.id_pedido,
                dc.user_id as cliente_id,
                dc.full_name as cliente_nombre,
                dc.gender as cliente_genero,
                dc.age as cliente_edad,
                dc.age_group as cliente_grupo_etario,
                dz.nombre_zona as zona,
                dd.full_date as fecha,
                dd.month_name as mes,
                dd.day_of_week as dia_semana,
                dd.is_weekend as es_fin_de_semana,
                fp.estado,
                fp.metodo_pago,
                fp.tipo_vehiculo,
                fp.monto,
                fp.costo_operacion,
                fp.margen_bruto,
                fp.tiempo_entrega_minutos,
                fp.latitud,
                fp.longitud,
                fp.fecha_creacion,
                fp.fecha_entrega,
                dr.full_name as repartidor_nombre
            FROM gold.fact_pedidos fp
            JOIN gold.dim_cliente dc ON fp.cliente_sk = dc.cliente_sk
            LEFT JOIN gold.dim_repartidor dr ON fp.repartidor_sk = dr.repartidor_sk
            JOIN gold.dim_zona dz ON fp.zona_sk = dz.zona_sk
            JOIN gold.dim_date dd ON fp.date_sk = dd.date_sk
            ORDER BY fp.fecha_creacion ASC;
        """)
        res_full = conn.execute(query_full_report)
        df_full = pd.DataFrame(res_full.fetchall(), columns=res_full.keys())

    # 3. Guardar KPIs consolidados en gold.kpi_reporte_zona
    with engine_dwh.begin() as conn:
        conn.execute(text("TRUNCATE TABLE gold.kpi_reporte_zona;"))
        for _, row in df_kpi_zonas.iterrows():
            conn.execute(text("""
                INSERT INTO gold.kpi_reporte_zona (
                    zona, pedidos_totales, pedidos_entregados, tiempo_promedio_entrega_min,
                    ingresos_totales, costo_total, margen_total, ticket_promedio, updated_at
                ) VALUES (
                    :zona, :pedidos_totales, :pedidos_entregados, :tiempo_promedio_entrega_min,
                    :ingresos_totales, :costo_total, :margen_total, :ticket_promedio, CURRENT_TIMESTAMP
                )
            """), row.to_dict())

    # 4. Exportar reporte físico CSV en rutas estándar
    output_paths = [
        os.path.join(os.getcwd(), "dwh", "reports", "reporte_pedidos.csv"),
        os.path.join(os.getcwd(), "data", "reporte_pedidos.csv"),
        "/opt/airflow/dwh/reports/reporte_pedidos.csv",
    ]

    for p in output_paths:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            df_full.to_csv(p, index=False, encoding="utf-8")
            logger.info(f">>> [GOLD] Archivo reporte generado en: {p}")
        except Exception as e:
            logger.debug(f"No se pudo escribir en {p}: {e}")

    logger.info("=== RESUMEN DE KPIS GENERADOS (RÚBRICA ASSESSMENT) ===")
    logger.info(f"\n--- Métricas por Zona ---\n{df_kpi_zonas.to_string(index=False)}")
    logger.info(f"\n--- Pedidos por Estado ---\n{df_kpi_estados.to_string(index=False)}")
    logger.info(f">>> [GOLD] Pipeline finalizado con {len(df_full)} registros exportados.")
    return len(df_full)
