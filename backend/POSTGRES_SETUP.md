# 🚀 PostgreSQL Enhanced Schema - Setup Guide

**Versión:** 1.0.0  
**Base de Datos:** PostgreSQL 13+  
**Fecha:** Abril 2026

---

## 📋 Contenido

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación PostgreSQL](#instalación-postgresql)
3. [Setup Automático](#setup-automático)
4. [Setup Manual](#setup-manual)
5. [Integración con API](#integración-con-api)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## ✅ Requisitos Previos

### Software Necesario
```bash
✅ PostgreSQL 13+ (https://www.postgresql.org/download/)
✅ Python 3.9+ (Ya tienes)
✅ pip (Ya tienes)
```

### Verificar Instalación
```powershell
# Verificar PostgreSQL
psql --version

# Tema deber ser algo como: psql (PostgreSQL) 15.X
```

### Paquetes Python Requeridos
```bash
pip install psycopg2-binary
pip install sqlalchemy
pip install python-multipart
```

---

## 🔧 Instalación PostgreSQL (Windows)

### Opción 1: Instalador Oficial (Recomendado)

1. Descargar: https://www.postgresql.org/download/windows/
2. Ejecutar instalador
3. Default settings, **RECORDAR LA CONTRASEÑA DEL USUARIO `postgres`**
4. Puerto: 5432 (default)
5. Componentes: ✅ PostgreSQL Server, ✅ pgAdmin

### Opción 2: Windows Subsystem for Linux (WSL)
```bash
# En WSL (PowerShell/Bash)
wsl
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
```

### Verificar PostgreSQL está corriendo
```powershell
# Windows: Verificar en Services (services.msc) que postgresql está running
# O desde PowerShell:
psql -U postgres -h localhost -l

# Debe mostrar lista de bases de datos
```

---

## 🤖 Setup Automático (RECOMENDADO)

### Paso 1: Navegar al directorio backend
```powershell
cd c:\Eaq\Proyectos\SafeMarket\Aplicativo\safemarket_proyecto\backend
```

### Paso 2: Ejecutar script setup
```powershell
# Primero, activar venv si no está activo
.\env\Scripts\Activate.ps1

# Luego ejecutar setup
python setup_postgres.py

# Output esperado:
# ✅ Database 'safemarket' created successfully
# ✅ SQL script executed: schema_improved.sql
# ✅ Connection test passed!
# ✅ Users: 5
# ✅ Transactions: 20
# ✅ Devices: 3
```

### Resultado
- ✅ Base de datos creada
- ✅ Schema completo con 15 tablas
- ✅ Datos de prueba cargados
- ✅ Listo para usar

---

## 💻 Setup Manual

Si el automático falla, hazlo manualmente:

### Paso 1: Conectar a PostgreSQL
```powershell
# Abre psql (CLI de PostgreSQL)
psql -U postgres -h localhost

# Te pedirá contraseña (la que pusiste en instalación)
```

### Paso 2: Crear Base de Datos
```sql
-- En psql, ejecuta:
CREATE DATABASE safemarket;

-- Salir con \q
\q
```

### Paso 3: Cargar Schema
```powershell
# De regreso en PowerShell
cd c:\Eaq\Proyectos\SafeMarket\Aplicativo\safemarket_proyecto\backend

# Ejecutar script SQL
psql -U postgres -h localhost -d safemarket -f schema_improved.sql

# Output esperado:
# CREATE EXTENSION
# CREATE EXTENSION
# CREATE TABLE
# CREATE INDEX
# ... (muchas líneas)
# INSERT 0 5
# INSERT 0 20
# ✅ Database schema and seed data loaded successfully!
```

---

## 🔌 Integración con API

### Paso 1: Actualizar `.env`

Abrir `.env` en raíz del proyecto y configurar PostgreSQL:

```ini
# Cambiar DATABASE_URL
DATABASE_URL=postgresql://postgres:tu_contraseña@localhost:5432/safemarket

# O si usaste contraseña por defecto:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/safemarket
```

### Paso 2: Actualizar `core/config.py`

El archivo ya soporta PostgreSQL, pero verifica:

```python
# core/config.py debe tener:
DATABASE_URL = settings("DATABASE_URL", 
    default="postgresql://postgres:postgres@localhost:5432/safemarket",
    cast=str
)
```

### Paso 3: Actualizar `main.py`

Cambiar los imports para usar los nuevos modelos:

```python
# CAMBIAR DE:
from db.models import User, Transaction

# A:
from db.models_enhanced import User, Transaction, Device, Session as DBSession
```

### Paso 4: Actualizar `routers/users.py`

Usar el servicio mejorado:

```python
# CAMBIAR DE:
from services.user_service import UserService

# A:
from services.user_service_enhanced import EnhancedUserService as UserService
```

---

## 🧪 Testing

### Test 1: Verificar Conexión PostgreSQL
```powershell
cd backend

python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='safemarket',
        user='postgres',
        password='postgres'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    print(f'✅ Connected! Users in DB: {cursor.fetchone()[0]}')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### Test 2: Ejecutar Test Suite Completo
```powershell
# Primero, iniciar API (en otra ventana PowerShell)
cd backend
python main.py

# En primera ventana:
python test_enhanced_schema.py

# Output esperado:
# ✅ API is healthy
# ✅ User registration successful
# ✅ User login successful
# ✅ Profile retrieved successfully
# ✅ Users retrieved: 5
# 🎉 All tests passed!
```

### Test 3: Verificar Tablas en PostgreSQL
```powershell
psql -U postgres -h localhost -d safemarket -c "\dt"

# Debe mostrar (presencia es suficiente):
# users | public | table | postgres
# transactions | public | table | postgres
# devices | public | table | postgres
# sessions | public | table | postgres
# ... (15 tablas totales)
```

### Test 4: Ver Datos de Prueba
```powershell
psql -U postgres -h localhost -d safemarket

# En psql:
SELECT email, role, status FROM users LIMIT 5;

-- Resultado esperado:
-- email                 | role    | status
-- admin@safemarket.io   | ADMIN   | ACTIVE
-- analyst@safemarket.io | ANALYST | ACTIVE
```

---

## 🚀 Flujo Completo: De Cero a Funcional

### 1. Instalar PostgreSQL (5 min)
```powershell
# Descargar e instalar desde: https://www.postgresql.org/download/windows/
```

### 2. Setup Automático (2 min)
```powershell
cd c:\Eaq\Proyectos\SafeMarket\Aplicativo\safemarket_proyecto\backend
.\env\Scripts\Activate.ps1
python setup_postgres.py
```

### 3. Actualizar .env (1 min)
```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/safemarket
```

### 4. Iniciar API (1 min)
```powershell
cd backend
python main.py
```

### 5. Correr Tests (2 min)
```powershell
# Nueva ventana PowerShell
cd backend
python test_enhanced_schema.py
```

### ✅ ¡Listo!
Todo funcionando. Accede a:
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐛 Troubleshooting

### Error: "psql: command not found"
```powershell
# PostgreSQL no está en PATH
# Solución:
# 1. Reinstalar PostgreSQL
# 2. O agregar manualmente a PATH:
#    C:\Program Files\PostgreSQL\15\bin
```

### Error: "FATAL: password authentication failed"
```powershell
# Contraseña incorrecta
# Opción 1: Resetear contraseña
# Buscar pg_hba.conf y editar authentication method

# Opción 2: Usar psql sin contraseña si localhost
psql -U postgres -h localhost --password

# Opción 3: Resetear contraseña con:
ALTER USER postgres PASSWORD 'nueva_contraseña';
```

### Error: "database 'safemarket' does not exist"
```powershell
# Run setup again:
python setup_postgres.py

# Si falla, resetear completo:
python setup_postgres.py --reset
```

### Error: "port 5432 already in use"
```powershell
# Cambiar puerto en config
# DATABASE_URL=postgresql://postgres:postgres@localhost:5433/safemarket
# (nota: 5433 en lugar de 5432)

# O encontrar proceso usando puerto:
netstat -ano | findstr :5432
taskkill /PID {PID}
```

### Error: "relation 'users' does not exist"
```powershell
# Schema no fue cargado correctamente
# Solución:
python setup_postgres.py --reset

# Verificar tablas creadas:
psql -U postgres -h localhost -d safemarket -c "\dt"
```

### API Lento o Timeouts
```python
# Editar db/database_enhanced.py:
# Aumentar timeout y pool size:

engine = create_engine(
    DATABASE_URL,
    pool_size=30,  # Aumentar de 20
    max_overflow=50,  # Aumentar de 40
    pool_pre_ping=True,
    connect_args={"connect_timeout": 30}  # Aumentar timeout
)
```

---

## 📊 Comandos Útiles PostgreSQL

### Ver Estado
```sql
-- Conecta primero:
-- psql -U postgres -h localhost -d safemarket

-- Ver todas las tablas
\dt

-- Ver estructura de tabla
\d users

-- Contar registros
SELECT tablename, (SELECT COUNT(*) FROM information_schema.tables 
  WHERE table_schema = 'public') as count
FROM pg_tables WHERE tableschema = 'public';

-- Ver índices
\di

-- Ver todas las conexiones
SELECT * FROM pg_stat_activity;
```

### Backup
```bash
# Backup completo
pgdump -U postgres safemarket > safemarket_backup.sql

# Restore
psql -U postgres safemarket < safemarket_backup.sql
```

---

## 📈 Verificar Datos de Prueba

```powershell
psql -U postgres -h localhost -d safemarket

-- Dentro de psql:
-- Ver usuarios
SELECT user_id, email, role, status, created_at FROM users LIMIT 5;

-- Ver transacciones
SELECT transaction_id, amount, status, is_fraud, created_at FROM transactions LIMIT 5;

-- Ver dispositivos
SELECT device_id, device_name, device_type, risk_level FROM devices LIMIT 5;

-- Ver sesiones
SELECT session_id, login_time, risk_level, status FROM sessions LIMIT 5;

-- Estadísticas
SELECT 
  (SELECT COUNT(*) FROM users) as users,
  (SELECT COUNT(*) FROM transactions) as transactions,
  (SELECT COUNT(*) FROM devices) as devices,
  (SELECT COUNT(*) FROM alerts) as alerts;
```

---

## ✨ Próximos Pasos

1. **Implementar Endpoints Faltantes**
   - POST /transactions (crear)
   - GET /transactions/{id}
   - GET /devices
   - GET /sessions
   - GET /alerts

2. **Implementar Score Engine (Fase 2)**
   - Calcular risk_scores automáticamente
   - Aplicar rules engine
   - Generar alerts

3. **Implementar MLOps**
   - Feature engineering automático
   - Modelo de fraude
   - Ground truth feedback loop

4. **Production Deployment**
   - Docker containerization
   - PostgreSQL en RDS/Cloud
   - Redis caching
   - CI/CD pipeline

---

## 📞 Soporte

**Contacto:** Developer team  
**Documentación:** Desplazarse a TECHNICAL.md, DATABASE.md  
**Logs:** `logs/` directory

---

**¡Configuración completa de PostgreSQL lista!** 🎉
