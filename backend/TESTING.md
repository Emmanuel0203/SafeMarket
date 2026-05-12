# SafeMarket API - Guía Rápida de Testing

Este archivo contiene ejemplos curl para probar todos los endpoints de la API.

## 📌 Configuración Básica

**URL Base:** `http://localhost:8000`

### Variables
- `{email}`: ejemplo@correo.com
- `{password}`: SecurePass123
- `{user_id}`: ID del usuario
- `{token}`: Access token obtenido del login

---

## ✅ 1. Health Check

```bash
# Verificar que la API está activa
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/api/v1
```

---

## 🔐 2. Autenticación

### 2.1 Registrar Usuario

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

**Response esperado:**
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

### 2.2 Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=juan@example.com&password=SecurePass123" \
  -c cookies.txt
```

**Nota:** `-c cookies.txt` guarda las cookies automáticamente

### 2.3 Renovar Token

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
  -b cookies.txt
```

### 2.4 Logout

```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -b cookies.txt
```

---

## 👥 3. Usuarios (CRUD)

### 3.1 Listar Todos los Usuarios

```bash
curl -X GET "http://localhost:8000/users/" \
  -b cookies.txt
```

O con paginación:

```bash
curl -X GET "http://localhost:8000/users/?skip=0&limit=10" \
  -b cookies.txt
```

### 3.2 Obtener Perfil del Usuario Autenticado

```bash
curl -X GET "http://localhost:8000/users/profile" \
  -b cookies.txt
```

### 3.3 Obtener Usuario por ID

```bash
curl -X GET "http://localhost:8000/users/1" \
  -b cookies.txt
```

### 3.4 Actualizar Usuario

```bash
curl -X PUT "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Juan García Updated",
    "company": "Nueva Empresa",
    "plan": "Enterprise"
  }'
```

### 3.5 Cambiar Contraseña

```bash
curl -X POST "http://localhost:8000/users/1/change-password" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "current_password": "SecurePass123",
    "new_password": "NewSecurePass123",
    "confirm_password": "NewSecurePass123"
  }'
```

### 3.6 Eliminar Usuario (como Admin)

```bash
curl -X DELETE "http://localhost:8000/users/2" \
  -b cookies.txt
```

### 3.7 Estadísticas de Usuarios (solo admin)

```bash
curl -X GET "http://localhost:8000/users/statistics/summary" \
  -b cookies.txt
```

---

## 🧪 Testing Workflow Completo

```bash
#!/bin/bash

API="http://localhost:8000"

echo "1️⃣  Registrando usuario..."
REGISTER_RESPONSE=$(curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123",
    "company": "Test Company",
    "plan": "Starter"
  }')

echo "Response: $REGISTER_RESPONSE"

echo -e "\n2️⃣  Login..."
curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPass123" \
  -c cookies.txt

echo -e "\n3️⃣  Obteniendo perfil..."
curl -s -X GET "$API/users/profile" \
  -b cookies.txt | jq .

echo -e "\n4️⃣  Listando usuarios..."
curl -s -X GET "$API/users/" \
  -b cookies.txt | jq .

echo -e "\n5️⃣  Actualizando usuario..."
curl -s -X PUT "$API/users/1" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Test User Updated",
    "company": "Updated Company"
  }' | jq .

echo -e "\n6️⃣  Logout..."
curl -s -X POST "$API/auth/logout" \
  -b cookies.txt

echo -e "\n✅ Testing completado!"
```

Guardar como `test_api.sh` y ejecutar:

```bash
chmod +x test_api.sh
./test_api.sh
```

---

## ⚠️ Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `401 Unauthorized` | Token expirado | Usar `/auth/refresh` para renovar |
| `403 Forbidden` | Sin permisos | Verificar rol del usuario |
| `404 Not Found` | Usuario no existe | Verificar ID del usuario |
| `400 Bad Request` | Datos inválidos | Revisar validaciones de entrada |
| `409 Conflict` | Email duplicado | Usar otro email |

---

## 🔧 Usando Postman

1. **Importar colección:**
   - File → Import → Seleccionar `postman_collection.json`

2. **Configurar variables:**
   - Environment → Set `base_url = http://localhost:8000`
   - Set `token` variable (se actualiza automáticamente)

3. **Ejecutar secuencial:**
   - Usar la carpeta de pruebas
   - Cada request en orden (register → login → CRUD)

---

## 📝 Notas Importantes

- ✅ Las cookies se guardan con `-c cookies.txt` y se envían con `-b cookies.txt`
- ✅ Para ver JSON formateado, usar `| jq .`
- ✅ Las contraseñas deben tener: mín. 8 chars, mayúscula, número
- ✅ Los tokens de acceso expiran en 60 minutos (configurable)
- ✅ Solo Admin puede cambiar/eliminar otros usuarios

---

## 🚀 Próximas Pruebas

Cuando se implementen los siguientes módulos:
- Transacciones
- Scoring Engine
- Reglas Engine
- Feedback Loop
- Dashboard

se agregarán más ejemplos aquí.

---

**¡Happy Testing! 🎉**
