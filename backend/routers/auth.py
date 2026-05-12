"""
Router de autenticacion.

Este archivo expone registro/login/refresh/logout y utiliza
el servicio unificado de usuarios sobre PostgreSQL enhanced.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Dict
from jose import jwt, JWTError

from db import get_db
from schemas.user import UserCreate
from services.user_service import get_user_by_email, create_user
from core.security import (
    create_refresh_token,
    create_access_token,
    verify_password,
)
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=Dict)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema.

    - **name**: Nombre completo del usuario
    - **email**: Correo electrónico único
    - **password**: Contraseña (mínimo 8 caracteres)
    - **company**: Empresa (opcional)
    - **plan**: Plan de suscripción (opcional)

    Retorna el usuario creado con access y refresh tokens.
    """
    # Verificar si el usuario ya existe
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correo electrónico ya registrado"
        )

    # Crear usuario
    user = create_user(db, user_data)
    
    # Generar tokens
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "user_id": str(user.user_id),
        "email": user.email,
        "role": user.role,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Dict)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autentica un usuario y retorna JWT tokens.

    - **username**: Email del usuario
    - **password**: Contraseña

    Retorna access_token y refresh_token.
    """
    # Obtener usuario por email
    user = get_user_by_email(db, form_data.username)

    # Validar credenciales
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    # Generar tokens
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.email})

    # Establecer cookies seguras (opcional, para compatibilidad)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=False,
        samesite="lax"
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.user_id),
            "email": user.email,
            "role": user.role
        }
    }


@router.post("/refresh", response_model=Dict)
def refresh_token_endpoint(refresh_data: Dict, db: Session = Depends(get_db)):
    """
    Refresca el access token usando el refresh token.
    
    - **refresh_token**: Refresh token válido
    
    Retorna nuevo access token.
    """
    refresh_token = refresh_data.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token requerido"
        )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        email = payload.get("sub")
        user = get_user_by_email(db, email)
        
        if not user or user.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no válido"
            )
        
        # Generar nuevo access token
        new_access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}"
        )


@router.post("/logout")
def logout(response: Response):
    """
    Cierra la sesión eliminando las cookies.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Sesión cerrada correctamente"}