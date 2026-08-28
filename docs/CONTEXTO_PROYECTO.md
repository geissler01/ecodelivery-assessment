# Contexto Maestro del Proyecto - EcoDelivery Assessment
## Guía de Continuidad y Estado Integral para Desarrolladores y Agentes IA

---

## 1. Información General del Proyecto

* **Nombre del Proyecto:** EcoDelivery S.A.S. Assessment de Empleabilidad (Cohorte 6 - Análisis de Datos).
* **Propósito:** Plataforma integral de logística sostenible de última milla con vehículos cero emisiones (bicicletas y motos eléctricas) en el Valle de Aburrá (Medellín y área metropolitana).
* **Repositorio Local:** `c:\Users\ASUS\Desktop\RIWI\complementos\assessment`

---

## 2. Infraestructura y Despliegue en Producción (VPS)

* **Proveedor:** AWS Lightsail (Ubuntu Linux, Docker y Docker Compose).
* **IP Estática Pública:** `100.60.229.203` (Usuario SSH: `gcache`).
* **Dominios / DNS Activos:**
  * **Backend API (FastAPI):** `http://ecodelivery.geisler.coderhivex.com`
  * **Apache Airflow UI:** `http://airflow.geisler.coderhivex.com`
* **Base de Datos:** PostgreSQL en contenedor Docker (`ecodelivery_db`, usuario: `ecodelivery_user`, password: `ecodelivery_secure_pass`, puerto interno: 5432).
* **Backend API:** FastAPI corriendo en contenedor Docker (`backend`, puerto interno: 8000, mapeado a `80` o reverse proxy NGINX).
* **Airflow API Server:** Airflow 3.0 Web UI (`airflow-api-server`, puerto interno: 8080, reverse proxy NGINX).

---

## 3. Credenciales Maestras y Datos de Prueba (Seed Dataset)

Todos los 150 usuarios y 1.000 pedidos provienen de los archivos semilla `data/users_db_ready.csv` y `data/pedidos_db_ready.csv`.

| Rol | Correo Electrónico | Contraseña | Identificador / Nombre |
| :--- | :--- | :--- | :--- |
| **Super Administrador** | `admin@ecodelivery.com` | `Admin1234!` | Administrador General de la Plataforma |
| **Repartidor Oficial** | `andres.gomez91@ecodelivery.com` | `EcoDelivery2026!` | Andrés Gómez (Rol: `repartidor`, Zona: `Norte`, Vehículo: `bicicleta`) |
| **Cliente Oficial** | `diego.gonzalez7@ecodelivery.com` | `EcoDelivery2026!` | Diego González (Rol: `cliente`, Zona: `Chapinero`) |

> **Nota:** Todos los usuarios semilla cuentan con contraseñas hasheadas en base de datos mediante **Argon2id** (`pwdlib[argon2]`).

---

## 4. Reglas de Negocio, Geoespaciales y Financieras

1. **Delimitación Geográfica (Valle de Aburrá):**  
   Toda la operación está situada en Medellín y municipios vecinos:
   * **Sur:** Lat: `6.1649`, Lon: `-75.5953` (Envigado, Itagüí, Sabaneta)
   * **Occidente:** Lat: `6.2566`, Lon: `-75.6045` (Laureles, Belén, San Javier)
   * **Centro:** Lat: `6.2502`, Lon: `-75.5594` (La Candelaria, Prado)
   * **Chapinero / Nororiente:** Lat: `6.2649`, Lon: `-75.5497` (Manrique, Aranjuez)
   * **Norte:** Lat: `6.2839`, Lon: `-75.5654` (Castilla, Bello)

2. **Modelo Financiero de Costos Operativos:**
   $$\text{Costo Operación} = \begin{cases} \text{monto} \times 0.10 & \text{si el transporte es Bicicleta} \\ \text{monto} \times 0.15 & \text{si el transporte es Moto Eléctrica} \end{cases}$$

3. **Máquina de Estados y Reglas de Conciliación Temporal (TTL):**
   * **Regla de 30 Minutos:** Si un pedido pendiente asignado no es aceptado en 30 minutos, se libera (`repartidor_id = NULL`), quedando disponible en la bolsa abierta de la ciudad.
   * **Regla de 2 Horas:** Si un pedido pendiente supera 120 minutos sin ser despachado, pasa automáticamente a `CANCELADO`.
   * **Auto-Asignación Garantizada:** Al despachar (`PENDIENTE` $\rightarrow$ `EN_CAMINO`), el backend sella `repartidor_id = ID del conductor` y `fecha_asignacion = NOW()`.

