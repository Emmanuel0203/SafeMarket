"""
SafeMarket Pocket SDK - Core Module
====================================

Módulo core con configuración, modelos y excepciones del SDK.
"""

from .exceptions import (
    SDKError,
    ConfigError,
    ValidationError,
    ConnectionError,
    ModelError,
    DataExtractionError,
    IntegrationError,
    TimeoutError,
    FeatureExtractionError,
)

from .models import (
    Transaction,
    ScoringResult,
    FeatureSet,
    RiskLevel,
    DecisionType,
    TransactionStatus,
)

from .config import (
    Config,
    get_default_config,
)

__all__ = [
    # Exceptions
    'SDKError',
    'ConfigError',
    'ValidationError',
    'ConnectionError',
    'ModelError',
    'DataExtractionError',
    'IntegrationError',
    'TimeoutError',
    'FeatureExtractionError',
    # Models
    'Transaction',
    'ScoringResult',
    'FeatureSet',
    'RiskLevel',
    'DecisionType',
    'TransactionStatus',
    # Config
    'Config',
    'get_default_config',
]
