-- ==============================================================================
-- SCRIPT DE INICIALIZACIÓN DE BASES DE DATOS Y ESQUEMAS MEDALLÓN
-- Proyecto: EcoDelivery Assessment (Data Warehouse)
-- ==============================================================================

-- 1. Crear base de datos para los metadatos de Airflow si no existe
SELECT 'CREATE DATABASE airflow_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_db')\gexec

-- 2. Crear base de datos para el Data Warehouse de EcoDelivery si no existe
SELECT 'CREATE DATABASE ecodelivery_dwh'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ecodelivery_dwh')\gexec

-- 3. Conectarse a ecodelivery_dwh y crear los esquemas Medallón
\connect ecodelivery_dwh;

-- Esquema Bronze: Ingesta cruda con metadatos de auditoría
CREATE SCHEMA IF NOT EXISTS bronze;

-- Esquema Silver: Datos limpios, normalizados, tipados y enriquecidos
CREATE SCHEMA IF NOT EXISTS silver;

-- Esquema Gold: Modelado dimensional en esquema estrella (Facts y Dims)
CREATE SCHEMA IF NOT EXISTS gold;

-- Conceder permisos al usuario del proyecto en los esquemas
GRANT ALL ON SCHEMA bronze TO ecodelivery_user;
GRANT ALL ON SCHEMA silver TO ecodelivery_user;
GRANT ALL ON SCHEMA gold TO ecodelivery_user;
