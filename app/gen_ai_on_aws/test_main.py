from fastapi.testclient import TestClient
from gen_ai_on_aws.main import app

client = TestClient(app)


def test_hello():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == "Hello, world!"


def test_extract_user():
    pass
