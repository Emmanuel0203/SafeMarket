"""
Tests de funcionamiento de API (sin servidor externo).

Este archivo valida endpoints principales usando TestClient:
- health check
- registro
- login
- perfil autenticado
- listado de usuarios
"""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_endpoints() -> None:
    """La API responde correctamente en endpoints de salud."""
    root_response = client.get("/")
    health_response = client.get("/health")
    info_response = client.get("/api/v1")

    assert root_response.status_code == 200
    assert health_response.status_code == 200
    assert info_response.status_code == 200


def test_auth_and_users_flow() -> None:
    """Flujo completo minimo: register -> login -> profile -> users."""
    email = f"api_test_{uuid4().hex[:8]}@safemarket.com"
    password = "SecurePass123"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "company": "SafeMarket QA",
        },
    )
    assert register_response.status_code == 200
    register_payload = register_response.json()
    assert register_payload["email"] == email

    login_response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert "access_token" in login_payload

    access_token = login_payload["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    profile_response = client.get("/users/profile", headers=headers)
    assert profile_response.status_code == 200
    profile_payload = profile_response.json()
    assert profile_payload["email"] == email

    list_response = client.get("/users/", headers=headers)
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)
