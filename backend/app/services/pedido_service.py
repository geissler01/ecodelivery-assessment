from datetime import UTC, datetime
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.pedido import EstadoPedido, Pedido
from app.models.user import User
from app.schemas.pedido import PedidoCreate, PedidoEstadisticas, PedidoResponse, PedidoUpdateEstado


def _build_pedido_response(pedido: Pedido) -> PedidoResponse:
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


def create_pedido(
    db: Session,
    pedido_in: PedidoCreate,
    cliente_id_autenticado: UUID | None = None,
) -> PedidoResponse:
    """Crea un nuevo pedido con estado inicial PENDIENTE."""
    final_cliente_id = pedido_in.cliente_id or cliente_id_autenticado
    if not final_cliente_id:
        raise ValueError("Se requiere el cliente_id para registrar el pedido.")

    # Validar que el cliente exista
    cliente = db.get(User, final_cliente_id)
    if not cliente:
        raise ValueError("El cliente especificado no existe.")

    db_pedido = Pedido(
        cliente_id=final_cliente_id,
        repartidor_id=pedido_in.repartidor_id,
        zona=pedido_in.zona,
        estado=EstadoPedido.PENDIENTE,
        metodo_pago=pedido_in.metodo_pago,
        monto=pedido_in.monto,
        tipo_vehiculo=pedido_in.tipo_vehiculo,
        costo_operacion=pedido_in.costo_operacion,
        latitud=pedido_in.latitud,
        longitud=pedido_in.longitud,
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
    return _build_pedido_response(pedido_loaded or db_pedido)


def get_pedidos(
    db: Session,
    estado: EstadoPedido | None = None,
    zona: str | None = None,
    cliente_id: UUID | None = None,
    repartidor_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[PedidoResponse]:
    """Lista pedidos con soporte de filtros por estado, zona, cliente y repartidor."""
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
    return [_build_pedido_response(p) for p in pedidos]


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
    return _build_pedido_response(pedido)


def update_pedido_estado(
    db: Session,
    id_pedido: UUID,
    update_in: PedidoUpdateEstado,
) -> PedidoResponse:
    """
    Actualiza el estado de un pedido validando transiciones lógicas de la máquina de estados.
    Transiciones válidas:
      - PENDIENTE -> EN_CAMINO
      - PENDIENTE -> CANCELADO
      - EN_CAMINO -> ENTREGADO
      - EN_CAMINO -> CANCELADO
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

    # Validar transiciones permitidas
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

    return _build_pedido_response(pedido)


def get_estadisticas_generales(db: Session) -> PedidoEstadisticas:
    """Calcula las métricas generales de pedidos para analítica."""
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
