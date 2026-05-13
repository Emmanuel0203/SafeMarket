"""
Punto de entrada de la aplicación FastAPI - SafeMarket API.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import logging

from db import Base, engine, test_connection
from db.models_enhanced import *  # noqa: F401, F403
from routers import auth, users, transactions, ml
from core.config import (
    ALLOWED_ORIGINS,
    API_TITLE,
    API_VERSION,
    API_DESCRIPTION,
    ENVIRONMENT
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test database connection
logger.info(f"Connecting to database: {ENVIRONMENT} mode")
if not test_connection():
    logger.warning("⚠️ Database connection failed - API may not work properly")
else:
    logger.info("✅ Database connection successful")
    
# Crear tablas en base de datos
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database schema verified and ready")
except Exception as e:
    logger.error(f"❌ Failed to create database schema: {str(e)}")
    raise

# Inicializar aplicación FastAPI
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    openapi_url="/api/v1/openapi.json" if ENVIRONMENT == "development" else None
)

# ✅ Botón Authorize con JWT en los docs
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# === MIDDLEWARE ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ROUTERS ===
# Autenticación
app.include_router(auth.router)

# Usuarios
app.include_router(users.router)

# Próximos routers para SafeMarket:
app.include_router(transactions.router)
# app.include_router(scoring.router)
# app.include_router(feedback.router)
# app.include_router(dashboard.router)
app.include_router(ml.router)


# === HEALTH CHECK ===
@app.get("/", tags=["Health"])
def root():
    """
    Endpoint de verificación de estado (health check).

    Retorna un mensaje indicando que la API está funcionando.
    """
    return {
        "message": "SafeMarket API corriendo",
        "environment": ENVIRONMENT,
        "version": API_VERSION
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Verificación de salud detallada.

    Retorna información sobre el estado de la aplicación.
    """
    return {
        "status": "healthy",
        "service": API_TITLE,
        "version": API_VERSION,
        "environment": ENVIRONMENT
    }


@app.get("/api/v1", tags=["Info"])
def api_info():
    """
    Información de la API.
    """
    return {
        "title": API_TITLE,
        "version": API_VERSION,
        "environment": ENVIRONMENT,
        "endpoints": {
            "auth": "/auth",
            "users": "/users",
            "docs": "/docs",
            "health": "/health"
        }
    }


# === MANEJO DE ERRORES ===
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Manejador de excepciones no capturadas.
    """
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "error": str(exc) if ENVIRONMENT == "development" else "Internal server error",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=ENVIRONMENT == "development"
    )
