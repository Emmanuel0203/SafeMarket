"""
Router SDK - SafeMarket
Endpoints para autenticación con API Key (para integración externa).
Permite que el SDK de SafeMarket se autentique sin JWT.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from db import get_db
from ml.score_engine import ScoreEngine

router = APIRouter(prefix="/sdk", tags=["SDK"])


# ── Validación de API Key ─────────────────────────────────────────────────
def validate_api_key(x_api_key: str = Header(..., description="API Key de la empresa cliente")):
    """
    Valida que la API Key sea válida.
    En producción esto consultaría la tabla de empresas en la BD.
    """
    if not x_api_key or not x_api_key.startswith("sm_"):
        raise HTTPException(
            status_code=401,
            detail="API Key inválida. Debe empezar con 'sm_live_' o 'sm_demo_'"
        )
    return x_api_key


# ── Schema de entrada ─────────────────────────────────────────────────────
class SDKScoreRequest(BaseModel):
    user_id:             str
    amount:              float = Field(..., gt=0)
    transaction_type:    str   = Field(..., description="PURCHASE|TRANSFER|WITHDRAWAL|DEPOSIT")
    source_type:         str   = Field("CARD")
    currency:            str   = Field("USD")
    merchant_risk_level: str   = Field("MEDIUM")
    old_balance_orig:    float = Field(0.0)
    new_balance_orig:    float = Field(0.0)
    old_balance_dest:    float = Field(0.0)
    new_balance_dest:    float = Field(0.0)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id":            "uuid-del-usuario",
                "amount":             350000,
                "transaction_type":   "PURCHASE",
                "source_type":        "CARD",
                "currency":           "COP",
                "merchant_risk_level": "LOW",
                "old_balance_orig":   500000,
                "new_balance_orig":   150000,
            }
        }


# ── Endpoint principal del SDK ────────────────────────────────────────────
@router.post("/score")
def sdk_score(
    req:     SDKScoreRequest,
    api_key: str = Depends(validate_api_key),
    db:      Session = Depends(get_db),
):
    """
    Analiza una transacción usando API Key (sin JWT).
    Este endpoint es el que usa el SDK embebible en plataformas externas.
    """
    tx = {
        "user_id":             req.user_id,
        "amount":              req.amount,
        "transaction_type":    req.transaction_type,
        "source_type":         req.source_type,
        "currency":            req.currency,
        "merchant_risk_level": req.merchant_risk_level,
        "old_balance_orig":    req.old_balance_orig,
        "new_balance_orig":    req.new_balance_orig,
        "old_balance_dest":    req.old_balance_dest,
        "new_balance_dest":    req.new_balance_dest,
    }

    try:
        result = ScoreEngine(db=db).score(tx=tx)
        return {
            "overall_score":     result.overall_score,
            "fraud_probability": result.fraud_probability,
            "risk_level":        result.risk_level,
            "decision":          result.decision,
            "confidence_level":  result.confidence_level,
            "triggered_rules":   result.triggered_rules,
            "risk_factors":      result.risk_factors,
            "explanation":       result.explanation,
            "recommendation": (
                "✅ Transacción aprobada."          if result.decision == "APPROVE"
                else "⚠️ Requiere revisión manual." if result.decision == "MANUAL_REVIEW"
                else "🚫 Transacción bloqueada."
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health check del SDK ──────────────────────────────────────────────────
@router.get("/status")
def sdk_status(api_key: str = Depends(validate_api_key)):
    """Verifica que el SDK esté conectado correctamente."""
    return {
        "status":  "connected",
        "version": "1.0.0",
        "message": "✅ SafeMarket SDK conectado correctamente.",
    }
