# SafeMarket Backend API

API REST desarrollada con **FastAPI** para **SafeMarket** - Comercio Digital Seguro.

> Mapa de archivos y responsabilidades: ver `FILE_PURPOSES.md`.

## 🚀 Características Actuales

✅ **Autenticación JWT** con Access & Refresh Tokens  
✅ **Cookies Seguras** (httpOnly, samesite)  
✅ **CRUD de Usuarios** completo  
✅ **Gestión de Contraseñas** con hashing bcrypt  
✅ **Control de Acceso** basado en roles (RBAC)  
✅ **Base de Datos** con SQLAlchemy ORM  
✅ **Documentación Automática** (Swagger UI)  

---

## 📋 Requisitos

- **Python 3.11+**
- **pip** o **conda**
- **Virtual Environment** (recomendado)

---

## 🔧 Instalación y Configuración

### 1. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
```

### 4. Iniciar servidor

```bash
# Desarrollo (con recarga automática)
uvicorn main:app --reload --port 8000

# Producción
uvicorn main:app --host 0.0.0.0 --port 8000
```

✅ API disponible en: **http://localhost:8000**  
📄 Swagger UI (docs): **http://localhost:8000/docs**  
📄 ReDoc: **http://localhost:8000/redoc**

---

## 📚 Endpoints de la API

### Health Check

```http
GET /
GET /health
GET /api/v1
```

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/auth/register` | Registrar nuevo usuario |
| `POST` | `/auth/login` | Iniciar sesión |
| `POST` | `/auth/refresh` | Renovar access token |
| `POST` | `/auth/logout` | Cerrar sesión |

### Usuarios

| Método | Endpoint | Descripción | Requiere Auth |
|--------|----------|-------------|---------------|
| `GET` | `/users/` | Listar todos los usuarios | ✅ |
| `GET` | `/users/{user_id}` | Obtener usuario por ID | ✅ |
| `GET` | `/users/profile` | Obtener perfil del usuario actual | ✅ |
| `PUT` | `/users/{user_id}` | Actualizar usuario | ✅ |
| `DELETE` | `/users/{user_id}` | Eliminar usuario | ✅ |
| `POST` | `/users/{user_id}/change-password` | Cambiar contraseña | ✅ |
| `GET` | `/users/statistics/summary` | Estadísticas de usuarios | ✅ Admin |

---

## 🔐 Autenticación y Autorización

### Flujo de Autenticación

```
1. Usuario se registra (POST /auth/register)
   ↓
2. Obtiene access_token y refresh_token
   ↓
3. Access token se almacena en cookie (httpOnly)
   ↓
4. Request a rutas protegidas incluye cookie automáticamente
   ↓
5. Si token expira, cliente usa refresh token para renovar
```

### Headers de Request Protegido

```http
GET /users/ HTTP/1.1
Cookie: access_token=eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Códigos de Estado HTTP

- `200` - Éxito
- `201` - Creado
- `400` - Solicitud inválida
- `401` - No autenticado
- `403` - No autorizado
- `404` - No encontrado
- `409` - Conflicto (ej: email duplicado)
- `500` - Error del servidor

---

## 📝 Ejemplos de Uso

### 1. Registrar Usuario

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Juan García",
    "email": "juan@example.com",
    "password": "SecurePass123",
    "company": "Mi Empresa",
    "plan": "Pro"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "Juan García",
    "email": "juan@example.com",
    "company": "Mi Empresa",
    "plan": "Pro",
    "role": "Admin"
  }
}
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=juan@example.com&password=SecurePass123"
```

### 3. Obtener Perfil del Usuario

```bash
curl -X GET "http://localhost:8000/users/profile" \
  -H "Cookie: access_token=<your_token_here>"
```

### 4. Actualizar Usuario

```bash
curl -X PUT "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=<your_token_here>" \
  -d '{
    "name": "Juan García Updated",
    "company": "Nueva Empresa"
  }'
```

### 5. Cambiar Contraseña

