# Documentación Técnica: Sistema EcoDelivery S.A.S.

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

## 🔑 Gestión de Autenticación y Roles (RBAC)

1. **Hashing Seguro:** Las contraseñas se encriptan con **Argon2id** (`pwdlib`).
2. **Tokens JWT:** Generación y validación de tokens Bearer con expiración configurable.
3. **Roles Soportados:**
   - `admin`: Acceso total y gestión de usuarios.
   - `repartidor`: Visualización de pedidos asignados y cambio de estado.
   - `cliente`: Creación de pedidos y consulta de historial.
4. **OAuth 2.0:** Integración lista con Google y GitHub en `/api/v1/auth/google/login` y `/api/v1/auth/github/login`.
