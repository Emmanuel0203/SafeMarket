"""
SafeMarket Pocket SDK - Configuración
======================================

Configuración centralizada del SDK. Soporta carga desde:
- Variables de entorno
- Archivo .env
- Diccionario de configuración

Uso:
    from safemarket_pocket_sdk.core import Config
    
    config = Config()
    print(config.MODEL_VERSION)
    
    # O con personalización
    config = Config(
        API_URL="https://api.client.local",
        API_KEY="sk_test_xxx",
        TIMEOUT_MS=50
    )
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Config:
    """
    Configuración del SafeMarket SDK.
    
    La configuración puede especificarse en este orden de precedencia:
    1. Parámetros pasados al constructor
    2. Variables de entorno (SAFEMARKET_*)
    3. Valores por default
    
    Attributes:
        # API Configuration
        API_URL (str): URL base de la API SafeMarket
        API_KEY (str): API key para autenticación
        API_TIMEOUT_MS (int): Timeout para llamadas a API (ms)
        
        # Scoring Configuration
        SCORING_TIMEOUT_MS (int): Timeout máximo para scoring (ms)
        MIN_SCORE_THRESHOLD (float): Score mínimo para APPROVE (0-100)
        MAX_SCORE_THRESHOLD (float): Score máximo para DECLINE (0-100)
        
        # Rules Configuration
        ENABLE_RULES (bool): Activa el Rules Engine
        RULES_VERSION (str): Versión de reglas a usar
        
        # Model Configuration
        MODEL_VERSION (str): Versión del modelo ML
        MODEL_PATH (str): Path local del modelo ML (si aplica)
        
        # Database Configuration
        DB_CONNECTION_TIMEOUT_MS (int): Timeout para conexión a BD
        DB_QUERY_TIMEOUT_MS (int): Timeout para queries
        
        # Logging Configuration
        LOG_LEVEL (str): Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        LOG_FILE (str): Archivo de log (None = stderr only)
        
        # Feature Configuration
        USE_CACHE (bool): Cachear features de buyer/seller
        CACHE_TTL_SECONDS (int): TTL del cache
        
        # Environment
        ENVIRONMENT (str): Ambiente (development, staging, production)
        
    Ejemplo de uso:
        # Config default
        config = Config()
        
        # Config personalizada
        config = Config(
            API_URL="https://safemarket-prod.api.io",
            API_KEY=os.getenv("SAFEMARKET_KEY"),
            ENVIRONMENT="production",
            LOG_LEVEL="INFO"
        )
        
        # Usar en SDK
        sdk = SafeMarketSDK(config=config)
    """
    
    # API Configuration
    API_URL: str = ""  # Sin default para forzar definición
    API_KEY: str = ""  # Sin default para seguridad
    API_TIMEOUT_MS: int = 5000
    
    # Scoring Configuration
    SCORING_TIMEOUT_MS: int = 100
    MIN_SCORE_THRESHOLD: float = 30.0
    MAX_SCORE_THRESHOLD: float = 70.0
    
    # Rules Configuration
    ENABLE_RULES: bool = True
    RULES_VERSION: str = "1.0.0"
    
    # Model Configuration
    MODEL_VERSION: str = "1.0.0"
    MODEL_PATH: Optional[str] = None
    
    # Database Configuration
    DB_CONNECTION_TIMEOUT_MS: int = 5000
    DB_QUERY_TIMEOUT_MS: int = 30000
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # Feature Configuration
    USE_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600
    
    # Environment
    ENVIRONMENT: str = "development"
    
    def __post_init__(self):
        """
        Carga configuración desde variables de entorno después de inicializar.
        
        Busca variables en formato SAFEMARKET_* y las mapea a atributos.
        """
        env_config = self._load_from_env()
        for key, value in env_config.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @staticmethod
    def _load_from_env() -> Dict[str, Any]:
        """
        Carga configuración desde variables de entorno.
        
        Busca variables de la forma SAFEMARKET_* y las convierte
        a tipos apropiados (int, bool, str).
        
        Returns:
            dict: Configuración cargada del ambiente
        """
        config = {}
        
        # Mapeo de conversiones de tipo
        type_map = {
            'API_TIMEOUT_MS': int,
            'SCORING_TIMEOUT_MS': int,
            'MIN_SCORE_THRESHOLD': float,
            'MAX_SCORE_THRESHOLD': float,
            'ENABLE_RULES': lambda x: x.lower() in ('true', '1', 'yes'),
            'USE_CACHE': lambda x: x.lower() in ('true', '1', 'yes'),
            'CACHE_TTL_SECONDS': int,
            'DB_CONNECTION_TIMEOUT_MS': int,
            'DB_QUERY_TIMEOUT_MS': int,
        }
        
        for key, type_converter in type_map.items():
            env_var = f"SAFEMARKET_{key}"
            if env_var in os.environ:
                try:
                    config[key] = type_converter(os.environ[env_var])
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid value for {env_var}: {e}")
        
        # Cargar variables string directamente
        for key in ['API_URL', 'API_KEY', 'RULES_VERSION', 'MODEL_VERSION', 
                    'LOG_LEVEL', 'ENVIRONMENT', 'LOG_FILE', 'MODEL_PATH']:
            env_var = f"SAFEMARKET_{key}"
            if env_var in os.environ:
                config[key] = os.environ[env_var]
        
        return config
    
    def to_dict(self) -> dict:
        """
        Convierte configuración a diccionario (sin datos sensibles).
        
        Returns:
            dict: Config como diccionario
        """
        config_dict = {}
        for key in self.__dataclass_fields__:
            value = getattr(self, key)
            # No incluir API_KEY en output
            if key == 'API_KEY':
                config_dict[key] = '***' if value else ''
            else:
                config_dict[key] = value
        return config_dict
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Valida que la configuración sea correcta.
        
        Returns:
            tuple[bool, list[str]]: (es_válida, lista_de_errores)
        """
        errors = []
        
        if not self.API_URL:
            errors.append("API_URL must be configured")
        if not self.API_KEY:
            errors.append("API_KEY must be configured")
        if self.MIN_SCORE_THRESHOLD >= self.MAX_SCORE_THRESHOLD:
            errors.append("MIN_SCORE_THRESHOLD must be < MAX_SCORE_THRESHOLD")
        if not (0 <= self.MIN_SCORE_THRESHOLD <= 100):
            errors.append("MIN_SCORE_THRESHOLD must be between 0-100")
        if not (0 <= self.MAX_SCORE_THRESHOLD <= 100):
            errors.append("MAX_SCORE_THRESHOLD must be between 0-100")
        
        return len(errors) == 0, errors


def get_default_config() -> Config:
    """
    Retorna configuración default cargando desde ambiente.
    
    Returns:
        Config: Configuración default del sistema
    """
    return Config()