---

## 5. Arquitectura del Código y Estructura por Capas

### 5.1. Backend (`backend/`)
* **Patrón:** Clean Architecture / DDD Modularizado.
* **Paquete de Servicios de Pedidos (`backend/app/services/pedidos/`):**
  * `geo_service.py`: Generación y acotamiento geoespacial en el Valle de Aburrá.
  * `cost_calculator.py`: Cálculo de costo operativo (0.10 / 0.15).
  * `dispatcher_service.py`: Asignación y sorteo de conductores por zona.
  * `pedido_creator.py`: Creación y persistencia de órdenes.
  * `pedido_reader.py`: Lectura con eager loading y conciliación automática.
  * `pedido_state_machine.py`: Transiciones RBAC, auto-asignación y conciliación TTL.
  * `pedido_analytics.py`: Agregación de KPIs para analítica.
* **Paquete de Servicios de Usuarios (`backend/app/services/users/`):**
  * `user_manager.py`: Creación, hashing y consultas de usuarios.
  * `user_metrics_service.py`: Métricas por rol para `/users/me/resumen`.
* **Seguridad RBAC (`backend/app/api/v1/endpoints/pedidos.py`):**
  * `GET /pedidos/`: Retorna `403 Forbidden` para clientes, restringe a `PENDIENTE` para repartidores y otorga acceso total con paginación a administradores.

### 5.2. Frontend Móvil (`app_flutter/`)
* **Patrón:** Clean Architecture + Domain-Driven Design (DDD) organizado en *Vertical Slices* (`features/auth/`, `features/users/`, `features/pedidos/`).
* **Vistas Especializadas por Rol:**
  * **Cliente:** Únicamente pantalla *"Mis Pedidos"* (`/users/me/pedidos`), botón *"Nuevo Pedido"* y filtros por estado de sus propias órdenes.
  * **Repartidor:** Pestañas *"Mis Entregas Asignadas"* vs *"Disponibles en mi Zona"*, botones *"Aceptar y Despachar"* y *"Confirmar Entrega"*.
  * **Admin:** Barra de búsqueda en tiempo real (por cliente, ID, zona, repartidor), filtros globales y paginador.
* **Autenticación:** Login nativo, Registro completo con auto-login y soporte de Social OAuth (Google / GitHub).

---

## 6. Estado Actual de los Módulos del Assessment

| Módulo | Descripción | Estado |
| :--- | :--- | :---: |
| **Módulo 1: App Móvil (Flutter)** | Clean DDD, Material 3, Login/Register, Gestión de Pedidos por Rol, Búsqueda Admin, Paginación, 0 errores en `dart analyze`. | **Completado al 100%** |
| **Módulo 2: Backend RESTful (FastAPI)** | OAuth2 JWT, Argon2id, RBAC estricto, Máquina de Estados, Conciliación TTL, Tests E2E 10/10 pasados, Desplegado en VPS. | **Completado al 100%** |
| **Módulo 3: Pipeline de Datos (Airflow)** | DAG modular `airflow/dags/etl_pedidos_diario.py`, Arquitectura Medallón (Bronze -> Silver -> Gold), Enriquecimiento RandomUser sin sobreescritura de zonas/emails, Star Schema en PostgreSQL y generación de `reporte_pedidos.csv`. | **Completado al 100%** |
| **Módulo 4: Dashboard (Power BI)** | Creación del tablero analítico consumiendo `gold.fact_pedidos` / `reporte_pedidos.csv`, con 3 visualizaciones (barras, líneas, KPIs), slicers y medidas DAX personalizadas. | **Pendiente / Siguiente Paso** |

---

## 7. Instrucciones Clave para Próximos Chats y Agentes

> [!IMPORTANT]
> **1. Control de Versiones (Git):**  
> El usuario gestiona de forma manual y autónoma todos los comandos de `git add`, `git commit` y `git push`. **Nunca ejecutes comandos de commit/push directamente en la terminal.**
>
> **2. Despliegue en VPS:**  
> Airflow y los servicios se ejecutan en la VPS AWS Lightsail (`100.60.229.203`) mediante Docker Compose.
>
> **3. Siguiente Paso Inmediato:**  
> Construir el **Módulo 4: Dashboard en Power BI** (`powerbi/`) conectándose al Modelo Estrella (`gold.fact_pedidos` / `gold.dim_*`) o importando `reporte_pedidos.csv`.

