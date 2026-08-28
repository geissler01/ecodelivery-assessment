-- ==============================================================================
-- DDL CAPA GOLD (STAR SCHEMA DIMENSIONAL PARA POWER BI Y ANALÍTICA)
-- Base de datos: ecodelivery_dwh | Esquema: gold
-- ==============================================================================

\connect ecodelivery_dwh;
CREATE SCHEMA IF NOT EXISTS gold;

-- 1. Dimensión Cliente
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

-- 2. Dimensión Repartidor
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

-- 3. Dimensión Zona (Medellín y Valle de Aburrá)
CREATE TABLE IF NOT EXISTS gold.dim_zona (
    zona_sk BIGSERIAL PRIMARY KEY,
    nombre_zona VARCHAR(50) UNIQUE NOT NULL,
    latitud_centro NUMERIC(10,6),
    longitud_centro NUMERIC(10,6),
    region VARCHAR(50) DEFAULT 'Valle de Aburrá'
);

-- 4. Dimensión Fecha (Calendario Completo)
CREATE TABLE IF NOT EXISTS gold.dim_date (
    date_sk INT PRIMARY KEY,                  -- Formato YYYYMMDD (ej. 20260729)
    full_date DATE UNIQUE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month_number INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- 5. Tabla de Hechos: Pedidos y Operaciones
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

-- Índices de alto rendimiento para Power BI
CREATE INDEX IF NOT EXISTS idx_fact_pedidos_cliente ON gold.fact_pedidos(cliente_sk);
CREATE INDEX IF NOT EXISTS idx_fact_pedidos_repartidor ON gold.fact_pedidos(repartidor_sk);
CREATE INDEX IF NOT EXISTS idx_fact_pedidos_zona ON gold.fact_pedidos(zona_sk);
CREATE INDEX IF NOT EXISTS idx_fact_pedidos_date ON gold.fact_pedidos(date_sk);
CREATE INDEX IF NOT EXISTS idx_fact_pedidos_estado ON gold.fact_pedidos(estado);
