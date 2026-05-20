"""
SafeMarket Pocket SDK - Integration Adapter
=============================================

Adaptador principal para integradores externos (ej: CLQ Software).

Este es el punto de entrada recomendado para aplicativos que quieren
integrar SafeMarket como módulo de scoring.

Uso:
    from safemarket_pocket_sdk.integration import SafeMarketAdapter
    from safemarket_pocket_sdk.core import Transaction, DecisionType
    
    # Crear adaptador
    adapter = SafeMarketAdapter(api_url=\"https://api.safemarket.io\")
    
    # Scoring de transacción
    tx = Transaction(
        id=\"tx_123\",
        amount=1000,
        buyer_id=\"buyer_456\",
        seller_id=\"seller_789\"
    )
    
    result = adapter.validate_transaction(tx)
    
    if result['approved']:
        print(\"✅ Transacción aprobada\")
    else:
        print(f\"❌ Rechazada. Razón: {result['reason']}\")
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from safemarket_pocket_sdk.core import (
    Config,
    Transaction,
    ScoringResult,
    DecisionType,
    RiskLevel,
)
from safemarket_pocket_sdk.features import FeatureExtractor
from safemarket_pocket_sdk.scoring import ScoreEngine


logger = logging.getLogger(__name__)


class SafeMarketAdapter:
    \"\"\"
    Adaptador para integradores externos.
    
    Proporciona una interfaz simple para scoring de transacciones
    desde aplicativos terceros (CLQ Software, etc).
    
    Características:
    - Scoring rápido local (<100ms)
    - Sin dependencia de API remota (opcional)
    - Configuración flexible
    - Explicabilidad de decisiones
    - Manejo de feedback humano
    
    Ejemplo de uso completo:
        from safemarket_pocket_sdk.integration import SafeMarketAdapter
        
        # Crear adaptador
        adapter = SafeMarketAdapter()
        
        # Configurar históricos (idealmente de BD)
        adapter.set_buyer_data(
            buyer_id=\"buyer_123\",
            tx_count=50,
            avg_amount=500.0
        )
        
        # Scoring
        tx = Transaction(
            id=\"tx_1\",
            amount=1500,
            buyer_id=\"buyer_123\",
            seller_id=\"seller_456\",
            category=\"electronics\"
        )
        
        result = adapter.validate_transaction(tx)
        print(f\"Score: {result['score']}\")
        print(f\"Decision: {result['decision']}\")
        print(f\"Factors: {result['risk_factors']}\")
        
        # Feedback
        if result['decision'] == 'MANUAL_REVIEW':
            # Después de revisión manual...
            adapter.submit_feedback(
                transaction_id=\"tx_1\",
                label=\"LEGITIMATE\",  # o \"FRAUD\"
                reviewer_id=\"reviewer_1\",
                notes=\"Buyer confirmó pago\"
            )
    \"\"\"
    
    def __init__(
        self,
        config: Optional[Config] = None,
        use_remote_api: bool = False,
        api_key: Optional[str] = None
    ):
        \"\"\"
        Inicializa el adaptador.
        
        Args:
            config (Config): Configuración del SDK (opcional)
            use_remote_api (bool): Usar API remota para scoring (default: local)
            api_key (str): API key para integración remota
        
        Ejemplo:
            # Scoring local (recomendado)
            adapter = SafeMarketAdapter()
            
            # Con integración remota
            adapter = SafeMarketAdapter(
                use_remote_api=True,
                api_key=\"sk_live_xxx\"
            )
        \"\"\"
        self.config = config or Config()
        self.use_remote_api = use_remote_api
        self.api_key = api_key
        
        # Inicializar motores locales
        self.feature_extractor = FeatureExtractor()
        self.score_engine = ScoreEngine(config=self.config)
        
        # Caché de feedback
        self.feedback_log: List[Dict[str, Any]] = []
    
    def validate_transaction(
        self,
        transaction: Transaction,
        timeout_ms: int = 100
    ) -> Dict[str, Any]:
        \"\"\"
        Valida y puntúa una transacción.
        
        Este es el método principal de integración.
        
        Args:
            transaction (Transaction): Transacción a validar
            timeout_ms (int): Timeout máximo para scoring (ms)
        
        Returns:
            dict: Resultado de scoring con estructura:
            {
                'transaction_id': str,
                'approved': bool,
                'score': float,  # 0-100
                'risk_level': str,  # 'LOW'|'MEDIUM'|'HIGH'
                'decision': str,  # 'APPROVE'|'MANUAL_REVIEW'|'DECLINE'
                'risk_factors': [str],
                'confidence': float,
                'reason': str,
                'ttl_seconds': int,
                'timestamp': str,
            }
        
        Ejemplo:
            result = adapter.validate_transaction(tx)
            
            if result['approved']:
                # Procesar pago
                process_payment(tx)
            elif result['decision'] == 'MANUAL_REVIEW':
                # Poner en cola de revisión
                queue_for_review(tx, result)
            else:
                # Rechazar
                reject_payment(tx, result['reason'])
        \"\"\"
        try:
            # Validar estructura
            is_valid, errors = transaction.validate()
            if not is_valid:
                return {
                    'transaction_id': transaction.id,
                    'approved': False,
                    'score': 0,
                    'risk_level': 'HIGH',
                    'decision': 'DECLINE',
                    'risk_factors': errors,
                    'confidence': 1.0,
                    'reason': f\"Invalid transaction: {', '.join(errors)}\",
                    'ttl_seconds': 3600,
                    'timestamp': datetime.utcnow().isoformat(),
                }
            
            # Extraer features
            features = self.feature_extractor.extract(transaction)
            
            # Calcular score
            score_result = self.score_engine.calculate_score(features)
            
            # Construir resultado para integrador
            return {
                'transaction_id': score_result.transaction_id,
                'approved': score_result.decision == DecisionType.APPROVE,
                'score': score_result.score,
                'risk_level': score_result.risk_level.value,
                'decision': score_result.decision.value,
                'risk_factors': score_result.risk_factors,
                'confidence': score_result.confidence,
                'reason': self._build_reason(score_result),
                'ttl_seconds': score_result.ttl,
                'timestamp': score_result.timestamp.isoformat(),
            }
        
        except Exception as e:
            logger.error(f\"Error validating transaction: {str(e)}\")
            return {
                'transaction_id': transaction.id,
                'approved': False,
                'score': 0,
                'risk_level': 'HIGH',
                'decision': 'DECLINE',
                'risk_factors': ['System error'],
                'confidence': 0,
                'reason': 'Internal error during validation',
                'ttl_seconds': 60,
                'timestamp': datetime.utcnow().isoformat(),
            }
    
    def set_buyer_data(
        self,
        buyer_id: str,
        tx_count: int,
        avg_amount: float,
        is_new: bool = False
    ) -> None:
        \"\"\"
        Establece datos históricos de un buyer.
        
        En producción, estos datos se cargarían de la BD.
        
        Args:
            buyer_id (str): ID del buyer
            tx_count (int): Cantidad de transacciones previas
            avg_amount (float): Monto promedio
            is_new (bool): ¿Es buyer nuevo?
        
        Ejemplo:
            # Cargar datos de buyer
            buyer_data = db.get_buyer_stats(\"buyer_123\")
            adapter.set_buyer_data(
                buyer_id=\"buyer_123\",
                tx_count=buyer_data['tx_count'],
                avg_amount=buyer_data['avg_amount'],
                is_new=buyer_data['is_new']
            )
        \"\"\"
        self.feature_extractor.set_buyer_history(
            buyer_id=buyer_id,
            tx_count=tx_count,
            avg_amount=avg_amount,
            is_new=is_new
        )
        logger.debug(f\"Set buyer data for {buyer_id}\")
    
    def set_seller_data(
        self,
        seller_id: str,
        tx_count: int,
        avg_amount: float
    ) -> None:
        \"\"\"
        Establece datos históricos de un seller.
        
        Args:
            seller_id (str): ID del seller
            tx_count (int): Cantidad de transacciones
            avg_amount (float): Monto promedio
        \"\"\"
        self.feature_extractor.set_seller_history(
            seller_id=seller_id,
            tx_count=tx_count,
            avg_amount=avg_amount
        )
        logger.debug(f\"Set seller data for {seller_id}\")
    
    def add_custom_rule(
        self,
        name: str,
        condition,
        score_delta: float,
        severity: str = \"LOW\",
        reason: str = \"\"
    ) -> None:
        \"\"\"
        Añade regla de negocio personalizada.
        
        Permite integradores definir reglas específicas de su dominio.
        
        Args:
            name (str): Nombre de la regla
            condition (callable): Función (features) -> bool
            score_delta (float): Ajuste al score si se dispara
            severity (str): Severidad (LOW|MEDIUM|HIGH|CRITICAL)
            reason (str): Descripción
        
        Ejemplo:
            # Regla: rechazar si buyer es de países bloqueados
            adapter.add_custom_rule(
                name=\"blocked_countries\",
                condition=lambda f: f.buyer_country in [\"KP\", \"IR\"],
                score_delta=+100,
                severity=\"CRITICAL\",
                reason=\"Buyer from sanctioned country\"
            )
            
            # Regla: confianza extra si es cliente VIP
            adapter.add_custom_rule(
                name=\"vip_customer\",
                condition=lambda f: f.metadata.get('is_vip'),
                score_delta=-20,
                severity=\"LOW\",
                reason=\"VIP customer\"
            )
        \"\"\"
        self.score_engine.rules_engine.add_rule(
            name=name,
            condition=condition,
            score_delta=score_delta,
            severity=severity,
            reason=reason
        )
        logger.info(f\"Added custom rule: {name}\")
    
    def submit_feedback(
        self,
        transaction_id: str,
        label: str,
        reviewer_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        \"\"\"
        Registra feedback humano sobre una transacción.
        
        Este feedback se usa para:
        - Auditoría y trazabilidad
        - Reentrenamiento del modelo (en API remota)
        - Métricas de desempeño
        
        Args:
            transaction_id (str): ID de la transacción
            label (str): Clasificación (\"FRAUD\" o \"LEGITIMATE\")
            reviewer_id (str): ID de quien hizo la revisión
            notes (str): Notas del reviewer
        
        Returns:
            bool: True si el feedback fue registrado
        
        Ejemplo:
            # Después de revisión manual
            adapter.submit_feedback(
                transaction_id=\"tx_123\",
                label=\"FRAUD\",
                reviewer_id=\"reviewer_user_1\",
                notes=\"Buyer denies transaction\"
            )
        \"\"\"
        try:
            feedback_record = {
                'transaction_id': transaction_id,
                'label': label,
                'reviewer_id': reviewer_id,
                'notes': notes,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            self.feedback_log.append(feedback_record)
            logger.info(f\"Feedback registered for {transaction_id}: {label}\")
            
            # En producción, enviar a API para reentrenamiento
            if self.use_remote_api and self.api_key:
                self._send_feedback_to_api(feedback_record)
            
            return True
        
        except Exception as e:
            logger.error(f\"Error registering feedback: {e}\")
            return False
    
    def get_feedback_log(self) -> List[Dict[str, Any]]:
        \"\"\"
        Retorna log de todos los feedbacks registrados.
        
        Returns:
            list[dict]: Lista de registros de feedback
        \"\"\"
        return self.feedback_log.copy()
    
    def get_model_health(self) -> Dict[str, Any]:
        \"\"\"
        Retorna métricas de salud del modelo.
        
        Returns:
            dict: Métricas del modelo
        
        Ejemplo:
            health = adapter.get_model_health()
            print(f\"Model version: {health['model_version']}\")
            print(f\"Rules configured: {health['rules_count']}\")
        \"\"\"
        return {
            'model_version': self.config.MODEL_VERSION,
            'rules_count': len(self.score_engine.rules_engine.rules),
            'feedback_count': len(self.feedback_log),
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    # Métodos privados
    
    def _build_reason(self, score_result: ScoringResult) -> str:
        \"\"\"Construye explicación legible de la decisión.\"\"\"
        parts = []
        
        if score_result.decision == DecisionType.APPROVE:
            parts.append(f\"Low risk score ({score_result.score:.0f})\")
        elif score_result.decision == DecisionType.MANUAL_REVIEW:
            parts.append(f\"Medium risk score ({score_result.score:.0f})\")
            parts.append(f\"Risk factors: {', '.join(score_result.risk_factors[:3])}\")
        else:
            parts.append(f\"High risk score ({score_result.score:.0f})\")
            parts.append(f\"Risk factors: {', '.join(score_result.risk_factors)}\")
        
        return \"; \".join(parts) if parts else \"No factors\"
    
    def _send_feedback_to_api(self, feedback_record: Dict[str, Any]) -> None:
        \"\"\"Envía feedback al API remoto de SafeMarket.\"\"\"
        # Implementar cuando haya API integrado
        pass
