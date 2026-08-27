"""
Fachada de compatibilidad para el servicio de pedidos.
Toda la lógica modular reside en app.services.pedidos.
"""

from app.services.pedidos import (
    CostCalculator,
    DispatcherService,
    GeoService,
    PedidoAnalytics,
    PedidoCreator,
    PedidoReader,
    PedidoStateMachine,
    ZONE_COORDINATES,
    build_pedido_response,
    create_pedido,
    get_estadisticas_generales,
    get_pedido_by_id,
    get_pedidos,
    update_pedido_estado,
)

__all__ = [
    "CostCalculator",
    "DispatcherService",
    "GeoService",
    "ZONE_COORDINATES",
    "PedidoAnalytics",
    "PedidoCreator",
    "PedidoReader",
    "PedidoStateMachine",
    "build_pedido_response",
    "create_pedido",
    "get_pedidos",
    "get_pedido_by_id",
    "update_pedido_estado",
    "get_estadisticas_generales",
]
