# SafeMarket Pocket SDK - Guía de Uso e Integración

## 📖 Introducción

SafeMarket Pocket SDK es un módulo compacto, portátil e integrable que empaqueta las capacidades centrales de prevención de fraude y scoring de riesgo de SafeMarket.

Diseñado para ser usado como librería en aplicativos terceros (CLQ Software, plataformas de pago, marketplaces), el SDK permite:

- **Scoring en tiempo real** (<100ms) sin API remota
- **Configuración flexible** con reglas de negocio personalizables
- **Extracción de datos** para entrenamientos de modelos
- **Explicabilidad** de decisiones de scoring
- **Auditoría completa** de transacciones y feedback

---

## 🚀 Inicio Rápido (5 minutos)

### 1. Instalación

```bash
# El SDK es parte del backend de SafeMarket
# Solo necesitas importarlo en tu aplicativo
```

### 2. Uso Básico

```python
from safemarket_pocket_sdk.integration import SafeMarketAdapter
from safemarket_pocket_sdk.core import Transaction

# Crear adaptador
adapter = SafeMarketAdapter()

# Crear transacción
tx = Transaction(
    id="tx_123",
    amount=1000.0,
    buyer_id="buyer_456",
    seller_id="seller_789"
)

# Obtener decisión
result = adapter.validate_transaction(tx)

print(f"Decision: {result['decision']}")  # APPROVE|MANUAL_REVIEW|DECLINE
print(f"Score: {result['score']}")        # 0-100
print(f"Risk Level: {result['risk_level']}")  # LOW|MEDIUM|HIGH
```

---

## 📚 Documentación Completa

### Interfaz Principal: `SafeMarketAdapter`

La clase `SafeMarketAdapter` es el punto de entrada para integradores:

```python
class SafeMarketAdapter:
    """
    Punto de entrada para scoring de transacciones.
    
    Métodos principales:
    - validate_transaction(tx): Puntúa una transacción
    - set_buyer_data(buyer_id, ...): Configura histórico de buyer
    - set_seller_data(seller_id, ...): Configura histórico de seller
    - add_custom_rule(...): Añade regla personalizada
    - submit_feedback(...): Registra feedback humano
    - get_model_health(): Retorna métricas
    """
```

### Modelos de Datos

#### `Transaction`
Representa una transacción a ser puntuada.

**Parámetros requeridos:**
- `id`: str - Identificador único
- `amount`: float - Monto de la transacción
- `buyer_id`: str - ID del comprador
- `seller_id`: str - ID del vendedor

**Parámetros opcionales:**
```python
Transaction(
    id="tx_123",
    amount=1000.0,
    buyer_id="buyer_456",
    seller_id="seller_789",
    currency="USD",  # default: USD
    category="electronics",
    buyer_email="buyer@example.com",
    buyer_country="US",
    seller_country="CN",
    payment_method="credit_card",
    metadata={...}  # Datos adicionales
)
```

#### `ScoringResult`
Resultado del scoring.

```python
result = adapter.validate_transaction(tx)

# Resultado tiene estos campos:
{
    'transaction_id': 'tx_123',
    'approved': True,           # ¿Fue aprobada?
    'score': 25.0,              # 0-100
    'risk_level': 'LOW',        # LOW|MEDIUM|HIGH
    'decision': 'APPROVE',      # APPROVE|MANUAL_REVIEW|DECLINE
    'risk_factors': [],         # Lista de factores de riesgo
    'confidence': 0.85,         # 0-1
    'reason': 'Low risk score', # Explicación
    'ttl_seconds': 3600,        # Duración del score
    'timestamp': '2026-05-19T...' # ISO timestamp
}
```

---

## 🔧 Casos de Uso Comunes

### Caso 1: Scoring Básico

```python
adapter = SafeMarketAdapter()

tx = Transaction(
    id="tx_001",
    amount=500,
    buyer_id="buyer_123",
    seller_id="seller_456"
)

result = adapter.validate_transaction(tx)

if result['approved']:
    process_payment(tx)
else:
    reject_payment(tx, result['reason'])
```

### Caso 2: Scoring con Datos Históricos

