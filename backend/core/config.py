"""
Configuraciones globales del proyecto (desarrollo, producción, testing).
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Modo de ambiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # desarrollo, producción, testing

# === SEGURIDAD ===
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "safemarket-secret-key-2026-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "2"))

# === BASE DE DATOS ===
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/safemarket"
)

# Configuración específica de SQLite para desarrollo
SQLALCHEMY_ECHO = ENVIRONMENT == "development"

# === CORS ===
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"
).split(",")

# === LOGGING ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if ENVIRONMENT == "production" else "DEBUG")

# === API ===
API_TITLE = "SafeMarket API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
**SafeMarket** - Comercio Digital Seguro

Sistema híbrido de detección de fraude y análisis de riesgo con:
- Motor de Score + Rules Engine
- Detección por anomalías
- Análisis por grafos
- Sistema explicable
- Feedback loop para aprendizaje continuo
"""

# === SEGURIDAD EN COOKIES ===
COOKIE_SECURE = ENVIRONMENT == "production"  # HTTPS solo en producción
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"

# === RATE LIMITING (próximas fases) ===
RATE_LIMIT_ENABLED = True
RATE_LIMIT_REQUESTS_PER_MINUTE = 60

# === VALIDACIÓN ===
MIN_PASSWORD_LENGTH = 8
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 100

# === PAGINACIÓN ===
DEFAULT_SKIP = 0
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000

# === TESTING ===
TESTING = ENVIRONMENT == "testing"

if TESTING:
    DATABASE_URL = "sqlite:///:memory:"