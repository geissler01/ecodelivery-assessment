from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.pedido import Pedido


class UserRole(str, Enum):
    CLIENTE = "cliente"
    REPARTIDOR = "repartidor"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Nullable para usuarios OAuth
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
        default=UserRole.CLIENTE,
        nullable=False,
    )
    # Campos para caracterización y normalización de usuarios
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zona_principal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tipo_vehiculo_predilecto: Mapped[str | None] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relaciones ORM
    pedidos_como_cliente: Mapped[List["Pedido"]] = relationship(
        "Pedido",
        foreign_keys="[Pedido.cliente_id]",
        back_populates="cliente",
        cascade="all, delete-orphan",
    )
    pedidos_como_repartidor: Mapped[List["Pedido"]] = relationship(
        "Pedido",
        foreign_keys="[Pedido.repartidor_id]",
        back_populates="repartidor",
    )
