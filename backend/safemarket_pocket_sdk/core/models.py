"""
SafeMarket Pocket SDK - Modelos de Datos
==========================================

Define los modelos de datos principales que circulan por el SDK.
Estos modelos actúan como contratos entre el SDK y los aplicativos integradores.

Uso:
    from safemarket_pocket_sdk.core import Transaction, ScoringResult
    
    # Crear transacción
    tx = Transaction(
        id="tx_123",
        amount=1000.0,
        buyer_id="user_456"
    )
    
    # Recibir resultado de scoring
    result = sdk.score_transaction(tx)
    print(f"Score: {result.score}")
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """
    Clasificación de nivel de riesgo de una transacción.
    
    Valores:
        - LOW: Riesgo bajo, transacción segura
        - MEDIUM: Riesgo medio, requiere revisión
        - HIGH: Riesgo alto, posible fraude
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DecisionType(str, Enum):
    """
    Decisión final del scoring.
    
    Valores:
        - APPROVE: Aprobar transacción automáticamente
        - MANUAL_REVIEW: Derivar a revisión manual
        - DECLINE: Rechazar transacción automáticamente
    """
    APPROVE = "APPROVE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    DECLINE = "DECLINE"


class TransactionStatus(str, Enum):
    """
    Estado de una transacción en el sistema.
    
    Valores:
        - PENDING: Pendiente de scoring
        - SCORED: Scored completado
        - REVIEWED: Revisado manualmente
        - APPROVED: Aprobado final
        - DECLINED: Rechazado final
    """
    PENDING = "PENDING"
    SCORED = "SCORED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"


