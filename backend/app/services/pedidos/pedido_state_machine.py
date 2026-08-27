from datetime import UTC, datetime, timedelta
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.pedido import EstadoPedido, Pedido
from app.models.user import User, UserRole
from app.schemas.pedido import PedidoResponse, PedidoUpdateEstado

from .pedido_reader import build_pedido_response


class PedidoStateMachine:
    @staticmethod
    def reconcile_stale_orders(db: Session) -> dict[str, int]:
        """
        Aplica las reglas de negocio de expiración y liberación de pedidos pendientes:
        1. Regla 2h (Auto-Cancelación): Si un pedido lleva > 2 horas en estado pendiente, pasa a CANCELADO.
        2. Regla 30m (Liberación al Pool): Si un pedido lleva > 30 minutos pendiente con repartidor asignado,
           se libera (repartidor_id = None) para que cualquier conductor disponible de la ciudad lo tome.
        """
        now = datetime.now(UTC)
        limit_30m = now - timedelta(minutes=30)
        limit_2h = now - timedelta(hours=2)

        # 1. Auto-cancelar pedidos pendientes vencidos (> 2 horas)
        stmt_cancel = select(Pedido).where(
            Pedido.estado == EstadoPedido.PENDIENTE,
            Pedido.fecha_creacion <= limit_2h,
        )
        pedidos_to_cancel = list(db.scalars(stmt_cancel).all())
        for p in pedidos_to_cancel:
            p.estado = EstadoPedido.CANCELADO

        # 2. Liberar pedidos pendientes sin aceptar a los 30 minutos (que no hayan sido cancelados)
        stmt_release = select(Pedido).where(
            Pedido.estado == EstadoPedido.PENDIENTE,
            Pedido.repartidor_id.isnot(None),
            Pedido.fecha_creacion <= limit_30m,
        )
        pedidos_to_release = list(db.scalars(stmt_release).all())
        for p in pedidos_to_release:
            p.repartidor_id = None

        if pedidos_to_cancel or pedidos_to_release:
            db.commit()

        return {
            "cancelados_por_timeout": len(pedidos_to_cancel),
            "liberados_a_pool": len(pedidos_to_release),
        }

    @staticmethod
    def update_pedido_estado(
        db: Session,
        id_pedido: UUID,
        update_in: PedidoUpdateEstado,
        user_solicitante: User | None = None,
    ) -> PedidoResponse:
        """
        Actualiza el estado de un pedido validando transiciones lógicas de la máquina de estados
        y reglas de negocio por rol:
          - Cliente: Solo puede cancelar si el pedido está 'pendiente'.
          - Repartidor:
              * Al tomar un pedido ('pendiente' -> 'en_camino'), se auto-asigna la orden.
              * Al entregar ('en_camino' -> 'entregado'), finaliza la orden y registra fecha_entrega.
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

        # Control de rol y permisos
        if user_solicitante:
            if user_solicitante.role == UserRole.CLIENTE:
                if nuevo_estado != EstadoPedido.CANCELADO:
                    raise ValueError("Los clientes solo tienen autorización para cancelar pedidos pendientes.")
                if estado_actual != EstadoPedido.PENDIENTE:
                    raise ValueError("No es posible cancelar un pedido que ya está en camino o entregado.")
            elif user_solicitante.role == UserRole.REPARTIDOR:
                if estado_actual == EstadoPedido.ENTREGADO:
                    raise ValueError("Un pedido entregado no puede ser modificado.")
                # Si está en camino y ya tiene otro repartidor asignado distinto al solicitante
                if (
                    estado_actual == EstadoPedido.EN_CAMINO
                    and pedido.repartidor_id
                    and pedido.repartidor_id != user_solicitante.id
                ):
                    raise ValueError("Este pedido ya está siendo atendido por otro repartidor.")

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

        # Aplicar cambios y auto-generar fechas y asignación
        pedido.estado = nuevo_estado

        if nuevo_estado == EstadoPedido.EN_CAMINO:
            if not pedido.fecha_asignacion:
                pedido.fecha_asignacion = datetime.now(UTC)
            # Auto-asignación al repartidor que toma la orden
            if user_solicitante and user_solicitante.role == UserRole.REPARTIDOR:
                pedido.repartidor_id = user_solicitante.id
                if user_solicitante.tipo_vehiculo_predilecto and not pedido.tipo_vehiculo:
                    pedido.tipo_vehiculo = user_solicitante.tipo_vehiculo_predilecto

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
