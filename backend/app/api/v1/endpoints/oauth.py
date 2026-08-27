from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.token import Token
from app.services.oauth_service import (
    exchange_code_for_github_user,
    exchange_code_for_google_user,
    get_github_url,
    get_google_oauth_url,
)
from app.services.user_service import create_oauth_user, get_user_by_email

router = APIRouter()


@router.get("/google/login", summary="Redireccionar a pantalla de autenticación de Google OAuth")
def google_login():
    url = get_google_oauth_url()
    return RedirectResponse(url=url)


@router.get("/google/callback", response_model=Token, summary="Callback de retorno de Google OAuth")
def google_callback(code: str, db: Session = Depends(get_db)):
    try:
        google_user = exchange_code_for_google_user(code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en intercambio OAuth con Google: {str(e)}",
        )

    email = google_user.get("email")
    name = google_user.get("name")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener el correo del perfil de Google.",
        )

    user = get_user_by_email(db=db, email=email)
    if not user:
        user = create_oauth_user(db, email=email, full_name=name)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo.",
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "email": user.email,
        }
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/github/login", summary="Redireccionar a pantalla de autenticación de GitHub OAuth")
def github_login():
    url = get_github_url()
    return RedirectResponse(url=url)


@router.get("/github/callback", response_model=Token, summary="Callback de retorno de GitHub OAuth")
def github_callback(code: str, db: Session = Depends(get_db)):
    try:
        github_user = exchange_code_for_github_user(code=code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en intercambio OAuth con GitHub: {str(e)}",
        )

    email = github_user.get("email")
    name = github_user.get("name")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener el correo verificado de GitHub.",
        )

    user = get_user_by_email(db=db, email=email)
    if not user:
        user = create_oauth_user(db=db, email=email, full_name=name)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo.",
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "email": user.email,
        }
    )
    return {"access_token": access_token, "token_type": "bearer"}
