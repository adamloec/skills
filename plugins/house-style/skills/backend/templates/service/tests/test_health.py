from httpx2 import ASGITransport, AsyncClient

from {{pkg}}.main import app


async def test_health_is_open_for_probes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://api") as http:
        response = await http.get("/health")
    assert response.status_code == 204


async def test_v1_fails_closed_without_an_identity_verifier():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://api") as http:
        response = await http.get("/v1/notes/")
    assert response.status_code == 401, response.text
    assert response.json()["code"] == "unauthenticated"
