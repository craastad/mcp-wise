"""
Shared fixtures for the Wise API client tests.

All tests run against a mocked ``requests`` module, so no network access or
real API token is needed.
"""

from unittest.mock import MagicMock, patch

import pytest

from wise_mcp.api.wise_client import WiseApiClient


@pytest.fixture(autouse=True)
def wise_env(monkeypatch):
    """Provide a dummy token and pin the client to the production base URL."""
    monkeypatch.setenv("WISE_API_TOKEN", "test-token")
    monkeypatch.setenv("WISE_IS_SANDBOX", "false")


@pytest.fixture
def client() -> WiseApiClient:
    return WiseApiClient()


@pytest.fixture
def mock_request():
    """Patch ``requests.request`` and yield the mock so tests can set responses."""
    with patch("wise_mcp.api.wise_client.requests.request") as mocked:
        yield mocked


def make_response(status_code: int = 200, json_data=None, content: bytes = b"", headers=None):
    """Build a fake ``requests.Response``-like object."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.content = content
    response.headers = headers or {}
    return response
