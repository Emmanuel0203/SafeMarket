<!-- Quick Start Guide - PostgreSQL Enhanced Schema -->

# ⚡ Quick Start - PostgreSQL Enhanced Schema

**Tiempo estimado: 10 minutos**

---

## 🚀 PASOS RÁPIDOS

### 1️⃣ INSTALAR POSTGRESQL (5 min)
```
Descarga: https://www.postgresql.org/download/windows/
↓
Ejecuta instalador
↓
Password: postgres
Port: 5432
↓
Termina instalación
```

### 2️⃣ EJECUTAR SETUP (2 min)
```powershell
cd C:\Eaq\Proyectos\SafeMarket\Aplicativo\safemarket_proyecto\backend

.\env\Scripts\Activate.ps1

python setup_postgres.py

# Verás: ✅ Database created ✅ Schema loaded ✅ Seed data inserted
```

### 3️⃣ CONFIGURAR API (1 min)
```
Archivo: C:\...\safemarket_proyecto\.env

CAMBIAR:
DATABASE_URL=sqlite:///./safemarket.db

POR:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/safemarket
```

### 4️⃣ INICIAR API (1 min)
```powershell
cd backend
python main.py

# Verás: INFO:     Application startup complete
#       INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5️⃣ PROBAR (1 min)
```powershell
# Nueva ventana PowerShell:
cd backend
python test_enhanced_schema.py

# Verás: 🎉 All tests passed!
```

---

## 📊 QUÉ INCLUYE

✅ **15 Tablas PostgreSQL:**
- users (con role, company, status)
- transactions (con fraud detection)
- devices (fingerprinting)
- sessions (tracking)
- alerts, cases (fraud management)
- risk_scores, rules, rule_matches
- audit_logs, feature_cache
- + más...

✅ **Datos de Prueba:**
- 5 usuarios (Admin, Analyst, Reviewer, 2 Customers)
- 20+ transacciones
- 3 dispositivos
- 2 sesiones
- Todos set up y listos para testing

✅ **Código Python:**
- `db/models_enhanced.py` - SQLAlchemy ORM models
- `db/database_enhanced.py` - Database connection
- `services/user_service_enhanced.py` - Enhanced service
- `setup_postgres.py` - Automatic setup script
- `test_enhanced_schema.py` - Full test suite

✅ **Documentación:**
- `schema_improved.sql` - Raw SQL (copia/pega directo)
- `POSTGRES_SETUP.md` - Guía estándar
- `DATABASE.md` - Documentación de BD
- `TECHNICAL.md` - API reference

---

## 🔗 URLS IMPORTANTES

| Recurso | URL |
|---------|-----|
| API Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |
| DB Admin (pgAdmin) | http://localhost:5050 |

---

## 🐛 PROBLEMAS COMUNES

### "psql: command not found"
```
→ PostgreSQL no instalado o no en PATH
→ Descargar e instalar desde postgresql.org
```

### "password authentication failed"  
```
→ Cambiar en .env:
DATABASE_URL=postgresql://postgres:NUEVA_PASSWORD@localhost:5432/safemarket
```

### "database 'safemarket' does not exist"
```
→ Correr setup de nuevo:
python setup_postgres.py
```

### "port 5432 already in use"
```
→ PostgreSQL no se cerró correctamente
→ Reinicia Windows o cambia puerto en .env
```

---

## ✅ VALIDAR INSTALACIÓN

### Comando 1: Ver si PostgreSQL corre
```powershell
psql -U postgres -h localhost -l

# Debe mostrar lista de bases de datos
# Una de ellas: safemarket
```

### Comando 2: Contar registros
```powershell
psql -U postgres -h localhost -d safemarket -c "SELECT COUNT(*) FROM users"

# Debe mostrar: 5
```

### Comando 3: Ver todas las tablas
```powershell
psql -U postgres -h localhost -d safemarket -c "\dt"

# Debe mostrar ~15 tablas diferentes
```

---

## 📈 FLUJO DE DATOS

```
┌─────────────────────────────────────────┐
│     Cliente (Frontend)                  │
└──────────────────┬──────────────────────┘
                   │ HTTP Request
                   ▼
┌─────────────────────────────────────────┐
│   FastAPI (main.py)                     │
│   ├─ routers/auth.py                    │
│   ├─ routers/users.py                   │
│   └─ core/security.py                   │
└──────────────────┬──────────────────────┘
                   │ ORM
                   ▼
┌─────────────────────────────────────────┐
│ SQLAlchemy Models (models_enhanced.py)  │
│   ├─ User                               │
│   ├─ Transaction                        │
│   ├─ Device, Session                    │
│   ├─ Alert, Case                        │
│   └─ RiskScore, RuleMatch               │
└──────────────────┬──────────────────────┘
                   │ SQL
                   ▼
┌─────────────────────────────────────────┐
│   PostgreSQL Database                   │
│   15 Tables (users, transactions, ...)  │
│   Seed Data Included                    │
└─────────────────────────────────────────┘
```

---

## 🎯 USUARIOS DE PRUEBA

```
Email: admin@safemarket.io
Pass: SecurePass123!
Role: ADMIN

Email: analyst@safemarket.io
Pass: SecurePass123!
Role: ANALYST

Email: customer1@example.com
Pass: SecurePass123!
Role: VIEWER
```

Todos los usuarios tienen la misma contraseña: `SecurePass123!`

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
backend/
├── schema_improved.sql              # SQL puro (para copy/paste)
├── setup_postgres.py                # Setup automático ← EJECUTAR ESTO
├── test_enhanced_schema.py          # Test suite
├── POSTGRES_SETUP.md                # Guía estándar
├── db/
│   ├── models_enhanced.py           # Modelos SQLAlchemy
│   └── database_enhanced.py         # Conexión a BD
├── services/
│   └── user_service_enhanced.py     # Servicios mejorados
└── .env                             # ← Actualizar DATABASE_URL
```

---

## ⏱️ TIEMPO ESTIMADO

| Tarea | Tiempo |
|-------|--------|
| Instalar PostgreSQL | 5 min |
| Ejecutar setup | 2 min |
| Actualizar .env | 1 min |
| Iniciar API | 1 min |
| Correr tests | 1 min |
| **TOTAL** | **10 min** ✅ |

---

## 🚨 SI ALGO FALLA

1. **Revisar logs de PostgreSQL:** `Program Files\PostgreSQL\15\data\log`
2. **Reintentar setup:** `python setup_postgres.py --reset`
3. **Consultar guía completa:** `POSTGRES_SETUP.md`
4. **Ver error específico:** `test_enhanced_schema.py`

---

## 🎉 SIGUIENTE

Una vez que todo funciona:

1. ✅ API + PostgreSQL corriendo
2. ✅ Datos de prueba cargados
3. ✅ Endpoints testeados

**Ahora puedes:**
- Implementar más endpoints
- Integrar frontend
- Comenzar Fase 2 (Score Engine)
- Deployar a producción

---

**¡Listo en 10 minutos!** ⚡
