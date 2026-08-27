from datetime import UTC, datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.pedido import EstadoPedido, Pedido
from app.models.user import User
from app.schemas.pedido import PedidoCreate, PedidoResponse

from .cost_calculator import CostCalculator
from .dispatcher_service import DispatcherService
from .geo_service import GeoService
from .pedido_reader import build_pedido_response


class PedidoCreator:
    @staticmethod
    def create_pedido(
        db: Session,
        pedido_in: PedidoCreate,
        cliente_id_autenticado: UUID | None = None,
    ) -> PedidoResponse:
        """
        Crea un nuevo pedido con estado inicial PENDIENTE aplicando:
        1. Validación de cliente existente.
        2. Auto-cálculo de coordenadas GPS según la zona.
        3. Auto-cálculo de costo operativo (0.10 bicicleta, 0.15 moto).
        4. Sorteo y asignación de repartidor activo.
        """
        final_cliente_id = pedido_in.cliente_id or cliente_id_autenticado
        if not final_cliente_id:
            raise ValueError("Se requiere el cliente_id para registrar el pedido.")

        # Validar que el cliente exista
        cliente = db.get(User, final_cliente_id)
        if not cliente:
            raise ValueError("El cliente especificado no existe.")

        # 1. Resolver vehículo por defecto si no se indica
        tipo_vehiculo_final = pedido_in.tipo_vehiculo or "bicicleta"

        # 2. Calcular costo de operación
        if pedido_in.costo_operacion is not None:
            costo_final = pedido_in.costo_operacion
        else:
            costo_final = CostCalculator.calculate_operational_cost(
                monto=pedido_in.monto,
                tipo_vehiculo=tipo_vehiculo_final,
            )

        # 3. Calcular coordenadas GPS según la zona
        if pedido_in.latitud is not None and pedido_in.longitud is not None:
            lat_final, lon_final = pedido_in.latitud, pedido_in.longitud
        else:
            lat_final, lon_final = GeoService.get_zone_coordinates(pedido_in.zona, jitter=True)

        # 4. Sorteo y asignación automática de repartidor
        final_repartidor_id = pedido_in.repartidor_id
        if not final_repartidor_id:
            final_repartidor_id = DispatcherService.auto_assign_repartidor(
                db=db,
                zona=pedido_in.zona,
            )

        db_pedido = Pedido(
            cliente_id=final_cliente_id,
            repartidor_id=final_repartidor_id,
            zona=pedido_in.zona,
            estado=EstadoPedido.PENDIENTE,
            metodo_pago=pedido_in.metodo_pago,
            monto=pedido_in.monto,
            tipo_vehiculo=tipo_vehiculo_final,
            costo_operacion=costo_final,
            latitud=lat_final,
            longitud=lon_final,
            fecha_creacion=datetime.now(UTC),
        )
        db.add(db_pedido)
        db.commit()
        db.refresh(db_pedido)

        # Recargar con relaciones
        stmt = (
            select(Pedido)
            .options(joinedload(Pedido.cliente), joinedload(Pedido.repartidor))
            .where(Pedido.id_pedido == db_pedido.id_pedido)
        )
        pedido_loaded = db.scalar(stmt)
        return build_pedido_response(pedido_loaded or db_pedido)
