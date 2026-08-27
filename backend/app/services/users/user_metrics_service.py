from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pedido import EstadoPedido, Pedido
from app.models.user import User, UserRole
from app.schemas.user import UserResumen


class UserMetricsService:
    @staticmethod
    def get_user_resumen(db: Session, user: User) -> UserResumen:
        """Calcula estadísticas agregadas del usuario cliente o repartidor."""
        if user.role == UserRole.CLIENTE:
            stmt = select(Pedido).where(Pedido.cliente_id == user.id)
        elif user.role == UserRole.REPARTIDOR:
            stmt = select(Pedido).where(Pedido.repartidor_id == user.id)
        else:
            stmt = select(Pedido)

        pedidos = list(db.scalars(stmt).all())

        total = len(pedidos)
        monto = sum(p.monto for p in pedidos)
        pendientes = sum(1 for p in pedidos if p.estado == EstadoPedido.PENDIENTE)
        en_camino = sum(1 for p in pedidos if p.estado == EstadoPedido.EN_CAMINO)
        entregados = sum(1 for p in pedidos if p.estado == EstadoPedido.ENTREGADO)
        cancelados = sum(1 for p in pedidos if p.estado == EstadoPedido.CANCELADO)

        return UserResumen(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            total_pedidos=total,
            monto_total=round(monto, 2),
            pedidos_pendientes=pendientes,
            pedidos_en_camino=en_camino,
            pedidos_entregados=entregados,
            pedidos_cancelados=cancelados,
        )
