-- ==============================================================================
-- DDL CAPA BRONZE (RAW / INGESTA CRUDA)
-- Base de datos: ecodelivery_dwh | Esquema: bronze
-- ==============================================================================

\connect ecodelivery_dwh;
CREATE SCHEMA IF NOT EXISTS bronze;

-- 1. Ingesta cruda de Pedidos (Fuente: ecodelivery_db.pedidos)
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

-- 2. Ingesta cruda de Usuarios (Fuente: ecodelivery_db.users)
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

-- 3. Ingesta cruda de Perfiles Demográficos (Fuente: RandomUser API)
CREATE TABLE IF NOT EXISTS bronze.raw_randomuser_profiles (
    user_index INT,
    gender VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    age VARCHAR(10),
    dob_date VARCHAR(50),
    phone VARCHAR(50),
    picture_url VARCHAR(500),
    raw_json JSONB,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
