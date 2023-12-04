import json
from pathlib import Path

from fastapi.testclient import TestClient

from examples.customization import app, versions


def test_customization_example():
    test_client = TestClient(app)

    assert versions == ["1", "2"]

    cookie = {
        "butter": 250,
        "chocolate": 200,
        "eggs": 2,
        "flour": 360,
        "salt": 3,
        "sugar": 100,
        "vanilla": 5,
        "heat": 180,
        "baking_time": 600,
    }
    cookie_response = test_client.post("/version1/cookies", json=cookie)
    assert cookie_response.status_code == 202
    assert test_client.get(f"/version1/cookies/{cookie_response.text}").status_code == 200

    cookie_response = test_client.post("/version2/cookies", json=cookie)
    assert cookie_response.status_code == 202
    assert test_client.get(f"/version2/cookies/{cookie_response.text}").status_code == 412

    cake_response = test_client.get("/version1/cake")
    assert cake_response.status_code == 404
    assert cake_response.json() == {"detail": "The cake is a lie."}


def test_openapi_and_docs():
    test_client = TestClient(app)
    openapi_definitions = json.loads((Path(__file__).parent / "openapi_definitions.json").read_text())

    assert test_client.get("/version1/swagger.json").json() == openapi_definitions["v1"]
    assert test_client.get("/version2/swagger.json").json() == openapi_definitions["v2"]

    assert test_client.get("/swagger").status_code == 200
    assert test_client.get("/redoc").status_code == 404

    swagger_html = test_client.get("/swagger").text
    assert "https://www.google.com/favicon.ico" in swagger_html
    assert "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css" in swagger_html
    assert "All Routes" not in swagger_html
    assert "obsidian" in swagger_html
