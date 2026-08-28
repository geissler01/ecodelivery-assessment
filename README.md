# Sistema Integral de Logistica y Plataforma Analitica - EcoDelivery S.A.S.

Solucion tecnologica empresarial de extremo a extremo (End-to-End) para la gestion de pedidos de ultima milla con vehiculos cero emisiones (bicicletas y motos electricas) en el Valle de Aburra (Medellin, Colombia). El sistema integra una aplicacion movil en **Flutter**, un backend RESTful en **FastAPI**, persistencia transaccional y analitica en **PostgreSQL**, un pipeline de datos ETL con arquitectura Medallon en **Apache Airflow 3.0** y un modelo dimensional en **Power BI**.

---

## Indice de Contenidos

1. [Arquitectura General del Sistema](#1-arquitectura-general-del-sistema)
2. [Estructura del Repositorio](#2-estructura-del-repositorio)
3. [Requisitos Previos](#3-requisitos-previos)
4. [Guia de Variables de Entorno (.env)](#4-guia-de-variables-de-entorno-env)
5. [Guia de Despliegue y Ejecucion](#5-guia-de-despliegue-y-ejecucion)
   - [Paso 1: Infraestructura y Backend en VPS / Servidor](#paso-1-infraestructura-y-backend-en-vps--servidor)
   - [Paso 2: Pipeline de Datos en Apache Airflow (Local / Orquestador)](#paso-2-pipeline-de-datos-en-apache-airflow-local--orquestador)
   - [Paso 3: Aplicacion Movil (Flutter)](#paso-3-aplicacion-movil-flutter)
   - [Paso 4: Tableros Analiticos en Power BI](#paso-4-tableros-analiticos-en-power-bi)
6. [Modelo de Seguridad, Roles (RBAC) y Credenciales](#6-modelo-de-seguridad-roles-rbac-y-credenciales)
7. [Reglas de Negocio y Modelo Financiero](#7-reglas-de-negocio-y-modelo-financiero)
8. [Pipeline Medallon y Modelo Estrella (DWH)](#8-pipeline-medallon-y-modelo-estrella-dwh)
9. [Suite de Pruebas y Verificacion](#9-suite-de-pruebas-y-verificacion)
10. [Como Replicar este Proyecto en Otro Entorno](#10-como-replicar-este-proyecto-en-otro-entorno)

---

## 1. Arquitectura General del Sistema

El ecosistema esta disenado bajo principios de alta cohesion y bajo acoplamiento:

```text
[ Cliente / Repartidor / Admin ]
               |
               v
      [ Flutter Mobile App ] (Clean Architecture / DDD Vertical Slices)
               |
               v (HTTP REST / JSON Web Tokens)
      [ Nginx Reverse Proxy ] (Puerto 80 / 443)
               |
               v
      [ FastAPI Backend ] (OAuth2 Argon2id + RBAC + Motor Geoespacial + State Machine)
               |
               +----------------------------+
               | (Transaccional OLTP)       | (Lectura de Eventos)
               v                            v
    [ PostgreSQL ecodelivery_db ]    [ Apache Airflow 3.0 DAGs ]
                                            |
                                            | (Bronze -> Silver -> Gold + RandomUser API)
                                            v
                                     [ PostgreSQL ecodelivery_dwh ]
                                     (Star Schema: fact_pedidos + dims)
                                            |
                                            v
                                     [ Power BI Desktop ]
```

---

## 2. Estructura del Repositorio

```text
assessment/
├── .env.example                     # Plantilla de configuracion de variables de entorno
├── .gitignore                       # Proteccion estricta de secretos y temporales
├── docker-compose.yml               # Orquestador del servidor (PostgreSQL, Backend, Nginx)
├── docker-compose.local.yml         # Orquestador de Airflow 3.0 (Scheduler, API Server, DAG Processor)
├── README.md                        # Documentacion principal en Espanol
├── README.en.md                     # Documentacion principal en Ingles
├── airflow/                         # Modulo 3: Pipeline de Ingenieria de Datos
│   ├── dags/
│   │   └── etl_pedidos_diario.py    # Definicion del DAG con TaskGroups Medallon
│   ├── tasks/
│   │   ├── extract/                 # Tareas Bronze (OLTP y API RandomUser)
│   │   ├── transform_silver/        # Tareas Silver (Limpieza, SLA, Enriquecimiento)
│   │   └── load_gold/               # Tareas Gold (Star Schema Kimball y CSV)
│   ├── scripts/
│   │   └── reset_airflow_db.py      # Utilidad de inicializacion de base de metadatos
│   ├── Dockerfile                   # Imagen personalizada de Airflow 3.0
│   └── requirements.txt             # Dependencias de Python para el pipeline
├── app_flutter/                     # Modulo 1: Aplicacion Movil Multiplataforma
│   ├── lib/
│   │   ├── core/                    # Red, temas Material 3, constantes y utilidades
│   │   └── features/
│   │       ├── auth/                # Autenticacion JWT y Social OAuth (Google/GitHub)
│   │       ├── users/               # Perfiles, resumen de usuario y metricas
│   │       └── pedidos/             # Gestion de pedidos por rol, filtros y detalle
│   └── pubspec.yaml
├── backend/                         # Modulo 2: API RESTful de Alto Rendimiento
│   ├── app/
│   │   ├── api/v1/                  # Controladores REST, deps de auth y RBAC
│   │   ├── core/                    # Configuracion Pydantic Settings, hash Argon2id, JWT
│   │   ├── db/                      # Sesion SQLAlchemy 2.0 y conexion a PostgreSQL
│   │   ├── models/                  # Modelos ORM (User, Pedido)
│   │   ├── schemas/                 # Esquemas de validacion Pydantic v2
│   │   ├── services/                # Logica de dominio modularizada (Geo, Costos, TTL)
│   │   ├── main.py                  # Punto de entrada FastAPI y middleware CORS
│   │   └── seed.py                  # Script de migracion inicial y seed de 150 users y 1000 pedidos
│   ├── tests/
│   │   └── test_live_api.py         # Suite de pruebas E2E automatizadas (10/10)
│   ├── Dockerfile                   # Imagen liviana de produccion
│   └── requirements.txt
├── data/                            # Datasets semilla del assessment
│   ├── pedidos_db_ready.csv         # 1.000 pedidos historicos
│   └── users_db_ready.csv           # 150 usuarios clasificados
├── docs/                            # Documentacion tecnica detallada
│   ├── CONTEXTO_PROYECTO.md         # Guia de arquitectura y estado del proyecto
│   ├── DOCUMENTACION_FEATURES.md    # Especificacion funcional de cada feature
│   └── LOGICA_NEGOCIO_Y_DECISIONES.md# Modelos matematicos, SLA, TTL y geoespacial
├── dwh/                             # Scripts DDL y reportes generados
│   ├── reports/                     # Salida de reportes analiticos (reporte_pedidos.csv)
│   └── sql/                         # DDLs de esquemas Bronze, Silver y Gold
└── powerbi/                         # Modulo 4: Modelo Analitico y Tableros
    ├── dashboard_assessment.pbip    # Proyecto nativo de Power BI (Fabric PBIR)
    ├── dashboard_assessment.Report/ # Definicion JSON de vistas y visualizaciones
    └── dashboard_assessment.SemanticModel/ # Definicion TMDL del modelo estrella
```

---

## 3. Requisitos Previos

* **Docker Engine** (v24.0 o superior) y **Docker Compose** (v2.20 o superior).
* **Python** (v3.11 o v3.12) para ejecucion de scripts locales o pruebas.
* **Flutter SDK** (v3.19 o superior) para compilar y ejecutar la app movil.
* **Power BI Desktop** (Version 2024 o superior con soporte de proyectos `.pbip`).
* Acceso de red a los puertos `80`, `443`, `8000`, `8080` y `5432`.

---

## 4. Guia de Variables de Entorno (.env)

Copia el archivo de plantilla a la raiz del proyecto antes de iniciar:

```bash
cp .env.example .env
```

A continuacion se detallan todas las variables agrupadas por servicio y su funcion:

### 4.1. Base de Datos PostgreSQL y Data Warehouse
| Variable | Descripcion | Valor Ejemplo / Produccion | Que cambiar si replicas |
| :--- | :--- | :--- | :--- |
| `POSTGRES_HOST` | Host o IP del servidor PostgreSQL | `100.60.229.203` (o `localhost`) | Cambiar a la IP de tu VPS o `localhost` si es local. |
| `POSTGRES_PORT` | Puerto de escucha de PostgreSQL | `5432` | Mantener `5432` salvo puerto personalizado. |
| `POSTGRES_USER` | Usuario maestro de PostgreSQL | `ecodelivery_user` | Tu usuario de base de datos. |
| `POSTGRES_PASSWORD` | Contrasena del usuario maestro | `tu_password_segura` | Asigna una contrasena fuerte. |
| `POSTGRES_DB` | Base de datos operativa (OLTP) | `ecodelivery_db` | Nombre de base de datos transaccional. |
| `AIRFLOW_DB_NAME` | Base de datos de metadatos de Airflow | `airflow_db` | Base de datos dedicada para Airflow. |
| `DWH_DB_NAME` | Base de datos del Data Warehouse | `ecodelivery_dwh` | Base de datos para capas Bronze, Silver, Gold. |
| `AIRFLOW_OLTP_URI` | Cadena SQLAlchemy hacia la base OLTP | `postgresql+psycopg2://user:pass@host:5432/ecodelivery_db` | Ajustar usuario, clave y host. |
| `AIRFLOW_DWH_URI` | Cadena SQLAlchemy hacia el DWH | `postgresql+psycopg2://user:pass@host:5432/ecodelivery_dwh` | Ajustar usuario, clave y host. |

### 4.2. Apache Airflow 3.0
| Variable | Descripcion | Valor Ejemplo / Produccion | Que cambiar si replicas |
| :--- | :--- | :--- | :--- |
| `AIRFLOW_UID` | UID de Linux del usuario airflow | `50000` | Mantener `50000` (estandar de Airflow). |
| `AIRFLOW__CORE__FERNET_KEY` | Llave Fernet para encriptar conexiones | `generar_con_fernet_key` | Generar con `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. |
| `AIRFLOW__WEBSERVER__SECRET_KEY` | Clave de sesion de Flask/FastAPI | `generar_cadena_aleatoria` | Generar con `openssl rand -hex 32`. |
| `AIRFLOW__API_AUTH__JWT_SECRET` | Secreto para tokens de la API interna | `generar_cadena_aleatoria` | Generar con `openssl rand -hex 32`. |
| `AIRFLOW_ADMIN_USERNAME` | Usuario administrador del panel web | `admin` | Usuario de login para `localhost:8080`. |
| `AIRFLOW_ADMIN_PASSWORD` | Contrasena del administrador | `admin` | Contrasena de acceso a la UI. |

### 4.3. Backend FastAPI y Autenticacion
| Variable | Descripcion | Valor Ejemplo / Produccion | Que cambiar si replicas |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | Clave secreta para firmar tokens JWT | `generar_clave_jwt` | Generar con `openssl rand -hex 32`. |
| `ALGORITHM` | Algoritmo criptografico de firma | `HS256` | Mantener `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| Duracion de validez del JWT | `1440` (24 horas) | Ajustar segun politica de sesion. |
| `GOOGLE_CLIENT_ID` | Client ID de Google OAuth 2.0 | `id.apps.googleusercontent.com` | Tu ID de Google Cloud Console. |
| `GOOGLE_CLIENT_SECRET` | Secret de Google OAuth 2.0 | `GOCSPX-secret` | Tu secreto de Google Cloud Console. |
| `GITHUB_CLIENT_ID` | Client ID de GitHub OAuth App | `github_client_id` | Tu ID de GitHub Developer Settings. |
| `GITHUB_CLIENT_SECRET` | Secret de GitHub OAuth App | `github_client_secret` | Tu secreto de GitHub. |

---

## 5. Guia de Despliegue y Ejecucion

### Paso 1: Infraestructura y Backend en VPS / Servidor

En el servidor o VPS principal (ej. AWS Lightsail), ejecuta:

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd assessment

# 2. Configurar el archivo .env con las credenciales correspondientes
cp .env.example .env
nano .env

# 3. Construir y levantar los servicios centrales (PostgreSQL, Backend FastAPI, Nginx)
docker compose up -d --build

# 4. Ejecutar el script de poblado inicial de datos (Seed de 150 usuarios y 1.000 pedidos)
docker compose exec backend python -m app.seed
```

Verificacion:
* Swagger UI disponible en: `http://ecodelivery.geisler.coderhivex.com/docs` (o `http://localhost:8000/docs`).
* Endpoint de salud: `curl http://localhost:8000/api/v1/health`

---

### Paso 2: Pipeline de Datos en Apache Airflow (Local / Orquestador)

Para procesar y transformar los datos hacia el Data Warehouse:

```bash
# 1. Levantar el stack local de Airflow 3.0
docker compose -f docker-compose.local.yml up -d --build

# 2. Verificar estado de los contenedores
docker compose -f docker-compose.local.yml ps
```

* Interfaz Web de Airflow: **`http://localhost:8080`**
* **Usuario:** `admin` | **Contrasena:** `admin`
* Enciende el DAG **`etl_pedidos_diario`** y presiona **Trigger DAG**.
* El pipeline ejecutara automaticamente:
  1. `bronze_ingestion_group`: Extraccion cruda desde PostgreSQL y API RandomUser.
  2. `silver_transformation_group`: Limpieza, calculo de SLA de entrega y enriquecimiento demografico.
  3. `gold_star_schema_group`: Carga de dimensiones, tabla de hechos y exportacion del reporte `dwh/reports/reporte_pedidos.csv`.

---

### Paso 3: Aplicacion Movil (Flutter)

La aplicacion movil consume directamente la API REST:

```bash
cd app_flutter

# 1. Instalar dependencias de Flutter
flutter pub get

# 2. Verificar integridad del codigo
dart analyze

# 3. Ejecutar en Navegador Web
flutter run -d chrome

# 4. Ejecutar en Dispositivo Fisico o Emulador Android
flutter run
```

> **Configuracion de Red en Flutter:** Si pruebas en un dispositivo fisico o emulador, la URL base esta configurada en `app_flutter/lib/core/constants/api_constants.dart` apuntando a `http://ecodelivery.geisler.coderhivex.com/api/v1`.

---

### Paso 4: Tableros Analiticos en Power BI

El proyecto analitico esta estructurado en formato nativo **PBIP** (Fabric Git Integration) en la carpeta `powerbi/`:

1. Abre el archivo **`powerbi/dashboard_assessment.pbip`** en Power BI Desktop.
2. Haz clic en **Actualizar (Refresh)** en la cinta superior.
3. Las 5 tablas del modelo estrella (`fact_pedidos`, `dim_cliente`, `dim_repartidor`, `dim_zona`, `dim_date`) se cargaran directamente desde el esquema `gold` de PostgreSQL o desde `dwh/reports/reporte_pedidos.csv`.
4. El reporte contiene dos tableros ejecutivos interactivos:
   - **Resumen Ejecutivo:** Total de pedidos, facturacion global, margen operativo, ticket promedio y distribucion temporal por zona.
   - **Operaciones y Repartidores:** Tiempos promedio de entrega en minutos (SLA), rendimiento por tipo de vehiculo y volumen por estado.

---

## 6. Modelo de Seguridad, Roles (RBAC) y Credenciales

### Control de Acceso Basado en Roles (RBAC)
* **`admin`:** Control total de la plataforma, buscador reactivo global de pedidos, visualizacion y creacion de usuarios.
* **`repartidor`:** Vista especializada de entregas asignadas, aceptacion y despacho de ordenes en su zona, y confirmacion de entrega.
* **`cliente`:** Vista exclusiva de sus propios pedidos, creacion de nuevas solicitudes y cancelacion de ordenes pendientes.

### Credenciales de Prueba Precargadas

| Rol | Correo Electronico | Contrasena | Identificador / Nombre |
| :--- | :--- | :--- | :--- |
| **Super Administrador** | `admin@ecodelivery.com` | `Admin1234!` | Administrador General |
| **Repartidor Semilla** | `andres.gomez91@ecodelivery.com` | `EcoDelivery2026!` | Andres Gomez (Zona: Norte, Vehiculo: Bicicleta) |
| **Cliente Semilla** | `diego.gonzalez7@ecodelivery.com` | `EcoDelivery2026!` | Diego Gonzalez (Zona: Chapinero / Nororiente) |

> **Nota de Seguridad:** Las contrasenas se encuentran hasheadas en base de datos mediante **Argon2id** (`pwdlib[argon2]`), cumpliendo con los estandares de seguridad OWASP.

---

## 7. Reglas de Negocio y Modelo Financiero

### 7.1. Modelo Financiero de Costos
$$\text{Costo Operacion} = \begin{cases} \text{monto} \times 0.10 & \text{si el transporte es Bicicleta} \\ \text{monto} \times 0.15 & \text{si el transporte es Moto Electrica} \end{cases}$$

$$\text{Margen Bruto} = \text{monto} - \text{Costo Operacion}$$

### 7.2. Delimitacion Geoespacial (Valle de Aburra)
Todas las ordenes se ubican en el area metropolitana de Medellin:
* **Sur:** Envigado, Itagui, Sabaneta (Lat: `6.1649`, Lon: `-75.5953`)
* **Occidente:** Laureles, San Javier, Belen (Lat: `6.2566`, Lon: `-75.6045`)
* **Centro:** La Candelaria, Prado (Lat: `6.2502`, Lon: `-75.5594`)
* **Chapinero / Nororiente:** Manrique, Aranjuez (Lat: `6.2649`, Lon: `-75.5497`)
* **Norte:** Castilla, Bello (Lat: `6.2839`, Lon: `-75.5654`)

### 7.3. Maquina de Estados y Conciliacion Temporal (TTL)
* **Regla de 30 Minutos:** Si un pedido pendiente asignado no se acepta en 30 minutos, se libera (`repartidor_id = NULL`) quedando disponible para cualquier conductor disponible.
* **Regla de 2 Horas:** Si una orden permanece 120 minutos sin ser despachada, el backend la cancela automaticamente (`CANCELADO`).
* **Auto-Asignacion:** Al despachar (`en_camino`), el backend sella el ID del conductor y la fecha de asignacion de forma atomica.

---

## 8. Pipeline Medallon y Modelo Estrella (DWH)

```text
Capas del Pipeline:
1. BRONZE:
   - raw_pedidos (OLTP) + Metadatos (_extracted_at, _source)
   - raw_users (OLTP) + Metadatos
   - raw_randomuser_profiles (API Externa)

2. SILVER:
   - users_enriched: Cruce con RandomUser (edad, genero, grupo etario: 18-25, 26-35, 36-50, 50+, telefono, avatar).
   - pedidos_cleaned: Tipado estricto UTC, validacion de estados y calculo de tiempo de entrega en minutos.

3. GOLD (Star Schema Kimball):
   - dim_cliente (cliente_sk, nombre, email, edad, genero, grupo_etario, zona)
   - dim_repartidor (repartidor_sk, nombre, tipo_vehiculo, zona)
   - dim_zona (zona_sk, nombre_zona, latitud_centro, longitud_centro, region)
   - dim_date (date_sk, full_date, year, quarter, month, day, day_of_week, is_weekend)
   - fact_pedidos (pedido_sk, cliente_sk, repartidor_sk, zona_sk, date_sk, monto, costo_operacion, margen_bruto, tiempo_entrega_minutos)
   - Salida exportada: dwh/reports/reporte_pedidos.csv
```

---

## 9. Suite de Pruebas y Verificacion

Para validar el funcionamiento del sistema:

```bash
# Pruebas E2E del Backend (10/10 pruebas de ciclo completo)
python backend/tests/test_live_api.py

# Analisis estatico del codigo Flutter
cd app_flutter && dart analyze
```

---

## 10. Como Replicar este Proyecto en Otro Entorno

Si deseas desplegar esta solucion en un nuevo servidor o maquina local desde cero:

1. **Clona el repositorio** en la maquina destino.
2. **Crea el archivo `.env`** a partir de `.env.example` y ajusta `POSTGRES_PASSWORD`, `SECRET_KEY` y `POSTGRES_HOST`.
3. **Inicia los servicios del servidor:** `docker compose up -d --build`.
4. **Puebla los datos iniciales:** `docker compose exec backend python -m app.seed`.
5. **Ejecuta Airflow:** `docker compose -f docker-compose.local.yml up -d --build` y corre el DAG `etl_pedidos_diario`.
6. **Abre Power BI:** Abre `powerbi/dashboard_assessment.pbip` y presiona Actualizar para sincronizar con la nueva base de datos.
