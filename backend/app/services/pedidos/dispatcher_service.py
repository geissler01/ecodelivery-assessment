import random
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


class DispatcherService:
    @staticmethod
    def auto_assign_repartidor(db: Session, zona: str) -> UUID | None:
        """
        Sortea y asigna automáticamente un repartidor activo:
        1. Prioriza repartidores activos cuya zona base coincide con la del pedido.
        2. Si no hay en esa zona, sortea entre todos los repartidores activos del sistema.
        """
        # 1. Buscar en la zona del pedido
        stmt_zona = select(User).where(
            User.role == UserRole.REPARTIDOR,
            User.is_active == True,
            func.lower(User.zona_principal) == zona.lower().strip(),
        )
        repartidores_zona = list(db.scalars(stmt_zona).all())

        if repartidores_zona:
            return random.choice(repartidores_zona).id

        # 2. Buscar en el pool general de repartidores activos
        stmt_all = select(User).where(
            User.role == UserRole.REPARTIDOR,
            User.is_active == True,
        )
        repartidores_all = list(db.scalars(stmt_all).all())
        if repartidores_all:
            return random.choice(repartidores_all).id

        return None
