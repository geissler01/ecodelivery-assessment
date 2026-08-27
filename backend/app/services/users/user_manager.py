from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserAdminUpdate, UserCreate, UserUpdate


class UserManager:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.lower().strip())
        return db.scalar(stmt)

    @staticmethod
    def get_user_by_id(db: Session, user_id: str | UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return db.scalar(stmt)

    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        password_hashed = get_password_hash(user_create.password)
        db_user = User(
            email=user_create.email.lower().strip(),
            hashed_password=password_hashed,
            full_name=user_create.full_name,
            role=user_create.role,
            telefono=user_create.telefono,
            zona_principal=user_create.zona_principal,
            tipo_vehiculo_predilecto=user_create.tipo_vehiculo_predilecto,
            is_active=True,
            is_verified=False,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        user = UserManager.get_user_by_email(db, email=email)
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_oauth_user(db: Session, email: str, full_name: str | None = None) -> User:
        user = User(
            email=email.lower().strip(),
            full_name=full_name,
            hashed_password=None,
            is_verified=True,
            role=UserRole.CLIENTE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        role: UserRole | None = None,
    ) -> list[User]:
        stmt = select(User)
        if role:
            stmt = stmt.where(User.role == role)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def update_user(db: Session, db_user: User, user_in: UserUpdate | UserAdminUpdate) -> User:
        update_data = user_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
