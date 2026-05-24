"""
tests/test_antifraude.py
Pruebas unitarias e integración para los 4 módulos del sistema antifraude SafeMarket.

Cubre:
  - transaction_validator.py
  - rules_engine.py
  - score_engine.py
  - feedback_manager.py
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml.transaction_validator import TransactionValidator, ValidationResult
from ml.rules_engine import RulesEngine, RulesEngineResult
from ml.score_engine import ScoreEngine, ScoreResult


# ══════════════════════════════════════════════════════════════════════════
# FIXTURES REUTILIZABLES
# ══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def tx_valida():
    """Transacción completamente válida — caso base."""
    return {
        "user_id":            "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
        "amount":             350000.0,
        "transaction_type":   "PURCHASE",
        "source_type":        "CARD",
        "currency":           "COP",
        "merchant_risk_level": "LOW",
        "old_balance_orig":   500000.0,
        "new_balance_orig":   150000.0,
        "old_balance_dest":   0.0,
        "new_balance_dest":   350000.0,
    }

@pytest.fixture
def tx_fraude():
    """Transacción con patrón clásico de fraude — cuenta vaciada en TRANSFER."""
    return {
        "user_id":            "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
        "amount":             5000000.0,
        "transaction_type":   "TRANSFER",
        "source_type":        "BANK",
        "currency":           "COP",
        "merchant_risk_level": "HIGH",
        "old_balance_orig":   5000000.0,
        "new_balance_orig":   0.0,
        "old_balance_dest":   0.0,
        "new_balance_dest":   5000000.0,
    }

@pytest.fixture
def device_confiable():
    return {
        "is_trusted":   True,
        "trust_score":  0.92,
        "country":      "CO",
        "created_at":   (datetime.utcnow() - timedelta(days=90)).isoformat(),
    }

@pytest.fixture
def device_sospechoso():
    return {
        "is_trusted":   False,
        "trust_score":  0.15,
        "country":      "NG",
        "created_at":   (datetime.utcnow() - timedelta(hours=2)).isoformat(),
    }

@pytest.fixture
def validator():
    return TransactionValidator(db=None)

@pytest.fixture
def rules():
    return RulesEngine()


# ══════════════════════════════════════════════════════════════════════════
# 1. TRANSACTION VALIDATOR
# ══════════════════════════════════════════════════════════════════════════

class TestTransactionValidator:

    # ── Casos válidos ─────────────────────────────────────────────────────

    def test_transaccion_valida_aprobada(self, validator, tx_valida):
        """Transacción con todos los campos correctos debe ser válida."""
        result = validator.validate(tx_valida)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_tipos_validos(self, validator, tx_valida):
        """Todos los tipos válidos deben pasar la validación."""
        for tipo in ["PURCHASE", "TRANSFER", "WITHDRAWAL", "DEPOSIT"]:
            tx = {**tx_valida, "transaction_type": tipo}
            result = validator.validate(tx)
            assert result.is_valid, f"Tipo {tipo} debería ser válido"

    def test_fuentes_validas(self, validator, tx_valida):
        """Todos los tipos de fuente válidos deben pasar."""
        for fuente in ["CARD", "BANK", "WALLET"]:
            tx = {**tx_valida, "source_type": fuente}
            result = validator.validate(tx)
            assert result.is_valid, f"Fuente {fuente} debería ser válida"

    # ── Campos requeridos ─────────────────────────────────────────────────

    def test_sin_user_id(self, validator, tx_valida):
        """Sin user_id debe ser inválida."""
        tx = {**tx_valida, "user_id": None}
        result = validator.validate(tx)
        assert result.is_valid is False
        assert any("user_id" in e for e in result.errors)

    def test_sin_amount(self, validator, tx_valida):
        """Sin amount debe ser inválida."""
        tx = {**tx_valida, "amount": None}
        result = validator.validate(tx)
        assert result.is_valid is False

    def test_sin_transaction_type(self, validator, tx_valida):
        """Sin transaction_type debe ser inválida."""
        tx = {**tx_valida, "transaction_type": None}
        result = validator.validate(tx)
        assert result.is_valid is False

    def test_sin_currency(self, validator, tx_valida):
        """Sin currency debe ser inválida."""
        tx = {**tx_valida, "currency": None}
        result = validator.validate(tx)
        assert result.is_valid is False

    # ── Validación de montos ──────────────────────────────────────────────

    def test_monto_negativo(self, validator, tx_valida):
        """Monto negativo debe ser inválido."""
        tx = {**tx_valida, "amount": -100}
        result = validator.validate(tx)
        assert result.is_valid is False
        assert any("monto" in e.lower() or "amount" in e.lower() for e in result.errors)

    def test_monto_cero(self, validator, tx_valida):
        """Monto cero debe ser inválido."""
        tx = {**tx_valida, "amount": 0}
        result = validator.validate(tx)
        assert result.is_valid is False

    def test_monto_supera_limite_purchase(self, validator, tx_valida):
        """Monto mayor al límite de PURCHASE debe ser inválido."""
        tx = {**tx_valida, "amount": 60_000_000, "transaction_type": "PURCHASE"}
        result = validator.validate(tx)
        assert result.is_valid is False

    def test_monto_supera_limite_withdrawal(self, validator, tx_valida):
        """Monto mayor al límite de WITHDRAWAL debe ser inválido."""
        tx = {**tx_valida, "amount": 25_000_000, "transaction_type": "WITHDRAWAL"}
        result = validator.validate(tx)
        assert result.is_valid is False

    def test_monto_alto_genera_warning(self, validator, tx_valida):
        """Monto superior a $10M debe generar warning aunque sea válido."""
        tx = {**tx_valida, "amount": 12_000_000, "transaction_type": "TRANSFER"}
        result = validator.validate(tx)
        assert result.is_valid is True
        assert len(result.warnings) > 0

    # ── Validación de tipos ───────────────────────────────────────────────

    def test_tipo_invalido(self, validator, tx_valida):
        """Tipo de transacción no reconocido debe ser inválido."""
        tx = {**tx_valida, "transaction_type": "CRYPTO_SWAP"}
        result = validator.validate(tx)
        assert result.is_valid is False

    def test_fuente_invalida(self, validator, tx_valida):
        """Fuente no reconocida debe ser inválida."""
        tx = {**tx_valida, "source_type": "BITCOIN"}
        result = validator.validate(tx)
        assert result.is_valid is False

    # ── Coherencia de saldos ──────────────────────────────────────────────

    def test_cuenta_vaciada_genera_warning(self, validator, tx_fraude):
        """Cuenta que queda en $0 después de TRANSFER debe generar warning."""
        result = validator.validate(tx_fraude)
        assert result.is_valid is True
        assert any("$0" in w or "vaciada" in w.lower() or "saldo" in w.lower()
                   for w in result.warnings)

    def test_monto_supera_saldo_genera_warning(self, validator, tx_valida):
        """Monto mayor al saldo disponible debe generar warning."""
        tx = {**tx_valida, "amount": 900_000, "old_balance_orig": 500_000}
        result = validator.validate(tx)
        assert len(result.warnings) > 0

    # ── UUID ──────────────────────────────────────────────────────────────

    def test_uuid_invalido(self, validator, tx_valida):
        """UUID malformado debe ser inválido."""
        tx = {**tx_valida, "user_id": "no-es-un-uuid"}
        result = validator.validate(tx)
        assert result.is_valid is False

    def test_uuid_valido_diferentes_formatos(self, validator, tx_valida):
        """UUIDs en formato estándar deben ser válidos."""
        uuids_validos = [
            "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            "00000000-0000-0000-0000-000000000001",
        ]
        for uid in uuids_validos:
            tx = {**tx_valida, "user_id": uid}
            result = validator.validate(tx)
            assert result.is_valid, f"UUID {uid} debería ser válido"

    # ── Múltiples errores ─────────────────────────────────────────────────

    def test_multiples_errores_acumulados(self, validator):
        """Una transacción con varios problemas debe acumular todos los errores."""
        tx_rota = {
            "user_id":          None,
            "amount":           -500,
            "transaction_type": "DESCONOCIDO",
            "source_type":      None,
            "currency":         None,
        }
        result = validator.validate(tx_rota)
        assert result.is_valid is False
        assert len(result.errors) >= 3


# ══════════════════════════════════════════════════════════════════════════
# 2. RULES ENGINE
# ══════════════════════════════════════════════════════════════════════════

class TestRulesEngine:

    # ── Regla ACCOUNT_DRAIN ───────────────────────────────────────────────

    def test_account_drain_dispara(self, rules, tx_fraude):
        """Cuenta vaciada en TRANSFER debe disparar ACCOUNT_DRAIN como CRITICAL."""
        result = rules.evaluate(tx=tx_fraude)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "ACCOUNT_DRAIN" in nombres
        assert result.should_block is True
        assert result.max_severity == "CRITICAL"

    def test_account_drain_no_dispara_si_saldo_queda(self, rules, tx_valida):
        """Si el saldo no queda en $0, ACCOUNT_DRAIN no debe dispararse."""
        result = rules.evaluate(tx=tx_valida)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "ACCOUNT_DRAIN" not in nombres

    def test_account_drain_solo_en_transfer_withdrawal(self, rules, tx_fraude):
        """ACCOUNT_DRAIN no debe dispararse en PURCHASE aunque el saldo quede en 0."""
        tx = {**tx_fraude, "transaction_type": "PURCHASE"}
        result = rules.evaluate(tx=tx)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "ACCOUNT_DRAIN" not in nombres

    # ── Regla HIGH_AMOUNT ─────────────────────────────────────────────────

    def test_monto_alto_dispara(self, rules, tx_valida):
        """Monto mayor a $10M debe disparar HIGH_AMOUNT."""
        tx = {**tx_valida, "amount": 15_000_000}
        result = rules.evaluate(tx=tx)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_AMOUNT" in nombres

    def test_monto_normal_no_dispara(self, rules, tx_valida):
        """Monto normal no debe disparar HIGH_AMOUNT."""
        result = rules.evaluate(tx=tx_valida)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_AMOUNT" not in nombres

    # ── Regla ROUND_AMOUNT ────────────────────────────────────────────────

    def test_monto_redondo_dispara(self, rules, tx_fraude):
        """Monto exactamente redondo >= $100K debe disparar ROUND_AMOUNT."""
        result = rules.evaluate(tx=tx_fraude)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "ROUND_AMOUNT" in nombres

    def test_monto_no_redondo_no_dispara(self, rules, tx_valida):
        """Monto no redondo no debe disparar ROUND_AMOUNT."""
        tx = {**tx_valida, "amount": 347_823.50}
        result = rules.evaluate(tx=tx)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "ROUND_AMOUNT" not in nombres

    # ── Regla HIGH_RISK_TYPE ──────────────────────────────────────────────

    def test_transfer_dispara_high_risk_type(self, rules, tx_fraude):
        """TRANSFER debe disparar HIGH_RISK_TYPE."""
        result = rules.evaluate(tx=tx_fraude)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_RISK_TYPE" in nombres

    def test_withdrawal_dispara_high_risk_type(self, rules, tx_valida):
        """WITHDRAWAL debe disparar HIGH_RISK_TYPE."""
        tx = {**tx_valida, "transaction_type": "WITHDRAWAL"}
        result = rules.evaluate(tx=tx)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_RISK_TYPE" in nombres

    def test_purchase_no_dispara_high_risk_type(self, rules, tx_valida):
        """PURCHASE no debe disparar HIGH_RISK_TYPE."""
        result = rules.evaluate(tx=tx_valida)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_RISK_TYPE" not in nombres

    # ── Regla UNTRUSTED_DEVICE ────────────────────────────────────────────

    def test_dispositivo_no_confiable_dispara(self, rules, tx_valida, device_sospechoso):
        """Dispositivo con trust_score < 0.30 debe disparar UNTRUSTED_DEVICE."""
        result = rules.evaluate(tx=tx_valida, device=device_sospechoso)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "UNTRUSTED_DEVICE" in nombres

    def test_dispositivo_confiable_no_dispara(self, rules, tx_valida, device_confiable):
        """Dispositivo confiable no debe disparar UNTRUSTED_DEVICE."""
        result = rules.evaluate(tx=tx_valida, device=device_confiable)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "UNTRUSTED_DEVICE" not in nombres

    def test_dispositivo_confiable_reduce_score(self, rules, tx_valida, device_confiable):
        """Dispositivo confiable debe aportar delta negativo (reduce el riesgo)."""
        result = rules.evaluate(tx=tx_valida, device=device_confiable)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "TRUSTED_DEVICE" in nombres
        trusted = next(r for r in result.triggered_rules if r.rule_name == "TRUSTED_DEVICE")
        assert trusted.score_delta < 0

    # ── Regla HIGH_RISK_COUNTRY ───────────────────────────────────────────

    def test_pais_alto_riesgo_dispara(self, rules, tx_valida, device_sospechoso):
        """País de alto riesgo (NG) debe disparar HIGH_RISK_COUNTRY."""
        result = rules.evaluate(tx=tx_valida, device=device_sospechoso)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_RISK_COUNTRY" in nombres

    def test_pais_normal_no_dispara(self, rules, tx_valida, device_confiable):
        """País normal (CO) no debe disparar HIGH_RISK_COUNTRY."""
        result = rules.evaluate(tx=tx_valida, device=device_confiable)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_RISK_COUNTRY" not in nombres

    # ── Regla NEW_DEVICE ──────────────────────────────────────────────────

    def test_dispositivo_nuevo_dispara(self, rules, tx_valida):
        """Dispositivo registrado hace menos de 24h debe disparar NEW_DEVICE."""
        device = {"created_at": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                  "is_trusted": True, "trust_score": 0.8, "country": "CO"}
        result = rules.evaluate(tx=tx_valida, device=device)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "NEW_DEVICE" in nombres

    def test_dispositivo_antiguo_no_dispara(self, rules, tx_valida, device_confiable):
        """Dispositivo registrado hace más de 24h no debe disparar NEW_DEVICE."""
        result = rules.evaluate(tx=tx_valida, device=device_confiable)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "NEW_DEVICE" not in nombres

    # ── Regla HIGH_VELOCITY ───────────────────────────────────────────────

    def test_alta_velocidad_dispara(self, rules, tx_valida):
        """Más de 5 transacciones en 1 hora debe disparar HIGH_VELOCITY."""
        history = {"tx_last_hour": 8, "avg_amount": 300_000}
        result = rules.evaluate(tx=tx_valida, user_history=history)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_VELOCITY" in nombres

    def test_velocidad_normal_no_dispara(self, rules, tx_valida):
        """Menos de 5 transacciones en 1 hora no debe disparar HIGH_VELOCITY."""
        history = {"tx_last_hour": 2, "avg_amount": 300_000}
        result = rules.evaluate(tx=tx_valida, user_history=history)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_VELOCITY" not in nombres

    # ── Regla AMOUNT_EXCEEDS_HISTORY ──────────────────────────────────────

    def test_monto_supera_promedio_dispara(self, rules, tx_fraude):
        """Monto 3x mayor al promedio histórico debe disparar AMOUNT_EXCEEDS_HISTORY."""
        history = {"avg_amount": 500_000, "tx_last_hour": 1}
        result = rules.evaluate(tx=tx_fraude, user_history=history)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "AMOUNT_EXCEEDS_HISTORY" in nombres

    def test_monto_normal_vs_promedio_no_dispara(self, rules, tx_valida):
        """Monto dentro del promedio histórico no debe disparar AMOUNT_EXCEEDS_HISTORY."""
        history = {"avg_amount": 400_000, "tx_last_hour": 1}
        result = rules.evaluate(tx=tx_valida, user_history=history)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "AMOUNT_EXCEEDS_HISTORY" not in nombres

    # ── Regla HIGH_RISK_MERCHANT ──────────────────────────────────────────

    def test_comercio_alto_riesgo_dispara(self, rules, tx_fraude):
        """merchant_risk_level HIGH debe disparar HIGH_RISK_MERCHANT."""
        result = rules.evaluate(tx=tx_fraude)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_RISK_MERCHANT" in nombres

    def test_comercio_bajo_riesgo_no_dispara(self, rules, tx_valida):
        """merchant_risk_level LOW no debe disparar HIGH_RISK_MERCHANT."""
        result = rules.evaluate(tx=tx_valida)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "HIGH_RISK_MERCHANT" not in nombres

    # ── Regla LOW_AMOUNT ──────────────────────────────────────────────────

    def test_monto_pequeno_reduce_score(self, rules, tx_valida):
        """Monto menor a $50K debe disparar LOW_AMOUNT con delta negativo."""
        tx = {**tx_valida, "amount": 30_000}
        result = rules.evaluate(tx=tx)
        nombres = [r.rule_name for r in result.triggered_rules]
        assert "LOW_AMOUNT" in nombres
        low = next(r for r in result.triggered_rules if r.rule_name == "LOW_AMOUNT")
        assert low.score_delta < 0

    # ── Acumulación de reglas ─────────────────────────────────────────────

    def test_transaccion_fraude_dispara_multiples_reglas(self, rules, tx_fraude, device_sospechoso):
        """Una transacción fraudulenta con dispositivo sospechoso debe disparar varias reglas."""
        history = {"tx_last_hour": 7, "avg_amount": 200_000}
        result = rules.evaluate(tx=tx_fraude, device=device_sospechoso, user_history=history)
        assert len(result.triggered_rules) >= 5
        assert result.should_block is True

    def test_transaccion_limpia_pocas_reglas(self, rules, tx_valida, device_confiable):
        """Una transacción limpia debe disparar pocas o ninguna regla de riesgo."""
        history = {"tx_last_hour": 1, "avg_amount": 350_000}
        result = rules.evaluate(tx=tx_valida, device=device_confiable, user_history=history)
        reglas_riesgo = [r for r in result.triggered_rules if r.score_delta > 0]
        assert len(reglas_riesgo) == 0

    def test_delta_total_acotado(self, rules, tx_fraude, device_sospechoso):
        """El delta total de reglas nunca debe superar 1.0."""
        history = {"tx_last_hour": 10, "avg_amount": 100_000}
        result = rules.evaluate(tx=tx_fraude, device=device_sospechoso, user_history=history)
        assert result.total_score_delta <= 1.0
        assert result.total_score_delta >= -1.0


# ══════════════════════════════════════════════════════════════════════════
# 3. SCORE ENGINE
# ══════════════════════════════════════════════════════════════════════════

class TestScoreEngine:

    @pytest.fixture
    def engine(self):
        return ScoreEngine(db=None)

    # ── Score final en rango ──────────────────────────────────────────────

    def test_score_siempre_entre_0_y_1(self, engine, tx_valida):
        """El score final siempre debe estar entre 0 y 1."""
        result = engine.score(tx=tx_valida)
        assert 0.0 <= result.overall_score <= 1.0

    def test_score_fraude_mayor_que_valida(self, engine, tx_valida, tx_fraude):
        """Una transacción fraudulenta debe tener score mayor que una válida."""
        score_valida = engine.score(tx=tx_valida).overall_score
        score_fraude = engine.score(tx=tx_fraude).overall_score
        assert score_fraude > score_valida

    # ── Decisiones correctas ──────────────────────────────────────────────

    def test_transaccion_valida_tiende_a_approve(self, engine, tx_valida, device_confiable):
        """Una transacción válida con dispositivo confiable debe tender a APPROVE."""
        result = engine.score(tx=tx_valida, device=device_confiable)
        assert result.decision in ["APPROVE", "MANUAL_REVIEW"]
        assert result.risk_level in ["low", "medium"]

    def test_transaccion_fraude_tiende_a_decline(self, engine, tx_fraude, device_sospechoso):
        """Una transacción fraudulenta con dispositivo sospechoso debe tender a DECLINE."""
        result = engine.score(tx=tx_fraude, device=device_sospechoso)
        assert result.decision in ["DECLINE", "MANUAL_REVIEW"]
        assert result.risk_level in ["high", "medium"]

    def test_account_drain_fuerza_decline(self, engine, tx_fraude):
        """ACCOUNT_DRAIN (CRITICAL) debe forzar DECLINE sin importar el ML score."""
        result = engine.score(tx=tx_fraude)
        assert result.decision == "DECLINE"
        assert result.overall_score >= 0.60

    # ── Umbrales de decisión ──────────────────────────────────────────────

    def test_umbral_approve_menor_035(self, engine, tx_valida, device_confiable):
        """Score < 0.35 debe resultar en APPROVE."""
        result = engine.score(tx=tx_valida, device=device_confiable)
        if result.overall_score < 0.35:
            assert result.decision == "APPROVE"

    def test_umbral_decline_mayor_060(self, engine, tx_fraude):
        """Score >= 0.60 debe resultar en DECLINE."""
        result = engine.score(tx=tx_fraude)
        if result.overall_score >= 0.60:
            assert result.decision == "DECLINE"

    # ── Validación integrada ──────────────────────────────────────────────

    def test_transaccion_invalida_resulta_en_decline(self, engine):
        """Transacción con datos inválidos debe resultar en DECLINE directamente."""
        tx_invalida = {
            "user_id":          None,
            "amount":           -100,
            "transaction_type": "DESCONOCIDO",
            "source_type":      None,
            "currency":         None,
        }
        result = engine.score(tx=tx_invalida)
        assert result.is_valid is False
        assert result.decision == "DECLINE"
        assert len(result.validation_errors) > 0

    # ── Campos de resultado ───────────────────────────────────────────────

    def test_resultado_tiene_todos_los_campos(self, engine, tx_valida):
        """El resultado debe tener todos los campos requeridos."""
        result = engine.score(tx=tx_valida)
        assert hasattr(result, "overall_score")
        assert hasattr(result, "ml_score")
        assert hasattr(result, "rules_delta")
        assert hasattr(result, "risk_level")
        assert hasattr(result, "decision")
        assert hasattr(result, "confidence_level")
        assert hasattr(result, "fraud_probability")
        assert hasattr(result, "triggered_rules")
        assert hasattr(result, "risk_factors")
        assert hasattr(result, "explanation")

    def test_confianza_entre_0_y_1(self, engine, tx_valida):
        """La confianza siempre debe estar entre 0 y 1."""
        result = engine.score(tx=tx_valida)
        assert 0.0 <= result.confidence_level <= 1.0

    def test_probabilidad_fraude_entre_0_y_100(self, engine, tx_valida):
        """La probabilidad de fraude debe estar entre 0 y 100."""
        result = engine.score(tx=tx_valida)
        assert 0.0 <= result.fraud_probability <= 100.0

    def test_risk_level_valores_validos(self, engine, tx_valida):
        """risk_level siempre debe ser low, medium o high."""
        result = engine.score(tx=tx_valida)
        assert result.risk_level in ["low", "medium", "high"]

    def test_decision_valores_validos(self, engine, tx_valida):
        """decision siempre debe ser APPROVE, MANUAL_REVIEW o DECLINE."""
        result = engine.score(tx=tx_valida)
        assert result.decision in ["APPROVE", "MANUAL_REVIEW", "DECLINE"]

    # ── Pesos del modelo ──────────────────────────────────────────────────

    def test_peso_ml_65_porciento(self, engine, tx_valida):
        """El explanation debe mostrar que el ML aporta el 65%."""
        result = engine.score(tx=tx_valida)
        assert result.explanation.get("ml_weight") == 0.65

    def test_peso_reglas_35_porciento(self, engine, tx_valida):
        """El explanation debe mostrar que las reglas aportan el 35%."""
        result = engine.score(tx=tx_valida)
        assert result.explanation.get("rules_weight") == 0.35

    # ── Escenarios combinados ─────────────────────────────────────────────

    def test_scenario_compra_normal(self, engine, device_confiable):
        """Compra pequeña con dispositivo confiable debe ser de bajo riesgo."""
        tx = {
            "user_id": "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            "amount": 45_000, "transaction_type": "PURCHASE",
            "source_type": "CARD", "currency": "COP",
            "merchant_risk_level": "LOW",
            "old_balance_orig": 500_000, "new_balance_orig": 455_000,
            "old_balance_dest": 0, "new_balance_dest": 45_000,
        }
        result = engine.score(tx=tx, device=device_confiable)
        assert result.risk_level == "low"
        assert result.decision == "APPROVE"

    def test_scenario_transferencia_sospechosa(self, engine, device_sospechoso):
        """Transferencia grande en país de riesgo con dispositivo sospechoso debe dar DECLINE."""
        tx = {
            "user_id": "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            "amount": 8_000_000, "transaction_type": "TRANSFER",
            "source_type": "BANK", "currency": "COP",
            "merchant_risk_level": "HIGH",
            "old_balance_orig": 8_000_000, "new_balance_orig": 0,
            "old_balance_dest": 0, "new_balance_dest": 8_000_000,
        }
        result = engine.score(tx=tx, device=device_sospechoso)
        assert result.decision == "DECLINE"
        assert result.overall_score >= 0.60


# ══════════════════════════════════════════════════════════════════════════
# 4. FEEDBACK MANAGER
# ══════════════════════════════════════════════════════════════════════════

class TestFeedbackManager:
    """
    Las pruebas del FeedbackManager usan mocks de la BD
    para no depender de PostgreSQL en los tests unitarios.
    """

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.scalar.return_value = 0
        return db

    def test_feedback_confirmed_fraud_registrado(self, mock_db):
        """CONFIRMED_FRAUD debe registrarse sin errores."""
        from ml.feedback_manager import FeedbackManager, FeedbackType
        manager = FeedbackManager(db=mock_db)
        result = manager.submit_feedback(
            transaction_id="6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            reviewer_id="rev-001",
            feedback_type=FeedbackType.CONFIRMED_FRAUD,
        )
        assert result["success"] is True
        assert result["feedback_type"] == FeedbackType.CONFIRMED_FRAUD
        mock_db.commit.assert_called_once()

    def test_feedback_false_positive_registrado(self, mock_db):
        """FALSE_POSITIVE debe registrarse y marcar la transacción como no fraude."""
        from ml.feedback_manager import FeedbackManager, FeedbackType

        mock_tx = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tx

        manager = FeedbackManager(db=mock_db)
        result = manager.submit_feedback(
            transaction_id="6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            reviewer_id="rev-001",
            feedback_type=FeedbackType.FALSE_POSITIVE,
        )
        assert result["success"] is True
        mock_db.commit.assert_called_once()

    def test_feedback_con_notas(self, mock_db):
        """Feedback con notas del revisor debe registrarse correctamente."""
        from ml.feedback_manager import FeedbackManager, FeedbackType
        manager = FeedbackManager(db=mock_db)
        result = manager.submit_feedback(
            transaction_id="6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            reviewer_id="rev-001",
            feedback_type=FeedbackType.CONFIRMED_LEGIT,
            notes="El cliente confirmó por teléfono que realizó la transacción.",
        )
        assert result["success"] is True

    def test_feedback_con_alert_id(self, mock_db):
        """Feedback asociado a una alerta debe resolverla."""
        from ml.feedback_manager import FeedbackManager, FeedbackType

        mock_alert = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert

        manager = FeedbackManager(db=mock_db)
        result = manager.submit_feedback(
            transaction_id="6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            reviewer_id="rev-001",
            feedback_type=FeedbackType.CONFIRMED_FRAUD,
            alert_id="alert-uuid-001",
        )
        assert result["success"] is True

    def test_metricas_feedback_retorna_dict(self, mock_db):
        """get_feedback_metrics debe retornar un diccionario con las claves esperadas."""
        from ml.feedback_manager import FeedbackManager
        manager = FeedbackManager(db=mock_db)
        metrics = manager.get_feedback_metrics()
        assert isinstance(metrics, dict)

    def test_pending_review_retorna_lista(self, mock_db):
        """get_pending_review debe retornar una lista."""
        from ml.feedback_manager import FeedbackManager
        mock_db.query.return_value.join.return_value.filter.return_value \
               .order_by.return_value.limit.return_value.all.return_value = []
        manager = FeedbackManager(db=mock_db)
        pending = manager.get_pending_review()
        assert isinstance(pending, list)

    def test_error_bd_no_propaga_excepcion_inesperada(self, mock_db):
        """Un error de BD debe lanzar RuntimeError con mensaje descriptivo."""
        from ml.feedback_manager import FeedbackManager, FeedbackType
        mock_db.commit.side_effect = Exception("DB connection lost")
        manager = FeedbackManager(db=mock_db)
        with pytest.raises(RuntimeError, match="Error al registrar feedback"):
            manager.submit_feedback(
                transaction_id="6500fef8-8795-4b1b-9ccb-414ab17b04b6",
                reviewer_id="rev-001",
                feedback_type=FeedbackType.CONFIRMED_FRAUD,
            )


# ══════════════════════════════════════════════════════════════════════════
# 5. PRUEBAS DE INTEGRACIÓN — FLUJO COMPLETO
# ══════════════════════════════════════════════════════════════════════════

class TestFlujoCompleto:
    """
    Pruebas end-to-end que simulan el flujo completo:
    Validación → Score Engine → Decisión
    """

    @pytest.fixture
    def engine(self):
        return ScoreEngine(db=None)

    def test_flujo_compra_legitima(self, engine, device_confiable):
        """Flujo completo: compra pequeña legítima debe aprobarse."""
        tx = {
            "user_id":            "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            "amount":             120_000,
            "transaction_type":   "PURCHASE",
            "source_type":        "CARD",
            "currency":           "COP",
            "merchant_risk_level": "LOW",
            "old_balance_orig":   800_000,
            "new_balance_orig":   680_000,
            "old_balance_dest":   0,
            "new_balance_dest":   120_000,
        }
        result = engine.score(tx=tx, device=device_confiable)
        assert result.is_valid is True
        assert result.decision == "APPROVE"
        assert result.risk_level == "low"
        assert result.overall_score < 0.35

    def test_flujo_fraude_tipico_paysim(self, engine, device_sospechoso):
        """Flujo completo: patrón de fraude clásico de PaySim (CASH_OUT) debe bloquearse."""
        tx = {
            "user_id":            "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            "amount":             3_000_000,
            "transaction_type":   "CASH_OUT",
            "source_type":        "BANK",
            "currency":           "COP",
            "merchant_risk_level": "HIGH",
            "old_balance_orig":   3_000_000,
            "new_balance_orig":   0,
            "old_balance_dest":   0,
            "new_balance_dest":   3_000_000,
        }
        result = engine.score(tx=tx, device=device_sospechoso)
        assert result.is_valid is True
        assert result.decision == "DECLINE"
        assert result.overall_score >= 0.60

    def test_flujo_datos_invalidos_bloqueados_antes_de_ml(self, engine):
        """Datos inválidos deben ser bloqueados antes de llegar al modelo ML."""
        tx_invalida = {
            "user_id": "no-uuid",
            "amount": -500,
            "transaction_type": "HACK",
            "source_type": "NONE",
            "currency": "ZZZ",
        }
        result = engine.score(tx=tx_invalida)
        assert result.is_valid is False
        assert result.decision == "DECLINE"
        assert len(result.validation_errors) > 0

    def test_flujo_score_consistency(self, engine, tx_valida):
        """El mismo input siempre debe producir el mismo score (determinismo)."""
        r1 = engine.score(tx=tx_valida)
        r2 = engine.score(tx=tx_valida)
        assert r1.overall_score == r2.overall_score
        assert r1.decision == r2.decision

    def test_flujo_multiples_transacciones_distintas(self, engine):
        """Transacciones con distintos perfiles de riesgo deben tener scores diferenciados."""
        # Caso bajo: compra pequeña con saldo disponible
        tx_bajo = {
            "user_id": "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            "amount": 50_000, "transaction_type": "PURCHASE",
            "source_type": "CARD", "currency": "COP",
            "merchant_risk_level": "LOW",
            "old_balance_orig": 500_000, "new_balance_orig": 450_000,
            "old_balance_dest": 0, "new_balance_dest": 50_000,
        }
        # Caso medio: transfer con saldo parcial (no vacía la cuenta)
        tx_medio = {
            "user_id": "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            "amount": 2_000_000, "transaction_type": "TRANSFER",
            "source_type": "BANK", "currency": "COP",
            "merchant_risk_level": "MEDIUM",
            "old_balance_orig": 5_000_000, "new_balance_orig": 3_000_000,
            "old_balance_dest": 0, "new_balance_dest": 2_000_000,
        }
        # Caso alto: transfer que vacía la cuenta completamente
        tx_alto = {
            "user_id": "6500fef8-8795-4b1b-9ccb-414ab17b04b6",
            "amount": 8_000_000, "transaction_type": "TRANSFER",
            "source_type": "BANK", "currency": "COP",
            "merchant_risk_level": "HIGH",
            "old_balance_orig": 8_000_000, "new_balance_orig": 0,
            "old_balance_dest": 0, "new_balance_dest": 8_000_000,
        }
        score_bajo  = engine.score(tx=tx_bajo).overall_score
        score_medio = engine.score(tx=tx_medio).overall_score
        score_alto  = engine.score(tx=tx_alto).overall_score

        # El score debe ser claramente mayor en el caso alto
        assert score_bajo < score_alto
        assert score_medio < score_alto
