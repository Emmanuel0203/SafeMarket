from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from safemarket_pocket_sdk.integration.adapter import SafeMarketAdapter
from safemarket_pocket_sdk.core import Transaction

router = APIRouter(prefix="/simulate", tags=["Simulator"])


class SimulateRequest(BaseModel):
    transaction_id: Optional[str] = None
    amount: float
    buyer_id: str
    seller_id: str
    currency: Optional[str] = "USD"
    category: Optional[str] = "general"
    use_remote_api: Optional[bool] = False


@router.post("/submit")
def submit_simulation(req: SimulateRequest):
    """Endpoint utilizado por la UI para simular una transacción.

    Usa el `SafeMarketAdapter` embebido; si `use_remote_api` es True,
    el adaptador intentará llamar al endpoint `/sdk/score` remoto.
    """
    try:
        adapter = SafeMarketAdapter(use_remote_api=req.use_remote_api)
        tx = Transaction(
            id=req.transaction_id or f"sim_{int(datetime.utcnow().timestamp())}",
            amount=req.amount,
            buyer_id=req.buyer_id,
            seller_id=req.seller_id,
            currency=req.currency,
            category=req.category,
        )
        result = adapter.validate_transaction(tx)
        return {"ok": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ui", response_class=HTMLResponse)
def simulator_ui():
    """Sirve una página HTML simple para enviar simulaciones desde el navegador."""
    with open("static/simulate.html", "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)
