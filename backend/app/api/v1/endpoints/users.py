from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps.auth import get_current_user
from app.api.v1.deps.roles import require_admin
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.pedido import PedidoResponse
from app.schemas.user import UserAdminUpdate, UserResponse, UserResumen, UserUpdate
from app.services.pedido_service import get_pedidos
from app.services.user_service import (
    get_user_by_id,
    get_user_resumen,
    get_users,
    update_user,
)

router = APIRouter()


@router.get("/me", response_model=UserResponse, summary="Obtener perfil del usuario autenticado")
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse, summary="Actualizar perfil del usuario autenticado")
def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_user(db=db, db_user=current_user, user_in=user_in)


@router.get(
    "/me/pedidos",
    response_model=list[PedidoResponse],
    summary="Obtener pedidos asociados al usuario autenticado (como cliente o repartidor)",
)
def read_user_pedidos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    if current_user.role == UserRole.CLIENTE:
        return get_pedidos(db=db, cliente_id=current_user.id, skip=skip, limit=limit)
    elif current_user.role == UserRole.REPARTIDOR:
        return get_pedidos(db=db, repartidor_id=current_user.id, skip=skip, limit=limit)
    else:
        return get_pedidos(db=db, skip=skip, limit=limit)


@router.get(
    "/me/resumen",
    response_model=UserResumen,
    summary="Obtener métricas y resumen de actividad del usuario autenticado",
)
def read_user_resumen(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_resumen(db=db, user=current_user)


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Listar todos los usuarios del sistema (Requiere rol Admin)",
)
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    role: UserRole | None = Query(default=None, description="Filtrar por rol"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_users(db=db, skip=skip, limit=limit, role=role)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener detalle de un usuario por ID (Requiere rol Admin)",
)
def get_user_detail(
    user_id: UUID,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db=db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario o cambiar rol/estado (Requiere rol Admin)",
)
def admin_update_user(
    user_id: UUID,
    user_in: UserAdminUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db=db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return update_user(db=db, db_user=user, user_in=user_in)
