# Backend File Purposes

Este mapa documenta por que existe cada archivo activo del backend, donde se utiliza y para que sirve dentro de SafeMarket.

## Aplicacion

- `main.py`: punto de entrada FastAPI; registra middlewares, routers y health checks; lo usa `uvicorn` para levantar la API.
- `requirements.txt`: dependencias de Python necesarias para ejecutar API y tests.
- `.env.example`: plantilla de variables de entorno para nuevos entornos.
- `.env`: configuracion local sensible para conectar a PostgreSQL y parametros runtime.

## Core

- `core/config.py`: carga y expone configuraciones globales (DB URL, JWT, CORS, ambiente); lo importan `main.py`, `db` y `routers`.
- `core/security.py`: hashing y JWT (access/refresh); lo usan `routers/auth.py` y `services/user_service.py`.
- `core/deps.py`: dependencia `get_current_user` para autenticar rutas protegidas; lo usa `routers/users.py`.
- `core/__init__.py`: marca el paquete `core` y documenta su rol.

## Base de datos

- `db/models_enhanced.py`: modelos SQLAlchemy del esquema PostgreSQL mejorado (users, companies, transactions, etc.); lo usan `db`, `services` y `main.py`.
- `db/database_enhanced.py`: engine, session factory y test de conexion para PostgreSQL; lo usa `db/__init__.py`.
- `db/__init__.py`: facade unificada de capa DB (engine, SessionLocal, Base, modelos y helpers).
- `db/database.py`: wrapper de compatibilidad para imports historicos que redirige a `db` unificado.

## Routers

- `routers/auth.py`: endpoints `/auth/*` para registro/login/refresh/logout usando servicio de usuarios y JWT.
- `routers/users.py`: endpoints `/users/*` para perfil, listado, actualizacion, password y estadisticas.
- `routers/__init__.py`: marca paquete de routers.

## Servicios

- `services/user_service.py`: logica de negocio de usuarios (create/read/update/delete, password y conteos); lo usan routers y dependencias.
- `services/__init__.py`: init de paquete, evita imports legacy rotos.

## Schemas

- `schemas/user.py`: contratos Pydantic de request/response para auth y usuarios.
- `schemas/transaction.py`: contratos Pydantic para transacciones (siguiente fase funcional).
- `schemas/__init__.py`: init de paquete de schemas.

## Utilidades

- `utils/seed.py`: punto central de seed (actualmente neutro para evitar datos no deterministas).
- `utils/__init__.py`: init del paquete utilitario.

## Tests

- `tests/test_api_endpoints.py`: pruebas de funcionamiento de la API (health + flujo auth/users) con `TestClient`.
- `tests/test_postgres_integration_db.py`: pruebas de integracion directa con PostgreSQL (conexion, tablas y roundtrip SQL).
- `test_db_connection.py`: script manual de diagnostico de conexion y estado de tablas para soporte rapido.

## Scripts de operacion

- `run_api.ps1`: script Windows para ejecutar la API en desarrollo.
- `run_api.sh`: script Unix para ejecutar la API en desarrollo.
- `start_api.ps1`: wrapper rapido para iniciar API desde PowerShell.
- `setup_postgres.py`: asistente de setup de PostgreSQL (flujo completo).
- `setup_postgres_simple.py`: version simplificada de setup para escenarios basicos.
- `schema_improved.sql`: DDL de referencia para crear/validar esquema PostgreSQL mejorado.

## Documentacion funcional conservada

- `README.md`: guia principal de uso del backend.
- `ARCHITECTURE.md`: explicacion arquitectonica de alto nivel.
- `POSTGRES_SETUP.md`: guia de configuracion de PostgreSQL para el proyecto.
- `QUICKSTART.md`: pasos rapidos de arranque.
- `TESTING.md`: guia de pruebas y comandos de verificacion.
