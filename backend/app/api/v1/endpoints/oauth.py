from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.services.oauth_service import (
    exchange_code_for_github_user,
    exchange_code_for_google_user,
    get_github_url,
    get_google_oauth_url,
)
from app.services.user_service import create_oauth_user, get_user_by_email

router = APIRouter()


def _build_oauth_response(access_token: str, accept_header: Optional[str] = None, format_param: Optional[str] = None):
    """Retorna respuesta adaptada para Web y Móvil (Deep Link + HTML + JSON fallback)."""
    if format_param == "json" or (accept_header and "application/json" in accept_header):
        return JSONResponse(content={"access_token": access_token, "token_type": "bearer"})

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EcoDelivery - Autenticación Exitosa</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f0fdf4;
            color: #1e293b;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 16px;
        }}
        .card {{
            background: white;
            max-width: 440px;
            width: 100%;
            padding: 36px 24px;
            border-radius: 24px;
            box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
            text-align: center;
        }}
        .icon {{
            width: 68px;
            height: 68px;
            background-color: #dcfce7;
            color: #16a34a;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 34px;
            margin: 0 auto 16px;
        }}
        h2 {{ color: #15803d; margin: 0 0 8px; font-size: 22px; }}
        p {{ color: #64748b; font-size: 14px; line-height: 1.5; margin: 0 0 24px; }}
        .btn {{
            display: block;
            width: 100%;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 14px 0;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            box-sizing: border-box;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            margin-bottom: 12px;
        }}
        .btn-secondary {{
            display: block;
            width: 100%;
            background: #f1f5f9;
            color: #475569;
            padding: 12px 0;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            box-sizing: border-box;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🌿</div>
        <h2>¡Autenticación Exitosa!</h2>
        <p>Redirigiendo de vuelta a la aplicación EcoDelivery...</p>
        <a class="btn" href="ecodelivery://auth-callback?token={access_token}">Abrir en la App Móvil</a>
        <a class="btn-secondary" href="/#/pedidos?token={access_token}" onclick="if (window.opener) {{ window.opener.postMessage({{token: '{access_token}'}}, '*'); window.close(); }}">Continuar en la Web</a>
    </div>
    <script>
        // 1. Si es ventana emergente (Popup en Web), notificar a la ventana principal
        if (window.opener) {{
            try {{
                window.opener.postMessage({{ token: "{access_token}" }}, "*");
            }} catch(e) {{}}
        }}
        // 2. Si es Móvil, disparar Deep Link para abrir la App
        setTimeout(function() {{
            window.location.href = "ecodelivery://auth-callback?token={access_token}";
        }}, 350);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@router.get("/google/login", summary="Redireccionar a pantalla de autenticación de Google OAuth")
def google_login():
    url = get_google_oauth_url()
    return RedirectResponse(url=url)


@router.get("/google/callback", summary="Callback de retorno de Google OAuth")
def google_callback(
    code: str,
    db: Session = Depends(get_db),
    accept: Optional[str] = Header(None),
    format: Optional[str] = Query(None),
):
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
    return _build_oauth_response(access_token, accept_header=accept, format_param=format)


@router.get("/github/login", summary="Redireccionar a pantalla de autenticación de GitHub OAuth")
def github_login():
    url = get_github_url()
    return RedirectResponse(url=url)


@router.get("/github/callback", summary="Callback de retorno de GitHub OAuth")
def github_callback(
    code: str,
    db: Session = Depends(get_db),
    accept: Optional[str] = Header(None),
    format: Optional[str] = Query(None),
):
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
    return _build_oauth_response(access_token, accept_header=accept, format_param=format)
