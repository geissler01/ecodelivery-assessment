from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.pedido import EstadoPedido, MetodoPago, Zona


class PedidoBase(BaseModel):
    zona: str = Field(..., description="Zona de entrega: Norte, Sur, Centro, Occidente, Chapinero")
    metodo_pago: str = Field(..., description="Método de pago: efectivo, tarjeta, app")
    monto: float = Field(..., gt=0, description="Monto del pedido")
    tipo_vehiculo: str | None = Field(default=None, description="moto_electrica o bicicleta")
    costo_operacion: float | None = Field(default=None, description="Costo operativo del despacho")
    latitud: float | None = Field(default=None, description="Latitud de entrega")
    longitud: float | None = Field(default=None, description="Longitud de entrega")


class PedidoCreate(PedidoBase):
    cliente_id: UUID | None = Field(default=None, description="ID del cliente (si es omitido, se toma del usuario autenticado)")
    repartidor_id: UUID | None = Field(default=None, description="ID del repartidor asignado (opcional)")


class PedidoUpdateEstado(BaseModel):
    nuevo_estado: EstadoPedido = Field(..., description="Nuevo estado: pendiente, en_camino, entregado, cancelado")
    repartidor_id: UUID | None = Field(default=None, description="ID del repartidor al asignar o reasignar")
    tipo_vehiculo: str | None = Field(default=None, description="Tipo de vehículo: moto_electrica o bicicleta")


class PedidoResponse(PedidoBase):
    id_pedido: UUID
    cliente_id: UUID
    repartidor_id: UUID | None = None
    estado: EstadoPedido
    fecha_creacion: datetime
    fecha_asignacion: datetime | None = None
    fecha_entrega: datetime | None = None

    # Información complementaria de las relaciones
    cliente_nombre: str | None = None
    cliente_email: str | None = None
    repartidor_nombre: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PedidoEstadisticas(BaseModel):
    total_pedidos: int
    pedidos_pendientes: int
    pedidos_en_camino: int
    pedidos_entregados: int
    pedidos_cancelados: int
    ingresos_totales: float
    tiempo_promedio_entrega_minutos: float | None
