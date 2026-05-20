# SafeMarket Pocket Software - Perfil Estratégico

## 🎯 Visión General

**SafeMarket Pocket SDK** es un módulo compacto, modular e integrable que empaqueta las capacidades centrales de prevención de fraude de SafeMarket para ser usado como librería en aplicativos terceros (ej: CLQ Software, plataformas de pago, marketplaces).

### Características Principales

| Característica | Descripción |
|---|---|
| **Scoring Rápido** | Genera score de riesgo 0-100 en <100ms |
| **Rules Engine** | Aplica reglas de negocio configurables sin reentrenamiento |
| **Feature Extraction** | Construye variables de riesgo en tiempo real |
| **Data Connectors** | Extrae datos de múltiples BD para entrenamientos |
| **Explicabilidad** | Retorna factores de riesgo y decisión |
| **Zero Dependencies** | Puede funcionar sin API REST (standalone) |
| **Pluggable** | Arquitectura basada en interfaces para extensión |

---

## 🏗️ Arquitectura del Pocket Software

```
safemarket_pocket_sdk/
│
├── __init__.py                          # Punto de entrada principal
├── core/
│   ├── config.py                        # Configuración del SDK
│   ├── models.py                        # Modelos base (Transaction, Score, etc)
│   └── exceptions.py                    # Excepciones del SDK
│
├── scoring/
│   ├── score_engine.py                  # Motor de scoring
│   ├── rules_engine.py                  # Motor de reglas
│   └── fraud_model.py                   # Modelo ML portátil
│
├── features/
│   ├── extractor.py                     # Extractor de características
│   ├── builders.py                      # Builders de variables de riesgo
│   └── validation.py                    # Validación de transacciones
│
├── data/
│   ├── connectors/
│   │   ├── base.py                      # Interfaz base de conectores
│   │   ├── postgresql.py                # Conector PostgreSQL
│   │   ├── mysql.py                     # Conector MySQL
│   │   ├── mongo.py                     # Conector MongoDB
│   │   └── csv.py                       # Conector CSV
│   │
│   ├── extractors.py                    # Lógica de extracción
│   └── schema.py                        # Esquema de datos esperados
│
├── integration/
│   ├── api_client.py                    # Cliente HTTP para SafeMarket API
│   ├── webhooks.py                      # Manejadores de webhooks
│   └── adapters.py                      # Adaptadores para integraciones
│
├── utils/
│   ├── logger.py                        # Logging
│   ├── validators.py                    # Validadores
│   └── helpers.py                       # Funciones auxiliares
│
├── cli/
│   ├── commands.py                      # Comandos CLI
│   └── __main__.py                      # Punto de entrada CLI
│
└── examples/
    ├── standalone_scoring.py            # Ejemplo: scoring sin API
    ├── with_api_integration.py          # Ejemplo: con API REST
    ├── data_extraction.py               # Ejemplo: extracción de datos
    └── custom_rules.py                  # Ejemplo: reglas personalizadas
```

---

## 🔌 Modos de Integración

### 1. **Standalone (Sin API)**
```python
from safemarket_pocket_sdk import SafeMarketSDK

sdk = SafeMarketSDK()
score = sdk.score_transaction(transaction_data)
# Retorna: {score: 75, risk_level: "HIGH", decision: "MANUAL_REVIEW"}
```

### 2. **Integración con API SafeMarket**
```python
sdk = SafeMarketSDK(
    api_url="https://api.safemarket.io",
    api_key="sk_live_xxx"
)
score = sdk.score_transaction(transaction_data)
# Remotamente: scoring + reglas + feedback
```

### 3. **Integración con Aplicativo Tercero (CLQ Software)**
```python
# CLQ Software importa el SDK
from safemarket_pocket_sdk.integration import SafeMarketAdapter

adapter = SafeMarketAdapter(config={...})
result = adapter.validate_transaction(transaction)
# CLQ obtiene: {approved: bool, score: float, reason: str}
```

---

## 📊 Flujos de Datos

### Flujo 1: Scoring en Tiempo Real
```
Transacción Externa
    ↓
[Feature Extraction] → Variables de riesgo
    ↓
[Score Engine] → Score ML (0-100)
    ↓
[Rules Engine] → Aplicar reglas → Score final
    ↓
[Decision] → APPROVE | MANUAL_REVIEW | DECLINE
    ↓
Resultado a Aplicativo Externo
```

### Flujo 2: Extracción de Datos para Entrenamientos
```
BD Externa (PostgreSQL/MySQL/Mongo)
    ↓
[DataConnector] → Valida conexión + esquema
    ↓
[DataExtractor] → Obtiene transacciones etiquetadas
    ↓
[FeatureBuilder] → Construye dataset
    ↓
Archivo CSV/Parquet
    ↓
[API SafeMarket] → Envía para reentrenamiento
```

### Flujo 3: Retroalimentación Humana
```
Caso MANUAL_REVIEW
    ↓
Reviewer clasifica: [FRAUD | LEGITIMATE]
    ↓
[FeedbackLoop] → Registra decisión + transacción
    ↓
[Model Retraining] → SafeMarket backend
    ↓
Modelo mejorado
```

---

