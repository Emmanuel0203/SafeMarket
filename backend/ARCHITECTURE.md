Documentación de Arquitectura - SafeMarket Backend
==============================================

## 🏗️ Visión General del Sistema

SafeMarket es un **sistema híbrido de detección de fraude y análisis de riesgo** para transacciones digitales.

### Componentes Principales

1. **API REST** - Endpoints para operaciones CRUD
2. **Score Engine** - Cálculo de puntaje de riesgo
3. **Rules Engine** - Aplicación de reglas de negocio
4. **Anomaly Detection** - Detección de patrones anómalos
5. **Graph Analysis (ML)** - Análisis de relaciones entre entidades
6. **Manual Review Panel** - Interfaz para revisión manual
7. **Feedback Loop** - Sistema de aprendizaje continuo
8. **Monitoring & Observability** - Logging, métricas, alertas

---

## 📁 Estructura de Directorios Propuesta

```
backend/
├── core/                          # Configuración y utilidades core
│   ├── __init__.py
│   ├── config.py                  # Variables de entorno
│   ├── security.py                # JWT, crypto, tokens
│   └── deps.py                    # Dependencias (get_current_user)
│
├── db/                            # Capa de datos
│   ├── __init__.py
│   ├── database.py                # SQLAlchemy setup
│   ├── models.py                  # Modelos ORM
│   └── migrations/                # Alembic migrations (próximo)
│
├── routers/                       # Endpoints organizados por módulos
│   ├── __init__.py
│   ├── auth.py                    # Autenticación
│   ├── users.py                   # Gestión de usuarios
│   ├── transactions.py            # Transacciones (próximo)
│   ├── scoring.py                 # Endpoints de scoring (próximo)
│   ├── feedback.py                # Feedback loop (próximo)
│   ├── manual_review.py           # Panel de revisión (próximo)
│   └── health.py                  # Health check endpoints
│
├── schemas/                       # Modelos Pydantic para validación
│   ├── __init__.py
│   ├── user.py                    # Schemas de usuario
│   ├── transaction.py             # Schemas de transacción
│   ├── score.py                   # Schemas de scoring (próximo)
│   └── feedback.py                # Schemas de feedback (próximo)
│
├── services/                      # Lógica de negocio
│   ├── __init__.py
│   ├── user_service.py            # CRUD usuarios
│   ├── transaction_service.py     # Gestión de transacciones
│   ├── score_service.py           # Lógica de scoring (próximo)
│   ├── rules_service.py           # Aplicación de reglas (próximo)
│   └── feedback_service.py        # Lógica de feedback (próximo)
│
├── engines/                       # Motores de análisis
│   ├── __init__.py
│   ├── score_engine.py            # Score Engine (próximo)
│   ├── rules_engine.py            # Rules Engine (próximo)
│   ├── anomaly_engine.py          # Detección de anomalías (próximo)
│   └── graph_engine.py            # Graph ML engine (próximo)
│
├── utils/                         # Utilidades
│   ├── __init__.py
│   ├── seed.py                    # Datos de prueba
│   ├── helpers.py                 # Funciones auxiliares (próximo)
│   └── logger.py                  # Logging (próximo)
│
├── main.py                        # Punto de entrada
├── requirements.txt               # Dependencias
├── .env.example                   # Variables de ejemplo
├── TESTING.md                     # Guía de testing
├── ARCHITECTURE.md                # Este archivo
└── README.md                      # Documentación principal
```

---

## 🔄 Flujos de Datos Clave

### 1. Flujo de Registro y Autenticación

```
Cliente
  │
  ├─→ POST /auth/register
  │   │
  │   ├─→ user_service.create_user()
  │   │   ├─→ Hash contraseña (bcrypt)
  │   │   ├─→ Guardar en DB
  │   │   └─→ seed_transactions() [datos demo]
  │   │
  │   └─→ Retornar access_token + user_info
  │
  └─→ POST /auth/login
      │
      ├─→ user_service.get_user_by_email()
      ├─→ verify_password()
      ├─→ create_access_token()
      ├─→ create_refresh_token()
      ├─→ Set cookies (httpOnly)
      └─→ Retornar success
```

### 2. Flujo de Transacción (Futuro)

```
Cliente
  │
  └─→ POST /transactions/analyze
      │
      ├─→ Validar autenticación (JWT)
      ├─→ Guardar transacción en DB
      │
      ├─→ score_engine.calculate_score()
      │   ├─→ Análisis de monto
      │   ├─→ Histórico del cliente
      │   └─→ Geolocalización
      │
      ├─→ rules_engine.apply_rules()
      │   ├─→ Verificar reglas de negocio
      │   ├─→ Aplicar thresholds
      │   └─→ Determinar acción
      │
      ├─→ anomaly_engine.detect()
      │   ├─→ Análisis estadístico
      │   ├─→ Detección de outliers
      │   └─→ Machine Learning
      │
      ├─→ Guardar resultado en DB
      ├─→ Agregar a feedback_queue
      │
      └─→ Retornar:
          {
            "risk_score": 0.75,
            "risk_level": "HIGH",
            "action": "MANUAL_REVIEW",
            "factors": [...],
            "confidence": 0.92
          }
```

### 3. Flujo de Feedback Loop (Futuro)

```
Revisor Manual
  │
  └─→ POST /feedback
      │
      ├─→ Obtener transacción
      ├─→ Enviar veredicto (fraude/legítima)
      │
      ├─→ feedback_service.process_feedback()
      │   ├─→ Guardar en DB
      │   ├─→ Calcular error del modelo
      │   └─→ Agregar a training set
      │
      └─→ Modelo se entrena (offline)
          └─→ Mejora precisión
```

