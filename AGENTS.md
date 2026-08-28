# Directrices del Proyecto y Contexto Operativo para Agentes IA

Este archivo define el contexto fundamental, decisiones arquitectónicas, reglas de negocio y restricciones operativas del proyecto **EcoDelivery Assessment**:

---

## 1. Regla Mandatoria sobre Git
* **El usuario es el único responsable de ejecutar `git add`, `git commit` y `git push`.**
* Ningún agente debe ejecutar comandos de confirmación o subida a Git en la terminal bajo ninguna circunstancia.

---

## 2. Infraestructura y Entorno
* **VPS AWS Lightsail:** `100.60.229.203` (Dominio activo: `http://ecodelivery.geisler.coderhivex.com`).
* **Base de Datos:** PostgreSQL en contenedor Docker (`ecodelivery_db`, user: `ecodelivery_user`, pass: `ecodelivery_secure_pass`).
* **Documentación Completa:** Consultar [`docs/CONTEXTO_PROYECTO.md`](file:///c:/Users/ASUS/Desktop/RIWI/complementos/assessment/docs/CONTEXTO_PROYECTO.md), [`docs/DOCUMENTACION_FEATURES.md`](file:///c:/Users/ASUS/Desktop/RIWI/complementos/assessment/docs/DOCUMENTACION_FEATURES.md) y [`docs/LOGICA_NEGOCIO_Y_DECISIONES.md`](file:///c:/Users/ASUS/Desktop/RIWI/complementos/assessment/docs/LOGICA_NEGOCIO_Y_DECISIONES.md).

---

## 3. Estado de los Módulos
* **Módulo 1 (Flutter Mobile):** Finalizado al 100% (Clean DDD, Login/Register, Vistas especializadas por Rol: Cliente, Repartidor, Admin).
* **Módulo 2 (Backend FastAPI):** Finalizado al 100% (OAuth2 JWT, Argon2id, RBAC, Servicios modulares, Tests E2E 10/10 pasados).
* **Módulo 3 (Airflow Pipeline):** Finalizado al 100% (Medallion Architecture Bronze/Silver/Gold, Enriquecimiento RandomUser, Star Schema y reporte CSV).
* **Módulo 4 (Power BI Dashboard):** Pendiente (`powerbi/`).

