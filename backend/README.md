# EcoDelivery API - Backend RESTful & Autenticación OAuth

Backend oficial para **EcoDelivery S.A.S.** construido con **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, **Argon2id (`pwdlib`)**, **PyJWT** y flujos **OAuth 2.0 (Google y GitHub)**.

---

## 🌟 Características Principales

1. **Autenticación Dual**:
   - **Local JWT Bearer (OAuth2)**: Hashing industrial de contraseñas con Argon2id.
   - **Social OAuth**: Endpoints listos para integración con Google y GitHub.
2. **Control de Acceso Basado en Roles (RBAC)**:
   - Roles: `cliente`, `repartidor`, `admin`.
3. **Gestión de Pedidos & Máquina de Estados**:
   - `POST /api/v1/pedidos`: Creación con estado inicial `pendiente`.
   - `GET /api/v1/pedidos`: Filtros dinámicos por `?estado=` y `?zona=`.
   - `GET /api/v1/pedidos/{id}`: Detalle de pedido con datos del cliente y repartidor.
   - `PATCH /api/v1/pedidos/{id}/estado`: Validación estricta de transiciones de estado (`pendiente` -> `en_camino` -> `entregado`/`cancelado`) y registro automático de `fecha_asignacion` y `fecha_entrega`.
4. **Caracterización de Usuarios & Analítica**:
   - `GET /api/v1/users/me/resumen`: Métricas de actividad, volumen de compras o entregas realizadas.
   - `GET /api/v1/pedidos/estadisticas/resumen`: KPIs operativos para Airflow y Power BI.
5. **Listo para Despliegue en VPS**:
   - Totalmente contenedorizado con Docker y orquestado con `docker-compose.yml`.

---

## 🚀 Despliegue Rápido en VPS con Docker (1 solo comando)

1. Clona el repositorio en tu VPS:
   ```bash
   git clone <tu-repo>
   cd assessment
   ```

2. Configura las variables de entorno en el archivo `.env`:
   ```bash
   cp .env.example .env
   ```

3. Levanta todos los servicios (PostgreSQL + FastAPI Backend):
   ```bash
   docker compose up -d --build
   ```

4. Ejecuta el script de poblamiento de base de datos con los 150 usuarios y 1000 pedidos:
   ```bash
   docker compose exec backend python -m app.seed
   ```

5. Accede a la documentación interactiva Swagger UI:
   - **En VPS**: `http://<IP_DE_TU_VPS>:8000/docs`
   - **Local**: `http://localhost:8000/docs`

---

## 🔑 Credenciales de Prueba Pre-cargadas (Seed)

| Rol | Correo Electrónico | Contraseña |
| :--- | :--- | :--- |
| **Administrador** | `admin@ecodelivery.com` | `Admin1234!` |
| **Cliente Semilla** | `diego.gonzalez7@ecodelivery.local` | `EcoDelivery2026!` |
| **Repartidor Semilla** | `carlos.perez63@ecodelivery.local` | `EcoDelivery2026!` |

> [!NOTE]
> Todos los 150 usuarios del dataset original han sido inicializados con la contraseña: `EcoDelivery2026!`.

---

## 📱 Conexión desde Flutter

Para conectar la aplicación Flutter a esta API:

* **Emulador Android**: Usa `http://10.0.2.2:8000/api/v1`
* **Simulador iOS**: Usa `http://127.0.0.1:8000/api/v1`
* **Dispositivo Físico o VPS**: Usa `http://<IP_PUBLICA_VPS>:8000/api/v1`

---

## 🛠️ Ejecución Local (Sin Docker)

Si deseas correr el backend de forma local en tu máquina:

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
