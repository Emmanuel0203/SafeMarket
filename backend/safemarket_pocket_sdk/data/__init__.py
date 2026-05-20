"""
SafeMarket Pocket SDK - Data Module
====================================

Módulo de acceso a datos y extracción.
"""

from .connectors import (
    DataConnectorBase,
    ConnectorConfig,
    PostgreSQLConnector,
)

__all__ = [
    'DataConnectorBase',
    'ConnectorConfig',
    'PostgreSQLConnector',
]