@dataclass
class Transaction:
    """
    Representa una transacción a ser puntuada por SafeMarket.
    
    Esta es la estructura principal que integradores enviarán al SDK.
    El SDK construirá características a partir de estos datos.
    
    Attributes:
        id (str): Identificador único de la transacción (requerido)
        amount (float): Monto de la transacción (requerido)
        currency (str): Código ISO de moneda (ej: "USD", "COP") - default: "USD"
        buyer_id (str): ID del comprador en el sistema externo (requerido)
        seller_id (str): ID del vendedor (requerido)
        timestamp (datetime): Cuando ocurrió la transacción - default: ahora
        
        category (str): Categoría de la transacción (ej: "electronics", "digital_services")
        description (str): Descripción de la transacción
        
        buyer_email (str): Email del comprador para validación
        buyer_phone (str): Teléfono del comprador
        seller_email (str): Email del vendedor
        
        buyer_country (str): País del comprador (código ISO)
        seller_country (str): País del vendedor
        buyer_ip (str): IP del comprador para análisis de ubicación
        
        payment_method (str): Método de pago (ej: "credit_card", "bank_transfer")
        card_last_4 (str): Últimos 4 dígitos de tarjeta si aplica
        
        metadata (dict): Datos adicionales específicos del integrador
    
    Ejemplo de uso:
        tx = Transaction(
            id="tx_20260519_001",
            amount=500.00,
            currency="COP",
            buyer_id="buyer_123",
            seller_id="seller_456",
            category="electronics",
            buyer_country="CO",
            payment_method="credit_card",
            metadata={"user_source": "mobile_app"}
        )
    """
    
    # Campos requeridos
    id: str
    amount: float
    buyer_id: str
    seller_id: str
    
    # Campos opcionales con defaults
    currency: str = "USD"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    category: Optional[str] = None
    description: Optional[str] = None
    
    # Información del comprador
    buyer_email: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_country: Optional[str] = None
    buyer_ip: Optional[str] = None
    
    # Información del vendedor
    seller_email: Optional[str] = None
    seller_country: Optional[str] = None
    
    # Información de pago
    payment_method: Optional[str] = None
    card_last_4: Optional[str] = None
    
    # Datos adicionales del integrador
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """
        Convierte la transacción a diccionario.
        
        Returns:
            dict: Representación diccionario de la transacción
        """
        return asdict(self)
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Valida que la transacción tenga los datos mínimos requeridos.
        
        Returns:
            tuple[bool, List[str]]: (es_válida, lista_de_errores)
            
        Ejemplo:
            tx = Transaction(id="tx_1", amount=100)  # Falta buyer_id
            is_valid, errors = tx.validate()
            if not is_valid:
                print(f"Transaction invalid: {errors}")
        """
        errors = []
        
        if not self.id:
            errors.append("Transaction ID is required")
        if self.amount is None or self.amount <= 0:
            errors.append("Transaction amount must be positive")
        if not self.buyer_id:
            errors.append("buyer_id is required")
        if not self.seller_id:
            errors.append("seller_id is required")
        
        return len(errors) == 0, errors


@dataclass
class ScoringResult:
    """
    Resultado del scoring de una transacción.
    
    Esta es la estructura que el SDK retorna a integradores con la decisión
    y detalles del scoring.
    
    Attributes:
        transaction_id (str): ID de la transacción scored
        score (float): Score numérico 0-100
        risk_level (RiskLevel): Nivel de riesgo (LOW|MEDIUM|HIGH)
        decision (DecisionType): Decisión (APPROVE|MANUAL_REVIEW|DECLINE)
        
        fraud_probability (float): Probabilidad de fraude 0-1 según modelo ML
        confidence (float): Confianza en la decisión 0-1
        
        triggered_rules (list[str]): Reglas que se dispararon
        risk_factors (list[str]): Factores que contribuyeron al riesgo
        
        ml_score_component (float): Componente del score del modelo ML
        rules_score_delta (float): Ajuste aplicado por las reglas
        
        explanation (dict): Explicabilidad de la decisión (para SHAP, etc)
        timestamp (datetime): Cuándo se generó el score
        
        model_version (str): Versión del modelo usado
        ttl (int): Segundos hasta que el score expira (para cache)
    
    Ejemplo de uso:
        result = sdk.score_transaction(transaction)
        
        if result.decision == DecisionType.APPROVE:
            print("✅ Transacción aprobada")
        elif result.decision == DecisionType.MANUAL_REVIEW:
            print(f"⚠️ Requiere revisión. Score: {result.score}")
            print(f"Factores de riesgo: {result.risk_factors}")
        else:
            print("❌ Transacción rechazada")
    """
    
    # Identificadores
    transaction_id: str
    
    # Scores y decisión
    score: float  # 0-100
    risk_level: RiskLevel
    decision: DecisionType
    
    # Componentes del scoring
    fraud_probability: float  # 0-1
    confidence: float  # 0-1
    ml_score_component: float
    rules_score_delta: float
    
    # Explicabilidad
    triggered_rules: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    explanation: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    model_version: str = "1.0.0"
    ttl: int = 3600  # 1 hora por default
    
    def to_dict(self) -> dict:
        """
        Convierte resultado a diccionario serializable a JSON.
        
        Returns:
            dict: Representación diccionario
        """
        data = asdict(self)
        data['risk_level'] = self.risk_level.value
        data['decision'] = self.decision.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def is_expired(self) -> bool:
        """
        Verifica si el resultado ya expiró según su TTL.
        
        Returns:
            bool: True si el resultado expiró
            
        Ejemplo:
            result = sdk.score_transaction(tx)
            if result.is_expired():
                result = sdk.score_transaction(tx)  # Re-score
        """
        age = (datetime.utcnow() - self.timestamp).total_seconds()
        return age > self.ttl


@dataclass
class FeatureSet:
    """
    Conjunto de características extraídas de una transacción.
    
    El FeatureExtractor construye esto a partir de Transaction,
    y el ScoreEngine lo usa para calcular el score.
    
    Attributes:
        transaction_id (str): ID de la transacción
        amount (float): Monto normalizado
        amount_z_score (float): Z-score del monto vs histórico
        
        buyer_transaction_count (int): Cantidad de tx del buyer
        buyer_avg_amount (float): Promedio de montos del buyer
        buyer_is_new (bool): ¿Es primer buyer?
        
        seller_transaction_count (int): Cantidad de tx del seller
        seller_avg_amount (float): Promedio de montos del seller
        
        time_of_day (int): Hora del día (0-23)
        day_of_week (int): Día de la semana (0-6)
        is_weekend (bool): ¿Es fin de semana?
        
        velocity_1h (int): Transacciones del buyer en última hora
        velocity_24h (int): Transacciones del buyer en últimas 24h
        
        is_repeated_seller (bool): ¿Seller repetido para este buyer?
        country_mismatch (bool): ¿Buyer y seller de países diferentes?
        
        extra_features (dict): Features adicionales específicas del integrador
    
    Ejemplo de uso (internamente):
        features = feature_extractor.extract(transaction)
        score_result = score_engine.calculate(features)
    """
    
    transaction_id: str
    
    # Amount features
    amount: float
    amount_z_score: float = 0.0
    
    # Buyer features
    buyer_transaction_count: int = 0
    buyer_avg_amount: float = 0.0
    buyer_is_new: bool = False
    
    # Seller features
    seller_transaction_count: int = 0
    seller_avg_amount: float = 0.0
    
    # Temporal features
    time_of_day: int = 0  # 0-23
    day_of_week: int = 0  # 0-6
    is_weekend: bool = False
    
    # Velocity features
    velocity_1h: int = 0
    velocity_24h: int = 0
    
    # Relational features
    is_repeated_seller: bool = False
    country_mismatch: bool = False
    
    # Custom features
    extra_features: Dict[str, Any] = field(default_factory=dict)
    
    def to_array(self) -> List[float]:
        """
        Convierte features a array numérico para modelo ML.
        
        Returns:
            list[float]: Features en orden estándar para modelo
        """
        return [
            self.amount,
            self.amount_z_score,
            self.buyer_transaction_count,
            self.buyer_avg_amount,
            float(self.buyer_is_new),
            self.seller_transaction_count,
            self.seller_avg_amount,
            self.time_of_day,
            self.day_of_week,
            float(self.is_weekend),
            self.velocity_1h,
            self.velocity_24h,
            float(self.is_repeated_seller),
            float(self.country_mismatch),
        ]
