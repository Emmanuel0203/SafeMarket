"""
Schemas de usuarios para la API unificada sobre el esquema enhanced.

Este archivo define los contratos de entrada/salida de los endpoints
de autenticacion y usuarios para mantener validaciones consistentes.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """
    Schema para crear un nuevo usuario (registro).
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    company: Optional[str] = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valida que la contraseña sea segura."""
        if not any(char.isupper() for char in v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not any(char.isdigit() for char in v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v


class UserLogin(BaseModel):
    """
    Schema para login.
    """
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """
    Schema para actualizar usuario.
    """
    phone: Optional[str] = Field(None, max_length=20)
    document_id: Optional[str] = Field(None, max_length=50)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)


class UserChangePassword(BaseModel):
    """
    Schema para cambiar contraseña.
    """
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Valida que la contraseña sea segura."""
        if not any(char.isupper() for char in v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not any(char.isdigit() for char in v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v


class UserOut(BaseModel):
    """
    Schema para respuesta de usuario (sin datos sensibles).
    """
    user_id: UUID
    email: str
    role: str
    status: str
    company_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """
    Schema para perfil de usuario (información completa pero sin contraseña).
    """
    user_id: UUID
    email: str
    phone: Optional[str] = None
    document_id: Optional[str] = None
    country_code: Optional[str] = None
    role: str
    status: str
    is_email_verified: bool
    is_phone_verified: bool
    company_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListOut(BaseModel):
    """
    Schema para listar usuarios (información básica).
    """
    user_id: UUID
    email: str
    role: str
    status: str

    class Config:
        from_attributes = True