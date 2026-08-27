from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps.auth import get_optional_current_user
from app.db.session import get_db
from app.models.pedido import EstadoPedido
from app.models.user import User
from app.schemas.pedido import (
    PedidoCreate,
    PedidoEstadisticas,
    PedidoResponse,
    PedidoUpdateEstado,
)
from app.services.pedido_service import (
    create_pedido,
    get_estadisticas_generales,
    get_pedido_by_id,
    get_pedidos,
    update_pedido_estado,
)

router = APIRouter()


@router.post(
    "/",
    response_model=PedidoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear pedido (POST /pedidos)",
)
def create_new_pedido(
    pedido_in: PedidoCreate,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_id = current_user.id if current_user else None
        return create_pedido(db=db, pedido_in=pedido_in, cliente_id_autenticado=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=list[PedidoResponse],
    summary="Listar pedidos con filtros (GET /pedidos?estado=&zona=)",
)
def list_pedidos(
    estado: EstadoPedido | None = Query(default=None, description="Filtrar por estado"),
    zona: str | None = Query(default=None, description="Filtrar por zona: Norte, Sur, Centro, Occidente, Chapinero"),
    cliente_id: UUID | None = Query(default=None, description="Filtrar por cliente"),
    repartidor_id: UUID | None = Query(default=None, description="Filtrar por repartidor"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_pedidos(
        db=db,
        estado=estado,
        zona=zona,
        cliente_id=cliente_id,
        repartidor_id=repartidor_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/estadisticas/resumen",
    response_model=PedidoEstadisticas,
    summary="Obtener métricas y KPIs de pedidos para análisis y dashboards",
)
def get_stats_resumen(
    db: Session = Depends(get_db),
):
    return get_estadisticas_generales(db=db)


@router.get(
    "/{id_pedido}",
    response_model=PedidoResponse,
    summary="Detalle de un pedido (GET /pedidos/:id)",
)
def get_pedido_detail(
    id_pedido: UUID,
    db: Session = Depends(get_db),
):
    pedido = get_pedido_by_id(db=db, id_pedido=id_pedido)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado.",
        )
    return pedido


@router.patch(
    "/{id_pedido}/estado",
    response_model=PedidoResponse,
    summary="Actualizar estado del pedido (PATCH /pedidos/:id/estado)",
)
def update_pedido_status(
    id_pedido: UUID,
    update_in: PedidoUpdateEstado,
    db: Session = Depends(get_db),
):
    try:
        return update_pedido_estado(db=db, id_pedido=id_pedido, update_in=update_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
