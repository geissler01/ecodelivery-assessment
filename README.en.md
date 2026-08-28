# Logistics Management and Analytics Platform - EcoDelivery S.A.S.

Enterprise-grade End-to-End technology solution for last-mile logistics management with zero-emission vehicles (bicycles and electric motorbikes) in the Aburra Valley (Medellin, Colombia). The system integrates a cross-platform mobile application in **Flutter**, a high-performance RESTful backend in **FastAPI**, transactional and analytical persistence in **PostgreSQL**, an ETL data pipeline following the Medallion architecture in **Apache Airflow 3.0**, and an executive dimensional model in **Power BI**.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Repository Structure](#2-repository-structure)
3. [Prerequisites](#3-prerequisites)
4. [Environment Variables Guide (.env)](#4-environment-variables-guide-env)
5. [Deployment and Execution Guide](#5-deployment-and-execution-guide)
   - [Step 1: VPS / Server Infrastructure & Backend](#step-1-vps--server-infrastructure--backend)
   - [Step 2: Data Pipeline in Apache Airflow (Local / Orchestrator)](#step-2-data-pipeline-in-apache-airflow-local--orchestrator)
   - [Step 3: Mobile Application (Flutter)](#step-3-mobile-application-flutter)
   - [Step 4: Analytical Dashboards in Power BI](#step-4-analytical-dashboards-in-power-bi)
6. [Security Model, Roles (RBAC) and Credentials](#6-security-model-roles-rbac-and-credentials)
7. [Business Logic and Financial Model](#7-business-logic-and-financial-model)
8. [Medallion Pipeline and Star Schema (DWH)](#8-medallion-pipeline-and-star-schema-dwh)
9. [Test Suite and Verification](#9-test-suite-and-verification)
10. [How to Replicate this Project in Another Environment](#10-how-to-replicate-this-project-in-another-environment)

---

## 1. System Architecture

The ecosystem is architected around high cohesion and loose coupling principles:

```text
[ Client / Courier / Admin ]
               |
               v
      [ Flutter Mobile App ] (Clean Architecture / DDD Vertical Slices)
               |
               v (HTTP REST / JSON Web Tokens)
      [ Nginx Reverse Proxy ] (Ports 80 / 443)
               |
               v
      [ FastAPI Backend ] (OAuth2 Argon2id + RBAC + Geospatial Engine + State Machine)
               |
               +----------------------------+
               | (Transactional OLTP)       | (Event Extraction)
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

## 2. Repository Structure

```text
assessment/
├── .env.example                     # Environment variables configuration template
├── .gitignore                       # Strict protection for secrets and temporary files
├── docker-compose.yml               # Server orchestrator (PostgreSQL, Backend, Nginx)
├── docker-compose.local.yml         # Airflow 3.0 orchestrator (Scheduler, API Server, DAG Processor)
├── README.md                        # Primary documentation in Spanish
├── README.en.md                     # Documentation in English
├── airflow/                         # Module 3: Data Engineering Pipeline
│   ├── dags/
│   │   └── etl_pedidos_diario.py    # Medallion DAG definition using TaskGroups
│   ├── tasks/
│   │   ├── extract/                 # Bronze tasks (OLTP and RandomUser API)
│   │   ├── transform_silver/        # Silver tasks (Cleansing, SLA, Enrichment)
│   │   └── load_gold/               # Gold tasks (Kimball Star Schema & CSV export)
│   ├── scripts/
│   │   └── reset_airflow_db.py      # Metadata database initialization utility
│   ├── Dockerfile                   # Custom Airflow 3.0 image
│   └── requirements.txt             # Pipeline Python dependencies
├── app_flutter/                     # Module 1: Cross-Platform Mobile Application
│   ├── lib/
│   │   ├── core/                    # Networking, Material 3 themes, constants & utils
│   │   └── features/
│   │       ├── auth/                # JWT Authentication & Social OAuth (Google/GitHub)
│   │       ├── users/               # User profiles, summaries, and metrics
│   │       └── pedidos/             # Role-based order management, filters, details
│   └── pubspec.yaml
├── backend/                         # Module 2: High-Performance RESTful API
│   ├── app/
│   │   ├── api/v1/                  # REST controllers, auth deps & RBAC guards
│   │   ├── core/                    # Pydantic Settings, Argon2id hashing, JWT helpers
│   │   ├── db/                      # SQLAlchemy 2.0 session & PostgreSQL engine
│   │   ├── models/                  # ORM database entities (User, Pedido)
│   │   ├── schemas/                 # Pydantic v2 validation and serialization schemas
│   │   ├── services/                # Modularized domain services (Geo, Costs, TTL)
│   │   ├── main.py                  # FastAPI entry point & CORS middleware
│   │   └── seed.py                  # Database initialization & seed script (150 users, 1000 orders)
│   ├── tests/
│   │   └── test_live_api.py         # Automated E2E test suite (10/10 tests passed)
│   ├── Dockerfile                   # Lightweight production container image
│   └── requirements.txt
├── data/                            # Assessment seed datasets
│   ├── pedidos_db_ready.csv         # 1,000 historical orders
│   └── users_db_ready.csv           # 150 categorized users
├── docs/                            # In-depth technical documentation
│   ├── CONTEXTO_PROYECTO.md         # Architecture blueprint and project status
│   ├── DOCUMENTACION_FEATURES.md    # Functional specification of each feature
│   └── LOGICA_NEGOCIO_Y_DECISIONES.md# Mathematical models, SLA, TTL, and geospatial analysis
├── dwh/                             # DDL scripts and generated analytical reports
│   ├── reports/                     # Analytical reports output (reporte_pedidos.csv)
│   └── sql/                         # Bronze, Silver, and Gold schema DDL scripts
└── powerbi/                         # Module 4: Analytical Model & Dashboards
    ├── dashboard_assessment.pbip    # Native Power BI project (Fabric PBIR)
    ├── dashboard_assessment.Report/ # JSON report layout definitions
    └── dashboard_assessment.SemanticModel/ # TMDL definitions for the star schema
```

---

## 3. Prerequisites

* **Docker Engine** (v24.0 or higher) and **Docker Compose** (v2.20 or higher).
* **Python** (v3.11 or v3.12) for local scripts and test execution.
* **Flutter SDK** (v3.19 or higher) to build and run the mobile application.
* **Power BI Desktop** (2024 version or higher with `.pbip` project support).
* Network access to ports `80`, `443`, `8000`, `8080`, and `5432`.

---

## 4. Environment Variables Guide (.env)

Copy the template file to the root directory before running the system:

```bash
cp .env.example .env
```

Below is the complete reference of all environment variables grouped by service:

### 4.1. PostgreSQL Database and Data Warehouse
| Variable | Description | Example / Production Value | What to change when replicating |
| :--- | :--- | :--- | :--- |
| `POSTGRES_HOST` | PostgreSQL server host or IP | `100.60.229.203` (or `localhost`) | Set to your VPS IP or `localhost` if running locally. |
| `POSTGRES_PORT` | PostgreSQL listening port | `5432` | Keep `5432` unless using a custom port. |
| `POSTGRES_USER` | PostgreSQL superuser/app user | `ecodelivery_user` | Your database username. |
| `POSTGRES_PASSWORD` | PostgreSQL user password | `your_secure_password` | Set a strong database password. |
| `POSTGRES_DB` | Operational database (OLTP) | `ecodelivery_db` | Transactional database name. |
| `AIRFLOW_DB_NAME` | Airflow metadata database | `airflow_db` | Dedicated database for Airflow state. |
| `DWH_DB_NAME` | Data Warehouse database | `ecodelivery_dwh` | Database for Bronze, Silver, Gold layers. |
| `AIRFLOW_OLTP_URI` | SQLAlchemy URI to OLTP DB | `postgresql+psycopg2://user:pass@host:5432/ecodelivery_db` | Update username, password, host. |
| `AIRFLOW_DWH_URI` | SQLAlchemy URI to DWH DB | `postgresql+psycopg2://user:pass@host:5432/ecodelivery_dwh` | Update username, password, host. |

### 4.2. Apache Airflow 3.0
| Variable | Description | Example / Production Value | What to change when replicating |
| :--- | :--- | :--- | :--- |
| `AIRFLOW_UID` | Linux UID of airflow container user | `50000` | Keep `50000` (Airflow standard). |
| `AIRFLOW__CORE__FERNET_KEY` | Fernet key for encrypting secrets | `generate_fernet_key` | Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. |
| `AIRFLOW__WEBSERVER__SECRET_KEY` | Web session secret key | `generate_random_hex` | Generate with `openssl rand -hex 32`. |
| `AIRFLOW__API_AUTH__JWT_SECRET` | Secret key for execution API JWTs | `generate_random_hex` | Generate with `openssl rand -hex 32`. |
| `AIRFLOW_ADMIN_USERNAME` | Web UI admin username | `admin` | Login username for `localhost:8080`. |
| `AIRFLOW_ADMIN_PASSWORD` | Web UI admin password | `admin` | Password for Web UI access. |

### 4.3. FastAPI Backend and Authentication
| Variable | Description | Example / Production Value | What to change when replicating |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | JWT signing secret key | `generate_jwt_secret` | Generate with `openssl rand -hex 32`. |
| `ALGORITHM` | Cryptographic signature algorithm | `HS256` | Keep `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| JWT validity duration in minutes | `1440` (24 hours) | Adjust based on session requirements. |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Client ID | `id.apps.googleusercontent.com` | From Google Cloud Console. |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 Client Secret | `GOCSPX-secret` | From Google Cloud Console. |
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID | `github_client_id` | From GitHub Developer Settings. |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret | `github_client_secret` | From GitHub Developer Settings. |

---

## 5. Deployment and Execution Guide

### Step 1: VPS / Server Infrastructure & Backend

On your main host or VPS (e.g., AWS Lightsail):

```bash
# 1. Clone the repository
git clone <repository-url>
cd assessment

# 2. Configure the .env file with your credentials
cp .env.example .env
nano .env

# 3. Build and launch core services (PostgreSQL, FastAPI Backend, Nginx)
docker compose up -d --build

# 4. Run the database seed script (150 users and 1,000 orders)
docker compose exec backend python -m app.seed
```

Verification:
* Interactive Swagger UI: `http://ecodelivery.geisler.coderhivex.com/docs` (or `http://localhost:8000/docs`).
* Health check endpoint: `curl http://localhost:8000/api/v1/health`

---

### Step 2: Data Pipeline in Apache Airflow (Local / Orchestrator)

To process and transform data into the Data Warehouse:

```bash
# 1. Start the local Airflow 3.0 stack
docker compose -f docker-compose.local.yml up -d --build

# 2. Check container health status
docker compose -f docker-compose.local.yml ps
```

* Airflow Web Interface: **`http://localhost:8080`**
* **Username:** `admin` | **Password:** `admin`
* Enable the **`etl_pedidos_diario`** DAG and click **Trigger DAG**.
* The pipeline will execute the following stages automatically:
  1. `bronze_ingestion_group`: Raw extraction from PostgreSQL and the RandomUser API.
  2. `silver_transformation_group`: Cleansing, SLA delivery time calculation, and demographic enrichment.
  3. `gold_star_schema_group`: Star schema dimension/fact loading and `dwh/reports/reporte_pedidos.csv` generation.

---

### Step 3: Mobile Application (Flutter)

The mobile application connects directly to the REST API:

```bash
cd app_flutter

# 1. Install Flutter packages
flutter pub get

# 2. Run static code analysis
dart analyze

# 3. Launch on Web Browser
flutter run -d chrome

# 4. Launch on Android Emulator or Physical Device
flutter run
```

> **Mobile Network Configuration:** The base API URL is defined in `app_flutter/lib/core/constants/api_constants.dart` pointing to `http://ecodelivery.geisler.coderhivex.com/api/v1`.

---

### Step 4: Analytical Dashboards in Power BI

The analytics model is organized in native **PBIP** format (Fabric Git Integration) in the `powerbi/` folder:

1. Open **`powerbi/dashboard_assessment.pbip`** in Power BI Desktop.
2. Click **Refresh** in the top ribbon.
3. The 5 star schema tables (`fact_pedidos`, `dim_cliente`, `dim_repartidor`, `dim_zona`, `dim_date`) will load directly from the `gold` schema in PostgreSQL or from `dwh/reports/reporte_pedidos.csv`.
4. The report provides two interactive executive dashboards:
   - **Executive Summary:** Total orders, global gross revenue, operating margin, average ticket, and order status breakdown over time.
   - **Operations & Couriers:** Average delivery times in minutes (SLA), vehicle performance metrics, and order volume by zone.

---

## 6. Security Model, Roles (RBAC) and Credentials

### Role-Based Access Control (RBAC)
* **`admin`:** Full platform control, global real-time search, user management, and operational analytics.
* **`repartidor` (Courier):** Specialized view for assigned deliveries, zone-based open pool claiming, and delivery confirmation.
* **`cliente` (Client):** Exclusive view of personal orders, order creation, and cancellation of pending orders.

### Pre-loaded Test Credentials

| Role | Email | Password | Name / Identifier |
| :--- | :--- | :--- | :--- |
| **Super Administrator** | `admin@ecodelivery.com` | `Admin1234!` | Global Platform Administrator |
| **Seed Courier** | `andres.gomez91@ecodelivery.com` | `EcoDelivery2026!` | Andres Gomez (Zone: Norte, Vehicle: Bicycle) |
| **Seed Client** | `diego.gonzalez7@ecodelivery.com` | `EcoDelivery2026!` | Diego Gonzalez (Zone: Chapinero / Northeast) |

> **Security Note:** All passwords in the database are hashed using **Argon2id** (`pwdlib[argon2]`), adhering to industry OWASP security recommendations.

---

## 7. Business Logic and Financial Model

### 7.1. Operating Cost Model
$$\text{Operating Cost} = \begin{cases} \text{amount} \times 0.10 & \text{if vehicle is Bicycle} \\ \text{amount} \times 0.15 & \text{if vehicle is Electric Motorbike} \end{cases}$$

$$\text{Gross Margin} = \text{amount} - \text{Operating Cost}$$

### 7.2. Geospatial Bounding Box (Aburra Valley)
All coordinates are located in the metropolitan area of Medellin:
* **Sur:** Envigado, Itagui, Sabaneta (Lat: `6.1649`, Lon: `-75.5953`)
* **Occidente:** Laureles, San Javier, Belen (Lat: `6.2566`, Lon: `-75.6045`)
* **Centro:** La Candelaria, Prado (Lat: `6.2502`, Lon: `-75.5594`)
* **Chapinero / Nororiente:** Manrique, Aranjuez (Lat: `6.2649`, Lon: `-75.5497`)
* **Norte:** Castilla, Bello (Lat: `6.2839`, Lon: `-75.5654`)

### 7.3. State Machine & Time-to-Live (TTL) Rules
* **30-Minute Rule:** If an assigned pending order is not accepted within 30 minutes, it is unassigned (`repartidor_id = NULL`) and returned to the open pool.
* **2-Hour Rule:** If an order stays pending for more than 120 minutes without dispatch, it is automatically marked as `CANCELADO`.
* **Auto-Assignment:** When a courier dispatches an order (`en_camino`), the backend atomically records `repartidor_id` and `fecha_asignacion = NOW()`.

---

## 8. Medallion Pipeline and Star Schema (DWH)

```text
Pipeline Stages:
1. BRONZE:
   - raw_pedidos (OLTP) + Audit metadata (_extracted_at, _source)
   - raw_users (OLTP) + Audit metadata
   - raw_randomuser_profiles (External API)

2. SILVER:
   - users_enriched: Joined with RandomUser (age, gender, age_group: 18-25, 26-35, 36-50, 50+, phone, avatar).
   - pedidos_cleaned: Strict UTC timestamp parsing, status validation, and delivery duration in minutes calculation.

3. GOLD (Kimball Star Schema):
   - dim_cliente (cliente_sk, name, email, age, gender, age_group, zone)
   - dim_repartidor (repartidor_sk, name, vehicle_type, zone)
   - dim_zona (zona_sk, zone_name, centroid_lat, centroid_lon, region)
   - dim_date (date_sk, full_date, year, quarter, month, day, day_of_week, is_weekend)
   - fact_pedidos (pedido_sk, cliente_sk, repartidor_sk, zona_sk, date_sk, amount, operating_cost, gross_margin, delivery_time_minutes)
   - Exported Report: dwh/reports/reporte_pedidos.csv
```

---

## 9. Test Suite and Verification

Run automated validation tests:

```bash
# Backend E2E tests (10/10 lifecycle tests)
python backend/tests/test_live_api.py

# Flutter static analysis
cd app_flutter && dart analyze
```

---

## 10. How to Replicate this Project in Another Environment

To replicate this solution on a new server or local machine:

1. **Clone the repository** to your target environment.
2. **Create `.env`** from `.env.example` and set your `POSTGRES_PASSWORD`, `SECRET_KEY`, and `POSTGRES_HOST`.
3. **Start backend services:** `docker compose up -d --build`.
4. **Seed database:** `docker compose exec backend python -m app.seed`.
5. **Start Airflow:** `docker compose -f docker-compose.local.yml up -d --build` and run `etl_pedidos_diario`.
6. **Open Power BI:** Open `powerbi/dashboard_assessment.pbip` and click Refresh to load data from your new database.
