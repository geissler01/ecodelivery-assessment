# EcoDelivery API - Backend RESTful y Autenticacion OAuth

Backend oficial para **EcoDelivery S.A.S.** construido con **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, **Argon2id (`pwdlib`)**, **PyJWT** y flujos **OAuth 2.0 (Google y GitHub)**.

---

## 1. Caracteristicas Principales

1. **Autenticacion Dual**:
   - **Local JWT Bearer (OAuth2)**: Hashing industrial de contrasenas con Argon2id.
   - **Social OAuth**: Endpoints listos para integracion con Google y GitHub.
2. **Control de Acceso Basado en Roles (RBAC)**:
   - Roles: `cliente`, `repartidor`, `admin`.
3. **Gestion de Pedidos y Maquina de Estados**:
   - `POST /api/v1/pedidos`: Creacion con estado inicial `pendiente`.
   - `GET /api/v1/pedidos`: Filtros dinamicos por `?estado=` y `?zona=`.
   - `GET /api/v1/pedidos/{id}`: Detalle de pedido con datos del cliente y repartidor.
   - `PATCH /api/v1/pedidos/{id}/estado`: Validacion estricta de transiciones de estado (`pendiente` -> `en_camino` -> `entregado`/`cancelado`) y registro automatico de `fecha_asignacion` y `fecha_entrega`.
4. **Caracterizacion de Usuarios y Analitica**:
   - `GET /api/v1/users/me/resumen`: Metricas de actividad, volumen de compras o entregas realizadas.
   - `GET /api/v1/pedidos/estadisticas/resumen`: KPIs operativos para Airflow y Power BI.
5. **Listo para Despliegue en VPS**:
   - Totalmente contenedorizado con Docker y orquestado con `docker-compose.yml`.

---

## 2. Despliegue Rapido en VPS con Docker

1. Clona el repositorio en tu VPS:
   ```bash
   git clone <tu-repo>
   cd assessment
   ```

2. Configura las variables de entorno en el archivo `.env`:
   ```bash
   cp .env.example .env
   ```

3. Levanta todos los servicios (PostgreSQL + FastAPI Backend + Nginx):
   ```bash
   docker compose up -d --build
   ```

4. Ejecuta el script de poblamiento de base de datos con los 150 usuarios y 1000 pedidos:
   ```bash
   docker compose exec backend python -m app.seed
   ```

5. Accede a la documentacion interactiva Swagger UI:
   - **En VPS**: `http://ecodelivery.geisler.coderhivex.com/docs`
   - **Local**: `http://localhost:8000/docs`

---

## 3. Credenciales de Prueba Pre-cargadas (Seed)

| Rol | Correo Electronico | Contrasena |
| :--- | :--- | :--- |
| **Administrador** | `admin@ecodelivery.com` | `Admin1234!` |
| **Cliente Semilla** | `diego.gonzalez7@ecodelivery.com` | `EcoDelivery2026!` |
| **Repartidor Semilla** | `andres.gomez91@ecodelivery.com` | `EcoDelivery2026!` |

> Todos los 150 usuarios del dataset original han sido inicializados con la contrasena: `EcoDelivery2026!`.

---

## 4. Conexion desde Flutter

Para conectar la aplicacion Flutter a esta API:

* **Emulador Android**: Usa `http://10.0.2.2:8000/api/v1`
* **Simulador iOS**: Usa `http://127.0.0.1:8000/api/v1`
* **Dispositivo Fisico o VPS**: Usa `http://ecodelivery.geisler.coderhivex.com/api/v1`

---

## 5. Ejecucion Local (Sin Docker)

Si deseas correr el backend de forma local en tu maquina:

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate # En Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r backend/requirements.txt

# 3. Ejecutar seed de datos
python -m backend.app.seed

# 4. Iniciar servidor FastAPI con recarga en vivo
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
