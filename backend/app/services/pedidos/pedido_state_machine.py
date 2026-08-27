from datetime import UTC, datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.pedido import EstadoPedido, Pedido
from app.models.user import User, UserRole
from app.schemas.pedido import PedidoResponse, PedidoUpdateEstado

from .pedido_reader import build_pedido_response


class PedidoStateMachine:
    @staticmethod
    def update_pedido_estado(
        db: Session,
        id_pedido: UUID,
        update_in: PedidoUpdateEstado,
        user_solicitante: User | None = None,
    ) -> PedidoResponse:
        """
        Actualiza el estado de un pedido validando transiciones lógicas de la máquina de estados
        y permisos de rol:
          - Cliente: Solo puede cancelar si el pedido está 'pendiente'.
          - Repartidor: PENDIENTE -> EN_CAMINO -> ENTREGADO.
        """
        stmt = (
            select(Pedido)
            .options(joinedload(Pedido.cliente), joinedload(Pedido.repartidor))
            .where(Pedido.id_pedido == id_pedido)
        )
        pedido = db.scalar(stmt)
        if not pedido:
            raise ValueError("Pedido no encontrado.")

        estado_actual = pedido.estado
        nuevo_estado = update_in.nuevo_estado

        # Control de rol si el usuario está autenticado
        if user_solicitante:
            if user_solicitante.role == UserRole.CLIENTE:
                if nuevo_estado != EstadoPedido.CANCELADO:
                    raise ValueError("Los clientes solo tienen autorización para cancelar pedidos pendientes.")
                if estado_actual != EstadoPedido.PENDIENTE:
                    raise ValueError("No es posible cancelar un pedido que ya está en camino o entregado.")
            elif user_solicitante.role == UserRole.REPARTIDOR:
                if estado_actual == EstadoPedido.ENTREGADO:
                    raise ValueError("Un pedido entregado no puede ser modificado.")

        # Validar transiciones permitidas generales
        if estado_actual in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO] and estado_actual != nuevo_estado:
            raise ValueError(
                f"No se puede cambiar el estado de un pedido que ya está '{estado_actual.value}'."
            )

        if estado_actual == EstadoPedido.PENDIENTE:
            if nuevo_estado not in [EstadoPedido.PENDIENTE, EstadoPedido.EN_CAMINO, EstadoPedido.CANCELADO]:
                raise ValueError(
                    "Un pedido pendiente solo puede avanzar a 'en_camino' o ser 'cancelado'."
                )

        if estado_actual == EstadoPedido.EN_CAMINO:
            if nuevo_estado not in [EstadoPedido.EN_CAMINO, EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
                raise ValueError(
                    "Un pedido en camino solo puede pasar a 'entregado' o ser 'cancelado'."
                )

        # Aplicar cambios y auto-generar fechas
        pedido.estado = nuevo_estado

        if nuevo_estado == EstadoPedido.EN_CAMINO and not pedido.fecha_asignacion:
            pedido.fecha_asignacion = datetime.now(UTC)

        if nuevo_estado == EstadoPedido.ENTREGADO and not pedido.fecha_entrega:
            pedido.fecha_entrega = datetime.now(UTC)

        if update_in.repartidor_id:
            pedido.repartidor_id = update_in.repartidor_id
        if update_in.tipo_vehiculo:
            pedido.tipo_vehiculo = update_in.tipo_vehiculo

        db.add(pedido)
        db.commit()
        db.refresh(pedido)

        return build_pedido_response(pedido)
