"""
SafeMarket Pocket SDK - Data Connectors Module
===============================================

Conectores para diferentes fuentes de datos.
"""

from .base import DataConnectorBase, ConnectorConfig
from .postgresql import PostgreSQLConnector

__all__ = [
    'DataConnectorBase',
    'ConnectorConfig',
    'PostgreSQLConnector',
]
