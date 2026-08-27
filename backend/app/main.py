from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas DDL al inicializar la aplicación si no existen
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"⚠️ Advertencia al conectar/crear tablas en inicio: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API RESTful de alto desempeño para gestión de pedidos ecológicos, autenticación OAuth y analítica operativa - EcoDelivery S.A.S.",
    lifespan=lifespan,
)

# Middleware de Seguridad CORS para permitir acceso desde Flutter (móvil/web) y VPS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enrutador principal de versión 1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Salud del Sistema"], summary="Endpoint raíz de bienvenida")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health", tags=["Salud del Sistema"], summary="Health check para monitoreo y Docker")
def health_check():
    return JSONResponse(content={"status": "healthy"})
