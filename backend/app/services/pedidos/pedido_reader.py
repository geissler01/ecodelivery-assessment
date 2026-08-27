from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.pedido import EstadoPedido, Pedido
from app.schemas.pedido import PedidoResponse


def build_pedido_response(pedido: Pedido) -> PedidoResponse:
    """Helper para transformar un modelo Pedido en un PedidoResponse con datos de cliente y repartidor."""
    return PedidoResponse(
        id_pedido=pedido.id_pedido,
        cliente_id=pedido.cliente_id,
        repartidor_id=pedido.repartidor_id,
        zona=pedido.zona,
        estado=pedido.estado,
        metodo_pago=pedido.metodo_pago,
        monto=pedido.monto,
        tipo_vehiculo=pedido.tipo_vehiculo,
        costo_operacion=pedido.costo_operacion,
        latitud=pedido.latitud,
        longitud=pedido.longitud,
        fecha_creacion=pedido.fecha_creacion,
        fecha_asignacion=pedido.fecha_asignacion,
        fecha_entrega=pedido.fecha_entrega,
        cliente_nombre=pedido.cliente.full_name if pedido.cliente else None,
        cliente_email=pedido.cliente.email if pedido.cliente else None,
        repartidor_nombre=pedido.repartidor.full_name if pedido.repartidor else None,
    )


class PedidoReader:
    @staticmethod
    def get_pedidos(
        db: Session,
        estado: EstadoPedido | None = None,
        zona: str | None = None,
        cliente_id: UUID | None = None,
        repartidor_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
        reconcile: bool = True,
    ) -> list[PedidoResponse]:
        """Lista pedidos con soporte de filtros por estado, zona, cliente y repartidor."""
        if reconcile:
            from .pedido_state_machine import PedidoStateMachine
            PedidoStateMachine.reconcile_stale_orders(db)

        stmt = (
            select(Pedido)
            .options(joinedload(Pedido.cliente), joinedload(Pedido.repartidor))
            .order_by(Pedido.fecha_creacion.desc())
        )

        if estado:
            stmt = stmt.where(Pedido.estado == estado)
        if zona:
            stmt = stmt.where(func.lower(Pedido.zona) == zona.lower().strip())
        if cliente_id:
            stmt = stmt.where(Pedido.cliente_id == cliente_id)
        if repartidor_id:
            stmt = stmt.where(Pedido.repartidor_id == repartidor_id)

        stmt = stmt.offset(skip).limit(limit)
        pedidos = list(db.scalars(stmt).unique().all())
        return [build_pedido_response(p) for p in pedidos]

    @staticmethod
    def get_pedido_by_id(db: Session, id_pedido: UUID) -> PedidoResponse | None:
        """Obtiene el detalle completo de un pedido por su UUID."""
        stmt = (
            select(Pedido)
            .options(joinedload(Pedido.cliente), joinedload(Pedido.repartidor))
            .where(Pedido.id_pedido == id_pedido)
        )
        pedido = db.scalar(stmt)
        if not pedido:
            return None
        return build_pedido_response(pedido)
