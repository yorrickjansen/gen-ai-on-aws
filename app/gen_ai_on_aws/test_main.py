from fastapi.testclient import TestClient
from gen_ai_on_aws.main import app

client = TestClient(app)


async def test_hello():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


# @pytest.mark.asyncio
# async def test_extract_user():
#     async with AsyncClient(transport=app, base_url="http://test") as ac:
#         response = await ac.post(
#             "/extract-user",
#             json={"text": "My name is John Doe, I am 30 years old, and I don't have an email address."}
#         )
#     assert response.status_code == 200
#     assert response.json() == {"name": "John Doe", "age": 30, "email": None}
