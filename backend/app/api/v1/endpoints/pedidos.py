from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps.auth import get_current_user, get_optional_current_user
from app.api.v1.deps.roles import require_admin
from app.db.session import get_db
from app.models.pedido import EstadoPedido
from app.models.user import User, UserRole
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
    summary="Listar pedidos con control de acceso por rol",
)
def list_pedidos(
    estado: EstadoPedido | None = Query(default=None, description="Filtrar por estado"),
    zona: str | None = Query(default=None, description="Filtrar por zona"),
    cliente_id: UUID | None = Query(default=None, description="Filtrar por cliente"),
    repartidor_id: UUID | None = Query(default=None, description="Filtrar por repartidor"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Clientes no tienen acceso al catálogo global
    if current_user.role == UserRole.CLIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los clientes solo tienen autorización para consultar sus propios pedidos a través de /users/me/pedidos.",
        )

    # 2. Repartidores solo pueden consultar pedidos en estado PENDIENTE para tomar
    if current_user.role == UserRole.REPARTIDOR:
        estado = EstadoPedido.PENDIENTE

    # 3. Administradores tienen acceso total con cualquier filtro
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
    summary="Obtener estadísticas y KPIs generales del sistema (Admin / Airflow)",
)
def read_pedidos_estadisticas(
    db: Session = Depends(get_db),
):
    return get_estadisticas_generales(db=db)


@router.get(
    "/{id_pedido}",
    response_model=PedidoResponse,
    summary="Consultar detalle de un pedido por ID",
)
def get_pedido_detail(
    id_pedido: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pedido = get_pedido_by_id(db=db, id_pedido=id_pedido)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado.",
        )

    # Reglas de privacidad por rol
    if current_user.role == UserRole.CLIENTE and pedido.cliente_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar un pedido ajeno.",
        )

    return pedido


@router.patch(
    "/{id_pedido}/estado",
    response_model=PedidoResponse,
    summary="Actualizar estado del pedido (Máquina de estados)",
)
def change_pedido_estado(
    id_pedido: UUID,
    update_in: PedidoUpdateEstado,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    try:
        return update_pedido_estado(
            db=db,
            id_pedido=id_pedido,
            update_in=update_in,
            user_solicitante=current_user,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
