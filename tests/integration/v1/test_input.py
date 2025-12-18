import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_post_input_success(client):
    response = client.post(
        "/v1/input",
        json={"name": "Hello World"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": "Hi there Hello World",
        "status_code": 200,
    }


def test_post_input_missing_body(client):
    response = client.post("/v1/input")
    assert response.status_code == 422


def test_post_input_invalid_type(client):
    response = client.post("/v1/input", json={"input": 1})
    assert response.status_code == 422
