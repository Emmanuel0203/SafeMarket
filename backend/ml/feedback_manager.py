"""
feedback_manager.py - Bucle de retroalimentación
SafeMarket | Aprendizaje continuo del sistema antifraude.

Gestiona el feedback de revisores humanos sobre las decisiones del sistema.
Registra si una alerta fue fraude real o falso positivo para mejorar el modelo.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    CONFIRMED_FRAUD    = "CONFIRMED_FRAUD"      # Revisor confirmó que era fraude
    FALSE_POSITIVE     = "FALSE_POSITIVE"       # Era legítima, el sistema se equivocó
    CONFIRMED_LEGIT    = "CONFIRMED_LEGIT"      # Revisor confirmó que era legítima
    SUSPICIOUS_LEGIT   = "SUSPICIOUS_LEGIT"     # Legítima pero con comportamiento inusual


@dataclass
class FeedbackRecord:
    transaction_id:  str
    alert_id:        Optional[str]
    reviewer_id:     str
    feedback_type:   FeedbackType
    notes:           Optional[str]
    created_at:      datetime


class FeedbackManager:
    """
    Gestiona el feedback humano sobre decisiones del sistema antifraude.

    Responsabilidades:
    1. Registrar feedback en la BD (tabla alerts + audit_logs)
    2. Actualizar el estado de la alerta correspondiente
    3. Acumular feedback para reentrenamiento periódico del modelo
    4. Calcular métricas de precisión del sistema
    """

    def __init__(self, db):
        self.db = db

    def submit_feedback(
        self,
        transaction_id: str,
        reviewer_id:    str,
        feedback_type:  FeedbackType,
        alert_id:       Optional[str] = None,
        notes:          Optional[str] = None,
    ) -> dict:
        """
        Registra el feedback de un revisor humano sobre una transacción.

        Parámetros:
            transaction_id : UUID de la transacción revisada
            reviewer_id    : UUID del usuario revisor
            feedback_type  : tipo de feedback (ver FeedbackType)
            alert_id       : UUID de la alerta asociada (opcional)
            notes          : observaciones adicionales del revisor

        Retorna dict con resultado del registro.
        """
        try:
            # 1. Actualizar estado de la alerta si existe
            if alert_id:
                self._resolve_alert(alert_id, reviewer_id, feedback_type)

            # 2. Actualizar el campo is_fraud de la transacción según feedback
            self._update_transaction_fraud_label(transaction_id, feedback_type)

            # 3. Registrar en audit_logs para trazabilidad
            self._log_feedback(transaction_id, reviewer_id, feedback_type, notes)

            self.db.commit()

            return {
                "success":        True,
                "transaction_id": transaction_id,
                "feedback_type":  feedback_type,
                "message":        self._feedback_message(feedback_type),
                "recorded_at":    datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Error al registrar feedback: {str(e)}")

    def get_feedback_metrics(self) -> dict:
        """
        Calcula las métricas de precisión del sistema basadas en el feedback acumulado.

        Retorna tasas de falsos positivos, verdaderos positivos y precisión general.
        """
        try:
            from db.models_enhanced import AuditLog
            from sqlalchemy import func

            logs = self.db.query(AuditLog).filter(
                AuditLog.action.like("FEEDBACK_%")
            ).all()

            total             = len(logs)
            confirmed_fraud   = sum(1 for l in logs if "CONFIRMED_FRAUD"  in (l.action or ""))
            false_positives   = sum(1 for l in logs if "FALSE_POSITIVE"   in (l.action or ""))
            confirmed_legit   = sum(1 for l in logs if "CONFIRMED_LEGIT"  in (l.action or ""))

            precision = (
                round(confirmed_fraud / (confirmed_fraud + false_positives) * 100, 2)
                if (confirmed_fraud + false_positives) > 0 else None
            )

            return {
                "total_feedbacks":     total,
                "confirmed_fraud":     confirmed_fraud,
                "false_positives":     false_positives,
                "confirmed_legit":     confirmed_legit,
                "precision_pct":       precision,
                "false_positive_rate": round(false_positives / total * 100, 2) if total else 0,
                "needs_retraining":    false_positives > 10 or (precision and precision < 70),
            }

        except Exception:
            return {"error": "No se pudieron calcular las métricas de feedback."}

    def get_pending_review(self, limit: int = 20) -> list:
        """
        Retorna las alertas pendientes de revisión humana,
        ordenadas por nivel de riesgo (CRITICAL primero).
        """
        try:
            from db.models_enhanced import Alert, Transaction

            alerts = (
                self.db.query(Alert, Transaction)
                .join(Transaction, Alert.transaction_id == Transaction.transaction_id)
                .filter(Alert.status.in_(["OPEN", "IN_REVIEW"]))
                .order_by(
                    Alert.alert_level.desc(),
                    Alert.created_at.desc(),
                )
                .limit(limit)
                .all()
            )

            return [
                {
                    "alert_id":       str(a.alert_id),
                    "transaction_id": str(t.transaction_id),
                    "alert_level":    a.alert_level,
                    "status":         a.status,
                    "amount":         float(t.amount),
                    "tx_type":        t.transaction_type,
                    "risk_level":     t.risk_level,
                    "risk_score":     float(t.risk_score or 0),
                    "created_at":     a.created_at.isoformat() if a.created_at else None,
                }
                for a, t in alerts
            ]
        except Exception:
            return []

    # ── Métodos internos ──────────────────────────────────────────────────

    def _resolve_alert(self, alert_id: str, reviewer_id: str, feedback_type: FeedbackType):
        """Marca la alerta como resuelta o descartada según el feedback."""
        try:
            from db.models_enhanced import Alert

            alert = self.db.query(Alert).filter(
                Alert.alert_id == alert_id
            ).first()

            if alert:
                alert.status      = "RESOLVED" if feedback_type == FeedbackType.CONFIRMED_FRAUD else "DISMISSED"
                alert.assigned_to = reviewer_id
                alert.resolved_at = datetime.utcnow()
        except Exception:
            pass

    def _update_transaction_fraud_label(self, transaction_id: str, feedback_type: FeedbackType):
        """Actualiza el campo is_fraud de la transacción con la etiqueta confirmada por el revisor."""
        try:
            from db.models_enhanced import Transaction

            tx = self.db.query(Transaction).filter(
                Transaction.transaction_id == transaction_id
            ).first()

            if tx:
                if feedback_type == FeedbackType.CONFIRMED_FRAUD:
                    tx.is_fraud  = True
                    tx.status    = "DECLINED"
                elif feedback_type == FeedbackType.FALSE_POSITIVE:
                    tx.is_fraud  = False
                    tx.status    = "APPROVED"
                elif feedback_type == FeedbackType.CONFIRMED_LEGIT:
                    tx.is_fraud  = False
                    tx.status    = "APPROVED"
        except Exception:
            pass

    def _log_feedback(self, transaction_id: str, reviewer_id: str,
                      feedback_type: FeedbackType, notes: Optional[str]):
        """Registra el feedback en audit_logs para trazabilidad completa."""
        try:
            from db.models_enhanced import AuditLog

            log = AuditLog(
                entity_type = "TRANSACTION",
                entity_id   = str(transaction_id),
                action      = f"FEEDBACK_{feedback_type.value}",
                performed_by = reviewer_id,
                metadata    = {"notes": notes, "feedback_type": feedback_type.value},
            )
            self.db.add(log)
        except Exception:
            pass

    def _feedback_message(self, feedback_type: FeedbackType) -> str:
        messages = {
            FeedbackType.CONFIRMED_FRAUD:  "✅ Fraude confirmado. La transacción ha sido bloqueada y registrada para reentrenamiento.",
            FeedbackType.FALSE_POSITIVE:   "⚠️ Falso positivo registrado. La transacción ha sido aprobada y el modelo será ajustado.",
            FeedbackType.CONFIRMED_LEGIT:  "✅ Transacción legítima confirmada.",
            FeedbackType.SUSPICIOUS_LEGIT: "⚠️ Transacción legítima pero sospechosa registrada para monitoreo.",
        }
        return messages.get(feedback_type, "Feedback registrado.")
