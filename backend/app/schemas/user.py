from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: UserRole = UserRole.CLIENTE
    telefono: str | None = None
    zona_principal: str | None = None
    tipo_vehiculo_predilecto: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str | None = None
    role: UserRole = UserRole.CLIENTE
    telefono: str | None = None
    zona_principal: str | None = None
    tipo_vehiculo_predilecto: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    telefono: str | None = None
    zona_principal: str | None = None
    tipo_vehiculo_predilecto: str | None = None


class UserAdminUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    telefono: str | None = None
    zona_principal: str | None = None
    tipo_vehiculo_predilecto: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    role: UserRole
    telefono: str | None = None
    zona_principal: str | None = None
    tipo_vehiculo_predilecto: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResumen(BaseModel):
    id: UUID
    full_name: str | None = None
    email: str
    role: UserRole
    total_pedidos: int
    monto_total: float
    pedidos_pendientes: int
    pedidos_en_camino: int
    pedidos_entregados: int
    pedidos_cancelados: int
