"""
SafeMarket Pocket SDK
=======================

SDK portátil de SafeMarket para detección de fraude y scoring de riesgo.

Módulo compacto e integrable para aplicativos terceros (CLQ Software, etc).

Características Principales:
- Scoring rápido local (<100ms)
- Configuración flexible con reglas personalizadas
- Explicabilidad de decisiones
- Extracción de datos para entrenamientos
- Sin dependencias externas (excepto conector BD opcional)

Uso Rápido (Standalone):
    from safemarket_pocket_sdk.integration import SafeMarketAdapter
    from safemarket_pocket_sdk.core import Transaction
    
    adapter = SafeMarketAdapter()
    
    tx = Transaction(
        id="tx_123",
        amount=1000.0,
        buyer_id="buyer_456",
        seller_id="seller_789"
    )
    
    result = adapter.validate_transaction(tx)
    print(f"Decision: {result['decision']}, Score: {result['score']}")

Uso Avanzado (Con datos históricos):
    # Configurar históricos (idealmente de BD)
    adapter.set_buyer_data(
        buyer_id="buyer_456",
        tx_count=50,
        avg_amount=500.0
    )
    
    # Añadir regla personalizada
    adapter.add_custom_rule(
        name="high_vip_threshold",
        condition=lambda f: f.amount > 50000 and not f.buyer_is_new,
        score_delta=-15,
        severity="LOW",
        reason="Large transaction from established buyer"
    )
    
    result = adapter.validate_transaction(tx)
    
    # Registrar feedback
    if result['decision'] == 'MANUAL_REVIEW':
        # ... revisar manualmente ...
        adapter.submit_feedback(
            transaction_id="tx_123",
            label="LEGITIMATE",
            reviewer_id="reviewer_1"
        )

Extracción de Datos para Entrenamientos:
    from safemarket_pocket_sdk.data import PostgreSQLConnector
    
    connector = PostgreSQLConnector(
        connection_string="postgresql://user:pass@localhost/db",
        transaction_table="transactions"
    )
    
    try:
        if connector.validate()[0]:
            txs = connector.fetch_transactions(limit=50000)
            print(f"Extracted {len(txs)} transactions for training")
    finally:
        connector.close()

Documentación Completa:
    Ver POCKET_SOFTWARE_PROFILE.md en el directorio raíz del backend.

Soporte y Contribuciones:
    SafeMarket - https://safemarket.io
"""

__version__ = "1.0.0-alpha"
__author__ = "SafeMarket Team"
__all__ = [
    # Core
    'Transaction',
    'ScoringResult',
    'FeatureSet',
    'Config',
    'RiskLevel',
    'DecisionType',
    # Exceptions
    'SDKError',
    'ValidationError',
    'ConnectionError',
    # Main Adapter
    'SafeMarketAdapter',
    # Scoring
    'ScoreEngine',
    'RulesEngine',
    # Features
    'FeatureExtractor',
    # Data
    'PostgreSQLConnector',
    'DataConnectorBase',
]

# Imports principales
from safemarket_pocket_sdk.core import (
    Transaction,
    ScoringResult,
    FeatureSet,
    Config,
    RiskLevel,
    DecisionType,
    SDKError,
    ValidationError,
    ConnectionError,
)

from safemarket_pocket_sdk.integration import SafeMarketAdapter
from safemarket_pocket_sdk.scoring import ScoreEngine, RulesEngine
from safemarket_pocket_sdk.features import FeatureExtractor
from safemarket_pocket_sdk.data import (
    PostgreSQLConnector,
    DataConnectorBase,
)


def create_adapter(
    use_remote_api: bool = False,
    api_key: str = None,
    config: Config = None
) -> SafeMarketAdapter:
    """
    Factory function para crear un adaptador configurado.
    
    Args:
        use_remote_api (bool): Si usar API remota de SafeMarket
        api_key (str): API key para integración remota
        config (Config): Configuración personalizada
    
    Returns:
        SafeMarketAdapter: Adaptador listo para usar
    
    Ejemplo:
        adapter = create_adapter(use_remote_api=False)
        result = adapter.validate_transaction(tx)
    """
    return SafeMarketAdapter(
        config=config,
        use_remote_api=use_remote_api,
        api_key=api_key
    )
