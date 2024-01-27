import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from examples.simple import app, versions


def test_simple_example():
    test_client = TestClient(app)

    assert versions == ["1", "2", "3"]

    # Assert not versioned routes does not exist (except /health)
    assert test_client.get("/health").status_code == 200
    assert test_client.get("/items").status_code == 404
    assert test_client.get("/items/1").status_code == 404
    assert test_client.post("/items").status_code == 404

    # Version 1
    v1_body = {
        "id": 1,
        "name": "Item 1",
    }
    assert test_client.post("/v1/items", json=v1_body).status_code == 201
    assert test_client.get("v1/items").status_code == 200
    assert test_client.get("v1/items/1").status_code == 200

    # Version 2
    v2_body = {
        "id": 2,
        "name": "Item 2",
        "description": "The cake is al lie?",
    }
    assert test_client.post("/v2/items", json=v2_body).status_code == 201
    assert test_client.get("v2/items/2").status_code == 200

    assert test_client.get("v2/items/1").status_code == 404
    assert test_client.post("/v2/items", json=v1_body).status_code == 422
    assert test_client.get("v2/items").status_code == 405

    # Version 3
    v3_body = {
        "id": 3,
        "name": "Item 3",
        "description": "The cake is al lie?",
        "price": 420,
    }
    assert test_client.post("/v3/items", json=v3_body).status_code == 201

    assert test_client.post("/v3/items", json=v2_body).status_code == 422
    assert test_client.get("v3/items").status_code == 405
    assert test_client.get("v3/items/3").status_code == 404


@pytest.mark.openapi_test
def test_openapi():
    test_client = TestClient(app)
    openapi_definitions = json.loads(
        (Path(__file__).parent / "openapi_definitions.json").read_text()
    )

    assert test_client.get("/openapi.json").json() == openapi_definitions["all"]
    assert test_client.get("/v1/openapi.json").json() == openapi_definitions["v1"]
    assert test_client.get("/v2/openapi.json").json() == openapi_definitions["v2"]
    assert test_client.get("/v3/openapi.json").json() == openapi_definitions["v3"]


def test_docs():
    test_client = TestClient(app)
    assert test_client.get("/docs").status_code == 200
    assert test_client.get("/redoc").status_code == 200

    swagger_html = test_client.get("/docs").text
    assert "StandaloneLayout" in swagger_html
    for url in (
        "/openapi.json",
        "/v1/openapi.json",
        "/v2/openapi.json",
        "/v2/openapi.json",
    ):
        assert url in swagger_html