## 🔧 Capacidades de Extracción de Datos

### Conectores Soportados

| Conector | Estado | Uso |
|---|---|---|
| PostgreSQL | ✅ Implementado | BD principal recomendada |
| MySQL | 🔄 Pendiente | Alternativa relacional |
| MongoDB | 🔄 Pendiente | BD NoSQL |
| CSV | ✅ Implementado | Importación manual |
| REST API | 🔄 Pendiente | APIs tercero |

### Funcionalidad de Extracción

```python
from safemarket_pocket_sdk.data import DataExtractor

extractor = DataExtractor(
    source="postgresql",
    connection_string="postgresql://user:pass@localhost/db",
    query="SELECT * FROM transactions WHERE created_at > NOW() - INTERVAL '30 days'"
)

# Valida conexión y esquema
if extractor.validate():
    # Extrae y construye features
    dataset = extractor.extract_and_build_features(
        label_column="is_fraud",
        training=True  # Prepara para entrenamiento
    )
    
    # Exporta dataset
    dataset.to_csv("safemarket_training_data.csv")
    dataset.to_parquet("safemarket_training_data.parquet")
```

---

## 📡 Interfaz de Integración Externa

### API del SDK para Terceros

```python
class SafeMarketAdapter:
    """
    Adaptador para integración con aplicativos externos.
    Implementa interfaz estándar de scoring.
    """
    
    def validate_transaction(self, transaction: dict) -> ScoringResult:
        """
        Valida y puntúa una transacción.
        
        Args:
            transaction: {
                "id": str,
                "amount": float,
                "currency": str,
                "buyer_id": str,
                "seller_id": str,
                "timestamp": datetime,
                ...
            }
        
        Returns:
            ScoringResult: {
                "transaction_id": str,
                "approved": bool,
                "score": float,  # 0-100
                "risk_level": str,  # LOW|MEDIUM|HIGH
                "factors": [str],  # Factores de riesgo
                "confidence": float,  # 0-1
                "ttl": int  # Segundos hasta cache expiry
            }
        """
    
    def get_case_status(self, case_id: str) -> dict:
        """Obtiene estado de un caso en MANUAL_REVIEW."""
    
    def submit_feedback(self, transaction_id: str, label: str) -> bool:
        """Registra feedback humano para reentrenamiento."""
    
    def get_model_health(self) -> dict:
        """Retorna métricas de salud del modelo."""
```

---

## 🚀 Beneficios para Integradores

| Beneficio | Descripción |
|---|---|
| **Bajo Acoplamiento** | El SDK es independiente, puede vivir en el mismo repo o como paquete |
| **Sin Latencia de Red** | Scoring local en <100ms sin llamadas remotas |
| **Configuración Flexible** | Reglas, modelos y umbrales ajustables por cliente |
| **Explicabilidad** | Cada decisión incluye factores y scores componentes |
| **Escalabilidad** | Funciona en monolitos, microservicios, serverless |
| **Auditoría Completa** | Todas las decisiones quedan registradas |

---

## 📋 Roadmap de Implementación

### Fase 1: MVP del Pocket SDK ✅ (Semana 1-2)
- [ ] Estructura modular del SDK
- [ ] Score Engine + Rules Engine portátil
- [ ] Feature Extractor básico
- [ ] Conector PostgreSQL
- [ ] Ejemplos de integración

### Fase 2: Extracción de Datos 🔄 (Semana 2-3)
- [ ] DataExtractor completo
- [ ] Conectores MySQL, MongoDB
- [ ] Schema validation
- [ ] Pipeline de entrenamiento

### Fase 3: Integración API ⏳ (Semana 3-4)
- [ ] Cliente HTTP para SafeMarket API
- [ ] Webhooks de feedback
- [ ] Sincronización de modelos
- [ ] Monitoreo remoto

### Fase 4: Documentación y Ejemplos ⏳ (Semana 4-5)
- [ ] Guía de integración para CLQ
- [ ] Ejemplos completos
- [ ] Docstrings exhaustivos
- [ ] Tests de integración

---

## 📖 Documentación de Funcionalidades

Cada módulo del SDK incluirá:

1. **Docstrings en Función** - Qué hace, parámetros, retorno, excepciones
2. **Ejemplos de Uso** - Casos de uso comunes
3. **Interfaz Clara** - Contratos bien definidos
4. **Manejo de Errores** - Excepciones tipadas
5. **Logging Detallado** - Trazas para debugging

---

## 🔐 Consideraciones de Seguridad

- API keys se guardan en environment variables
- Datos sensibles nunca se guardan en logs
- Conexiones a BD soportan SSL/TLS
- Modelos ML se distribuyen encriptados
- Todas las operaciones son auditables

---

## 📞 Soporte para Integradores

Los integradores (como CLQ Software) tendrán acceso a:

- **SDK de bolsillo** - Importable como librería Python
- **API REST** - Para usuarios que prefieren HTTP
- **CLI** - Para operaciones batch
- **Documentación** - Docstrings, guías, ejemplos
- **Webhook Support** - Para eventos de retro-alimentación

---

**Siguiente Paso:** Crear estructura modular del SDK en [safemarket_pocket_sdk/](safemarket_pocket_sdk/)
