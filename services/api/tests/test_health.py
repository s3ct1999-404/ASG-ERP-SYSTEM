from unittest import mock

import pytest
from django.db import OperationalError
from rest_framework.test import APIClient


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_live_returns_ok_without_auth(client: APIClient) -> None:
    response = client.get("/api/v1/health/live/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_ready_returns_ok_when_database_is_up(client: APIClient) -> None:
    response = client.get("/api/v1/health/ready/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_503_and_leaks_nothing_when_database_is_down(client: APIClient) -> None:
    broken = mock.MagicMock()
    broken.cursor.side_effect = OperationalError("connection to server at secret-host failed")
    with mock.patch("core.views.connection", broken):
        response = client.get("/api/v1/health/ready/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "secret-host" not in response.content.decode()


def test_responses_carry_a_request_id(client: APIClient) -> None:
    response = client.get("/api/v1/health/live/")
    assert len(response["X-Request-ID"]) >= 8
