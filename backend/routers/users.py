"""
Router de usuarios.

Este archivo implementa operaciones de perfil y administracion
de usuarios autenticados usando UUID y esquema enhanced.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from db import get_db
from db.models_enhanced import User
from schemas.user import (
    UserOut,
    UserUpdate,
    UserListOut,
    UserProfile,
    UserChangePassword
)
from services.user_service import (
    get_all_users,
    get_user_by_id,
    update_user as update_user_service,
    delete_user,
    change_password as change_password_service,
    get_user_count,
    get_active_users
)
from core.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserListOut])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos los usuarios (requiere autenticación).

    - **skip**: Número de registros a saltar (paginación)
    - **limit**: Número máximo de registros (máximo 100)
    """
    users = get_all_users(db, skip=skip, limit=limit)
    return users


@router.get("/profile", response_model=UserProfile)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el perfil del usuario autenticado.

    Retorna toda la información del usuario sin datos sensibles.
    """
    user = get_user_by_id(db, current_user.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la información de un usuario específico.

    Solo administradores pueden ver información de otros usuarios,
    cualquiera puede ver su propio perfil.
    """
    # Verificar permisos
    if user_id != current_user.user_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este usuario"
        )

    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza la información de un usuario.

    - **name**: Nombre completo
    - **company**: Empresa
    - **plan**: Plan de suscripción

    Solo administradores pueden actualizar otros usuarios.
    """
    # Verificar permisos
    if user_id != current_user.user_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este usuario"
        )

    user = update_user_service(db, user_id, data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return user


@router.delete("/{user_id}")
def delete_user_endpoint(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un usuario (marcado como inactivo).

    Solo administradores pueden eliminar usuarios.
    """
    # Verificar permisos
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar usuarios"
        )

    # No permitir auto-eliminación
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminarte a ti mismo"
        )

    success = delete_user(db, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return {"message": "Usuario eliminado exitosamente"}


@router.post("/change-password")
def change_password_endpoint(
    change_pass_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña del usuario autenticado.

    Requiere proporcionar la contraseña actual y confirmar la nueva.
    """
    # Validar que las contraseñas coincidan
    if change_pass_data.new_password != change_pass_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas nuevas no coinciden"
        )

    success = change_password_service(
        db,
        current_user.user_id,
        change_pass_data.current_password,
        change_pass_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña actual incorrecta"
        )

    return {"message": "Contraseña actualizada exitosamente"}


@router.post("/{user_id}/change-password")
def change_user_password(
    user_id: UUID,
    change_pass_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña de un usuario.

    Requiere proporcionar la contraseña actual y confirmar la nueva.
    """
    # No permitir cambiar contraseña de otros usuarios (excepto admin)
    if user_id != current_user.user_id and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para cambiar esta contraseña"
        )

    # Validar que las contraseñas coincidan
    if change_pass_data.new_password != change_pass_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas nuevas no coinciden"
        )

    success = change_password_service(
        db,
        user_id,
        change_pass_data.current_password,
        change_pass_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña actual incorrecta o usuario no encontrado"
        )

    return {"message": "Contraseña actualizada exitosamente"}


@router.get("/statistics/summary")
def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de usuarios (solo para administradores).
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden ver estadísticas"
        )

    total_users = get_user_count(db)
    active_users = get_active_users(db)

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users
    }