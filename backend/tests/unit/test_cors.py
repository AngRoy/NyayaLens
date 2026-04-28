"""CORS policy tests."""

from fastapi.testclient import TestClient
from httpx import Response

from nyayalens.config import Settings
from nyayalens.main import create_app


def _preflight(client: TestClient, origin: str) -> Response:
    return client.options(
        "/api/v1/datasets/upload",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )


def test_dev_cors_allows_flutter_web_ephemeral_localhost_port() -> None:
    client = TestClient(create_app(Settings(nyayalens_env="dev")))

    response = _preflight(client, "http://localhost:64024")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:64024"


def test_prod_cors_does_not_allow_ephemeral_localhost_by_default() -> None:
    client = TestClient(
        create_app(
            Settings(
                nyayalens_env="prod",
                cors_allowed_origins="https://nyayalens.web.app",
            )
        )
    )

    response = _preflight(client, "http://localhost:64024")

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
