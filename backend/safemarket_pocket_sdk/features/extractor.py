"""
SafeMarket Pocket SDK - Feature Extractor
===========================================

Extrae características de transacciones para alimentar al Score Engine.

Las características (features) son variables construidas a partir de la
transacción y datos históricos que alimentan el modelo ML.

Uso:
    from safemarket_pocket_sdk.features import FeatureExtractor
    from safemarket_pocket_sdk.core import Transaction
    
    extractor = FeatureExtractor()
    tx = Transaction(id="tx_1", amount=1000, buyer_id="b1", seller_id="s1")
    
    features = extractor.extract(tx)
    print(features.buyer_transaction_count)
    print(features.amount_z_score)
"""

from datetime import datetime
from typing import Optional, Dict, Any
import math

from safemarket_pocket_sdk.core import (
    Transaction,
    FeatureSet,
    FeatureExtractionError,
)


class FeatureExtractor:
    """
    Extrae características de transacciones.
    
    Construye un FeatureSet a partir de una Transaction, incluyendo:
    - Features de monto
    - Features de velocidad
    - Features temporales
    - Features relacionales
    
    El FeatureSet resultante se pasa al ScoreEngine para calcular riesgo.
    
    Ejemplo de uso:
        extractor = FeatureExtractor()
        
        # Con datos históricos del buyer (simulados)
        extractor.set_buyer_history(
            buyer_id="buyer_123",
            tx_count=50,
            avg_amount=500.0
        )
        
        # Extraer features de nueva transacción
        tx = Transaction(
            id="tx_456",
            amount=1500,
            buyer_id="buyer_123",
            seller_id="seller_789"
        )
        features = extractor.extract(tx)
        print(f"Amount Z-score: {features.amount_z_score}")
    """
    
    def __init__(self):
        """Inicializa el extractor de features."""
        # Caché de datos históricos
        self.buyer_history: Dict[str, Dict[str, Any]] = {}
        self.seller_history: Dict[str, Dict[str, Any]] = {}
    
    def set_buyer_history(
        self,
        buyer_id: str,
        tx_count: int,
        avg_amount: float,
        is_new: bool = False
    ) -> None:
        """
        Establece datos históricos de un buyer.
        
        En producción, estos datos vendrían de la BD.
        
        Args:
            buyer_id (str): ID del buyer
            tx_count (int): Cantidad de transacciones previas
            avg_amount (float): Monto promedio de sus transacciones
            is_new (bool): ¿Es buyer nuevo?
        """
        self.buyer_history[buyer_id] = {
            'tx_count': tx_count,
            'avg_amount': avg_amount,
            'is_new': is_new,
        }
    
    def set_seller_history(
        self,
        seller_id: str,
        tx_count: int,
        avg_amount: float
    ) -> None:
        """
        Establece datos históricos de un seller.
        
        Args:
            seller_id (str): ID del seller
            tx_count (int): Cantidad de transacciones previas
            avg_amount (float): Monto promedio de sus transacciones
        """
        self.seller_history[seller_id] = {
            'tx_count': tx_count,
            'avg_amount': avg_amount,
        }
    
    def extract(self, transaction: Transaction) -> FeatureSet:
        """
        Extrae features de una transacción.
        
        Args:
            transaction (Transaction): Transacción a procesar
        
        Returns:
            FeatureSet: Conjunto de características extraídas
        
        Raises:
            FeatureExtractionError: Si hay problemas extrayendo features
        
        Ejemplo:
            try:
                features = extractor.extract(tx)
                print(f"Features extraídas: {len(features.to_array())} dimensiones")
            except FeatureExtractionError as e:
                print(f"Error: {e}")
        """
        try:
            # Validar transacción
            is_valid, errors = transaction.validate()
            if not is_valid:
                raise FeatureExtractionError(
                    f"Invalid transaction: {', '.join(errors)}"
                )
            
            # Extraer features de buyer
            buyer_data = self.buyer_history.get(
                transaction.buyer_id,
                {'tx_count': 0, 'avg_amount': 0, 'is_new': True}
            )
            
            # Extraer features de seller
            seller_data = self.seller_history.get(
                transaction.seller_id,
                {'tx_count': 0, 'avg_amount': 0}
            )
            
            # Calcular Z-score del monto
            amount_z_score = self._calculate_z_score(
                transaction.amount,
                buyer_data.get('avg_amount', 0),
                buyer_data.get('tx_count', 0)
            )
            
            # Extraer features temporales
            time_features = self._extract_temporal_features(transaction.timestamp)
            
            # Determinar si es repetido seller
            is_repeated_seller = self._is_repeated_seller(
                transaction.buyer_id,
                transaction.seller_id
            )
            
            # Determinar si hay mismatch de país
            country_mismatch = self._check_country_mismatch(transaction)
            
            # Construir FeatureSet
            features = FeatureSet(
                transaction_id=transaction.id,
                
                # Amount features
                amount=transaction.amount,
                amount_z_score=amount_z_score,
                
                # Buyer features
                buyer_transaction_count=buyer_data.get('tx_count', 0),
                buyer_avg_amount=buyer_data.get('avg_amount', 0),
                buyer_is_new=buyer_data.get('is_new', True),
                
                # Seller features
                seller_transaction_count=seller_data.get('tx_count', 0),
                seller_avg_amount=seller_data.get('avg_amount', 0),
                
                # Temporal features
                time_of_day=time_features['hour'],
                day_of_week=time_features['weekday'],
                is_weekend=time_features['is_weekend'],
                
                # Velocity features (simulados en este MVP)
                velocity_1h=0,
                velocity_24h=0,
                
                # Relational features
                is_repeated_seller=is_repeated_seller,
                country_mismatch=country_mismatch,
                
                # Custom
                extra_features=transaction.metadata,
            )
            
            return features
            
        except FeatureExtractionError:
            raise
        except Exception as e:
            raise FeatureExtractionError(f"Feature extraction failed: {str(e)}")
    
    def _calculate_z_score(
        self,
        value: float,
        mean: float,
        count: int,
        std_dev: float = 500.0
    ) -> float:
        """
        Calcula Z-score de un valor.
        
        Z-score mide cuántas desviaciones estándar está un valor de la media.
        
        Args:
            value: Valor a normalizar
            mean: Media histórica
            count: Cantidad de datos históricos
            std_dev: Desviación estándar (default=500)
        
        Returns:
            float: Z-score
        """
        if count == 0 or std_dev == 0:
            return 0.0
        
        z_score = (value - mean) / std_dev
        return z_score
    
    def _extract_temporal_features(self, timestamp: datetime) -> Dict[str, Any]:
        """
        Extrae features temporales.
        
        Args:
            timestamp (datetime): Momento de la transacción
        
        Returns:
            dict: Features temporales
        """
        hour = timestamp.hour
        weekday = timestamp.weekday()  # 0=Monday, 6=Sunday
        is_weekend = weekday >= 5
        
        return {
            'hour': hour,
            'weekday': weekday,
            'is_weekend': is_weekend,
        }
    
    def _is_repeated_seller(
        self,
        buyer_id: str,
        seller_id: str
    ) -> bool:
        """
        Verifica si el buyer ha transaccionado con este seller antes.
        
        Nota: En producción esto consultaría una tabla de relaciones.
        """
        # Simulado - siempre False en MVP
        return False
    
    def _check_country_mismatch(self, transaction: Transaction) -> bool:
        """
        Verifica si hay mismatch de país entre buyer y seller.
        
        Args:
            transaction (Transaction): Transacción
        
        Returns:
            bool: True si países son diferentes
        """
        buyer_country = transaction.buyer_country
        seller_country = transaction.seller_country
        
        if not buyer_country or not seller_country:
            return False
        
        return buyer_country != seller_country


