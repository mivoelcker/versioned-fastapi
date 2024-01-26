import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--skip-openapi-tests",
        action="store_true",
        default=False,
        help="Skip testing the openapi json.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "openapi_test: Marks tests for openapi json tests."
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-openapi-tests"):
        skip_openapi = pytest.mark.skip(
            reason="Skipped due to command line option --skip_openapi"
        )
        for item in items:
            if "openapi_test" in item.keywords:
                item.add_marker(skip_openapi)
