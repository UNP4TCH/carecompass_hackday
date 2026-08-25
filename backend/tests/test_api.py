from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_short_input_rejected():
    response = client.post("/api/conversation/start", json={"symptoms": "hi"})
    assert response.status_code == 422
