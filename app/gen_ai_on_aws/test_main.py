from fastapi.testclient import TestClient
from gen_ai_on_aws.main import app, User

client = TestClient(app)


def test_hello():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == "Hello, world!"


def test_extract_user():
    test_text = (
        "My name is John Doe, I am 30 years old, and my email is john@example.com"
    )
    response = client.post("/extract-user", json={"text": test_text})

    assert response.status_code == 200
    data = response.json()

    user = User.model_validate(data)
    assert user.name == "John Doe"
    assert user.age == 30
    assert user.email == "john@example.com"

    # Test with missing email
    test_text_no_email = "My name is Jane Doe and I am 25 years old"
    response = client.post("/extract-user", json={"text": test_text_no_email})

    assert response.status_code == 200
    data = response.json()
    user = User.model_validate(data)

    assert user.name == "Jane Doe"
    assert user.age == 25
    assert user.email is None
