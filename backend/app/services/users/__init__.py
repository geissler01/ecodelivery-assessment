from .user_manager import UserManager
from .user_metrics_service import UserMetricsService

# Atajos funcionales
get_user_by_email = UserManager.get_user_by_email
get_user_by_id = UserManager.get_user_by_id
create_user = UserManager.create_user
authenticate_user = UserManager.authenticate_user
create_oauth_user = UserManager.create_oauth_user
get_users = UserManager.get_users
update_user = UserManager.update_user
get_user_resumen = UserMetricsService.get_user_resumen

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
