"""
transaction_validator.py - Validador de transacciones
SafeMarket | Capa de validación antes del motor de scoring.

Verifica que los datos de una transacción entrante estén completos,
sean coherentes y no estén duplicados antes de procesarlos.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import uuid


# ── Resultado de validación ───────────────────────────────────────────────
@dataclass
class ValidationResult:
    is_valid:  bool
    errors:    List[str] = field(default_factory=list)
    warnings:  List[str] = field(default_factory=list)

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)


# ── Tipos y valores válidos (alineados con tu BD) ─────────────────────────
VALID_TYPES       = {"PURCHASE", "TRANSFER", "WITHDRAWAL", "DEPOSIT", "CASH_OUT", "CASH_IN", "PAYMENT", "DEBIT"}
VALID_SOURCES     = {"CARD", "BANK", "WALLET"}
VALID_CURRENCIES  = {"USD", "COP", "EUR", "MXN", "BRL"}
VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}

# Límites de monto por tipo de transacción
AMOUNT_LIMITS = {
    "PURCHASE":   {"min": 0.01,  "max": 50_000_000},
    "TRANSFER":   {"min": 0.01,  "max": 100_000_000},
    "WITHDRAWAL": {"min": 0.01,  "max": 20_000_000},
    "DEPOSIT":    {"min": 0.01,  "max": 500_000_000},
}


class TransactionValidator:
    """
    Valida transacciones entrantes antes de enviarlas al score engine.
    Detecta datos faltantes, incoherencias y posibles duplicados.
    """

    def __init__(self, db=None):
        self.db = db  # SQLAlchemy session (opcional, para validar duplicados en BD)

    def validate(self, tx_data: dict) -> ValidationResult:
        """
        Punto de entrada principal. Ejecuta todas las validaciones.
        Retorna un ValidationResult con errores y warnings.
        """
        result = ValidationResult(is_valid=True)

        self._validate_required_fields(tx_data, result)
        if not result.is_valid:
            return result  # Sin campos requeridos no tiene sentido continuar

        self._validate_amount(tx_data, result)
        self._validate_transaction_type(tx_data, result)
        self._validate_source_type(tx_data, result)
        self._validate_currency(tx_data, result)
        self._validate_ids(tx_data, result)
        self._validate_balance_coherence(tx_data, result)
        self._validate_duplicate(tx_data, result)

        return result

    # ── Validaciones individuales ─────────────────────────────────────────

    def _validate_required_fields(self, tx: dict, result: ValidationResult):
        """Verifica que los campos obligatorios estén presentes."""
        required = ["user_id", "amount", "transaction_type", "source_type", "currency"]
        for f in required:
            if tx.get(f) is None or tx.get(f) == "":
                result.add_error(f"Campo requerido faltante: '{f}'")

    def _validate_amount(self, tx: dict, result: ValidationResult):
        """Verifica que el monto sea positivo y esté dentro del límite permitido."""
        try:
            amount = float(tx.get("amount", 0))
        except (TypeError, ValueError):
            result.add_error("El campo 'amount' debe ser un número válido.")
            return

        if amount <= 0:
            result.add_error(f"El monto debe ser mayor a 0. Recibido: {amount}")
            return

        tx_type = tx.get("transaction_type", "PURCHASE")
        limits  = AMOUNT_LIMITS.get(tx_type, AMOUNT_LIMITS["PURCHASE"])

        if amount < limits["min"]:
            result.add_error(f"Monto {amount} por debajo del mínimo permitido ({limits['min']}) para {tx_type}.")
        if amount > limits["max"]:
            result.add_error(f"Monto {amount} supera el límite máximo ({limits['max']:,}) para {tx_type}.")

        # Warning por montos inusualmente altos
        if amount > 10_000_000:
            result.add_warning(f"Monto inusualmente alto: ${amount:,.2f}. Requiere atención especial.")

    def _validate_transaction_type(self, tx: dict, result: ValidationResult):
        """Verifica que el tipo de transacción sea válido."""
        tx_type = tx.get("transaction_type")
        if tx_type not in VALID_TYPES:
            result.add_error(f"Tipo de transacción inválido: '{tx_type}'. Válidos: {VALID_TYPES}")

    def _validate_source_type(self, tx: dict, result: ValidationResult):
        """Verifica que el tipo de fuente sea válido."""
        source = tx.get("source_type")
        if source and source not in VALID_SOURCES:
            result.add_error(f"Tipo de fuente inválido: '{source}'. Válidos: {VALID_SOURCES}")

    def _validate_currency(self, tx: dict, result: ValidationResult):
        """Verifica que la moneda sea válida."""
        currency = (tx.get("currency") or "").strip().upper()
        if currency and currency not in VALID_CURRENCIES:
            result.add_warning(f"Moneda '{currency}' no reconocida. Puede causar problemas de conversión.")

    def _validate_ids(self, tx: dict, result: ValidationResult):
        """Verifica que user_id y device_id sean UUIDs válidos."""
        for field_name in ["user_id", "device_id"]:
            val = tx.get(field_name)
            if val:
                try:
                    uuid.UUID(str(val))
                except ValueError:
                    result.add_error(f"'{field_name}' no es un UUID válido: {val}")

    def _validate_balance_coherence(self, tx: dict, result: ValidationResult):
        """
        Detecta incoherencias en los saldos.
        Si el saldo anterior era 0 pero el monto es muy alto → sospechoso.
        Si el saldo nuevo es exactamente 0 en TRANSFER → patrón común de fraude.
        """
        try:
            amount          = float(tx.get("amount", 0))
            old_bal_orig    = float(tx.get("old_balance_orig") or 0)
            new_bal_orig    = float(tx.get("new_balance_orig") or 0)
            tx_type         = tx.get("transaction_type", "")

            # Cuenta vaciada completamente en TRANSFER o WITHDRAWAL
            if tx_type in ("TRANSFER", "WITHDRAWAL"):
                if old_bal_orig > 0 and new_bal_orig == 0:
                    result.add_warning(
                        "La cuenta origen quedó con saldo $0 después de la transacción. "
                        "Patrón asociado a fraude en transferencias."
                    )

            # El monto supera el saldo disponible
            if old_bal_orig > 0 and amount > old_bal_orig * 1.05:
                result.add_warning(
                    f"El monto (${amount:,.2f}) supera el saldo disponible (${old_bal_orig:,.2f})."
                )

        except (TypeError, ValueError):
            pass  # Si no hay datos de saldo, simplemente omitir

    def _validate_duplicate(self, tx: dict, result: ValidationResult):
        """
        Detecta posibles transacciones duplicadas consultando la BD.
        Marca como warning si en los últimos 60 segundos existe una transacción
        del mismo usuario, mismo monto y mismo tipo.
        """
        if not self.db:
            return

        try:
            from db.models_enhanced import Transaction
            from sqlalchemy import and_
            from datetime import timedelta

            user_id  = tx.get("user_id")
            amount   = float(tx.get("amount", 0))
            tx_type  = tx.get("transaction_type")
            since    = datetime.utcnow() - timedelta(seconds=60)

            duplicate = self.db.query(Transaction).filter(
                and_(
                    Transaction.user_id    == user_id,
                    Transaction.amount     == amount,
                    Transaction.transaction_type == tx_type,
                    Transaction.created_at >= since,
                )
            ).first()

            if duplicate:
                result.add_warning(
                    f"Posible transacción duplicada detectada. "
                    f"Transacción similar registrada hace menos de 60 segundos "
                    f"(ID: {duplicate.transaction_id})."
                )
        except Exception:
            pass  # No bloquear si la consulta falla
