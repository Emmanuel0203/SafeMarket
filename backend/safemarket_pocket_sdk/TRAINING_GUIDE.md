# SafeMarket Pocket SDK - Guía de Entrenamiento y Evaluación

## 🎯 Objetivo

Este documento guía el flujo completo de:
1. **Dataset**: 500 registros de entrenamiento embebidos
2. **Entrenamiento**: Random Forest con scikit-learn
3. **Evaluación**: Simulación de transacciones para medir precisión
4. **Integración**: Uso del modelo en scoring

---

## 📋 Requisitos

```bash
# Instalar dependencias
pip install scikit-learn numpy

# Verificar
python -c "import sklearn; print(f'scikit-learn {sklearn.__version__}')"
```

---

## 🚀 Inicio Rápido

### Opción 1: Ejecutar Ejemplo Completo

```bash
cd backend

# Ejecutar el ejemplo que entrena y evalúa el modelo
python -m safemarket_pocket_sdk.examples.train_and_evaluate
```

Esto generará un archivo `safemarket_fraud_model.pkl` con el modelo entrenado.

### Opción 2: Desde Python

```python
from safemarket_pocket_sdk.ml.simulator import TransactionSimulator

# Crear simulador
simulator = TransactionSimulator()

# Entrenar modelo (500 registros embebidos)
info = simulator.train_and_save()

# Simular 1000 transacciones y evaluar
results = simulator.simulate_and_evaluate(n_transactions=1000)

print(f"Accuracy: {results['accuracy']:.1%}")
print(f"Fraude detectado: {results['fraud_detected']}/{results['fraud_total']}")
```

### Opción 3: Integrar en Aplicativo

```python
from safemarket_pocket_sdk.integration import SafeMarketAdapter
from safemarket_pocket_sdk.core import Transaction

# Crear adaptador (usa el modelo entrenado si existe)
adapter = SafeMarketAdapter()

# Scoring de transacción
tx = Transaction(
    id="tx_123",
    amount=1000.0,
    buyer_id="buyer_456",
    seller_id="seller_789"
)

result = adapter.validate_transaction(tx)
print(f"Score: {result['score']}, Decision: {result['decision']}")
```

---

## 📊 Dataset de Entrenamiento

### Ubicación
```
safemarket_pocket_sdk/data/training_dataset.py
```

### Características
- **500 registros** embebidos (quemados en código)
- **~5% fraude** (realista)
- **12 features** por transacción:
  - `amount`: Monto de la transacción
  - `buyer_tx_count`: Transacciones previas del buyer
  - `buyer_avg_amount`: Monto promedio del buyer
  - `buyer_is_new`: Si es buyer nuevo
  - `seller_tx_count`: Transacciones del seller
  - `time_of_day`: Hora del día (0-23)
  - `day_of_week`: Día de la semana (0-6)
  - `is_weekend`: Si es fin de semana
  - `velocity_24h`: Transacciones en últimas 24h
  - `velocity_1h`: Transacciones en última hora
  - `country_mismatch`: Si hay country mismatch
  - `amount_z_score`: Z-score del monto

### Uso

```python
from safemarket_pocket_sdk.data.training_dataset import (
    get_training_data,
    get_dataset_summary
)

# Obtener dataset
data = get_training_data()
print(f"Registros: {len(data)}")

# Ver estadísticas
summary = get_dataset_summary()
print(f"Fraude: {summary['fraud_percentage']:.1f}%")
```

---

## 🤖 Entrenamiento del Modelo

### Ubicación
```
safemarket_pocket_sdk/ml/model_trainer.py
```

### Algoritmo
- **Random Forest Classifier** (scikit-learn)
- **100 árboles** por defecto
- **Max depth: 15**
- **Class weight: balanced** (maneja desbalance)

### Uso

```python
from safemarket_pocket_sdk.ml.model_trainer import ModelTrainer

# Crear trainer
trainer = ModelTrainer()

# Entrenar (carga dataset automáticamente)
info = trainer.train(n_estimators=100, max_depth=15)

print(f"Train accuracy: {info['train_accuracy']:.1%}")
print(f"Test accuracy: {info['test_accuracy']:.1%}")

# Guardar modelo
trainer.save_model()

# Cargar modelo después
trainer = ModelTrainer()
trainer.load_model()

# Predecir
features = {'amount': 1000, 'buyer_tx_count': 50, ...}
prediction = trainer.predict(features)  # 0 o 1
probability = trainer.predict_probability(features)  # 0-1
```

---

## 🎯 Evaluación y Simulación

### Ubicación
```
safemarket_pocket_sdk/ml/simulator.py
```

### Uso

```python
from safemarket_pocket_sdk.ml.simulator import TransactionSimulator

# Crear simulador
simulator = TransactionSimulator()

# Entrenar y guardar modelo
simulator.train_and_save()

# Simular 5000 transacciones
results = simulator.simulate_and_evaluate(
    n_transactions=5000,
    fraud_rate=0.05  # 5% fraude
)

# Resultados
print(f"Accuracy: {results['accuracy']:.1%}")
print(f"Precision: {results['precision']:.1%}")
print(f"Recall: {results['recall']:.1%}")
print(f"F1: {results['f1']:.1%}")

# Detalles
print(f"Fraude detectado: {results['fraud_detected']}/{results['fraud_total']}")
print(f"Falsos positivos: {results['false_positives']}")
print(f"Falsos negativos: {results['false_negatives']}")
```

