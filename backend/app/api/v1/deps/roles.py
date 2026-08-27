from fastapi import Depends, HTTPException, status

from app.api.v1.deps.auth import get_current_user
from app.models.user import User, UserRole


class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos insuficientes. Requiere uno de los roles: {[r.value for r in self.allowed_roles]}",
            )
        return current_user


# Inyectores de dependencias por rol
require_admin = RoleChecker([UserRole.ADMIN])
require_repartidor_or_admin = RoleChecker([UserRole.ADMIN, UserRole.REPARTIDOR])
require_cliente_or_admin = RoleChecker([UserRole.ADMIN, UserRole.CLIENTE])
