from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pedido import EstadoPedido, Pedido
from app.schemas.pedido import PedidoEstadisticas


class PedidoAnalytics:
    @staticmethod
    def get_estadisticas_generales(db: Session) -> PedidoEstadisticas:
        """Calcula las métricas generales y KPIs de pedidos para análisis y tableros."""
        pedidos = list(db.scalars(select(Pedido)).all())
        total = len(pedidos)
        monto_total = sum(p.monto for p in pedidos)
        pendientes = sum(1 for p in pedidos if p.estado == EstadoPedido.PENDIENTE)
        en_camino = sum(1 for p in pedidos if p.estado == EstadoPedido.EN_CAMINO)
        entregados = sum(1 for p in pedidos if p.estado == EstadoPedido.ENTREGADO)
        cancelados = sum(1 for p in pedidos if p.estado == EstadoPedido.CANCELADO)

        tiempos = []
        for p in pedidos:
            if p.estado == EstadoPedido.ENTREGADO and p.fecha_entrega and p.fecha_creacion:
                minutos = (p.fecha_entrega - p.fecha_creacion).total_seconds() / 60.0
                if minutos > 0:
                    tiempos.append(minutos)

        tiempo_promedio = round(sum(tiempos) / len(tiempos), 2) if tiempos else None

        return PedidoEstadisticas(
            total_pedidos=total,
            pedidos_pendientes=pendientes,
            pedidos_en_camino=en_camino,
            pedidos_entregados=entregados,
            pedidos_cancelados=cancelados,
            ingresos_totales=round(monto_total, 2),
            tiempo_promedio_entrega_minutos=tiempo_promedio,
        )
