"""
rules_engine.py - Motor de reglas configurables
SafeMarket | Reglas de negocio antifraude sin necesidad de reentrenar el modelo.

Permite adaptar la lógica a políticas del cliente y responder rápidamente
ante nuevos patrones de fraude detectados.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
from datetime import datetime


# ── Resultado de una regla ────────────────────────────────────────────────
@dataclass
class RuleResult:
    rule_name:    str
    triggered:    bool
    score_delta:  float       # cuánto suma al score de riesgo (-1.0 a +1.0)
    reason:       str = ""
    severity:     str = "LOW" # LOW | MEDIUM | HIGH | CRITICAL


# ── Resultado del motor completo ──────────────────────────────────────────
@dataclass
class RulesEngineResult:
    triggered_rules:  List[RuleResult] = field(default_factory=list)
    total_score_delta: float = 0.0
    max_severity:     str   = "LOW"
    should_block:     bool  = False
    reasons:          List[str] = field(default_factory=list)

    def add(self, result: RuleResult):
        if result.triggered:
            self.triggered_rules.append(result)
            self.total_score_delta += result.score_delta
            self.reasons.append(result.reason)

            # Actualizar severidad máxima
            severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            if severity_order.get(result.severity, 0) > severity_order.get(self.max_severity, 0):
                self.max_severity = result.severity

            # Bloqueo automático si una regla es CRITICAL
            if result.severity == "CRITICAL":
                self.should_block = True


# ── Motor de reglas ───────────────────────────────────────────────────────
class RulesEngine:
    """
    Evalúa un conjunto de reglas de negocio sobre una transacción.
    Cada regla puede aumentar o disminuir el score de riesgo.
    Las reglas son independientes del modelo ML — actúan como capa adicional.
    """

    def evaluate(self, tx: dict, device: dict = None, user_history: dict = None) -> RulesEngineResult:
        """
        Evalúa todas las reglas sobre la transacción.

        Parámetros:
            tx           : datos de la transacción
            device       : datos del dispositivo (de tabla devices)
            user_history : historial del usuario (transacciones previas)

        Retorna RulesEngineResult con todas las reglas disparadas y delta de score.
        """
        result = RulesEngineResult()
        device       = device or {}
        user_history = user_history or {}

        # ── Reglas de monto ───────────────────────────────────────────────
        result.add(self._rule_high_amount(tx))
        result.add(self._rule_round_amount(tx))
        result.add(self._rule_amount_exceeds_history(tx, user_history))

        # ── Reglas de tipo de transacción ─────────────────────────────────
        result.add(self._rule_high_risk_type(tx))
        result.add(self._rule_account_drain(tx))

        # ── Reglas de dispositivo ─────────────────────────────────────────
        result.add(self._rule_untrusted_device(device))
        result.add(self._rule_high_risk_country(device))
        result.add(self._rule_new_device(device))

        # ── Reglas de comportamiento ──────────────────────────────────────
        result.add(self._rule_off_hours(tx))
        result.add(self._rule_velocity(user_history))
        result.add(self._rule_merchant_risk(tx))

        # ── Reglas reductoras de riesgo (factores positivos) ──────────────
        result.add(self._rule_trusted_device(device))
        result.add(self._rule_low_amount(tx))

        # Clamp delta entre -1 y +1
        result.total_score_delta = max(-1.0, min(1.0, result.total_score_delta))

        return result

    # ── REGLAS DE MONTO ───────────────────────────────────────────────────

    def _rule_high_amount(self, tx: dict) -> RuleResult:
        """Transacciones por encima de $10M son de alto riesgo."""
        amount    = float(tx.get("amount", 0))
        triggered = amount > 10_000_000
        return RuleResult(
            rule_name   = "HIGH_AMOUNT",
            triggered   = triggered,
            score_delta = 0.25 if triggered else 0,
            reason      = f"Monto muy alto: ${amount:,.0f}" if triggered else "",
            severity    = "HIGH" if triggered else "LOW",
        )

    def _rule_round_amount(self, tx: dict) -> RuleResult:
        """Montos exactamente redondos son sospechosos (ej: 1000000.00 exacto)."""
        amount    = float(tx.get("amount", 0))
        triggered = amount >= 100_000 and amount % 100_000 == 0
        return RuleResult(
            rule_name   = "ROUND_AMOUNT",
            triggered   = triggered,
            score_delta = 0.10 if triggered else 0,
            reason      = f"Monto sospechosamente redondo: ${amount:,.0f}" if triggered else "",
            severity    = "MEDIUM" if triggered else "LOW",
        )

    def _rule_amount_exceeds_history(self, tx: dict, history: dict) -> RuleResult:
        """Si el monto es 3x mayor al promedio histórico del usuario → sospechoso."""
        amount   = float(tx.get("amount", 0))
        avg      = float(history.get("avg_amount", 0))
        triggered = avg > 0 and amount > avg * 3
        return RuleResult(
            rule_name   = "AMOUNT_EXCEEDS_HISTORY",
            triggered   = triggered,
            score_delta = 0.20 if triggered else 0,
            reason      = f"Monto ${amount:,.0f} es 3x mayor al promedio histórico ${avg:,.0f}" if triggered else "",
            severity    = "HIGH" if triggered else "LOW",
        )

    def _rule_low_amount(self, tx: dict) -> RuleResult:
        """Montos pequeños y habituales reducen el riesgo."""
        amount    = float(tx.get("amount", 0))
        triggered = amount < 50_000
        return RuleResult(
            rule_name   = "LOW_AMOUNT",
            triggered   = triggered,
            score_delta = -0.05 if triggered else 0,
            reason      = "",
            severity    = "LOW",
        )

    # ── REGLAS DE TIPO ────────────────────────────────────────────────────

    def _rule_high_risk_type(self, tx: dict) -> RuleResult:
        """TRANSFER y WITHDRAWAL concentran el 100% del fraude en el dataset."""
        tx_type   = tx.get("transaction_type", "")
        triggered = tx_type in ("TRANSFER", "WITHDRAWAL", "CASH_OUT")
        return RuleResult(
            rule_name   = "HIGH_RISK_TYPE",
            triggered   = triggered,
            score_delta = 0.15 if triggered else 0,
            reason      = f"Tipo de transacción de alto riesgo: {tx_type}" if triggered else "",
            severity    = "MEDIUM" if triggered else "LOW",
        )

    def _rule_account_drain(self, tx: dict) -> RuleResult:
        """
        Cuenta vaciada completamente en una sola transacción.
        Patrón más común de fraude en PaySim y en la vida real.
        """
        old_bal   = float(tx.get("old_balance_orig") or 0)
        new_bal   = float(tx.get("new_balance_orig") or 0)
        tx_type   = tx.get("transaction_type", "")
        triggered = (
            tx_type in ("TRANSFER", "WITHDRAWAL", "CASH_OUT")
            and old_bal > 0
            and new_bal == 0
        )
        return RuleResult(
            rule_name   = "ACCOUNT_DRAIN",
            triggered   = triggered,
            score_delta = 0.40 if triggered else 0,
            reason      = "Cuenta vaciada completamente en una sola operación." if triggered else "",
            severity    = "CRITICAL" if triggered else "LOW",
        )

    # ── REGLAS DE DISPOSITIVO ─────────────────────────────────────────────

    def _rule_untrusted_device(self, device: dict) -> RuleResult:
        """Dispositivo no confiable según la tabla devices."""
        is_trusted = device.get("is_trusted", True)
        trust_score = float(device.get("trust_score") or 0.5)
        triggered  = not is_trusted and trust_score < 0.3
        return RuleResult(
            rule_name   = "UNTRUSTED_DEVICE",
            triggered   = triggered,
            score_delta = 0.20 if triggered else 0,
            reason      = f"Dispositivo no confiable (trust_score: {trust_score})" if triggered else "",
            severity    = "HIGH" if triggered else "LOW",
        )

    def _rule_trusted_device(self, device: dict) -> RuleResult:
        """Dispositivo de confianza reduce el riesgo."""
        is_trusted  = device.get("is_trusted", False)
        trust_score = float(device.get("trust_score") or 0.5)
        triggered   = is_trusted and trust_score > 0.7
        return RuleResult(
            rule_name   = "TRUSTED_DEVICE",
            triggered   = triggered,
            score_delta = -0.10 if triggered else 0,
            reason      = "",
            severity    = "LOW",
        )

    def _rule_new_device(self, device: dict) -> RuleResult:
        """Dispositivo recién registrado (menos de 24h)."""
        created = device.get("created_at")
        if not created:
            return RuleResult("NEW_DEVICE", False, 0)
        try:
            if isinstance(created, str):
                created = datetime.fromisoformat(created)
            age_hours = (datetime.utcnow() - created).total_seconds() / 3600
            triggered = age_hours < 24
            return RuleResult(
                rule_name   = "NEW_DEVICE",
                triggered   = triggered,
                score_delta = 0.15 if triggered else 0,
                reason      = f"Dispositivo registrado hace {age_hours:.1f}h" if triggered else "",
                severity    = "MEDIUM" if triggered else "LOW",
            )
        except Exception:
            return RuleResult("NEW_DEVICE", False, 0)

    def _rule_high_risk_country(self, device: dict) -> RuleResult:
        """País de alto riesgo según la IP del dispositivo."""
        HIGH_RISK_COUNTRIES = {"NG", "RU", "CN", "KP", "IR", "VE"}
        country   = (device.get("country") or "").upper()
        triggered = country in HIGH_RISK_COUNTRIES
        return RuleResult(
            rule_name   = "HIGH_RISK_COUNTRY",
            triggered   = triggered,
            score_delta = 0.25 if triggered else 0,
            reason      = f"Transacción originada en país de alto riesgo: {country}" if triggered else "",
            severity    = "HIGH" if triggered else "LOW",
        )

    # ── REGLAS DE COMPORTAMIENTO ──────────────────────────────────────────

    def _rule_off_hours(self, tx: dict) -> RuleResult:
        """Transacciones entre 1am y 5am son más sospechosas."""
        now       = datetime.utcnow()
        triggered = 1 <= now.hour < 5
        return RuleResult(
            rule_name   = "OFF_HOURS",
            triggered   = triggered,
            score_delta = 0.10 if triggered else 0,
            reason      = f"Transacción fuera de horario habitual ({now.hour}:00 UTC)" if triggered else "",
            severity    = "LOW" if triggered else "LOW",
        )

    def _rule_velocity(self, history: dict) -> RuleResult:
        """Más de 5 transacciones en la última hora → posible ataque de velocidad."""
        tx_last_hour = int(history.get("tx_last_hour", 0))
        triggered    = tx_last_hour >= 5
        return RuleResult(
            rule_name   = "HIGH_VELOCITY",
            triggered   = triggered,
            score_delta = 0.30 if triggered else 0,
            reason      = f"Alta frecuencia: {tx_last_hour} transacciones en la última hora." if triggered else "",
            severity    = "HIGH" if triggered else "LOW",
        )

    def _rule_merchant_risk(self, tx: dict) -> RuleResult:
        """Comercio de alto riesgo según merchant_risk_level."""
        risk      = tx.get("merchant_risk_level", "")
        triggered = risk == "HIGH"
        return RuleResult(
            rule_name   = "HIGH_RISK_MERCHANT",
            triggered   = triggered,
            score_delta = 0.15 if triggered else 0,
            reason      = "Comercio categorizado como alto riesgo." if triggered else "",
            severity    = "MEDIUM" if triggered else "LOW",
        )