class AdvancedFeatureExtractor(FeatureExtractor):
    """
    Extractor de features avanzado con capacidades adicionales.
    
    Extiende FeatureExtractor con:
    - Cálculo de features de red (análisis de grafos)
    - Features de comportamiento temporal
    - Detección de patrones
    - Integración con datos externos
    
    Uso:
        extractor = AdvancedFeatureExtractor()
        features = extractor.extract(tx)
        
        # Features adicionales
        network_score = extractor.get_network_score(buyer_id, seller_id)
        anomaly_score = extractor.get_anomaly_score(tx)
    """
    
    def __init__(self):
        """Inicializa extractor avanzado."""
        super().__init__()
        self.buyer_seller_graph: Dict[str, set] = {}
    
    def get_network_score(self, buyer_id: str, seller_id: str) -> float:
        """
        Calcula score basado en análisis de red.
        
        Detecta si hay conexiones sospechosas entre buyer y seller.
        
        Args:
            buyer_id (str): ID del buyer
            seller_id (str): ID del seller
        
        Returns:
            float: Score de red 0-100
        """
        # Simulado - score neutral
        return 50.0
    
    def get_anomaly_score(self, transaction: Transaction) -> float:
        """
        Detecta anomalías en la transacción.
        
        Args:
            transaction (Transaction): Transacción
        
        Returns:
            float: Score de anomalía 0-100
        """
        # Simulado
        return 50.0
