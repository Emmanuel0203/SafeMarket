"""
SafeMarket Pocket SDK - Utils Module
====================================

Utilidades y helpers del SDK.
"""

import logging

__all__ = [
    'get_logger',
]


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Obtiene logger configurado para el SDK.
    
    Args:
        name (str): Nombre del logger
        level (str): Nivel de logging (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
