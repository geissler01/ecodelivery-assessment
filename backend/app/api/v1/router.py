from fastapi import APIRouter

from app.api.v1.endpoints import auth, oauth, pedidos, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación Local"])
api_router.include_router(oauth.router, prefix="/auth", tags=["Autenticación OAuth (Google/GitHub)"])
api_router.include_router(users.router, prefix="/users", tags=["Gestión y Perfiles de Usuarios"])
api_router.include_router(pedidos.router, prefix="/pedidos", tags=["Operación de Pedidos"])
