"""
SafeMarket Pocket SDK - Excepciones Personalizadas
===================================================

Define todas las excepciones que puede lanzar el SDK para manejo de errores
consistente en aplicativos integradores.

Uso:
    from safemarket_pocket_sdk.core import SDKError, ValidationError
    
    try:
        result = sdk.score_transaction(data)
    except ValidationError as e:
        print(f"Datos inválidos: {e}")
    except ConnectionError as e:
        print(f"Error de conexión: {e}")
"""


class SDKError(Exception):
    """
    Excepción base de SafeMarket SDK.
    
    Todas las excepciones del SDK heredan de esta clase. Permite
    a los integradores capturar cualquier error del SDK con:
    
        try:
            result = sdk.score_transaction(data)
        except SDKError as e:
            logger.error(f"SafeMarket error: {e}")
    """
    pass


class ConfigError(SDKError):
    """
    Lanzada cuando hay problemas con la configuración del SDK.
    
    Ejemplos:
        - Falta API key
        - Archivo de configuración inválido
        - Variables de entorno no definidas
    
    Ejemplo de uso:
        try:
            sdk = SafeMarketSDK()  # Sin API key
        except ConfigError as e:
            print(f"Config error: {e}")
    """
    pass


class ValidationError(SDKError):
    """
    Lanzada cuando los datos de entrada no pasan validación.
    
    Incluye detalles de qué campos son inválidos:
        - Tipo de dato incorrecto
        - Valor fuera de rango
        - Campo requerido faltante
    
    Atributo detail:
        dict: Detalles del error de validación
        
    Ejemplo de uso:
        try:
            result = sdk.score_transaction({
                "amount": "invalid"  # Debería ser float
            })
        except ValidationError as e:
            print(f"Invalid fields: {e.detail}")
    """
    
    def __init__(self, message: str, detail: dict = None):
        super().__init__(message)
        self.detail = detail or {}


class ConnectionError(SDKError):
    """
    Lanzada cuando hay problemas de conexión a base de datos o API.
    
    Ejemplos:
        - BD no accesible
        - Timeout en API SafeMarket
        - Credenciales inválidas
    
    Ejemplo de uso:
        try:
            extractor = DataExtractor(source="postgresql", ...)
            extractor.validate()
        except ConnectionError as e:
            logger.error(f"Cannot connect to database: {e}")
    """
    pass


class ModelError(SDKError):
    """
    Lanzada cuando hay problemas con el modelo ML.
    
    Ejemplos:
        - Modelo corrupto
        - Versión de modelo incompatible
        - Error durante predicción
    
    Ejemplo de uso:
        try:
            score = score_engine.calculate_score(features)
        except ModelError as e:
            print(f"Model error: {e}")
            # Fallback a scoring manual
    """
    pass


class DataExtractionError(SDKError):
    """
    Lanzada durante extracción de datos de BD.
    
    Ejemplos:
        - Query inválida
        - Tabla no encontrada
        - Esquema incompatible
    
    Ejemplo de uso:
        try:
            dataset = extractor.extract_and_build_features()
        except DataExtractionError as e:
            print(f"Data extraction failed: {e}")
    """
    
    def __init__(self, message: str, query: str = None):
        super().__init__(message)
        self.query = query


class IntegrationError(SDKError):
    """
    Lanzada cuando hay problemas en la integración con SafeMarket API o terceros.
    
    Ejemplos:
        - Respuesta inesperada de API
        - Webhook inválido
        - Feedback no procesado
    
    Ejemplo de uso:
        try:
            adapter.submit_feedback(tx_id, "FRAUD")
        except IntegrationError as e:
            print(f"Integration error: {e}")
    """
    pass


class TimeoutError(SDKError):
    """
    Lanzada cuando una operación excede el tiempo máximo permitido.
    
    El SDK implementa timeouts para garantizar:
        - Scoring rápido (<100ms default)
        - Respuesta del API (<5s default)
        - Extracción de datos con límite configurable
    
    Ejemplo de uso:
        try:
            score = sdk.score_transaction(data, timeout=50)  # 50ms max
        except TimeoutError as e:
            print(f"Operation took too long: {e}")
    """
    pass


class FeatureExtractionError(SDKError):
    """
    Lanzada cuando hay problemas extrayendo características de una transacción.
    
    Ejemplos:
        - Campo requerido para feature faltante
        - Conversión de tipo fallida
        - Cálculo de variable fallido
    
    Ejemplo de uso:
        try:
            features = extractor.extract(transaction)
        except FeatureExtractionError as e:
            print(f"Cannot extract features: {e}")
    """
    pass
