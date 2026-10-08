import pytest
from fastapi.testclient import TestClient

from tests.conftest import has_infra


def test_live(client: TestClient) -> None:
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.integration
@pytest.mark.skipif(not has_infra(), reason="set INTEGRATION=1 with docker compose up")
def test_ready(client: TestClient) -> None:
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["postgres"] == "ok"
    assert r.json()["redis"] == "ok"
