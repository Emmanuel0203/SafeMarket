"""
Router Admin - SafeMarket
Dashboard administrativo solo para roles ADMIN y ANALYST.
Muestra todas las transacciones de todos los clientes con información de empresa.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import Optional

from db import get_db
from db.models_enhanced import Transaction, User, Company, Alert
from core.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# ── Guard de roles ────────────────────────────────────────────────────────
def require_admin_or_analyst(current_user: User = Depends(get_current_user)):
    if current_user.role not in ("ADMIN", "ANALYST"):
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Se requiere rol ADMIN o ANALYST."
        )
    return current_user


# ── 1. Resumen general (KPIs globales) ────────────────────────────────────
@router.get("/stats")
def get_global_stats(
    current_user: User = Depends(require_admin_or_analyst),
    db: Session = Depends(get_db),
):
    """KPIs globales de todas las empresas clientes."""
    total_tx    = db.query(func.count(Transaction.transaction_id)).scalar() or 0
    total_monto = db.query(func.sum(Transaction.amount)).scalar() or 0
    bloqueadas  = db.query(func.count(Transaction.transaction_id)).filter(Transaction.status == "DECLINED").scalar() or 0
    en_revision = db.query(func.count(Transaction.transaction_id)).filter(Transaction.status == "REVIEW").scalar() or 0
    fraudes     = db.query(func.count(Transaction.transaction_id)).filter(Transaction.is_fraud == True).scalar() or 0
    alertas_abiertas = db.query(func.count(Alert.alert_id)).filter(Alert.status == "OPEN").scalar() or 0
    total_empresas = db.query(func.count(Company.company_id)).filter(Company.is_active == True).scalar() or 0
    total_usuarios = db.query(func.count(User.user_id)).filter(User.status == "ACTIVE").scalar() or 0

    return {
        "total_transacciones":  total_tx,
        "monto_total":          float(total_monto),
        "bloqueadas":           bloqueadas,
        "en_revision":          en_revision,
        "fraudes_detectados":   fraudes,
        "alertas_abiertas":     alertas_abiertas,
        "empresas_activas":     total_empresas,
        "usuarios_activos":     total_usuarios,
        "tasa_fraude_pct":      round((fraudes / total_tx * 100) if total_tx else 0, 2),
        "monto_protegido":      float(total_monto) * 0.95,
    }


# ── 2. Todas las transacciones con info de empresa ────────────────────────
@router.get("/transactions")
def get_all_transactions(
    skip:       int = Query(0, ge=0),
    limit:      int = Query(50, ge=1, le=200),
    empresa:    Optional[str] = Query(None, description="Filtrar por nombre de empresa"),
    status:     Optional[str] = Query(None, description="PENDING|APPROVED|DECLINED|REVIEW"),
    risk_level: Optional[str] = Query(None, description="LOW|MEDIUM|HIGH"),
    is_fraud:   Optional[bool] = Query(None, description="Filtrar solo fraudes"),
    current_user: User = Depends(require_admin_or_analyst),
    db: Session = Depends(get_db),
):
    """
    Lista todas las transacciones de todos los clientes.
    Incluye nombre de empresa, email del usuario y nivel de riesgo.
    Solo accesible para ADMIN y ANALYST.
    """
    query = (
        db.query(Transaction, User, Company)
        .join(User, Transaction.user_id == User.user_id)
        .outerjoin(Company, User.company_id == Company.company_id)
    )

    if empresa:
        query = query.filter(Company.name.ilike(f"%{empresa}%"))
    if status:
        query = query.filter(Transaction.status == status)
    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level)
    if is_fraud is not None:
        query = query.filter(Transaction.is_fraud == is_fraud)

    total = query.count()
    results = query.order_by(desc(Transaction.created_at)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "pagina": skip // limit + 1,
        "por_pagina": limit,
        "transacciones": [
            {
                "transaction_id":       str(tx.transaction_id),
                "empresa":              company.name if company else "Sin empresa",
                "empresa_industria":    company.industry if company else None,
                "usuario_email":        user.email,
                "usuario_rol":          user.role,
                "monto":                float(tx.amount),
                "moneda":               tx.currency.strip() if tx.currency else "USD",
                "tipo":                 tx.transaction_type,
                "estado":               tx.status,
                "nivel_riesgo":         tx.risk_level,
                "score_riesgo":         float(tx.risk_score) if tx.risk_score else None,
                "es_fraude":            tx.is_fraud,
                "tipo_fraude":          tx.fraud_type,
                "comercio_destino":     tx.destination_merchant,
                "categoria_comercio":   tx.merchant_category,
                "riesgo_comercio":      tx.merchant_risk_level,
                "fuente":               tx.source_type,
                "fecha":                tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx, user, company in results
        ]
    }


# ── 3. Transacciones agrupadas por empresa ────────────────────────────────
@router.get("/empresas")
def get_stats_por_empresa(
    current_user: User = Depends(require_admin_or_analyst),
    db: Session = Depends(get_db),
):
    """
    Estadísticas de transacciones agrupadas por empresa cliente.
    Permite ver qué empresa tiene más fraudes, más volumen, etc.
    """
    empresas = db.query(Company).filter(Company.is_active == True).all()
    resultado = []

    for empresa in empresas:
        usuarios_ids = [
            u.user_id for u in
            db.query(User.user_id).filter(User.company_id == empresa.company_id).all()
        ]

        # ✅ Mostrar TODAS las empresas aunque no tengan transacciones
        total = 0
        if usuarios_ids:
            total = db.query(func.count(Transaction.transaction_id)).filter(
                Transaction.user_id.in_(usuarios_ids)
            ).scalar() or 0

        monto = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id.in_(usuarios_ids)
        ).scalar() or 0

        fraudes = db.query(func.count(Transaction.transaction_id)).filter(
            Transaction.user_id.in_(usuarios_ids),
            Transaction.is_fraud == True
        ).scalar() or 0

        bloqueadas = db.query(func.count(Transaction.transaction_id)).filter(
            Transaction.user_id.in_(usuarios_ids),
            Transaction.status == "DECLINED"
        ).scalar() or 0

        resultado.append({
            "empresa_id":      str(empresa.company_id),
            "empresa":         empresa.name,
            "industria":       empresa.industry,
            "pais":            empresa.country_code.strip() if empresa.country_code else None,
            "total_tx":        total,
            "monto_total":     float(monto),
            "fraudes":         fraudes,
            "bloqueadas":      bloqueadas,
            "tasa_fraude_pct": round((fraudes / total * 100) if total else 0, 2),
        })

    return sorted(resultado, key=lambda x: x["monto_total"], reverse=True)


# ── 4. Alertas globales abiertas ──────────────────────────────────────────
@router.get("/alertas")
def get_alertas_globales(
    status:   Optional[str] = Query("OPEN", description="OPEN|IN_REVIEW|RESOLVED|DISMISSED"),
    limit:    int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin_or_analyst),
    db: Session = Depends(get_db),
):
    """Alertas de fraude de todas las empresas, ordenadas por criticidad."""
    query = (
        db.query(Alert, Transaction, User, Company)
        .join(Transaction, Alert.transaction_id == Transaction.transaction_id)
        .join(User, Transaction.user_id == User.user_id)
        .outerjoin(Company, User.company_id == Company.company_id)
    )
    if status:
        query = query.filter(Alert.status == status)

    alertas = query.order_by(
        desc(Alert.alert_level),
        desc(Alert.created_at)
    ).limit(limit).all()

    level_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

    return [
        {
            "alert_id":       str(a.alert_id),
            "nivel":          a.alert_level,
            "estado":         a.status,
            "empresa":        company.name if company else "Sin empresa",
            "usuario_email":  user.email,
            "transaction_id": str(tx.transaction_id),
            "monto":          float(tx.amount),
            "tipo_tx":        tx.transaction_type,
            "riesgo":         tx.risk_level,
            "score":          float(tx.risk_score) if tx.risk_score else None,
            "es_fraude":      tx.is_fraud,
            "fecha":          a.created_at.isoformat() if a.created_at else None,
        }
        for a, tx, user, company in alertas
    ]


# ── 5. Detalle de una empresa específica ──────────────────────────────────
@router.get("/empresas/{company_id}")
def get_empresa_detalle(
    company_id: str,
    current_user: User = Depends(require_admin_or_analyst),
    db: Session = Depends(get_db),
):
    """Detalle completo de una empresa: sus usuarios y sus últimas transacciones."""
    empresa = db.query(Company).filter(
        Company.company_id == company_id
    ).first()

    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada.")

    usuarios = db.query(User).filter(User.company_id == company_id).all()
    usuarios_ids = [u.user_id for u in usuarios]

    ultimas_tx = (
        db.query(Transaction)
        .filter(Transaction.user_id.in_(usuarios_ids))
        .order_by(desc(Transaction.created_at))
        .limit(20)
        .all()
    ) if usuarios_ids else []

    total_monto = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id.in_(usuarios_ids)
    ).scalar() or 0

    fraudes = db.query(func.count(Transaction.transaction_id)).filter(
        Transaction.user_id.in_(usuarios_ids),
        Transaction.is_fraud == True
    ).scalar() or 0

    return {
        "empresa": {
            "id":        str(empresa.company_id),
            "nombre":    empresa.name,
            "industria": empresa.industry,
            "pais":      empresa.country_code.strip() if empresa.country_code else None,
            "activa":    empresa.is_active,
            "desde":     empresa.created_at.isoformat() if empresa.created_at else None,
        },
        "resumen": {
            "total_usuarios":  len(usuarios),
            "monto_total":     float(total_monto),
            "fraudes":         fraudes,
        },
        "usuarios": [
            {
                "user_id": str(u.user_id),
                "email":   u.email,
                "rol":     u.role,
                "estado":  u.status,
            }
            for u in usuarios
        ],
        "ultimas_transacciones": [
            {
                "transaction_id": str(tx.transaction_id),
                "monto":          float(tx.amount),
                "tipo":           tx.transaction_type,
                "estado":         tx.status,
                "riesgo":         tx.risk_level,
                "score":          float(tx.risk_score) if tx.risk_score else None,
                "es_fraude":      tx.is_fraud,
                "fecha":          tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in ultimas_tx
        ]
    }
