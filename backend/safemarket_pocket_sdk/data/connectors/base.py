"""
SafeMarket Pocket SDK - Data Connectors Base
==============================================

Define la interfaz base para conectores de datos.

Todos los conectores (PostgreSQL, MySQL, MongoDB, CSV, etc) heredan
de DataConnectorBase e implementan estos métodos.

Uso:
    # PostgreSQL Connector
    from safemarket_pocket_sdk.data.connectors import PostgreSQLConnector
    
    connector = PostgreSQLConnector(connection_string="...")
    if connector.validate():
        data = connector.fetch_transactions(limit=1000)
        connector.close()
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ConnectorConfig:
    """
    Configuración base para conectores.
    
    Attributes:
        connection_timeout_ms (int): Timeout de conexión
        query_timeout_ms (int): Timeout de queries
        batch_size (int): Tamaño de batch para lectura
        max_retries (int): Intentos máximos de reconexión
    """
    connection_timeout_ms: int = 5000
    query_timeout_ms: int = 30000
    batch_size: int = 1000
    max_retries: int = 3


class DataConnectorBase(ABC):
    """
    Interfaz base para conectores de datos.
    
    Define el contrato que todos los conectores deben cumplir para que
    SafeMarket pueda extraer datos, construir features y entrenar modelos.
    
    Métodos que todo conector implementa:
    - connect(): Establece conexión
    - validate(): Valida esquema y conexión
    - fetch_transactions(): Obtiene transacciones
    - fetch_buyer_history(): Obtiene histórico de buyer
    - close(): Cierra conexión
    
    Ejemplo de uso:
        class CustomConnector(DataConnectorBase):
            def connect(self): ...
            def validate(self): ...
            def fetch_transactions(self, query, limit): ...
            def fetch_buyer_history(self, buyer_id): ...
            def close(self): ...
        
        connector = CustomConnector(config)
        connector.connect()
        if connector.validate():
            transactions = connector.fetch_transactions(...)
    """
    
    def __init__(self, config: ConnectorConfig = None):
        """
        Inicializa el conector.
        
        Args:
            config (ConnectorConfig): Configuración del conector
        """
        self.config = config or ConnectorConfig()
        self.is_connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establece conexión con la fuente de datos.
        
        Returns:
            bool: True si la conexión fue exitosa
        
        Raises:
            ConnectionError: Si hay problema conectando
        
        Ejemplo:
            try:
                connector.connect()
                print("✅ Connected")
            except ConnectionError as e:
                print(f"❌ {e}")
        """
        pass
    
    @abstractmethod
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Valida la conexión y esquema.
        
        Verifica que:
        - La conexión está activa
        - Las tablas esperadas existen
        - Los esquemas son compatibles
        
        Returns:
            tuple[bool, list]: (es_válido, lista_de_errores)
        
        Ejemplo:
            is_valid, errors = connector.validate()
            if not is_valid:
                for error in errors:
                    print(f"Validation error: {error}")
        """
        pass
    
    @abstractmethod
    def fetch_transactions(
        self,
        query: str,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene transacciones de la BD.
        
        Los registros retornados deben tener al menos:
        - id: Identificador único
        - amount: Monto
        - buyer_id: ID del comprador
        - seller_id: ID del vendedor
        - timestamp: Momento de la transacción
        - label (opcional): Para datos etiquetados (is_fraud, valid, etc)
        
        Args:
            query (str): SQL query personalizada (si aplica)
            limit (int): Cantidad máxima de registros
            offset (int): Offset para paginación
        
        Returns:
            list[dict]: Registros de transacciones
        
        Raises:
            DataExtractionError: Si hay problema en la query
        
        Ejemplo:
            txs = connector.fetch_transactions(
                query="SELECT * FROM transactions WHERE created_at > NOW() - INTERVAL '7 days'",
                limit=5000
            )
            print(f"Fetched {len(txs)} transactions")
        """
        pass
    
    @abstractmethod
    def fetch_buyer_history(self, buyer_id: str) -> Dict[str, Any]:
        """
        Obtiene histórico de un buyer.
        
        Retorna:
        - transaction_count: Total de transacciones
        - avg_amount: Monto promedio
        - min_amount: Monto mínimo
        - max_amount: Monto máximo
        - first_transaction_date: Primera transacción
        - last_transaction_date: Última transacción
        
        Args:
            buyer_id (str): ID del buyer
        
        Returns:
            dict: Histórico agregado
        
        Ejemplo:
            history = connector.fetch_buyer_history("buyer_123")
            print(f"Buyer has {history['transaction_count']} transactions")
            print(f"Average amount: {history['avg_amount']}")
        """
        pass
    
    @abstractmethod
    def fetch_seller_history(self, seller_id: str) -> Dict[str, Any]:
        """
        Obtiene histórico de un seller.
        
        Similar a fetch_buyer_history pero para sellers.
        
        Args:
            seller_id (str): ID del seller
        
        Returns:
            dict: Histórico agregado
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        Cierra la conexión con la BD.
        
        Libera recursos y cierra sesiones.
        
        Ejemplo:
            try:
                data = connector.fetch_transactions(...)
            finally:
                connector.close()  # Siempre cerrar
        """
        pass
    
    def __enter__(self):
        """Context manager support."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        self.close()
