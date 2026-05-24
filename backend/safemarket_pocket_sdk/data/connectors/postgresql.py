"""
SafeMarket Pocket SDK - PostgreSQL Connector
=============================================

Conector para bases de datos PostgreSQL.

Permite extraer transacciones y datos históricos de PostgreSQL
para construir datasets de entrenamiento.

Uso:
    from safemarket_pocket_sdk.data.connectors import PostgreSQLConnector
    
    connector = PostgreSQLConnector(
        connection_string="postgresql://user:pass@localhost/safemarket_db",
        transaction_table="transactions",
        buyer_table="users"
    )
    
    try:
        if connector.validate():
            txs = connector.fetch_transactions(limit=10000)
            print(f"Extracted {len(txs)} transactions")
    finally:
        connector.close()
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

try:
    import psycopg2
    from psycopg2 import sql, Error, connect
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from safemarket_pocket_sdk.core import ConnectionError, DataExtractionError
from .base import DataConnectorBase, ConnectorConfig


logger = logging.getLogger(__name__)


class PostgreSQLConnector(DataConnectorBase):
    """
    Conector para PostgreSQL.
    
    Extrae transacciones y datos históricos de una BD PostgreSQL.
    
    Ejemplo de uso completo:
        connector = PostgreSQLConnector(
            connection_string="postgresql://user:pass@localhost:5432/mydb",
            transaction_table="transactions",
            buyer_table="users",
            seller_table="merchants"
        )
        
        try:
            # Validar conexión y esquema
            is_valid, errors = connector.validate()
            if not is_valid:
                print(f"Validation errors: {errors}")
                return
            
            # Extraer transacciones
            txs = connector.fetch_transactions(
                query='''
                    SELECT id, amount, buyer_id, seller_id, created_at, is_fraud
                    FROM transactions
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    ORDER BY created_at DESC
                ''',
                limit=50000
            )
            
            # Extraer históricos
            for tx in txs[:10]:
                buyer_hist = connector.fetch_buyer_history(tx['buyer_id'])
                print(f"Buyer {tx['buyer_id']}: {buyer_hist['transaction_count']} txs")
        
        except (ConnectionError, DataExtractionError) as e:
            logger.error(f"Extraction error: {e}")
        finally:
            connector.close()
    """
    
    def __init__(
        self,
        connection_string: str,
        transaction_table: str = "transactions",
        buyer_table: str = "users",
        seller_table: str = "sellers",
        config: ConnectorConfig = None
    ):
        """
        Inicializa conector PostgreSQL.
        
        Args:
            connection_string (str): URL de conexión PostgreSQL
                Formato: postgresql://user:password@host:port/database
            transaction_table (str): Nombre de tabla de transacciones
            buyer_table (str): Nombre de tabla de buyers
            seller_table (str): Nombre de tabla de sellers
            config (ConnectorConfig): Configuración avanzada
        
        Raises:
            ImportError: Si psycopg2 no está instalado
        """
        super().__init__(config)
        
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "psycopg2 is required for PostgreSQL connector. "  "Install with: pip install psycopg2-binary"
            )
        
        self.connection_string = connection_string
        self.transaction_table = transaction_table
        self.buyer_table = buyer_table
        self.seller_table = seller_table
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """
        Conecta a la BD PostgreSQL.
        
        Returns:
            bool: True si conexión fue exitosa
        
        Raises:
            ConnectionError: Si hay problema conectando
        """
        try:
            self.connection = psycopg2.connect(
                self.connection_string,
                connect_timeout=self.config.connection_timeout_ms // 1000
            )
            self.cursor = self.connection.cursor()
            self.is_connected = True
            logger.info(f"✅ Connected to PostgreSQL")
            return True
        
        except Error as e:
            error_msg = f"Failed to connect to PostgreSQL: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Valida conexión y esquema.
        
        Verifica:
        - Conexión activa
        - Tablas existen
        - Columnas esperadas existen
        
        Returns:
            tuple[bool, list]: (es_válido, errores)
        """
        if not self.is_connected:
            return False, ["No connection established"]
        
        errors = []
        
        # Verificar tablas
        tables = {
            self.transaction_table: [
                'id', 'amount', 'buyer_id', 'seller_id', 'created_at'
            ],
            self.buyer_table: ['id', 'email'],  # Mínimo requerido
        }
        
        for table_name, required_cols in tables.items():
            table_exists = self._table_exists(table_name)
            if not table_exists:
                errors.append(f"Table not found: {table_name}")
                continue
            
            # Verificar columnas
            missing_cols = self._get_missing_columns(table_name, required_cols)
            for col in missing_cols:
                errors.append(
                    f"Missing column '{col}' in table '{table_name}'"
                )
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.info("✅ Schema validation passed")
        else:
            logger.warning(f"Schema validation failed: {errors}")
        
        return is_valid, errors
    
    def fetch_transactions(
        self,
        query: str = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene transacciones de la BD.
        
        Args:
            query (str): Query SQL personalizada. Si es None, usa default.
            limit (int): Máximo de registros
            offset (int): Offset para paginación
        
        Returns:
            list[dict]: Transacciones
        
        Raises:
            DataExtractionError: Si hay error en la query
        
        Ejemplo:
            txs = connector.fetch_transactions(
                query='''
                    SELECT * FROM transactions
                    WHERE created_at > NOW() - INTERVAL '30 days'
                ''',
                limit=5000
            )
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to database")
        
        try:
            if query is None:
                query = f"SELECT * FROM {self.transaction_table} LIMIT %s OFFSET %s"
                self.cursor.execute(query, (limit, offset))
            else:
                # Añadir LIMIT si no está en la query
                if "LIMIT" not in query.upper():
                    query += f" LIMIT {limit} OFFSET {offset}"
                self.cursor.execute(query)
            
            columns = [desc[0] for desc in self.cursor.description]
            transactions = []
            
            for row in self.cursor.fetchall():
                transactions.append(dict(zip(columns, row)))
            
            logger.info(f"Fetched {len(transactions)} transactions")
            return transactions
        
        except Error as e:
            error_msg = f"Query execution failed: {str(e)}"
            logger.error(error_msg)
            raise DataExtractionError(error_msg, query=query)
    
    def fetch_buyer_history(self, buyer_id: str) -> Dict[str, Any]:
        """
        Obtiene histórico de un buyer.
        
        Args:
            buyer_id (str): ID del buyer
        
        Returns:
            dict: Histórico (tx_count, avg_amount, etc)
        
        Raises:
            DataExtractionError: Si hay error en la query
        """
        try:
            query = f"""
                SELECT 
                    COUNT(*) as transaction_count,
                    AVG(amount) as avg_amount,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount,
                    MIN(created_at) as first_transaction_date,
                    MAX(created_at) as last_transaction_date
                FROM {self.transaction_table}
                WHERE buyer_id = %s
            """
            
            self.cursor.execute(query, (buyer_id,))
            row = self.cursor.fetchone()
            columns = [desc[0] for desc in self.cursor.description]
            
            return dict(zip(columns, row)) if row else {}
        
        except Error as e:
            error_msg = f"Failed to fetch buyer history: {str(e)}"
            logger.error(error_msg)
            raise DataExtractionError(error_msg, query=query)
    
    def fetch_seller_history(self, seller_id: str) -> Dict[str, Any]:
        """
        Obtiene histórico de un seller.
        
        Args:
            seller_id (str): ID del seller
        
        Returns:
            dict: Histórico
        """
        try:
            query = f"""
                SELECT 
                    COUNT(*) as transaction_count,
                    AVG(amount) as avg_amount,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount
                FROM {self.transaction_table}
                WHERE seller_id = %s
            """
            
            self.cursor.execute(query, (seller_id,))
            row = self.cursor.fetchone()
            columns = [desc[0] for desc in self.cursor.description]
            
            return dict(zip(columns, row)) if row else {}
        
        except Error as e:
            error_msg = f"Failed to fetch seller history: {str(e)}"
            logger.error(error_msg)
            raise DataExtractionError(error_msg, query=query)
    
    def close(self) -> None:
        """Cierra la conexión."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.is_connected = False
        logger.info("✅ PostgreSQL connection closed")
    
    # Métodos privados
    
    def _table_exists(self, table_name: str) -> bool:
        """Verifica si una tabla existe."""
        try:
            query = """
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = %s
                )
            """
            self.cursor.execute(query, (table_name,))
            return self.cursor.fetchone()[0]
        except Error:
            return False
    
    def _get_missing_columns(
        self,
        table_name: str,
        required_columns: List[str]
    ) -> List[str]:
        """Retorna columnas que faltan en la tabla."""
        try:
            query = """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s
            """
            self.cursor.execute(query, (table_name,))
            existing_cols = [row[0] for row in self.cursor.fetchall()]
            return [col for col in required_columns if col not in existing_cols]
        except Error:
            return required_columns
