from datetime import UTC, datetime, timedelta
import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Usamos Argon2id como algoritmo de hashing recomendado por OWASP
password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """Genera el hash seguro Argon2id para una contraseña plana."""
    return password_hash.hash(password=password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash almacenado."""
    if not hashed_password or not plain_password:
        return False
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Genera un JWT firmado con expiración configurable."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
