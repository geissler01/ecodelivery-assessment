# Retrospectiva de Ingenieria: Decisiones, Limitaciones y Oportunidades por Modulo
## Plataforma de Logistica y Analitica - EcoDelivery S.A.S.

Este documento formaliza la justificacion tecnica, el analisis de compensaciones (trade-offs), las restricciones superadas y la hoja de ruta de evolucion para cada uno de los 4 modulos del sistema **EcoDelivery**.

---

## Indice Modular

1. [Modulo 1: Frontend Movil (Flutter - Clean Architecture / DDD)](#1-modulo-1-frontend-movil-flutter---clean-architecture--ddd)
2. [Modulo 2: Backend RESTful y Seguridad (FastAPI + PostgreSQL)](#2-modulo-2-backend-restful-y-seguridad-fastapi--postgresql)
3. [Modulo 3: Pipeline de Datos e Ingenieria ETL (Apache Airflow 3.0 + DWH Medallon)](#3-modulo-3-pipeline-de-datos-e-ingenieria-etl-apache-airflow-30--dwh-medallon)
4. [Modulo 4: Analitica y Visualizacion Ejecutiva (Power BI - PBIP / TMDL)](#4-modulo-4-analitica-y-visualizacion-ejecutiva-power-bi---pbip--tmdl)

---

## 1. Modulo 1: Frontend Movil (Flutter - Clean Architecture / DDD)

### 1.1. Decisiones Tecnicas Tomadas
* **Arquitectura Clean DDD por Vertical Slices:** Organice el proyecto en modulos funcionales independientes (`features/auth`, `features/users`, `features/pedidos`), cada uno con sus tres capas clasicas: *Domain* (entidades y contratos), *Data* (modelos, datasources y repositorios) y *Presentation* (controladores y vistas).
* **Vistas Especializadas por Rol (RBAC Visual):**
  - **Cliente:** Interfaz enfocada exclusivamente en *Mis Pedidos*, creacion reactiva de solicitudes mediante boton flotante y cancelacion controlada de pedidos pendientes.
  - **Repartidor:** Tablero operativo con doble pestana (*Mis Entregas Asignadas* vs *Disponibles en mi Zona*), con botones dinamicos de avance de estado (*Aceptar y Despachar* -> *Confirmar Entrega*).
  - **Administrador:** Panel de control con barra de busqueda en tiempo real (por ID, cliente, repartidor o zona), filtros combinados multi-criterio y paginador.
* **Gestion de Estado Desacoplada (Provider / ChangeNotifier):** Uso de controladores reactivos ligeros con aislamiento de ciclo de vida.
* **Purga Atomica de Sesion:** Implemente una rutina de limpieza total de controladores y almacenamiento local al hacer Logout, previniendo que un usuario que cambia de cuenta herede datos en memoria de otra sesion.

### 1.2. Justificacion (¿Por que se hizo asi?)
* **Mantenibilidad:** Separar la logica de negocio de los widgets de UI permite modificar la API o las fuentes de datos sin reescribir las pantallas.
* **Seguridad y Experiencia de Usuario:** Ocultar acciones no autorizadas a nivel de interfaz evita errores 403 innecesarios y reduce la friccion operativa del usuario final.
* **Calidad de Codigo:** Se logro mantener el proyecto con **0 errores y 0 advertencias** bajo las reglas estrictas de `dart analyze`.

### 1.3. Limitaciones Encontradas y Solucionadas
* **Diferencias de Red entre Emulador, Dispositivo Fisico y VPS:** En desarrollo local, Android usa `10.0.2.2`, iOS usa `127.0.0.1` y produccion usa el dominio publico. Centralice la configuracion en `api_constants.dart` con soporte de fallback directo a la VPS en produccion.
* **Sincronizacion de Estados de Pedidos:** Para evitar inconsistencias cuando un repartidor despacha una orden asignada originalmente a otro, la aplicacion refresca las listas tras cada mutacion de estado.

### 1.4. Oportunidades de Mejora
* **Geolocalizacion en Vivo (GPS Tracking):** Integrar WebSockets para transmitir las coordenadas del repartidor en tiempo real y renderizarlas en un mapa con `flutter_map` o Google Maps.
* **Notificaciones Push:** Incorporar Firebase Cloud Messaging (FCM) para alertar instantaneamente a los clientes cuando su orden cambie a estado *En Camino* o *Entregado*.
* **Persistencia Offline (Local Cache):** Integrar Isar o Hive para permitir la consulta de pedidos historicos sin conexion a internet.

---

## 2. Modulo 2: Backend RESTful y Seguridad (FastAPI + PostgreSQL)

### 2.1. Decisiones Tecnicas Tomadas
* **Criptografia con Argon2id:** Implemente el estandar recomendado por OWASP para hashing de contrasenas mediante `pwdlib[argon2]`, garantizando maxima resistencia contra ataques por fuerza bruta y hardware especializado (GPU/ASIC).
* **Autenticacion Hibrida (JWT + OAuth 2.0 Social):** Disene un sistema de autenticacion local con tokens Bearer JWT firmados con `HS256`, complementado con endpoints para login social con Google y GitHub.
* **Maquina de Estados Idempotente y Robusta:** Valide estrictamente las transiciones de pedidos (`pendiente` -> `en_camino` -> `entregado` / `cancelado`), impidiendo mutaciones sobre estados finales y sellando marcas de tiempo de auditoria (`fecha_asignacion`, `fecha_entrega`).
* **Conciliacion Temporal Automatica (TTL):**
  - **Regla de 30 Minutos:** Desvincula al conductor si no acepta el pedido en media hora, liberando la orden a bolsa abierta.
  - **Regla de 2 Horas:** Cancela automaticamente pedidos desatendidos tras 120 minutos.
* **Modelo Financiero de Costos y Delimitacion Geoespacial:**
  - Costo operativo: 10% para Bicicletas y 15% para Motos Electricas.
  - Analisis de datos semilla que demostro que la zona denominada "Chapinero" pertenecia geograficamente a la zona Nororiente de Medellin (Manrique/Aranjuez), corrigiendo las coordenadas para el Valle de Aburra.

### 2.2. Justificacion (¿Por que se hizo asi?)
* **Rendimiento Asincrono:** FastAPI proporciona alta velocidad de respuesta y concurrencia nativa en Python 3.13 con validacion automatica de tipos mediante Pydantic v2.
* **Integridad de Datos:** Encapsular las reglas de transicion en la capa de servicio previene estados inconsistentes o condiciones de carrera durante los despachos concurrentes.

### 2.3. Limitaciones Encontradas y Solucionadas
* **Restriccion de Memoria en Servidor (1GB RAM en VPS):** La ejecucion simultanea de multiples contenedores en un servidor de 1GB genero problemas de saturacion de memoria (OOM). Se optimizo reduciendo los workers de Uvicorn a 1 proceso eficiente, ajustando buffers de Nginx y reubicando el orquestador de datos a un entorno local conectado remotamente.

### 2.4. Oportunidades de Mejora
* **Capa de Cache con Redis:** Implementar Redis para almacenar en cache las consultas de catalogos y perfiles frecuentes, reduciendo la carga de lectura sobre PostgreSQL.
* **Extension Geoespacial PostGIS:** Migrar los campos de latitud/longitud a tipos geometricos nativos de PostGIS (`GEOMETRY(Point, 4326)`) para habilitar calculos de distancias euclidianas y poligonos de geocercas en tiempo real.
* **Rate Limiting Distribuido:** Agregar control de peticiones por IP/Token con Redis para proteger la API contra ataques de denegacion de servicio (DDoS).

---

## 3. Modulo 3: Pipeline de Datos e Ingenieria ETL (Apache Airflow 3.0 + DWH Medallon)

### 3.1. Decisiones Tecnicas Tomadas
* **Arquitectura Medallon (Bronze -> Silver -> Gold):**
  - **Bronze:** Ingesta cruda de tablas OLTP y de la API externa RandomUser, inyectando metadatos de auditoria (`_extracted_at`, `_source`).
  - **Silver:** Limpieza de tipos, conversion a UTC, manejo estricto de nulos, calculo de SLA de entrega en minutos y enriquecimiento demografico (edad, genero, grupo etario: 18-25, 26-35, 36-50, 50+, avatar, telefono).
  - **Gold:** Construccion del Modelo Dimensional Kimball (Star Schema) con claves subrogadas (`*_sk`) y exportacion automatica de `reporte_pedidos.csv`.
* **Proteccion de Datos Semilla:** El enriquecimiento demografico protege absolutamente las zonas operativas de Medellin y los correos transaccionales originales, enriqueciendo unicamente variables de perfil.
* **Despliegue Hibrido Local-Remoto:** Configuracion del stack de Airflow 3.0 para correr localmente mientras consume y escribe directamente sobre las bases de datos de la VPS (`100.60.229.203`).

### 3.2. Justificacion (¿Por que se hizo asi?)
* **Trazabilidad y Calidad:** El patron Medallon permite reprocesar capas superiores ante cambios en reglas de negocio sin necesidad de re-extraer desde la fuente transaccional.
* **Eficiencia de Servidor:** Evita agotar la memoria RAM del servidor de produccion, manteniendo el orquestador liviano y aislado.

### 3.3. Limitaciones Encontradas y Solucionadas
* **Cambios de API en Airflow 3.0:** Se corrigieron parametros deprecados como `schedule_interval` por `schedule` y se solventaron incompatibilidades de Pydantic en el API Server mediante el control de dependencias en `requirements.txt`.
* **Resolucion de Migraciones Huerfanas de Alembic:** Se implemento un script de inicializacion limpia (`reset_airflow_db.py`) para sanear la base de metadatos ante cambios de version.

### 3.4. Oportunidades de Mejora
* **Validacion Automatica con Great Expectations / Soda:** Incorporar pruebas automatizadas de calidad de datos (Data Quality Checks) entre la capa Bronze y Silver para alertar valores atipicos o nulos antes de poblar Gold.
* **Notificaciones de Pipeline:** Configurar callbacks de fallo/exito que envien alertas automaticas a canales de Discord, Slack o Telegram.
* **Carga Incremental con CDC (Change Data Capture):** Migrar de extraccion por ventana a captura de cambios en tiempo real basada en logs de transaccion con Debezium.

---

## 4. Modulo 4: Analitica y Visualizacion Ejecutiva (Power BI - PBIP / TMDL)

### 4.1. Decisiones Tecnicas Tomadas
* **Formato Moderno PBIP (Fabric PBIR + TMDL):** El proyecto analitico se creo en formato abierto basado en texto (TMDL para el modelo semantico y JSON para los reportes), permitiendo control de versiones en Git y edicion modular.
* **Estructura de Dos Tableros Ejecutivos:**
  - **Tablero 1 (Resumen Ejecutivo):** Vision macro para direccion general con metricas de facturacion total, margen bruto operativo, porcentaje de rentabilidad, ticket promedio y distribucion por zonas y periodos.
  - **Tablero 2 (Operaciones y Repartidores):** Monitoreo del SLA de entrega en minutos por zona, analisis comparativo de eficiencia por tipo de transporte (bicicleta vs moto electrica) y balance de estados de ordenes.
* **Navegacion Nativa en Power Query (M):** Uso de claves compuestas exactas `Origen{[Schema="gold", Item="nombre_tabla"]}[Data]` para garantizar plegado de consultas (query folding) y eliminar popups de confirmacion de seguridad nativa.
* **Medidas DAX Optimizadas:** Implementacion de medidas explicitas (`Margen Bruto Total`, `Margen %`, `Tiempo Promedio Entrega (min)`, `Pedidos Fin de Semana`, etc.) para agilizar el calculo en memoria.

### 4.2. Justificacion (¿Por que se hizo asi?)
* **Soporte de Git y Colaboracion:** Los formatos binarios tradicionales (`.pbix`) dificultan el trabajo en equipo; PBIP permite rastrear cambios de columnas y medidas linea por linea.
* **Consumo Eficiente de Datos:** Conectar directamente a las tablas de la capa `gold` del Data Warehouse asegura que los usuarios de negocio visualicen datos limpios, consistentes y desnormalizados para alta velocidad de agregacion.

### 4.3. Limitaciones Encontradas y Solucionadas
* **Advertencias de Consultas SQL Nativas:** Power BI solicitaba aprobacion manual repetitiva para cada consulta SQL directa. Se soluciono migrando el codigo M a la navegacion por esquema de Power Query.
* **Ambiguedad de Filas en la Conexion:** Se resolvio pasando la clave compuesta unívoca `[Schema="gold", Item="..."]` en lugar de una referencia generica al esquema.

### 4.4. Oportunidades de Mejora
* **Publicacion en Power BI Service con Gateway:** Configurar una puerta de enlace de datos (On-Premises Data Gateway) para programar refrescos automaticos tras la finalizacion del DAG diario de Airflow.
* **Row-Level Security (RLS):** Implementar seguridad a nivel de fila para que los lideres de cada zona geografica (Norte, Sur, etc.) visualicen unicamente los datos correspondientes a su jurisdiccion.
* **Diseno Responsive para Dispositivos Moviles:** Crear vistas personalizadas para la aplicacion movil de Power BI en orientacion vertical.
