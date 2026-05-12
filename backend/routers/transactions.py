from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from db import get_db
from db.models_enhanced import Transaction
from core.deps import get_current_user
from db.models_enhanced import User

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/")
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transactions = (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "transaction_id": str(tx.transaction_id),
            "amount": float(tx.amount),
            "currency": tx.currency.strip() if tx.currency else "USD",
            "destination_merchant": tx.destination_merchant,
            "merchant_category": tx.merchant_category,
            "transaction_type": tx.transaction_type,
            "status": tx.status,
            "risk_level": tx.risk_level,
            "risk_score": float(tx.risk_score) if tx.risk_score else None,
            "is_fraud": tx.is_fraud,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }
        for tx in transactions
    ]


@router.get("/stats")
def get_transaction_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import func

    total = db.query(func.count(Transaction.transaction_id)).scalar() or 0
    total_amount = db.query(func.sum(Transaction.amount)).scalar() or 0
    blocked = db.query(func.count(Transaction.transaction_id)).filter(Transaction.status == "DECLINED").scalar() or 0
    reviewing = db.query(func.count(Transaction.transaction_id)).filter(Transaction.status == "REVIEW").scalar() or 0
    fraud_count = db.query(func.count(Transaction.transaction_id)).filter(Transaction.is_fraud == True).scalar() or 0

    low = db.query(func.count(Transaction.transaction_id)).filter(Transaction.risk_level == "LOW").scalar() or 0
    medium = db.query(func.count(Transaction.transaction_id)).filter(Transaction.risk_level == "MEDIUM").scalar() or 0
    high = db.query(func.count(Transaction.transaction_id)).filter(Transaction.risk_level == "HIGH").scalar() or 0

    return {
        "total_transactions": total,
        "total_sales": float(total_amount),
        "blocked_transactions": blocked,
        "reviewed_transactions": reviewing,
        "fraud_count": fraud_count,
        "protected_income": float(total_amount) * 0.95,
        "risk_level": "Alto" if high > low else "Medio" if medium > low else "Bajo",
        "risk_distribution": {
            "bajo": round((low / total * 100) if total else 0, 1),
            "medio": round((medium / total * 100) if total else 0, 1),
            "alto": round((high / total * 100) if total else 0, 1),
        }
    }