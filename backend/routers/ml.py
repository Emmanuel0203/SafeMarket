"""
Router ML completo - SafeMarket
Integra: score_engine + rules_engine + transaction_validator + feedback_manager
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from db import get_db
from db.models_enhanced import User
from core.deps import get_current_user
from ml.score_engine import ScoreEngine
from ml.feedback_manager import FeedbackManager, FeedbackType
from ml.fraud_model import get_model_metrics

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


class TransactionScoreRequest(BaseModel):
    user_id:            str
    amount:             float  = Field(..., gt=0)
    transaction_type:   str    = Field(..., description="PURCHASE|TRANSFER|WITHDRAWAL|DEPOSIT")
    source_type:        str    = Field("CARD")
    currency:           str    = Field("USD")
    merchant_risk_level: str   = Field("MEDIUM")
    old_balance_orig:   float  = Field(0.0)
    new_balance_orig:   float  = Field(0.0)
    old_balance_dest:   float  = Field(0.0)
    new_balance_dest:   float  = Field(0.0)
    device_id:          Optional[str]   = None
    device_is_trusted:  Optional[bool]  = None
    device_trust_score: Optional[float] = None
    device_country:     Optional[str]   = None
    device_created_at:  Optional[str]   = None


class FeedbackRequest(BaseModel):
    transaction_id: str
    feedback_type:  FeedbackType
    alert_id:       Optional[str] = None
    notes:          Optional[str] = None


@router.post("/score")
def score_transaction(
    req: TransactionScoreRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tx = {
        "user_id": req.user_id, "amount": req.amount,
        "transaction_type": req.transaction_type, "source_type": req.source_type,
        "currency": req.currency, "merchant_risk_level": req.merchant_risk_level,
        "old_balance_orig": req.old_balance_orig, "new_balance_orig": req.new_balance_orig,
        "old_balance_dest": req.old_balance_dest, "new_balance_dest": req.new_balance_dest,
    }
    device = {}
    if req.device_id:
        device = {"is_trusted": req.device_is_trusted, "trust_score": req.device_trust_score,
                  "country": req.device_country, "created_at": req.device_created_at}
    try:
        result = ScoreEngine(db=db).score(tx=tx, device=device)
        return {
            "overall_score": result.overall_score, "fraud_probability": result.fraud_probability,
            "risk_level": result.risk_level, "decision": result.decision,
            "confidence_level": result.confidence_level, "is_valid": result.is_valid,
            "triggered_rules": result.triggered_rules, "risk_factors": result.risk_factors,
            "explanation": result.explanation, "validation_errors": result.validation_errors,
            "recommendation": (
                "✅ Transacción aprobada automáticamente." if result.decision == "APPROVE"
                else "⚠️ Requiere revisión manual antes de procesar." if result.decision == "MANUAL_REVIEW"
                else "🚫 Transacción bloqueada por alto riesgo de fraude."
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def model_status(current_user: User = Depends(get_current_user)):
    import os
    from ml.fraud_model import MODEL_PATH
    if not os.path.exists(MODEL_PATH):
        return {"model_ready": False, "message": "Modelo no disponible."}
    metrics = get_model_metrics()
    return {
        "model_ready": True, "algorithm": "Random Forest (class_weight=balanced)",
        "trained_with": "100,000 transacciones PaySim1",
        "metrics": {
            "accuracy": f"{metrics.get('accuracy',0)}%", "precision": f"{metrics.get('precision',0)}%",
            "recall": f"{metrics.get('recall',0)}%", "f1_score": f"{metrics.get('f1_score',0)}%",
            "auc_roc": f"{metrics.get('auc_roc',0)}%",
        },
        "thresholds": {"approve": "score < 0.35", "manual_review": "0.35 ≤ score < 0.60", "decline": "score ≥ 0.60"}
    }


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return FeedbackManager(db=db).submit_feedback(
            transaction_id=req.transaction_id, reviewer_id=str(current_user.user_id),
            feedback_type=req.feedback_type, alert_id=req.alert_id, notes=req.notes,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/metrics")
def feedback_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return FeedbackManager(db=db).get_feedback_metrics()


@router.get("/feedback/pending")
def pending_reviews(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return FeedbackManager(db=db).get_pending_review(limit=20)
