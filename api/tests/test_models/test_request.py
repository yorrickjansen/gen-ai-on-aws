from gen_ai_on_aws.examples.types import (
    ExtractUserAsyncResponse,
    ExtractUserRequest,
    User,
)


def test_extract_user_request():
    """Test ExtractUserRequest model."""
    data = {"text": "This is a test text"}
    request = ExtractUserRequest(**data)
    assert request.text == "This is a test text"


def test_user_model():
    """Test User model."""
    data = {"name": "John Doe", "age": 30, "email": "john@example.com"}
    user = User(**data)
    assert user.name == "John Doe"
    assert user.age == 30
    assert user.email == "john@example.com"

    # Test with missing email
    data = {"name": "Jane Doe", "age": 25}
    user = User(**data)
    assert user.name == "Jane Doe"
    assert user.age == 25
    assert user.email is None


def test_extract_user_async_response():
    """Test ExtractUserAsyncResponse model."""
    data = {"request_id": "test-request-id-123"}
    response = ExtractUserAsyncResponse(**data)
    assert response.request_id == "test-request-id-123"
