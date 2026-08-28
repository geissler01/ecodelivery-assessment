"""
Script de Ejecución Directa del Pipeline Medallón (Local / Testing)
Permite correr todo el flujo ETL de Airflow directamente desde la consola
sin necesidad de levantar la UI, facilitando pruebas rápidas y verificación.
"""
import os
import sys
import logging

# Configurar PYTHONPATH para incluir el directorio actual
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("LocalPipelineRunner")

def run_local_pipeline():
    logger.info("=================================================================")
    logger.info("  INICIANDO EJECUCIÓN LOCAL DEL PIPELINE MEDALLÓN ECODELIVERY    ")
    logger.info("=================================================================")

    # Importar tareas
    from tasks.extract import (
        extract_oltp_pedidos,
        extract_oltp_users,
        extract_randomuser,
    )
    from tasks.transform_silver import (
        transform_users,
        transform_pedidos,
    )
    from tasks.load_gold import (
        load_gold_star_schema,
        export_kpi_reports,
    )

    try:
        # FASE 1: BRONZE
        logger.info("\n--- [FASE 1: BRONZE] Extracción Cruda ---")
        extract_oltp_pedidos()
        extract_oltp_users()
        extract_randomuser()
        logger.info(">>> Fase Bronze completada con éxito.")

        # FASE 2: SILVER
        logger.info("\n--- [FASE 2: SILVER] Transformación y Enriquecimiento ---")
        transform_users()
        transform_pedidos()
        logger.info(">>> Fase Silver completada con éxito.")

        # FASE 3: GOLD
        logger.info("\n--- [FASE 3: GOLD] Modelo Estrella y KPIs de Negocio ---")
        load_gold_star_schema()
        total_pedidos = export_kpi_reports()
        logger.info(f">>> Fase Gold completada con éxito. Total registros: {total_pedidos}")

        logger.info("\n=================================================================")
        logger.info("  ¡PIPELINE LOCAL COMPLETADO AL 100%! DATOS DISPONIBLES EN GOLD  ")
        logger.info("=================================================================")
    except Exception as e:
        logger.error(f"Error durante la ejecución del pipeline: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_local_pipeline()
