"""
Dependencias de seguridad para endpoints protegidos.

Este modulo centraliza la extraccion y validacion del access token
desde cookie o header Bearer y resuelve el usuario autenticado.
"""

from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from core.config import SECRET_KEY, ALGORITHM
from db import get_db
from services.user_service import get_user_by_email


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Obtiene el usuario autenticado desde cookie o Authorization header.

    Soporta:
    - Cookie: access_token
    - Header: Authorization: Bearer {token}

    :param request: Request HTTP
    :param db: Sesión de base de datos
    :return: Usuario autenticado
    """
    # Intentar obtener token de cookie
    token = request.cookies.get("access_token")

    # Si no hay en cookie, intentar header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # "Bearer " = 7 caracteres

    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token inválido")

        email = payload.get("sub")

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = get_user_by_email(db, email)

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user