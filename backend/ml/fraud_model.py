"""
Módulo de predicción de fraude - SafeMarket
Entrenado con dataset PaySim1 (100,000 transacciones reales simuladas)
AUC-ROC: 99.63% | Accuracy: 99.88%
"""

import numpy as np
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "fraud_model.pkl")

# Mapeo de tipos de tu BD → tipos del modelo
TYPE_MAP = {
    'PURCHASE':   'PURCHASE',
    'TRANSFER':   'TRANSFER',
    'WITHDRAWAL': 'WITHDRAWAL',
    'DEPOSIT':    'DEPOSIT',
}

TYPES = ['PURCHASE', 'TRANSFER', 'WITHDRAWAL', 'DEPOSIT']


def _encode(amount, transaction_type, old_balance_orig=0,
            new_balance_orig=0, old_balance_dest=0, new_balance_dest=0):
    """Convierte una transacción en el vector de features que espera el modelo."""
    amount            = float(amount or 0)
    old_balance_orig  = float(old_balance_orig or 0)
    new_balance_orig  = float(new_balance_orig or 0)
    old_balance_dest  = float(old_balance_dest or 0)
    new_balance_dest  = float(new_balance_dest or 0)

    balance_diff_orig = old_balance_orig - new_balance_orig
    balance_diff_dest = new_balance_dest - old_balance_dest
    orig_balance_zero = 1 if new_balance_orig == 0 else 0
    dest_balance_zero = 1 if old_balance_dest == 0 else 0
    amount_log        = float(np.log1p(amount))

    tx_type = TYPE_MAP.get(transaction_type, 'PURCHASE')
    type_features = [1 if tx_type == t else 0 for t in TYPES]

    return [
        amount, amount_log,
        old_balance_orig, new_balance_orig, balance_diff_orig, orig_balance_zero,
        old_balance_dest, new_balance_dest, balance_diff_dest, dest_balance_zero,
        *type_features,
    ]


def get_model_metrics():
    """Retorna las métricas del modelo entrenado."""
    if not os.path.exists(MODEL_PATH):
        return None
    data = joblib.load(MODEL_PATH)
    return data.get('metrics', {})


def predict_fraud(amount, transaction_type,
                  old_balance_orig=0, new_balance_orig=0,
                  old_balance_dest=0, new_balance_dest=0):
    """
    Predice si una transacción es fraudulenta.

    Parámetros:
        amount            : Monto de la transacción
        transaction_type  : PURCHASE | TRANSFER | WITHDRAWAL | DEPOSIT
        old_balance_orig  : Saldo del origen antes de la transacción (opcional)
        new_balance_orig  : Saldo del origen después de la transacción (opcional)
        old_balance_dest  : Saldo del destino antes (opcional)
        new_balance_dest  : Saldo del destino después (opcional)

    Retorna dict con: is_fraud, fraud_probability, risk_score,
                      predicted_status, predicted_risk, explanation
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "El modelo no ha sido entrenado. Contacta al administrador."
        )

    data    = joblib.load(MODEL_PATH)
    model   = data['model']
    features = _encode(
        amount, transaction_type,
        old_balance_orig, new_balance_orig,
        old_balance_dest, new_balance_dest,
    )

    X            = np.array([features])
    fraud_prob   = float(model.predict_proba(X)[0][1])
    is_fraud     = bool(model.predict(X)[0])

    # ── Categorizar según umbral de riesgo ───────────────────────────────
    if fraud_prob < 0.30:
        status = "APPROVED"
        risk   = "LOW"
        explanation = "Transacción dentro de parámetros normales. Aprobada automáticamente."
    elif fraud_prob < 0.60:
        status = "REVIEW"
        risk   = "MEDIUM"
        explanation = "Transacción con indicadores de riesgo moderado. Requiere revisión manual."
    else:
        status = "DECLINED"
        risk   = "HIGH"
        explanation = "Transacción con alta probabilidad de fraude. Bloqueada preventivamente."

    return {
        "is_fraud":            is_fraud,
        "fraud_probability":   round(fraud_prob * 100, 2),
        "risk_score":          round(fraud_prob, 4),
        "predicted_status":    status,
        "predicted_risk":      risk,
        "explanation":         explanation,
    }
