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
    with httpx.Client(timeout=10.0) as client:
        headers = {"Accept": "application/json"}
        token_res = client.post(token_url, data=github_data, headers=headers)
        token_res.raise_for_status()
        github_token = token_res.json().get("access_token")

        url_user_info = "https://api.github.com/user"
        headers_user = {"Authorization": f"Bearer {github_token}"}
        user_res = client.get(url_user_info, headers=headers_user)
        user_res.raise_for_status()
        user_data = user_res.json()

        email = user_data.get("email")
        name = user_data.get("name") or user_data.get("login")

        # Si el correo de GitHub es privado, consultar el endpoint secundario
        if not email:
            emails_res = client.get("https://api.github.com/user/emails", headers=headers_user)
            if emails_res.status_code == 200:
                emails_list = emails_res.json()
                email = next(
                    (item.get("email") for item in emails_list if item.get("primary") and item.get("verified")),
                    None,
                )

        return {"email": email, "name": name}
