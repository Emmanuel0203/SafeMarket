"""
Compatibilidad para imports historicos de base de datos.

Este archivo mantiene `db.database` como facade para no romper imports
antiguos, redirigiendo todo al modulo unificado `db`.
"""

from db import Base, SessionLocal, engine, get_db

__all__ = ["engine", "SessionLocal", "Base", "get_db"]