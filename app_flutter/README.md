# EcoDelivery Mobile App - Flutter (Clean Architecture / DDD)

Aplicación móvil oficial para **EcoDelivery S.A.S.** desarrollada con **Flutter**, estructurada bajo los principios de **Clean Architecture y Domain-Driven Design (DDD)** organizado por **Vertical Slices (Features)**.

---

## 🏛️ Arquitectura del Proyecto (Clean Architecture / DDD por Features)

Cada funcionalidad está encapsulada en su propia carpeta con aislamiento estricto de capas:

```text
lib/
├── core/                                # Componentes compartidos y transversales
│   ├── constants/                       # URLs y endpoints
│   ├── errors/                          # Excepciones y Failures de dominio
│   ├── network/                         # Cliente HTTP con manejo de tokens Bearer
│   ├── theme/                           # Diseño ecológico moderno (Material 3)
│   └── utils/                           # Formateadores de fecha y moneda COP
│
├── features/
│   ├── auth/                            # 🔐 Feature 1: Autenticación y OAuth Completo
│   │   ├── domain/                      # Entidades y contratos de repositorio
│   │   ├── data/                        # Modelos, datasources (remoto/local) y repos
│   │   └── presentation/                # Controladores, LoginScreen y botones OAuth
│   │
│   ├── users/                           # 👤 Feature 2: Gestión de Perfiles & Métricas
│   │   ├── domain/                      # Entidades UserProfile y UserMetrics
│   │   ├── data/                        # Modelos y consumo de /users/me y /me/resumen
│   │   └── presentation/                # ProfileScreen y UserStatsCard
│   │
│   └── pedidos/                         # 📦 Feature 3: Operación de Pedidos (Requerida)
│       ├── domain/                      # Entidad Pedido y reglas de transición
│       ├── data/                        # Consumo de /pedidos/ (GET, POST, PATCH)
│       └── presentation/                # Lista con filtros, detalle y creación
│
└── main.dart                            # MultiProvider y configuración global
```

---

## 📱 Pantallas y Funcionalidades

1. **Lista de Pedidos (`PedidosListScreen`):**
   * Visualización reactiva con **color por estado** (Ámbar: Pendiente, Azul: En Camino, Verde: Entregado, Rojo: Cancelado).
   * **Filtros combinados:** Por zona (`Norte`, `Sur`, `Centro`, `Occidente`, `Chapinero`) y por estado.
   * **Pull-to-refresh** para sincronización en vivo con la API.
2. **Detalle de Pedido (`PedidoDetailScreen`):**
   * Información completa del cliente, repartidor, método de pago, vehículo y línea de tiempo.
   * **Botón dinámico de avance de estado:** Respeta la máquina de estados (`Aceptar y Despachar` ➔ `Marcar como Entregado`).
3. **Crear Pedido (`CreatePedidoScreen`):**
   * Formulario reactivo con validación de campos obligatorios, zonas y tipo de transporte ecológico.
4. **Login & OAuth (`LoginScreen`):**
   * Login con JWT Bearer y accesos rápidos de prueba (Cliente, Admin, Repartidor).
   * Botones de Social OAuth listos para Google y GitHub.
5. **Perfil & Métricas (`ProfileScreen`):**
   * Resumen de pedidos completados, montos acumulados y roles.

---

## 🚀 Cómo Ejecutar la Aplicación

1. **Instalar Dependencias:**
   ```bash
   cd app_flutter
   flutter pub get
   ```

2. **Ejecutar en tu dispositivo o navegador:**
   ```bash
   # En navegador Web (Rápido)
   flutter run -d chrome

   # En Emulador Android o Dispositivo Físico
   flutter run
   ```

3. **Generar APK para instalación:**
   ```bash
   flutter build apk --release
   ```
