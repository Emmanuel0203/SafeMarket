"""
SafeMarket Pocket SDK - Score Engine
=====================================

Motor de scoring portátil que calcula riesgo a partir de features.
Combina modelo ML + reglas de negocio para score final.

Funciona 100% local sin depender de API remota.

Uso:
    from safemarket_pocket_sdk.scoring import ScoreEngine
    from safemarket_pocket_sdk.core import FeatureSet, ScoringResult
    
    engine = ScoreEngine()
    features = FeatureSet(transaction_id="tx_1", amount=1000.0)
    result = engine.calculate_score(features)
    print(f"Score: {result.score}, Decision: {result.decision}")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from safemarket_pocket_sdk.core import (
    FeatureSet,
    ScoringResult,
    RiskLevel,
    DecisionType,
    ModelError,
    Config,
)


@dataclass
class RuleResult:
    """
    Resultado de la evaluación de una regla.
    
    Attributes:
        rule_name (str): Nombre identificador de la regla
        triggered (bool): Si la regla se disparó
        score_delta (float): Ajuste al score (-100 a +100)
        reason (str): Explicación de por qué se disparó
        severity (str): Severidad (LOW|MEDIUM|HIGH|CRITICAL)
    """
    rule_name: str
    triggered: bool
    score_delta: float
    reason: str = ""
    severity: str = "LOW"


@dataclass
class RulesEngineResult:
    """
    Resultado de evaluar todas las reglas.
    
    Attributes:
        triggered_rules (list): Reglas que se dispararon
        total_score_delta (float): Suma de todos los deltas
        max_severity (str): Severidad máxima encontrada
        should_block (bool): True si alguna regla es CRITICAL
    """
    triggered_rules: List[RuleResult] = field(default_factory=list)
    total_score_delta: float = 0.0
    max_severity: str = "LOW"
    should_block: bool = False
    
    def add_rule(self, rule: RuleResult):
        \"\"\"Añade una regla al resultado.\"\"\"
        if rule.triggered:
            self.triggered_rules.append(rule)
            self.total_score_delta += rule.score_delta
            
            # Actualizar severidad máxima
            severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            if severity_order.get(rule.severity, 0) > severity_order.get(self.max_severity, 0):
                self.max_severity = rule.severity
            
            if rule.severity == "CRITICAL":
                self.should_block = True


class RulesEngine:
    \"\"\"
    Motor de reglas de negocio configurable.
    
    Permite aplicar reglas sin reentrenamiento del modelo ML.
    Las reglas pueden:
    - Aumentar o disminuir el score
    - Forzar decisiones (bloqueo automático)
    - Proporcionar explicabilidad
    
    Ejemplo de uso:
        engine = RulesEngine()
        engine.add_rule(
            name="velocity_check",
            condition=lambda features: features.velocity_24h > 100,
            score_delta=+15,
            reason="Velocity check: >100 tx/24h"
        )
        
        result = engine.evaluate(features)
        print(f"Triggered rules: {[r.rule_name for r in result.triggered_rules]}")
    \"\"\"
    
    def __init__(self):
        \"\"\"Inicializa el motor de reglas vacío.\"\"\"
        self.rules: Dict[str, Dict[str, Any]] = {}
    
    def add_rule(
        self,
        name: str,
        condition,
        score_delta: float,
        severity: str = "LOW",
        reason: str = ""
    ) -> None:
        \"\"\"
        Añade una regla configurable.
        
        Args:
            name (str): Nombre único de la regla
            condition (callable): Función que recibe FeatureSet y retorna bool
            score_delta (float): Cuánto ajustar el score si se dispara (-100 a +100)
            severity (str): Severidad (LOW|MEDIUM|HIGH|CRITICAL)
            reason (str): Descripción de la regla
        
        Ejemplo:
            engine.add_rule(
                name="high_amount",
                condition=lambda f: f.amount > 10000,
                score_delta=+20,
                severity="MEDIUM",
                reason="High transaction amount"
            )
        \"\"\"
        self.rules[name] = {
            'condition': condition,
            'score_delta': score_delta,
            'severity': severity,
            'reason': reason,
        }
    
    def evaluate(self, features: FeatureSet) -> RulesEngineResult:
        \"\"\"
        Evalúa todas las reglas contra un conjunto de features.
        
        Args:
            features (FeatureSet): Features a evaluar
        
        Returns:
            RulesEngineResult: Resultado de evaluación
        
        Ejemplo:
            result = engine.evaluate(features)
            for rule in result.triggered_rules:
                print(f"{rule.rule_name}: {rule.reason} (+{rule.score_delta})")
        \"\"\"
        result = RulesEngineResult()
        
        for rule_name, rule_config in self.rules.items():
            try:
                triggered = rule_config['condition'](features)
                
                if triggered:
                    rule_result = RuleResult(
                        rule_name=rule_name,
                        triggered=True,
                        score_delta=rule_config['score_delta'],
                        reason=rule_config['reason'],
                        severity=rule_config['severity'],
                    )
                    result.add_rule(rule_result)
            except Exception as e:
                print(f"Error evaluating rule {rule_name}: {e}")
        
        return result
    
    def get_rules_summary(self) -> Dict[str, Any]:
        \"\"\"Retorna resumen de reglas configuradas.\"\"\"
        return {
            'total_rules': len(self.rules),
            'rule_names': list(self.rules.keys()),
        }


class ScoreEngine:
    \"\"\"
    Motor de scoring que combina modelo ML + reglas de negocio.
    
    Calcula un score final 0-100 basado en:
    1. Score base del modelo ML (0-100)
    2. Ajustes por reglas de negocio
    3. Clasificación de riesgo
    4. Decisión final
    
    Ejemplo de uso:
        engine = ScoreEngine(config=config)
        
        # Configurar reglas
        engine.rules_engine.add_rule(
            name="new_buyer_high_amount",
            condition=lambda f: f.buyer_is_new and f.amount > 5000,
            score_delta=+25,
            severity="HIGH"
        )
        
        # Calcular score
        features = FeatureSet(
            transaction_id="tx_1",
            amount=1000,
            buyer_is_new=False
        )
        result = engine.calculate_score(features)
        
        print(f"Decision: {result.decision}")
        print(f"Risk factors: {result.risk_factors}")
    \"\"\"
    
    def __init__(self, config: Optional[Config] = None):
        \"\"\"
        Inicializa el Score Engine.
        
        Args:
            config (Config): Configuración del SDK (opcional)
        \"\"\"
        self.config = config or Config()
        self.rules_engine = RulesEngine()
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        \"\"\"Configura reglas por defecto del sistema.\"\"\"
        
        # Nuevo buyer con monto alto
        self.rules_engine.add_rule(
            name="new_buyer_high_amount",
            condition=lambda f: f.buyer_is_new and f.amount > 5000,
            score_delta=+25,
            severity=\"HIGH\",
            reason=\"New buyer with high transaction amount\"
        )
        
        # Velocity alta
        self.rules_engine.add_rule(
            name=\"high_velocity_24h\",
            condition=lambda f: f.velocity_24h > 50,
            score_delta=+20,
            severity=\"MEDIUM\",
            reason=\"High transaction velocity (>50 tx/24h)\"
        )
        
        # Monto anómalo (Z-score alto)
        self.rules_engine.add_rule(
            name=\"anomalous_amount\",
            condition=lambda f: f.amount_z_score > 3.0,
            score_delta=+15,
            severity=\"MEDIUM\",
            reason=\"Amount is anomalously high compared to buyer's history\"
        )
        
        # País mismatch
        self.rules_engine.add_rule(
            name=\"country_mismatch\",
            condition=lambda f: f.country_mismatch,
            score_delta=+10,
            severity=\"LOW\",
            reason=\"Buyer and seller from different countries\"
        )
    
    def calculate_score(
        self,
        features: FeatureSet,
        ml_score: Optional[float] = None
    ) -> ScoringResult:
        \"\"\"
        Calcula el score final de una transacción.
        
        Args:
            features (FeatureSet): Features de la transacción
            ml_score (float): Score del modelo ML (0-100). Si es None, usa valor default.
        
        Returns:
            ScoringResult: Resultado completo del scoring
        
        Raises:
            ModelError: Si hay problema calculando el score
        
        Ejemplo:
            features = FeatureSet(
                transaction_id=\"tx_123\",
                amount=1500.0,
                buyer_is_new=True,
                velocity_24h=5
            )
            result = engine.calculate_score(features)
        \"\"\"
        try:
            # Score base del modelo ML (simulado si no proporcionado)
            if ml_score is None:
                ml_score = self._estimate_ml_score(features)
            else:
                ml_score = max(0, min(100, ml_score))  # Clamping 0-100
            
            # Evaluar reglas
            rules_result = self.rules_engine.evaluate(features)
            
            # Score final con deltas
            final_score = ml_score + rules_result.total_score_delta
            final_score = max(0, min(100, final_score))  # Clamping 0-100
            
            # Determinar nivel de riesgo
            risk_level = self._determine_risk_level(final_score)
            
            # Determinar decisión
            decision = self._determine_decision(
                final_score,
                risk_level,
                rules_result.should_block
            )
            
            # Construir resultado
            result = ScoringResult(
                transaction_id=features.transaction_id,
                score=final_score,
                risk_level=risk_level,
                decision=decision,
                fraud_probability=final_score / 100.0,
                confidence=self._calculate_confidence(features),
                ml_score_component=ml_score,
                rules_score_delta=rules_result.total_score_delta,
                triggered_rules=[r.rule_name for r in rules_result.triggered_rules],
                risk_factors=self._extract_risk_factors(features, rules_result),
                explanation={
                    'ml_score': ml_score,
                    'rules_delta': rules_result.total_score_delta,
                    'triggered_rules': [
                        {
                            'name': r.rule_name,
                            'delta': r.score_delta,
                            'reason': r.reason
                        }
                        for r in rules_result.triggered_rules
                    ],
                    'risk_level': risk_level.value,
                    'decision': decision.value,
                },
                model_version=self.config.MODEL_VERSION,
                ttl=3600,  # 1 hora
            )
            
            return result
            
        except Exception as e:
            raise ModelError(f\"Error calculating score: {str(e)}\")
    
    def _estimate_ml_score(self, features: FeatureSet) -> float:
        \"\"\"
        Estima score ML cuando no se proporciona uno.
        
        Este es un estimador simulado. En producción, usaría un
        modelo ML real (LightGBM, Random Forest, etc).
        
        Args:
            features (FeatureSet): Features
        
        Returns:
            float: Score estimado 0-100
        \"\"\"
        # Estimación simple basada en features
        score = 50.0  # Base neutral
        
        # Ajustes por features individuales
        if features.buyer_is_new:
            score += 15
        
        if features.velocity_24h > 50:
            score += 20
        
        if features.amount_z_score > 3.0:
            score += 15
        
        if features.country_mismatch:
            score += 10
        
        # Normalizar
        score = max(0, min(100, score))
        
        return score
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        \"\"\"Clasifica el nivel de riesgo según el score.\"\"\"
        if score < self.config.MIN_SCORE_THRESHOLD:
            return RiskLevel.LOW
        elif score < self.config.MAX_SCORE_THRESHOLD:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def _determine_decision(
        self,
        score: float,
        risk_level: RiskLevel,
        should_block: bool
    ) -> DecisionType:
        \"\"\"Determina la decisión final.\"\"\"
        
        # Bloqueo automático por regla CRITICAL
        if should_block:
            return DecisionType.DECLINE
        
        # Decisión por score
        if risk_level == RiskLevel.LOW:
            return DecisionType.APPROVE
        elif risk_level == RiskLevel.MEDIUM:
            return DecisionType.MANUAL_REVIEW
        else:
            return DecisionType.DECLINE
    
    def _calculate_confidence(self, features: FeatureSet) -> float:
        \"\"\"
        Calcula confianza en la decisión.
        
        Mayor confianza con:
        - Buyer con histórico (no es nuevo)
        - Seller con histórico
        - Features completas
        \"\"\"
        confidence = 0.7  # Base
        
        if not features.buyer_is_new:
            confidence += 0.15
        
        if features.seller_transaction_count > 10:
            confidence += 0.1
        
        # Penalizar si faltan features
        if features.buyer_transaction_count == 0:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _extract_risk_factors(
        self,
        features: FeatureSet,
        rules_result: RulesEngineResult
    ) -> List[str]:
        \"\"\"Extrae factores de riesgo principales.\"\"\"
        factors = []
        
        # Añadir factores de features
        if features.buyer_is_new:
            factors.append(\"new_buyer\")
        
        if features.velocity_24h > 50:
            factors.append(f\"high_velocity: {features.velocity_24h} tx/24h\")
        
        if features.country_mismatch:
            factors.append(\"country_mismatch\")
        
        if features.amount_z_score > 2.0:
            factors.append(\"unusual_amount\")
        
        # Añadir nombres de reglas disparadas
        for rule in rules_result.triggered_rules:
            if rule.rule_name not in factors:
                factors.append(rule.rule_name)
        
        return factors
