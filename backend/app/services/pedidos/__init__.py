from .cost_calculator import CostCalculator
from .dispatcher_service import DispatcherService
from .geo_service import GeoService, ZONE_COORDINATES
from .pedido_analytics import PedidoAnalytics
from .pedido_creator import PedidoCreator
from .pedido_reader import PedidoReader, build_pedido_response
from .pedido_state_machine import PedidoStateMachine

# Atajos funcionales para compatibilidad transparente
create_pedido = PedidoCreator.create_pedido
get_pedidos = PedidoReader.get_pedidos
get_pedido_by_id = PedidoReader.get_pedido_by_id
update_pedido_estado = PedidoStateMachine.update_pedido_estado
get_estadisticas_generales = PedidoAnalytics.get_estadisticas_generales

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
