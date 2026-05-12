"""
Utilidades de siembra de datos.

Este archivo se conserva como punto unico para poblar datos demo.
Actualmente no inserta registros por defecto para no contaminar entornos
de desarrollo/testing con datos no deterministas.
"""

from sqlalchemy.orm import Session


def seed_database(db: Session | None = None) -> None:
    """Hook de seed llamado por inicializacion de DB."""
    return None


def seed_all_demo_data(db: Session, user_id: str) -> None:
    """Compatibilidad para llamadas historicas de seed."""
    _ = (db, user_id)
    return None