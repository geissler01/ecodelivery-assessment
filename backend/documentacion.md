# Documentacion Tecnica: Backend RESTful y Autenticacion EcoDelivery

Esta documentacion describe la arquitectura, endpoints, modelo de seguridad, validacion de datos, suite de pruebas automatizadas y procedimientos de despliegue para el Backend de **EcoDelivery S.A.S.**

---

## 1. Arquitectura del Sistema

* **Framework:** FastAPI (Python 3.13)
* **ORM y Base de Datos:** SQLAlchemy 2.0 + PostgreSQL 16
* **Criptografia y Seguridad:** Argon2id (`pwdlib`) + JSON Web Tokens (`PyJWT`)
* **Servidor Web y Proxy:** Uvicorn + Nginx Reverse Proxy
* **Orquestacion:** Docker Compose en AWS Lightsail VPS
* **Dominio:** `http://ecodelivery.geisler.coderhivex.com`

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── deps/
│   │       │   ├── auth.py          # Extraccion y validacion de JWT Bearer
│   │       │   └── roles.py         # Control de acceso RBAC (Admin, Repartidor, Cliente)
│   │       ├── endpoints/
│   │       │   ├── auth.py          # /register y /login (OAuth2 Password Request Form)
│   │       │   ├── oauth.py         # Google y GitHub OAuth callbacks
│   │       │   ├── users.py         # /me, /me/pedidos, /me/resumen, CRUD usuarios
│   │       │   └── pedidos.py       # POST /pedidos, GET /pedidos, PATCH /pedidos/:id/estado
│   │       └── router.py            # Enrutador centralizado de API v1
│   ├── core/
│   │   ├── config.py                # Pydantic Settings y carga de variables .env
│   │   └── security.py              # Funciones de hash Argon2id y creacion de JWT
│   ├── db/
│   │   ├── base.py                  # Base declarativa de SQLAlchemy
│   │   └── session.py               # Engine con connection pooling y SessionLocal
│   ├── models/
│   │   ├── user.py                  # Modelo relacional User (Roles y Caracterizacion)
│   │   └── pedido.py                # Modelo relacional Pedido (FKs y Maquina de Estados)
│   ├── schemas/
│   │   ├── token.py                 # Esquemas Pydantic de Tokens JWT
│   │   ├── user.py                  # Esquemas Pydantic de Usuario con validacion EmailStr
│   │   └── pedido.py                # Esquemas Pydantic de Pedido y Metricas
│   ├── services/
│   │   ├── user_service.py          # Logica de autenticacion, usuarios y resumenes
│   │   ├── pedido_service.py        # Gestion de pedidos, filtros y maquina de estados
│   │   └── oauth_service.py         # Integracion OAuth con Google y GitHub
│   ├── main.py                      # App FastAPI, Lifespan y Middleware CORS
│   └── seed.py                      # Poblamiento de datos con hashes reales y caracterizacion
├── tests/
│   └── test_live_api.py             # Suite de pruebas E2E automatizadas
├── Dockerfile                       # Definicion de contenedor liviano
└── requirements.txt                 # Dependencias exactas
```

---

## 2. Modelo de Seguridad y Roles (RBAC)

1. **Hashing de Contrasenas:**  
   Se utiliza **Argon2id** (`PasswordHash.recommended()` de `pwdlib`), cumpliendo con el estandar de OWASP contra ataques por GPU/ASIC.
2. **Autenticacion Bearer:**  
   Login compatible con el flujo estandar `OAuth2PasswordBearer`, habilitando el boton de autorizacion interactivo en Swagger UI.
3. **Roles Implementados:**
   * **`admin`**: Acceso total al dashboard administrativo y gestion de usuarios.
   * **`repartidor`**: Acceso a pedidos asignados y actualizacion de estado en ruta.
   * **`cliente`**: Creacion de pedidos, visualizacion de historial y resumen de gastos.

---

## 3. Catalogo de Endpoints

### 1. Autenticacion (`/api/v1/auth`)
* `POST /api/v1/auth/register`: Registro de nuevos clientes/repartidores con validacion `EmailStr`.
* `POST /api/v1/auth/login`: Autenticacion con formulario OAuth2 (devuelve Bearer JWT).
* `GET /api/v1/auth/google/login` & `/callback`: Flujo de autorizacion OAuth 2.0 con Google.
* `GET /api/v1/auth/github/login` & `/callback`: Flujo de autorizacion OAuth con GitHub.

### 2. Gestion de Usuarios y Perfiles (`/api/v1/users`)
* `GET /api/v1/users/me`: Perfil del usuario actualmente autenticado.
* `PATCH /api/v1/users/me`: Actualizacion de datos de perfil (telefono, zona principal, etc.).
* `GET /api/v1/users/me/pedidos`: Lista de pedidos asociados al usuario.
* `GET /api/v1/users/me/resumen`: Metricas agregadas (total de compras para cliente o entregas para repartidor).
* `GET /api/v1/users/`: Lista administrativa de usuarios con filtros por rol (Admin).
* `GET /api/v1/users/{id}`: Detalle de usuario por UUID (Admin).

### 3. Gestion de Pedidos (`/api/v1/pedidos`)
* `POST /api/v1/pedidos/`: Crear pedido con estado inicial `pendiente`.
* `GET /api/v1/pedidos/`: Listar pedidos con paginacion (`?skip=&limit=`) y filtros combinados (`?estado=&zona=`).
* `GET /api/v1/pedidos/{id}`: Detalle completo de un pedido con nombres de cliente y repartidor.
* `PATCH /api/v1/pedidos/{id}/estado`: Validacion de la maquina de estados:
  * `pendiente` -> `en_camino` (sella automaticamente `fecha_asignacion`).
  * `en_camino` -> `entregado` (sella automaticamente `fecha_entrega`).
  * `pendiente` o `en_camino` -> `cancelado`.
  * Estados terminales (`entregado`, `cancelado`) no admiten modificaciones posteriores.
* `GET /api/v1/pedidos/estadisticas/resumen`: KPIs operativos para Airflow y Power BI (total pedidos, ingresos totales, tiempo promedio de entrega en minutos).

---

## 4. Ejecucion de Pruebas Automatizadas

El script `backend/tests/test_live_api.py` ejecuta 9 pruebas automaticas cubriendo todos los flujos criticos.

Para ejecutarlo contra el servidor en vivo:

```bash
python backend/tests/test_live_api.py
```

O apuntando a un entorno local/staging:

```bash
API_BASE_URL=http://localhost:8000 python backend/tests/test_live_api.py
```

### Resultados de la ultima verificacion (100% Pass):

```text
======================================================================
INICIANDO PRUEBAS E2E CONTRA: http://ecodelivery.geisler.coderhivex.com
======================================================================
[1/9] Health Check -> OK (status: healthy)
[2/9] Login Superadmin -> OK (Token JWT emitido)
[3/9] Login Cliente Semilla -> OK (Argon2id verificado)
[4/9] Perfil /me -> Diego Gonzalez | Rol: cliente | Zona: Chapinero
[5/9] Resumen Usuario -> Pedidos: 7 | Gasto: $360,037.05
[6/9] Listar Pedidos -> 5 obtenidos (Muestra: ID 18bd281e... | Sur)
[7/9] Filtros Combinados (?zona=Chapinero&estado=entregado) -> 5 pedidos
[8/9] KPIs Operativos -> Total: 1000 | Ingresos: $55,138,075.66 | Tiempo Prom: 39.98 min
[9/9] Ciclo de Pedido (POST y PATCH Maquina de Estados) -> OK (ID: e909dee8... | Estado: en_camino)
======================================================================
TODAS LAS PRUEBAS E2E FUERON EXITOSAS AL 100%
======================================================================
```