### Metricas Explicadas

| Métrica | Explicación | Importante Para |
|---------|------------|-----------------|
| **Accuracy** | % de predicciones correctas | Vista general |
| **Precision** | De los que marcó fraude, cuántos eran reales | Falsos positivos |
| **Recall** | De los fraudes reales, cuántos detectó | Falsos negativos |
| **F1** | Balance entre Precision y Recall | Evaluación general |
| **ROC-AUC** | Área bajo la curva ROC | Ranking de probabilidades |

---

## 📈 Ejemplo Completo

```python
#!/usr/bin/env python3
"""
Ejemplo completo: Entrenar modelo, evaluar, y usar para scoring.
"""

from safemarket_pocket_sdk.ml.simulator import TransactionSimulator
from safemarket_pocket_sdk.integration import SafeMarketAdapter
from safemarket_pocket_sdk.core import Transaction

print("\n=== Paso 1: Entrenar Modelo ===\n")

simulator = TransactionSimulator()
info = simulator.train_and_save()

print(f"✅ Modelo entrenado")
print(f"   Train Accuracy: {info['train_accuracy']:.1%}")
print(f"   Test Accuracy: {info['test_accuracy']:.1%}")

print("\n=== Paso 2: Evaluar Modelo ===\n")

results = simulator.simulate_and_evaluate(n_transactions=2000)

print(f"Accuracy: {results['accuracy']:.1%}")
print(f"Precision: {results['precision']:.1%}")
print(f"Recall: {results['recall']:.1%}")
print(f"F1: {results['f1']:.1%}")

print("\n=== Paso 3: Usar en Scoring ===\n")

adapter = SafeMarketAdapter()

# Test 1: Transacción legítima
tx1 = Transaction(
    id="tx_001",
    amount=500,
    buyer_id="buyer_123",
    seller_id="seller_456"
)

result1 = adapter.validate_transaction(tx1)
print(f"Tx1: {result1['decision']} (Score: {result1['score']:.0f})")

# Test 2: Transacción sospechosa
tx2 = Transaction(
    id="tx_002",
    amount=8000,
    buyer_id="buyer_new",
    seller_id="seller_789",
    buyer_country="US",
    seller_country="CN"
)

result2 = adapter.validate_transaction(tx2)
print(f"Tx2: {result2['decision']} (Score: {result2['score']:.0f})")

print("\n✨ Ejemplo completado\n")
```

---

## 🔍 Troubleshooting

### Error: "No module named 'sklearn'"
```bash
pip install scikit-learn
```

### Error: "Modelo no encontrado"
- El modelo se guarda en `safemarket_fraud_model.pkl`
- Ejecutar `train_and_evaluate.py` primero

### Resultados bajos en métrica X
- **Baja Recall**: Aumentar umbral de decisión
- **Baja Precision**: Aumentar número de árboles (n_estimators)
- **Baja Accuracy**: Necesita más datos de entrenamiento

---

## 📊 Archivos Clave

```
safemarket_pocket_sdk/
├── data/
│   └── training_dataset.py      ← Dataset embebido (500 registros)
├── ml/
│   ├── model_trainer.py         ← Entrenar Random Forest
│   └── simulator.py             ← Simular y evaluar
├── examples/
│   ├── train_and_evaluate.py    ← Ejemplo completo (EJECUTAR ESTO)
│   ├── standalone_scoring.py    ← Scoring básico
│   └── custom_rules.py          ← Reglas personalizadas
└── integration/
    └── adapter.py               ← Interfaz para integradores
```

---

## 🎓 Conceptos Clave

### Train/Test Split
- **80%** para entrenamiento
- **20%** para evaluación (no visto durante entrenamiento)

### Stratified Split
- Mantiene la proporción de fraude en ambos sets
- Importante cuando hay desbalance de clases

### Class Weight = 'balanced'
- Da más peso a la clase minoritaria (fraude)
- Mejora detección de fraude vs falsos positivos

### Z-score
- Medida de cuántas desviaciones estándar está un valor de la media
- Alto Z-score = monto anómalo comparado con histórico

---

## 🚀 Próximos Pasos

1. **Aumentar datos**: Recolectar más transacciones reales
2. **Tuning de hiperparámetros**: GridSearchCV para optimizar
3. **Feature engineering**: Agregar nuevas características
4. **Balanceo de clases**: Oversampling/Undersampling
5. **Ensemble**: Combinar múltiples modelos
6. **Monitoreo en producción**: Tracking de drift de modelo

---

## 📞 Referencia Rápida

```python
# Entrenar
from safemarket_pocket_sdk.ml.model_trainer import ModelTrainer
trainer = ModelTrainer()
trainer.train()

# Simular
from safemarket_pocket_sdk.ml.simulator import TransactionSimulator
sim = TransactionSimulator()
sim.train_and_save()
results = sim.simulate_and_evaluate(n_transactions=5000)

# Usar en scoring
from safemarket_pocket_sdk.integration import SafeMarketAdapter
adapter = SafeMarketAdapter()
result = adapter.validate_transaction(tx)
```

---

**Última actualización**: Mayo 2026  
**Versión**: 1.0.0-alpha
