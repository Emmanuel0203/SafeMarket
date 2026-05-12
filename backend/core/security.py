"""
Manejo de tokens JWT (access y refresh) y hashing de contraseñas.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext

from core.config import SECRET_KEY, ALGORITHM

# Configurar contexto de criptografía para bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Genera un hash bcrypt de la contraseña.

    :param password: Contraseña en texto plano
    :return: Hash de la contraseña
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica que una contraseña en texto plano coincida con su hash.

    :param plain_password: Contraseña en texto plano
    :param hashed_password: Hash almacenado en base de datos
    :return: True si coinciden, False en caso contrario
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Genera un access token JWT de corta duración.

    :param data: Payload del token
    :param expires_delta: Tiempo de expiración
    :return: Token JWT
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Genera un refresh token JWT de larga duración.

    :param data: Payload del token
    :return: Refresh token JWT
    """
    expire = datetime.utcnow() + timedelta(days=7)
    data.update({"exp": expire, "type": "refresh"})

    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """
    Verifica y decodifica un token JWT.

    :param token: Token JWT a verificar
    :return: Payload del token o None si es inválido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None