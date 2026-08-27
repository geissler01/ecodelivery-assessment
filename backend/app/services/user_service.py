"""
Fachada de compatibilidad para el servicio de usuarios.
Toda la lógica modular reside en app.services.users.
"""

from app.services.users import (
    UserManager,
    UserMetricsService,
    authenticate_user,
    create_oauth_user,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_resumen,
    get_users,
    update_user,
)

__all__ = [
    "UserManager",
    "UserMetricsService",
    "get_user_by_email",
    "get_user_by_id",
    "create_user",
    "authenticate_user",
    "create_oauth_user",
    "get_users",
    "update_user",
    "get_user_resumen",
]
