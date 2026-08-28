# EcoDelivery Mobile App - Flutter (Clean Architecture / DDD)

Aplicacion movil oficial para **EcoDelivery S.A.S.** desarrollada con **Flutter**, estructurada bajo los principios de **Clean Architecture y Domain-Driven Design (DDD)** organizado por **Vertical Slices (Features)**.

---

## 1. Arquitectura del Proyecto (Clean Architecture / DDD por Features)

Cada funcionalidad esta encapsulada en su propia carpeta con aislamiento estricto de capas:

```text
lib/
├── core/                                # Componentes compartidos y transversales
│   ├── constants/                       # URLs y endpoints
│   ├── errors/                          # Excepciones y Failures de dominio
│   ├── network/                         # Cliente HTTP con manejo de tokens Bearer
│   ├── theme/                           # Diseno ecologico moderno (Material 3)
│   └── utils/                           # Formateadores de fecha y moneda COP
│
├── features/
│   ├── auth/                            # Feature 1: Autenticacion y OAuth Completo
│   │   ├── domain/                      # Entidades y contratos de repositorio
│   │   ├── data/                        # Modelos, datasources (remoto/local) y repos
│   │   └── presentation/                # Controladores, LoginScreen y botones OAuth
│   │
│   ├── users/                           # Feature 2: Gestion de Perfiles y Metricas
│   │   ├── domain/                      # Entidades UserProfile y UserMetrics
│   │   ├── data/                        # Modelos y consumo de /users/me y /me/resumen
│   │   └── presentation/                # ProfileScreen y UserStatsCard
│   │
│   └── pedidos/                         # Feature 3: Operacion de Pedidos (Requerida)
│       ├── domain/                      # Entidad Pedido y reglas de transicion
│       ├── data/                        # Consumo de /pedidos/ (GET, POST, PATCH)
│       └── presentation/                # Lista con filtros, detalle y creacion
│
└── main.dart                            # MultiProvider y configuracion global
```

---

## 2. Pantallas y Funcionalidades

1. **Lista de Pedidos (`PedidosListScreen`):**
   * Visualizacion reactiva con indicador de color por estado (Pendiente, En Camino, Entregado, Cancelado).
   * **Filtros combinados:** Por zona (`Norte`, `Sur`, `Centro`, `Occidente`, `Chapinero`) y por estado.
   * **Pull-to-refresh** para sincronizacion en vivo con la API.
2. **Detalle de Pedido (`PedidoDetailScreen`):**
   * Informacion completa del cliente, repartidor, metodo de pago, vehiculo y linea de tiempo.
   * **Boton dinamico de avance de estado:** Respeta la maquina de estados (`Aceptar y Despachar` -> `Marcar como Entregado`).
3. **Crear Pedido (`CreatePedidoScreen`):**
   * Formulario reactivo con validacion de campos obligatorios, zonas y tipo de transporte ecologico.
4. **Login y OAuth (`LoginScreen`):**
   * Login con JWT Bearer y accesos rapidos de prueba (Cliente, Admin, Repartidor).
   * Botones de Social OAuth listos para Google y GitHub.
5. **Perfil y Metricas (`ProfileScreen`):**
   * Resumen de pedidos completados, montos acumulados y roles.

---

## 3. Como Ejecutar la Aplicacion

1. **Instalar Dependencias:**
   ```bash
   cd app_flutter
   flutter pub get
   ```

2. **Ejecutar en tu dispositivo o navegador:**
   ```bash
   # En navegador Web
   flutter run -d chrome

   # En Emulador Android o Dispositivo Fisico
   flutter run
   ```

3. **Generar APK para instalacion:**
   ```bash
   flutter build apk --release
   ```
