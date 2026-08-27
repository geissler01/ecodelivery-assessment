from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class EstadoPedido(str, Enum):
    PENDIENTE = "pendiente"
    EN_CAMINO = "en_camino"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"


class MetodoPago(str, Enum):
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    APP = "app"


class Zona(str, Enum):
    NORTE = "Norte"
    SUR = "Sur"
    CENTRO = "Centro"
    OCCIDENTE = "Occidente"
    CHAPINERO = "Chapinero"


class Pedido(Base):
    __tablename__ = "pedidos"

    id_pedido: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    cliente_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    repartidor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    zona: Mapped[str] = mapped_column(String(50), nullable=False)
    estado: Mapped[EstadoPedido] = mapped_column(
        SQLEnum(EstadoPedido, values_callable=lambda obj: [e.value for e in obj]),
        default=EstadoPedido.PENDIENTE,
        nullable=False,
        index=True,
    )
    metodo_pago: Mapped[str] = mapped_column(String(50), nullable=False)
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    tipo_vehiculo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    costo_operacion: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitud: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitud: Mapped[float | None] = mapped_column(Float, nullable=True)

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    fecha_asignacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_entrega: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relaciones ORM
    cliente: Mapped["User"] = relationship(
        "User",
        foreign_keys=[cliente_id],
        back_populates="pedidos_como_cliente",
    )
    repartidor: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[repartidor_id],
        back_populates="pedidos_como_repartidor",
    )