```bash
curl -X POST "http://localhost:8000/users/1/change-password" \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=<your_token_here>" \
  -d '{
    "current_password": "SecurePass123",
    "new_password": "NewSecurePass123",
    "confirm_password": "NewSecurePass123"
  }'
```

---

## 🏗️ Estructura del Proyecto

```
backend/
├── core/
│   ├── __init__.py
│   ├── config.py          # Configuraciones globales
│   ├── security.py        # JWT, hashing, tokens
│   └── deps.py            # Dependencias (get_current_user)
│
├── db/
│   ├── __init__.py
│   ├── database.py        # Configuración SQLAlchemy
│   └── models.py          # Modelos ORM (User, Transaction)
│
├── routers/
│   ├── __init__.py
│   ├── auth.py            # Endpoints de autenticación
│   └── users.py           # Endpoints CRUD de usuarios
│
├── schemas/
│   ├── __init__.py
│   ├── user.py            # Modelos Pydantic
│   └── transaction.py     # Esquemas de transacciones
│
├── services/
│   ├── __init__.py
│   ├── user_service.py    # Lógica de usuarios
│   └── transaction_service.py
│
├── utils/
│   ├── __init__.py
│   └── seed.py            # Datos de prueba
│
├── main.py                # Punto de entrada
├── requirements.txt       # Dependencias
├── .env.example          # Variables de ejemplo
└── README.md             # Esta documentación
```

---

## 🛠️ Desarrollo

### Agregar nuevas rutas

1. Crear archivo en `routers/` (ej: `transactions.py`)
2. Definir router con FastAPI APIRouter
3. Incluir en `main.py`: `app.include_router(transactions.router)`

### Agregar nuevos modelos

1. Crear en `db/models.py`
2. Crear schemas en `schemas/`
3. Crear servicios en `services/`

### Agregar autenticación a una ruta

```python
from core.deps import get_current_user
from db.models import User

@router.get("/protegido")
def ruta_protegida(current_user: User = Depends(get_current_user)):
    return {"message": f"Hola {current_user.name}"}
```

---

## 🧪 Testing

(Próximamente: pytest, fixtures, test cases)

```bash
# Correr tests
pytest

# Con cobertura
pytest --cov=.
```

---

## 📊 Validación de Contraseñas

Las contraseñas deben cumplir:
- ✅ Mínimo 8 caracteres
- ✅ Al menos una mayúscula
- ✅ Al menos un número

---

## 🚨 Seguridad

### Buenas Prácticas Implementadas

✅ **Hashing de contraseñas** con bcrypt  
✅ **JWT con expiración** (access + refresh)  
✅ **Cookies httpOnly** (protección XSS)  
✅ **Same-site cookies** (protección CSRF)  
✅ **Validación de entrada** con Pydantic  
✅ **Control de acceso** basado en roles  
✅ **Rate limiting** (preparado para implementar)  

### ⚠️ IMPORTANTE para Producción

1. **Cambiar SECRET_KEY** en `.env`
2. **Configurar CORS** correctamente
3. **Habilitar HTTPS** (secure=True en cookies)
4. **Usar PostgreSQL** en lugar de SQLite
5. **Configurar certificados SSL/TLS**
6. **Implementar rate limiting**
7. **Habilitar logging y monitoreo**

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError"
```bash
# Asegúrate de estar en el entorno virtual
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### Error: "Database is locked"
```python
# En development, SQLite puede dar este error
# Solución: reinicia el servidor
```

### Error: "Token inválido"
```bash
# Asegúrate de que las cookies se envían correctamente
# En requests con fetch/axios, incluir: credentials: 'include'
```

---

## 📖 Próximas Fases

- 🔄 Motor de Score (Score Engine)
- 🎯 Motor de Reglas (Rules Engine)
- 📊 Detección de Anomalías
- 📈 Análisis por Grafos (Graph ML)
- 📋 Panel de Revisión Manual
- 💬 Sistema de Feedback Loop
- 📊 Dashboard y Observabilidad
- 🧪 Suite de Tests Completa

---

## 📞 Soporte

Para preguntas o reportar issues, contacta al equipo de desarrollo.

---

**Desarrollado con ❤️ para SafeMarket**