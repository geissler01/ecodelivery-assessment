# Sistema de Pedidos y Analítica - EcoDelivery S.A.S.

Solución integral de arquitectura empresarial que compone una API REST en **FastAPI**, modelo relacional normalizado en **PostgreSQL**, autenticación **JWT & OAuth 2.0 (Google/GitHub)**, pipeline de datos en **Airflow**, dashboard en **Power BI** y cliente móvil en **Flutter**.

---

## 🏗️ Estructura del Repositorio

```text
assessment/
├── backend/                  # API REST FastAPI + Auth + Dockerfile
│   ├── app/
│   │   ├── api/              # Routers, endpoints y dependencias RBAC
│   │   ├── core/             # Configuración y seguridad (Argon2id, JWT)
│   │   ├── db/               # Sesión y Base SQLAlchemy
│   │   ├── models/           # Modelos relacionales User y Pedido
│   │   ├── schemas/          # Esquemas de validación Pydantic
│   │   ├── services/         # Lógica de negocio y servicios OAuth
│   │   ├── main.py           # Instancia FastAPI y middleware CORS
│   │   └── seed.py           # Script de migración y seed con hashes reales
│   ├── Dockerfile
│   └── requirements.txt
├── airflow/                  # Pipeline de datos (ETL)
│   └── dags/
│       └── etl_pedidos_diario.py
├── app_flutter/              # Aplicación móvil en Flutter
├── powerbi/                  # Dashboard y reportes analíticos (.pbix)
├── data/                     # Datasets semilla (CSV)
├── docker-compose.yml        # Orquestador maestro de contenedores
├── .env.example              # Plantilla de variables de entorno
└── README.md
```

---

## 🚀 Despliegue en VPS (Un solo comando)

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

Documentación interactiva disponible en: `http://<IP_VPS_O_LOCALHOST>:8000/docs`

---

## 🔑 Credenciales de Acceso

* **Administrador:** `admin@ecodelivery.com` / `Admin1234!`
* **Clientes:** `[correo_del_dataset]@ecodelivery.local` / `EcoDelivery2026!`
* **Repartidores:** `[correo_del_dataset]@ecodelivery.local` / `EcoDelivery2026!`