```python
# Configurar históricos de buyer (idealmente de BD)
adapter.set_buyer_data(
    buyer_id="buyer_123",
    tx_count=50,            # Transacciones previas
    avg_amount=500.0,       # Monto promedio
    is_new=False            # ¿Es buyer nuevo?
)

# Scoring ahora considera histórico
result = adapter.validate_transaction(tx)
```

### Caso 3: Reglas Personalizadas

```python
# Rechazar si es buyer nuevo + monto alto
adapter.add_custom_rule(
    name="new_buyer_high_amount",
    condition=lambda f: f.buyer_is_new and f.amount > 5000,
    score_delta=+30,
    severity="HIGH",
    reason="New buyer with high transaction"
)

# Regla se aplica automáticamente
result = adapter.validate_transaction(tx)
```

### Caso 4: Feedback Humano

```python
# Después de revisión manual...
adapter.submit_feedback(
    transaction_id="tx_123",
    label="FRAUD",  # o "LEGITIMATE"
    reviewer_id="reviewer_john",
    notes="Card reported stolen"
)

# Feedback se usa para auditoría y reentrenamiento
```

### Caso 5: Extracción de Datos

```python
from safemarket_pocket_sdk.data import PostgreSQLConnector

# Conectar a BD
connector = PostgreSQLConnector(
    connection_string="postgresql://user:pass@localhost/db",
    transaction_table="transactions"
)

try:
    if connector.validate()[0]:
        # Extraer transacciones
        txs = connector.fetch_transactions(
            limit=10000,
            query="SELECT * FROM transactions WHERE created_at > NOW() - INTERVAL '30 days'"
        )
        
        # Extraer históricos
        buyer_hist = connector.fetch_buyer_history("buyer_123")
        seller_hist = connector.fetch_seller_history("seller_456")
        
        print(f"Buyer history: {buyer_hist}")
finally:
    connector.close()
```

---

## 📊 Features (Características)

El SDK construye automáticamente las siguientes características a partir de una transacción:

| Feature | Descripción | Rango |
|---------|-------------|-------|
| `amount` | Monto normalizado | 0-∞ |
| `amount_z_score` | Z-score del monto vs histórico | -∞ a ∞ |
| `buyer_tx_count` | Transacciones previas del buyer | 0-∞ |
| `buyer_avg_amount` | Monto promedio del buyer | 0-∞ |
| `buyer_is_new` | ¿Es buyer nuevo? | 0-1 |
| `seller_tx_count` | Transacciones previas del seller | 0-∞ |
| `time_of_day` | Hora del día | 0-23 |
| `day_of_week` | Día de la semana | 0-6 |
| `is_weekend` | ¿Es fin de semana? | 0-1 |
| `velocity_1h` | Tx del buyer en última hora | 0-∞ |
| `velocity_24h` | Tx del buyer en últimas 24h | 0-∞ |
| `is_repeated_seller` | ¿Seller repetido? | 0-1 |
| `country_mismatch` | ¿País mismatch? | 0-1 |

---

## ⚙️ Configuración Avanzada

### Config del SDK

```python
from safemarket_pocket_sdk.core import Config

config = Config(
    SCORING_TIMEOUT_MS=100,        # Timeout máximo para scoring
    MIN_SCORE_THRESHOLD=30,        # Score mín para APPROVE
    MAX_SCORE_THRESHOLD=70,        # Score máx para DECLINE
    ENABLE_RULES=True,             # Activar Rules Engine
    MODEL_VERSION="1.0.0",         # Versión del modelo
    LOG_LEVEL="INFO",              # Nivel de logging
    ENVIRONMENT="production"       # Ambiente
)

adapter = SafeMarketAdapter(config=config)
```

### Conectores de Datos

Soportados:
- **PostgreSQL** ✅ Implementado
- **MySQL** 🔄 Pendiente
- **MongoDB** 🔄 Pendiente
- **CSV** 🔄 Pendiente

```python
from safemarket_pocket_sdk.data import PostgreSQLConnector

connector = PostgreSQLConnector(
    connection_string="postgresql://...",
    transaction_table="transactions",
    buyer_table="users",
    seller_table="sellers"
)

# Validar esquema
is_valid, errors = connector.validate()

# Extraer datos
txs = connector.fetch_transactions(limit=5000)
buyer_hist = connector.fetch_buyer_history("buyer_123")
```

