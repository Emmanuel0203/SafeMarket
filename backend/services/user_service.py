"""
Servicio de usuarios unificado para el esquema enhanced.

Este archivo encapsula CRUD de usuarios y reglas de negocio para que
routers/dependencias no conozcan detalles de persistencia.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.security import get_password_hash, verify_password
from db.models_enhanced import Company, User
from schemas.user import UserCreate, UserUpdate


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca un usuario activo por email."""
    return db.query(User).filter(User.email == email, User.status == "ACTIVE").first()


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """Busca un usuario activo por UUID."""
    return db.query(User).filter(User.user_id == user_id, User.status == "ACTIVE").first()


def _get_or_create_company(db: Session, company_name: Optional[str]) -> Optional[UUID]:
    """Crea o recupera una empresa y devuelve su UUID."""
    if not company_name:
        return None
    existing_company = db.query(Company).filter(Company.name == company_name).first()
    if existing_company:
        return existing_company.company_id
    company = Company(name=company_name)
    db.add(company)
    db.flush()
    return company.company_id


def create_user(db: Session, user_data: UserCreate) -> User:
    """Crea un usuario activo con password hasheado."""
    if get_user_by_email(db, user_data.email):
        raise ValueError(f"El email {user_data.email} ya está registrado")

    company_id = _get_or_create_company(db, user_data.company)
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        company_id=company_id,
        role="VIEWER",
        status="ACTIVE",
        is_email_verified=False,
        is_phone_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Lista usuarios activos con paginacion."""
    return (
        db.query(User)
        .filter(User.status == "ACTIVE")
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_user(db: Session, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
    """Actualiza campos permitidos del usuario."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: UUID) -> bool:
    """Borrado logico de usuario."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    user.status = "INACTIVE"
    db.commit()
    return True


def change_password(db: Session, user_id: UUID, current_password: str, new_password: str) -> bool:
    """Cambia password si la actual es valida."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    if not verify_password(current_password, user.hashed_password):
        return False
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True


def get_user_count(db: Session) -> int:
    """Cuenta total de usuarios."""
    return db.query(func.count(User.user_id)).scalar() or 0


def get_active_users(db: Session) -> int:
    """Cuenta total de usuarios activos."""
    return db.query(func.count(User.user_id)).filter(User.status == "ACTIVE").scalar() or 0