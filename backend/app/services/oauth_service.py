from urllib.parse import quote
import httpx

from app.core.config import settings


def get_google_oauth_url() -> str:
    """Construye la URL de inicio de sesión de Google OAuth 2.0."""
    redirect_uri = quote(settings.GOOGLE_REDIRECT_URI, safe="")
    return (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline"
    )


def exchange_code_for_google_user(code: str) -> dict:
    """Intercambia el código de autorización por los datos del usuario en Google."""
    token_url = "https://oauth2.googleapis.com/token"
    google_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    with httpx.Client(timeout=10.0) as client:
        token_res = client.post(token_url, data=google_data)
        token_res.raise_for_status()
        google_access_token = token_res.json().get("access_token")

        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {google_access_token}"}
        user_res = client.get(user_info_url, headers=headers)
        user_res.raise_for_status()
        return user_res.json()


def get_github_url() -> str:
    """Construye la URL de inicio de sesión de GitHub OAuth."""
    redirect_uri = quote(settings.GITHUB_REDIRECT_URI, safe="")
    return (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=user:email"
    )


def exchange_code_for_github_user(code: str) -> dict:
    """Intercambia el código de autorización por los datos del usuario en GitHub."""
    token_url = "https://github.com/login/oauth/access_token"
    github_data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }
    default_headers = {
        "Accept": "application/json",
        "User-Agent": "EcoDelivery-Platform/1.0",
    }
    with httpx.Client(timeout=10.0, headers=default_headers) as client:
        token_res = client.post(token_url, data=github_data)
        token_res.raise_for_status()
        token_json = token_res.json()

        if "error" in token_json:
            error_desc = token_json.get("error_description", token_json.get("error"))
            raise ValueError(f"GitHub OAuth error: {error_desc}")

        github_token = token_json.get("access_token")
        if not github_token:
            raise ValueError(f"No se recibió access_token de GitHub: {token_json}")

        url_user_info = "https://api.github.com/user"
        headers_user = {
            "Authorization": f"Bearer {github_token}",
            "User-Agent": "EcoDelivery-Platform/1.0",
            "Accept": "application/json",
        }
        user_res = client.get(url_user_info, headers=headers_user)
        user_res.raise_for_status()
        user_data = user_res.json()

        email = user_data.get("email")
        name = user_data.get("name") or user_data.get("login") or "Usuario GitHub"
        username = user_data.get("login", "github_user")

        # Si el correo de GitHub es privado en el perfil, consultar el endpoint secundario /user/emails
        if not email:
            try:
                emails_res = client.get("https://api.github.com/user/emails", headers=headers_user)
                if emails_res.status_code == 200:
                    emails_list = emails_res.json()
                    if isinstance(emails_list, list) and len(emails_list) > 0:
                        # 1. Buscar email principal y verificado
                        email = next(
                            (item.get("email") for item in emails_list if item.get("primary") and item.get("verified")),
                            None,
                        )
                        # 2. Buscar cualquier email verificado
                        if not email:
                            email = next(
                                (item.get("email") for item in emails_list if item.get("verified")),
                                None,
                            )
                        # 3. Tomar el primer email disponible
                        if not email:
                            email = emails_list[0].get("email")
            except Exception:
                pass

        # Si aún no hay email, fallback con el dominio seguro de no-reply de GitHub
        if not email:
            email = f"{username}@users.noreply.github.com"

        return {"email": email, "name": name}
