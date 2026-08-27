# Documentación Técnica: Backend RESTful & Autenticación EcoDelivery

Esta documentación describe la arquitectura, endpoints, modelo de seguridad, validación de datos, suite de pruebas automatizadas y procedimientos de despliegue para el Backend de **EcoDelivery S.A.S.**

---

## 🏛️ Arquitectura del Sistema

* **Framework:** FastAPI (Python 3.13)
* **ORM & Base de Datos:** SQLAlchemy 2.0 + PostgreSQL 16
* **Criptografía & Seguridad:** Argon2id (`pwdlib`) + JSON Web Tokens (`PyJWT`)
* **Servidor Web & Proxy:** Uvicorn + Nginx Reverse Proxy
* **Orquestación:** Docker Compose en AWS Lightsail VPS
* **Dominio:** `http://ecodelivery.geisler.coderhivex.com`

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── deps/
│   │       │   ├── auth.py          # Extracción y validación de JWT Bearer
│   │       │   └── roles.py         # Control de acceso RBAC (Admin, Repartidor, Cliente)
│   │       ├── endpoints/
│   │       │   ├── auth.py          # /register y /login (OAuth2 Password Request Form)
│   │       │   ├── oauth.py         # Google y GitHub OAuth callbacks
│   │       │   ├── users.py         # /me, /me/pedidos, /me/resumen, CRUD usuarios
│   │       │   └── pedidos.py       # POST /pedidos, GET /pedidos, PATCH /pedidos/:id/estado
│   │       └── router.py            # Enrutador centralizado de API v1
│   ├── core/
│   │   ├── config.py                # Pydantic Settings y carga de variables .env
│   │   └── security.py              # Funciones de hash Argon2id y creación de JWT
│   ├── db/
│   │   ├── base.py                  # Base declarativa de SQLAlchemy
│   │   └── session.py               # Engine con connection pooling y SessionLocal
│   ├── models/
│   │   ├── user.py                  # Modelo relacional User (Roles y Caracterización)
│   │   └── pedido.py                # Modelo relacional Pedido (FKs y Máquina de Estados)
│   ├── schemas/
│   │   ├── token.py                 # Esquemas Pydantic de Tokens JWT
│   │   ├── user.py                  # Esquemas Pydantic de Usuario con validación EmailStr
│   │   └── pedido.py                # Esquemas Pydantic de Pedido y Métricas
│   ├── services/
│   │   ├── user_service.py          # Lógica de autenticación, usuarios y resúmenes
│   │   ├── pedido_service.py        # Gestión de pedidos, filtros y máquina de estados
│   │   └── oauth_service.py         # Integración OAuth con Google y GitHub
│   ├── main.py                      # App FastAPI, Lifespan y Middleware CORS
│   └── seed.py                      # Poblamiento de datos con hashes reales y caracterización
├── tests/
│   └── test_live_api.py             # Suite de pruebas E2E automatizadas
├── Dockerfile                       # Definición de contenedor liviano
└── requirements.txt                 # Dependencias exactas
```

---

## 🔐 Modelo de Seguridad y Roles (RBAC)

1. **Hashing de Contraseñas:**  
   Se utiliza **Argon2id** (`PasswordHash.recommended()` de `pwdlib`), cumpliendo con el estándar de OWASP contra ataques por GPU/ASIC.
2. **Autenticación Bearer:**  
   Login compatible con el flujo estándar `OAuth2PasswordBearer`, habilitando el botón de autorización interactivo en Swagger UI.
3. **Roles Implementados:**
   * **`admin`**: Acceso total al dashboard administrativo y gestión de usuarios.
   * **`repartidor`**: Acceso a pedidos asignados y actualización de estado en ruta.
   * **`cliente`**: Creación de pedidos, visualización de historial y resumen de gastos.

---

## 📡 Catálogo de Endpoints

### 1. Autenticación (`/api/v1/auth`)
* `POST /api/v1/auth/register`: Registro de nuevos clientes/repartidores con validación `EmailStr`.
* `POST /api/v1/auth/login`: Autenticación con formulario OAuth2 (devuelve Bearer JWT).
* `GET /api/v1/auth/google/login` & `/callback`: Flujo de autorización OAuth 2.0 con Google.
* `GET /api/v1/auth/github/login` & `/callback`: Flujo de autorización OAuth con GitHub.

### 2. Gestión de Usuarios y Perfiles (`/api/v1/users`)
* `GET /api/v1/users/me`: Perfil del usuario actualmente autenticado.
* `PATCH /api/v1/users/me`: Actualización de datos de perfil (teléfono, zona principal, etc.).
* `GET /api/v1/users/me/pedidos`: Lista de pedidos asociados al usuario.
* `GET /api/v1/users/me/resumen`: Métricas agregadas (total de compras para cliente o entregas para repartidor).
* `GET /api/v1/users/`: Lista administrativa de usuarios con filtros por rol (Admin).
* `GET /api/v1/users/{id}`: Detalle de usuario por UUID (Admin).

### 3. Gestión de Pedidos (`/api/v1/pedidos`)
* `POST /api/v1/pedidos/`: Crear pedido con estado inicial `pendiente`.
* `GET /api/v1/pedidos/`: Listar pedidos con paginación (`?skip=&limit=`) y filtros combinados (`?estado=&zona=`).
* `GET /api/v1/pedidos/{id}`: Detalle completo de un pedido con nombres de cliente y repartidor.
* `PATCH /api/v1/pedidos/{id}/estado`: Validación de la máquina de estados:
  * `pendiente` ➔ `en_camino` (sella automáticamente `fecha_asignacion`).
  * `en_camino` ➔ `entregado` (sella automáticamente `fecha_entrega`).
  * `pendiente` o `en_camino` ➔ `cancelado`.
  * Estados terminales (`entregado`, `cancelado`) no admiten modificaciones posteriores.
* `GET /api/v1/pedidos/estadisticas/resumen`: KPIs operativos para Airflow y Power BI (total pedidos, ingresos totales, tiempo promedio de entrega en minutos).

---

## 🧪 Ejecución de Pruebas Automatizadas

El script `backend/tests/test_live_api.py` ejecuta 9 pruebas automáticas cubriendo todos los flujos críticos.

Para ejecutarlo contra el servidor en vivo:

```bash
python backend/tests/test_live_api.py
```

O apuntando a un entorno local/staging:

```bash
API_BASE_URL=http://localhost:8000 python backend/tests/test_live_api.py
```

### Resultados de la última verificación (100% Pass):

```text
======================================================================
🚀 INICIANDO PRUEBAS E2E CONTRA: http://ecodelivery.geisler.coderhivex.com
======================================================================
✅ [1/9] Health Check -> OK (status: healthy)
✅ [2/9] Login Superadmin -> OK (Token JWT emitido)
✅ [3/9] Login Cliente Semilla -> OK (Argon2id verificado)
✅ [4/9] Perfil /me -> Diego Gonzalez | Rol: cliente | Zona: Chapinero
✅ [5/9] Resumen Usuario -> Pedidos: 7 | Gasto: $360,037.05
✅ [6/9] Listar Pedidos -> 5 obtenidos (Muestra: ID 18bd281e... | Sur)
✅ [7/9] Filtros Combinados (?zona=Chapinero&estado=entregado) -> 5 pedidos
✅ [8/9] KPIs Operativos -> Total: 1000 | Ingresos: $55,138,075.66 | Tiempo Prom: 39.98 min
✅ [9/9] Ciclo de Pedido (POST y PATCH Máquina de Estados) -> OK (ID: e909dee8... | Estado: en_camino)
======================================================================
🎉 ¡TODAS LAS PRUEBAS E2E FUERON EXITOSAS AL 100%!
======================================================================
```
