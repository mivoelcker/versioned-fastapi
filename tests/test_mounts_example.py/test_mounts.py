import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from examples.mounts import app


def test_simple_example():
    test_client = TestClient(app)

    # Base routes
    base_v1_response = test_client.get("/v1/")
    assert base_v1_response.status_code == 200
    assert base_v1_response.json() == {"message": "Hello World"}

    base_v2_response = test_client.get("/v2/")
    assert base_v2_response.status_code == 200
    assert base_v2_response.json() == {"message": "Hello Universe"}

    assert test_client.get("/docs").status_code == 200

    # Admin routes
    admin_v1_response = test_client.get("/admin/v1/")
    assert admin_v1_response.status_code == 200
    assert admin_v1_response.json() == {"message": "Hello Admin"}

    admin_v2_response = test_client.get("/admin/v2/")
    assert admin_v2_response.status_code == 200
    assert admin_v2_response.json() == {"message": "Hello Superadmin"}

    assert test_client.get("/admin/docs").status_code == 200


@pytest.mark.openapi_test
def test_openapi():
    test_client = TestClient(app)
    openapi_definitions = json.loads(
        (Path(__file__).parent / "openapi_definitions.json").read_text()
    )

    assert test_client.get("/openapi.json").json() == openapi_definitions["base"]["all"]
    assert (
        test_client.get("/v1/openapi.json").json() == openapi_definitions["base"]["v1"]
    )
    assert (
        test_client.get("/v2/openapi.json").json() == openapi_definitions["base"]["v2"]
    )

    assert (
        test_client.get("/admin/openapi.json").json()
        == openapi_definitions["admin"]["all"]
    )
    assert (
        test_client.get("/admin/v1/openapi.json").json()
        == openapi_definitions["admin"]["v1"]
    )
    assert (
        test_client.get("/admin/v2/openapi.json").json()
        == openapi_definitions["admin"]["v2"]
    )


@pytest.mark.openapi_test
def test_save_openapi():
    test_client = TestClient(app)
    path = Path(__file__).parent / "openapi_definitions.json"
    base_all = test_client.get("/openapi.json").json()
    base_v1 = test_client.get("/v1/openapi.json").json()
    base_v2 = test_client.get("/v2/openapi.json").json()

    admin_all = test_client.get("/admin/openapi.json").json()
    admin_v1 = test_client.get("/admin/v1/openapi.json").json()
    admin_v2 = test_client.get("/admin/v2/openapi.json").json()

    text = json.dumps(
        {
            "base": {
                "all": base_all,
                "v1": base_v1,
                "v2": base_v2,
            },
            "admin": {
                "all": admin_all,
                "v1": admin_v1,
                "v2": admin_v2,
            },
        },
    )
    path.write_text(text)
