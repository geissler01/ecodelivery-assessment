import csv
from datetime import datetime
import os
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.pedido import EstadoPedido, Pedido
from app.models.user import User, UserRole


def find_data_file(filename: str) -> Path:
    """Busca el archivo CSV en múltiples ubicaciones estándar (local y Docker)."""
    possible_paths = [
        Path(f"/data/{filename}"),
        Path(__file__).resolve().parent.parent.parent / "data" / filename,
        Path(__file__).resolve().parent.parent / "data" / filename,
        Path(f"data/{filename}"),
        Path(f"../data/{filename}"),
    ]
    for p in possible_paths:
        if p.exists():
            return p
    raise FileNotFoundError(f"No se encontró el archivo de datos '{filename}'.")


def parse_datetime(dt_str: str | None) -> datetime | None:
    if not dt_str or not dt_str.strip():
        return None
    dt_clean = dt_str.strip()
    for fmt in [
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
    ]:
        try:
            return datetime.strptime(dt_clean, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(dt_clean)
    except Exception:
        return None


def run_seed():
    print("🚀 Iniciando proceso de Seed y Migración de Datos para EcoDelivery...")

    # 1. Asegurar que las tablas existan
    print("🛠️ Verificando y creando tablas en PostgreSQL...")
    Base.metadata.create_all(bind=engine)

    users_file = find_data_file("users_db_ready.csv")
    pedidos_file = find_data_file("pedidos_db_ready.csv")

    print(f"📁 Archivo de usuarios detectado: {users_file}")
    print(f"📁 Archivo de pedidos detectado: {pedidos_file}")

    db: Session = SessionLocal()

    try:
        # 2. Generar hash real de Argon2id una sola vez (optimización de velocidad)
        print("🔐 Generando hash de seguridad Argon2id para los usuarios semilla...")
        default_hash = get_password_hash(settings.DEFAULT_SEED_PASSWORD)
        admin_hash = get_password_hash("Admin1234!")

        # 3. Crear o actualizar superadministrador
        admin_email = "admin@ecodelivery.com"
        admin_user = db.scalar(select(User).where(User.email == admin_email))
        if not admin_user:
            admin_user = User(
                email=admin_email,
                hashed_password=admin_hash,
                full_name="Administrador EcoDelivery",
                role=UserRole.ADMIN,
                telefono="+57 300 0000000",
                zona_principal="Centro",
                is_active=True,
                is_verified=True,
            )
            db.add(admin_user)
            print(f"👑 Superadmin creado: {admin_email} / Admin1234!")
        else:
            admin_user.hashed_password = admin_hash
            admin_user.role = UserRole.ADMIN
            db.add(admin_user)

        # 4. Cargar usuarios desde CSV
        print("👥 Cargando usuarios y normalizando perfiles...")
        with open(users_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            users_count = 0
            for row in reader:
                user_id = UUID(row["id"])
                # Normalizamos el dominio ficticio .local a un dominio válido RFC (.com) para validación estricta EmailStr
                user_email = row["email"].lower().strip().replace(".local", ".com")
                user_role_str = row["role"].lower().strip()
                user_role = UserRole.REPARTIDOR if user_role_str == "repartidor" else UserRole.CLIENTE

                db_user = db.get(User, user_id)
                if not db_user:
                    db_user = User(
                        id=user_id,
                        email=user_email,
                        hashed_password=default_hash,  # Reemplazamos el hash dummy por el hash real
                        full_name=row.get("full_name"),
                        role=user_role,
                        is_active=row.get("is_active", "True").lower() == "true",
                        is_verified=row.get("is_verified", "True").lower() == "true",
                        created_at=parse_datetime(row.get("created_at")) or datetime.utcnow(),
                        updated_at=parse_datetime(row.get("updated_at")) or datetime.utcnow(),
                    )
                    db.add(db_user)
                else:
                    db_user.email = user_email
                    db_user.hashed_password = default_hash
                    db_user.full_name = row.get("full_name")
                    db_user.role = user_role
                    db.add(db_user)
                users_count += 1

        db.commit()
        print(f"✅ {users_count} usuarios migrados y asegurados con contraseña: {settings.DEFAULT_SEED_PASSWORD}")

        # 5. Cargar pedidos desde CSV
        print("📦 Cargando y vinculando los 1000 pedidos con llaves foráneas...")
        with open(pedidos_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            pedidos_count = 0
            for row in reader:
                pedido_id = UUID(row["id_pedido"])
                cliente_id = UUID(row["cliente_id"])
                repartidor_id_raw = row.get("repartidor_id")
                repartidor_id = UUID(repartidor_id_raw) if repartidor_id_raw and repartidor_id_raw.strip() else None

                estado_raw = row.get("estado", "pendiente").lower().strip()
                estado_enum = {
                    "pendiente": EstadoPedido.PENDIENTE,
                    "en_camino": EstadoPedido.EN_CAMINO,
                    "entregado": EstadoPedido.ENTREGADO,
                    "cancelado": EstadoPedido.CANCELADO,
                }.get(estado_raw, EstadoPedido.PENDIENTE)

                db_pedido = db.get(Pedido, pedido_id)
                if not db_pedido:
                    db_pedido = Pedido(
                        id_pedido=pedido_id,
                        cliente_id=cliente_id,
                        repartidor_id=repartidor_id,
                        zona=row.get("zona", "Centro"),
                        estado=estado_enum,
                        metodo_pago=row.get("metodo_pago", "app"),
                        monto=float(row.get("monto", 0.0)),
                        tipo_vehiculo=row.get("tipo_vehiculo"),
                        costo_operacion=float(row["costo_operacion"]) if row.get("costo_operacion") else None,
                        latitud=float(row["latitud"]) if row.get("latitud") else None,
                        longitud=float(row["longitud"]) if row.get("longitud") else None,
                        fecha_creacion=parse_datetime(row.get("fecha_creacion")) or datetime.utcnow(),
                        fecha_asignacion=parse_datetime(row.get("fecha_asignacion")),
                        fecha_entrega=parse_datetime(row.get("fecha_entrega")),
                    )
                    db.add(db_pedido)
                else:
                    db_pedido.cliente_id = cliente_id
                    db_pedido.repartidor_id = repartidor_id
                    db_pedido.zona = row.get("zona", "Centro")
                    db_pedido.estado = estado_enum
                    db_pedido.metodo_pago = row.get("metodo_pago", "app")
                    db_pedido.monto = float(row.get("monto", 0.0))
                    db_pedido.tipo_vehiculo = row.get("tipo_vehiculo")
                    db.add(db_pedido)
                pedidos_count += 1

        db.commit()
        print(f"✅ {pedidos_count} pedidos insertados/actualizados correctamente.")

        # 6. Caracterización agregada de perfiles en base a pedidos
        print("🧠 Enriqueciendo perfiles de usuarios con su zona más frecuente y vehículo...")
        all_users = list(db.scalars(select(User)).all())
        for u in all_users:
            if u.role == UserRole.REPARTIDOR:
                # Buscar zona y vehículo más frecuente
                user_pedidos = list(db.scalars(select(Pedido).where(Pedido.repartidor_id == u.id)).all())
                if user_pedidos:
                    zonas = [p.zona for p in user_pedidos if p.zona]
                    vehiculos = [p.tipo_vehiculo for p in user_pedidos if p.tipo_vehiculo]
                    if zonas:
                        u.zona_principal = max(set(zonas), key=zonas.count)
                    if vehiculos:
                        u.tipo_vehiculo_predilecto = max(set(vehiculos), key=vehiculos.count)
                    db.add(u)
            elif u.role == UserRole.CLIENTE:
                user_pedidos = list(db.scalars(select(Pedido).where(Pedido.cliente_id == u.id)).all())
                if user_pedidos:
                    zonas = [p.zona for p in user_pedidos if p.zona]
                    if zonas:
                        u.zona_principal = max(set(zonas), key=zonas.count)
                    db.add(u)

        db.commit()
        print("✨ Caracterización de usuarios finalizada con éxito.")
        print("🎉 ¡Seed completado al 100%! La base de datos está lista para producción y desarrollo.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante el seed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