---

## 🤖 Entrenamiento de Modelo ML

SafeMarket Pocket SDK incluye capacidades de **Machine Learning** para entrenar modelos de Random Forest.

**Características:**
- 500 registros de entrenamiento embebidos
- Random Forest Classifier (scikit-learn)
- Evaluación automática con train/test split
- Simulación de transacciones
- Métricas detalladas (Accuracy, Precision, Recall, F1)

### Inicio Rápido

```bash
# Ejecutar ejemplo completo
cd backend
python -m safemarket_pocket_sdk.examples.train_and_evaluate
```

### Desde Python

```python
from safemarket_pocket_sdk.ml import TransactionSimulator

# Crear simulador
simulator = TransactionSimulator()

# Entrenar modelo
info = simulator.train_and_save()
print(f"Train Accuracy: {info['train_accuracy']:.1%}")

# Simular transacciones y evaluar
results = simulator.simulate_and_evaluate(n_transactions=5000)
print(f"Accuracy: {results['accuracy']:.1%}")
print(f"Precision: {results['precision']:.1%}")
print(f"Recall: {results['recall']:.1%}")
print(f"F1: {results['f1']:.1%}")
```

**Para documentación completa:**
Ver [TRAINING_GUIDE.md](./TRAINING_GUIDE.md)

---

## 🔐 Seguridad

- **API keys** guardadas en environment variables
- **Datos sensibles** nunca en logs
- **Conexiones SSL/TLS** soportadas
- **Auditoría completa** de decisiones
- **Modelos encriptados** en distribución

---

## 📦 Estructura del Código

```
safemarket_pocket_sdk/
├── core/                    # Configuración, modelos, excepciones
│   ├── config.py           # Configuración
│   ├── models.py           # Transaction, ScoringResult, FeatureSet
│   └── exceptions.py       # Excepciones tipadas
├── scoring/                # Engines de scoring y reglas
│   └── score_engine.py    # ScoreEngine + RulesEngine
├── features/               # Extracción de características
│   └── extractor.py       # FeatureExtractor
├── data/                   # Acceso a datos
│   ├── training_dataset.py # 500 registros embebidos
│   └── connectors/        # PostgreSQL, MySQL, etc
├── ml/                     # Machine Learning
│   ├── model_trainer.py   # Entrenar Random Forest
│   └── simulator.py       # Simular y evaluar
├── integration/            # Punto de entrada para integradores
│   └── adapter.py         # SafeMarketAdapter (USAR ESTO)
└── examples/               # Ejemplos de uso
    ├── standalone_scoring.py
    ├── data_extraction.py
    ├── custom_rules.py
    └── train_and_evaluate.py  # Entrenamiento (NUEVO)
```

---

## 🧪 Ejemplos Completos

Ver directorio `/examples/`:
- `standalone_scoring.py` - Scoring básico
- `data_extraction.py` - Extracción de datos
- `custom_rules.py` - Reglas personalizadas
- `train_and_evaluate.py` - **Entrenamiento ML completo** (NUEVO)

Ejecutar:
```bash
python safemarket_pocket_sdk/examples/standalone_scoring.py
python safemarket_pocket_sdk/examples/train_and_evaluate.py
```

---

## 🆘 Troubleshooting

### Error: "No connection established"
- Verificar que `connector.connect()` se ejecutó
- Verificar credenciales de BD

### Error: "Invalid transaction: buyer_id is required"
- Asegurar que `Transaction` tenga `id`, `amount`, `buyer_id`, `seller_id`

### Error: "No module named 'sklearn'"
- Instalar: `pip install scikit-learn`

### Resultado inesperado
- Verificar que datos históricos están configurados
- Verificar reglas personalizadas
- Ver logs con `LOG_LEVEL=DEBUG`

---

## 📞 Soporte

- **Documentación**: [POCKET_SOFTWARE_PROFILE.md](../POCKET_SOFTWARE_PROFILE.md)
- **Issues**: GitHub repo de SafeMarket
- **Email**: support@safemarket.io

---

## 📝 Licencia

SafeMarket Pocket SDK es propiedad de SafeMarket. Ver LICENSE para detalles.

---

**Última actualización**: Mayo 2026
**Versión**: 1.0.0-alpha
