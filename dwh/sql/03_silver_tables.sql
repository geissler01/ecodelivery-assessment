-- ==============================================================================
-- DDL CAPA SILVER (DATOS LIMPIOS, ENRIQUECIDOS Y NORMALIZADOS)
-- Base de datos: ecodelivery_dwh | Esquema: silver
-- ==============================================================================

\connect ecodelivery_dwh;
CREATE SCHEMA IF NOT EXISTS silver;

-- 1. Usuarios limpios y enriquecidos demográficamente
CREATE TABLE IF NOT EXISTS silver.users (
    user_id UUID PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    gender VARCHAR(20),
    age INT,
    age_group VARCHAR(50),
    dob_date DATE,
    phone VARCHAR(50),
    avatar_url VARCHAR(500),
    zona_principal VARCHAR(50),
    tipo_vehiculo_predilecto VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    silver_processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Pedidos limpios, validados y con métricas calculadas
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