---

## 🛠️ Stack Técnico

### Backend

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Framework | FastAPI | 0.111.0 |
| ASGI Server | Uvicorn | 0.29.0 |
| ORM | SQLAlchemy | 2.0.30 |
| Base de Datos | SQLite/PostgreSQL | - |
| Autenticación | JWT (python-jose) | 3.3.0 |
| Hash | Bcrypt (passlib) | 1.7.4 |
| Validación | Pydantic | 2.7.1 |

### Próximas Tecnologías

- **Detección de Anomalías**: scikit-learn, numpy
- **Análisis de Grafos**: NetworkX, PyG (PyTorch Geometric)
- **ML**: TensorFlow/PyTorch, scikit-learn
- **Bases de Datos**: PostgreSQL, Redis (caché)
- **Monitoreo**: Prometheus, Grafana
- **Logging**: ELK Stack o Datadog
- **Testing**: pytest, pytest-cov
- **CI/CD**: GitHub Actions o GitLab CI

---

## 🔒 Seguridad

### Implementado

✅ Hashing bcrypt para contraseñas  
✅ JWT con expiración configurable  
✅ Cookies httpOnly + SameSite  
✅ CORS configurado  
✅ Validación Pydantic  
✅ Control de acceso RBAC  

### Por Implementar

⏳ Rate limiting  
⏳ HTTPS enforce  
⏳ SQL injection prevention (SQLAlchemy ya lo hace)  
⏳ Input sanitization avanzada  
⏳ Auditoría (quien, qué, cuándo)  
⏳ Encriptación de datos sensibles en reposo  

---

## 📊 Modelos de Base de Datos

### User

```python
User
├── id (PK)
├── name
├── email (UNIQUE)
├── hashed_password
├── company
├── plan (Starter, Pro, Enterprise)
├── role (Admin, Analyst, Viewer)
├── is_active
├── created_at
├── updated_at
└── transactions (rel)
```

### Transaction

```python
Transaction
├── id (PK)
├── transaction_id (UNIQUE)
├── user_id (FK)
├── amount
├── customer
├── status (pending, approved, rejected, manual_review)
├── risk_level (low, medium, high)
├── risk_score (0.0-1.0)
├── date
├── description
├── created_at
└── updated_at
```

### Score (Futuro)

```python
Score
├── id (PK)
├── transaction_id (FK)
├── amount_score
├── frequency_score
├── velocity_score
├── device_score
├── location_score
├── total_score
├── created_at
└── factors (JSON)
```

### Feedback (Futuro)

```python
Feedback
├── id (PK)
├── transaction_id (FK)
├── reviewer_id (FK)
├── actual_label (fraud, legitimate)
├── our_prediction
├── was_correct
├── notes
├── created_at
└── processed
```

---

## 🔚 Puntos de Extensión

### Próximas Fases Ordenadas por Prioridad

#### Fase 2: Scoring Engine (2-3 semanas)
- [ ] Crear modelo Score
- [ ] Implementar score_engine con reglas básicas
- [ ] Endpoints de análisis
- [ ] Tests unitarios

#### Fase 3: Rules Engine (2-3 semanas)
- [ ] Crear motor de reglas configurable
- [ ] Rules management endpoint
- [ ] Aplicar reglas en transacciones
- [ ] Dashboard de reglas

#### Fase 4: Anomaly Detection (3-4 semanas)
- [ ] Análisis estadístico
- [ ] Aislation Forest
- [ ] Integración con scoring
- [ ] Tuning y validación

#### Fase 5: Graph Analysis (3-4 semanas)
- [ ] Modelo de relaciones
- [ ] Graph neural networks
- [ ] Detección de fraude anillo
- [ ] Community detection

#### Fase 6: Manual Review Panel (2-3 semanas)
- [ ] Interfaz web (frontend)
- [ ] Endpoints para revisor
- [ ] Estado de transacción
- [ ] Notas y resolución

#### Fase 7: Feedback Loop (2-3 semanas)
- [ ] Almacenar feedback
- [ ] Análisis de performance
- [ ] Re-entrenamiento automático
- [ ] A/B testing

#### Fase 8: Monitoreo y Observabilidad (2 semanas)
- [ ] Logging centralizado
- [ ] Métricas (Prometheus)
- [ ] Dashboards (Grafana)
- [ ] Alertas

#### Fase 9: Optimización y Escalabilidad (Continuo)
- [ ] Caché con Redis
- [ ] Async tasks (Celery)
- [ ] Database sharding
- [ ] Load balancing

---

## 📝 Convenciones de Código

### Naming

- **Archivos**: `snake_case.py`
- **Clases**: `PascalCase`
- **Funciones**: `snake_case()`
- **Constantes**: `SCREAMING_SNAKE_CASE`

### Estructura de Funciones

```python
def get_user_info(user_id: int, db: Session) -> Optional[User]:
    """
    Breve descripción.
    
    :param user_id: Descripción del parámetro
    :param db: Sesión de base de datos
    :return: Descripción del retorno
    """
    # Implementación
    pass
```

### Endpoints

```python
@router.get("/resource/{id}", response_model=ResponseSchema)
def get_resource(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Descripción del endpoint con detalles de parámetros.
    """
    # Implementación
    pass
```

---

## 🚀 Deployment

### Desarrollo
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Producción
```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Docker (Futuro)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📚 Referencias

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org)
- [Pydantic Docs](https://docs.pydantic.dev)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)

---

**Última actualización:** Abril 2026  
**Versión:** 1.0.0
