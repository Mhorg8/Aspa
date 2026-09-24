from typing import Never

from httpx import AsyncClient

from app.main import app
from app.modules.auth.dependencies import get_auth_service


async def test_unexpected_errors_use_safe_error_envelope(client: AsyncClient) -> None:
    async def broken_service() -> Never:
        raise RuntimeError("sensitive internal detail")

    app.dependency_overrides[get_auth_service] = broken_service
    response = await client.post(
        "/api/auth/login",
        json={"email": "athlete@example.com", "password": "strong-password"},
    )
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "An unexpected error occurred"}
    }
    assert "sensitive" not in response.text


async def test_auth_error_uses_consistent_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/users/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "error": {"code": "application_error", "message": "Authentication required"}
    }
