# Sistema de Pedidos y Analitica - EcoDelivery S.A.S.

Solucion integral de arquitectura empresarial que compone una API REST en **FastAPI**, modelo relacional normalizado en **PostgreSQL**, autenticacion **JWT & OAuth 2.0 (Google/GitHub)**, pipeline de datos en **Airflow**, dashboard en **Power BI** y cliente movil en **Flutter**.

---

## 1. Estructura del Repositorio

```text
assessment/
├── backend/                  # API REST FastAPI + Auth + Dockerfile
│   ├── app/
│   │   ├── api/              # Routers, endpoints y dependencias RBAC
│   │   ├── core/             # Configuracion y seguridad (Argon2id, JWT)
│   │   ├── db/               # Sesion y Base SQLAlchemy
│   │   ├── models/           # Modelos relacionales User y Pedido
│   │   ├── schemas/          # Esquemas de validacion Pydantic
│   │   ├── services/         # Logica de negocio y servicios OAuth
│   │   ├── main.py           # Instancia FastAPI y middleware CORS
│   │   └── seed.py           # Script de migracion y seed con hashes reales
│   ├── Dockerfile
│   └── requirements.txt
├── airflow/                  # Pipeline de datos (ETL)
│   └── dags/
│       └── etl_pedidos_diario.py
├── app_flutter/              # Aplicacion movil en Flutter
├── powerbi/                  # Dashboard y reportes analiticos (.pbip)
├── data/                     # Datasets semilla (CSV)
├── docker-compose.yml        # Orquestador de produccion para VPS
├── docker-compose.local.yml  # Orquestador local para Airflow
├── .env.example              # Plantilla de variables de entorno
└── README.md
```

---

## 2. Despliegue en VPS (Un solo comando)

```bash
# 1. Clonar e ingresar
git clone <repo-url>
cd assessment

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Construir y levantar contenedores
docker compose up -d --build

# 4. Poblar la base de datos con los 150 usuarios y 1000 pedidos
docker compose exec backend python -m app.seed
```

Documentacion interactiva disponible en: `http://ecodelivery.geisler.coderhivex.com/docs`

---

## 3. Credenciales de Acceso

* **Administrador:** `admin@ecodelivery.com` / `Admin1234!`
* **Clientes:** `[correo_del_dataset]@ecodelivery.local` / `EcoDelivery2026!`
* **Repartidores:** `[correo_del_dataset]@ecodelivery.local` / `EcoDelivery2026!`
