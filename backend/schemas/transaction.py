"""
Schemas de transacciones.
"""

from pydantic import BaseModel
from datetime import datetime


class TransactionOut(BaseModel):
    id: int
    transaction_id: str
    amount: float
    customer: str
    status: str
    risk_level: str
    date: datetime
    description: str

    class Config:
        from_attributes = True