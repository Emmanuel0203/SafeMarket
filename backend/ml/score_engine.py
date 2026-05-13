"""
score_engine.py - Motor de puntuación de riesgo
SafeMarket | Núcleo del sistema antifraude.

Combina el modelo ML + las reglas de negocio para generar un score
de riesgo final entre 0 y 1, con clasificación low/medium/high
y decisión: APPROVE | MANUAL_REVIEW | DECLINE.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import json

from ml.fraud_model import predict_fraud
from ml.rules_engine import RulesEngine, RulesEngineResult
from ml.transaction_validator import TransactionValidator, ValidationResult


# ── Resultado final del score engine ─────────────────────────────────────
@dataclass
class ScoreResult:
    # Score final combinado (0.0 - 1.0)
    overall_score:     float

    # Componentes individuales
    ml_score:          float   # Score del modelo ML
    rules_delta:       float   # Delta aportado por las reglas

    # Clasificación
    risk_level:        str     # low | medium | high
    decision:          str     # APPROVE | MANUAL_REVIEW | DECLINE
    confidence_level:  float   # Confianza en la decisión (0.0 - 1.0)

    # Detalle
    fraud_probability: float   # % de probabilidad de fraude según ML
    triggered_rules:   List[str] = field(default_factory=list)
    risk_factors:      List[str] = field(default_factory=list)
    explanation:       dict = field(default_factory=dict)
    is_valid:          bool = True
    validation_errors: List[str] = field(default_factory=list)

    def to_db_dict(self) -> dict:
        """Convierte el resultado al formato de la tabla risk_scores de tu BD."""
        return {
            "model_name":        "SafeMarket-RF-v1",
            "model_version":     "1.0.0",
            "overall_score":     round(self.overall_score, 2),
            "fraud_probability": round(self.fraud_probability / 100, 2),
            "anomaly_score":     round(self.rules_delta, 2),
            "score_components":  json.dumps(self.explanation),
            "risk_factors":      self.risk_factors,
            "decision":          self.decision.replace("MANUAL_REVIEW", "MANUAL_REVIEW"),
            "confidence_level":  round(self.confidence_level, 2),
            "explanation":       json.dumps({
                "risk_level":      self.risk_level,
                "triggered_rules": self.triggered_rules,
                "ml_score":        self.ml_score,
                "rules_delta":     self.rules_delta,
            }),
        }


# ── Motor principal ───────────────────────────────────────────────────────
class ScoreEngine:
    """
    Orquesta la validación, el modelo ML y las reglas de negocio
    para producir un score de riesgo final y una decisión.

    Flujo:
        1. Validar la transacción (TransactionValidator)
        2. Obtener score del modelo ML (RandomForest entrenado con PaySim)
        3. Aplicar reglas de negocio (RulesEngine)
        4. Combinar scores y tomar decisión final
        5. Guardar resultado en tabla risk_scores
    """

    # Umbrales de decisión
    APPROVE_THRESHOLD = 0.35   # score < 0.35 → APPROVE
    REVIEW_THRESHOLD  = 0.60   # 0.35 ≤ score < 0.60 → MANUAL_REVIEW
    # score ≥ 0.60 → DECLINE

    # Peso de cada componente en el score final
    ML_WEIGHT    = 0.65   # 65% del score viene del modelo ML
    RULES_WEIGHT = 0.35   # 35% viene de las reglas de negocio

    def __init__(self, db=None):
        self.db        = db
        self.validator = TransactionValidator(db=db)
        self.rules     = RulesEngine()

    def score(self, tx: dict, device: dict = None, user_history: dict = None) -> ScoreResult:
        """
        Calcula el score de riesgo completo de una transacción.

        Parámetros:
            tx           : datos de la transacción (campos de tu tabla transactions)
            device       : datos del dispositivo (campos de tabla devices)
            user_history : historial del usuario {avg_amount, tx_last_hour, ...}

        Retorna ScoreResult con score, decisión y explicación completa.
        """

        # ── 1. Validar ────────────────────────────────────────────────────
        validation: ValidationResult = self.validator.validate(tx)

        if not validation.is_valid:
            return ScoreResult(
                overall_score     = 1.0,
                ml_score          = 1.0,
                rules_delta       = 0.0,
                risk_level        = "high",
                decision          = "DECLINE",
                confidence_level  = 1.0,
                fraud_probability = 100.0,
                risk_factors      = validation.errors,
                triggered_rules   = [],
                explanation       = {"reason": "Transacción inválida", "errors": validation.errors},
                is_valid          = False,
                validation_errors = validation.errors,
            )

        # ── 2. Score ML ───────────────────────────────────────────────────
        try:
            ml_result = predict_fraud(
                amount            = float(tx.get("amount", 0)),
                transaction_type  = tx.get("transaction_type", "PURCHASE"),
                old_balance_orig  = float(tx.get("old_balance_orig") or 0),
                new_balance_orig  = float(tx.get("new_balance_orig") or 0),
                old_balance_dest  = float(tx.get("old_balance_dest") or 0),
                new_balance_dest  = float(tx.get("new_balance_dest") or 0),
            )
            ml_score          = float(ml_result["risk_score"])
            fraud_probability = float(ml_result["fraud_probability"])
        except FileNotFoundError:
            # Si el modelo no está disponible, usar score neutro
            ml_score          = 0.5
            fraud_probability = 50.0
        except Exception:
            ml_score          = 0.5
            fraud_probability = 50.0

        # ── 3. Reglas de negocio ──────────────────────────────────────────
        rules_result: RulesEngineResult = self.rules.evaluate(
            tx=tx,
            device=device or {},
            user_history=user_history or {},
        )

        # ── 4. Score combinado ────────────────────────────────────────────
        # Normalizar el delta de reglas (viene de -1 a +1) → contribución proporcional
        rules_contribution = rules_result.total_score_delta * self.RULES_WEIGHT

        combined = (ml_score * self.ML_WEIGHT) + rules_contribution
        combined = max(0.0, min(1.0, combined))  # clamp 0-1

        # Bloqueo forzado si una regla CRITICAL fue disparada
        if rules_result.should_block:
            combined = max(combined, 0.85)

        # ── 5. Clasificar ─────────────────────────────────────────────────
        if combined < self.APPROVE_THRESHOLD:
            risk_level = "low"
            decision   = "APPROVE"
            confidence = 1.0 - combined
        elif combined < self.REVIEW_THRESHOLD:
            risk_level = "medium"
            decision   = "MANUAL_REVIEW"
            confidence = 0.5
        else:
            risk_level = "high"
            decision   = "DECLINE"
            confidence = combined

        # ── 6. Armar factores de riesgo y explicación ─────────────────────
        risk_factors    = [r.reason for r in rules_result.triggered_rules if r.reason]
        triggered_rules = [r.rule_name for r in rules_result.triggered_rules]

        if validation.warnings:
            risk_factors.extend(validation.warnings)

        explanation = {
            "ml_score":          round(ml_score, 4),
            "ml_weight":         self.ML_WEIGHT,
            "rules_delta":       round(rules_result.total_score_delta, 4),
            "rules_weight":      self.RULES_WEIGHT,
            "combined_score":    round(combined, 4),
            "rules_triggered":   len(triggered_rules),
            "max_rule_severity": rules_result.max_severity,
            "forced_block":      rules_result.should_block,
        }

        return ScoreResult(
            overall_score     = round(combined, 4),
            ml_score          = round(ml_score, 4),
            rules_delta       = round(rules_result.total_score_delta, 4),
            risk_level        = risk_level,
            decision          = decision,
            confidence_level  = round(confidence, 4),
            fraud_probability = round(fraud_probability, 2),
            triggered_rules   = triggered_rules,
            risk_factors      = risk_factors,
            explanation       = explanation,
            is_valid          = True,
            validation_errors = [],
        )

    def score_and_save(self, tx: dict, transaction_id: str,
                       device: dict = None, user_history: dict = None) -> ScoreResult:
        """
        Calcula el score y lo persiste en la tabla risk_scores de la BD.
        """
        result = self.score(tx, device, user_history)

        if self.db and transaction_id:
            try:
                from db.models_enhanced import RiskScore
                import uuid

                db_record = RiskScore(
                    transaction_id    = transaction_id,
                    model_name        = "SafeMarket-RF-v1",
                    model_version     = "1.0.0",
                    overall_score     = result.overall_score,
                    fraud_probability = round(result.fraud_probability / 100, 2),
                    anomaly_score     = max(0.0, min(1.0, result.rules_delta)),
                    score_components  = result.explanation,
                    risk_factors      = result.risk_factors,
                    decision          = result.decision,
                    confidence_level  = result.confidence_level,
                    explanation       = {
                        "risk_level":      result.risk_level,
                        "triggered_rules": result.triggered_rules,
                    },
                )
                self.db.add(db_record)
                self.db.commit()
            except Exception as e:
                self.db.rollback()

        return result
