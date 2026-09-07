"""Tests for the low-level request helpers on WiseApiClient."""

import pytest

from tests.conftest import make_response


def test_get_sends_bearer_token_and_returns_json(client, mock_request):
    mock_request.return_value = make_response(200, {"ok": True})

    result = client._get("/v1/example", params={"a": 1})

    assert result == {"ok": True}
    mock_request.assert_called_once_with(
        "GET",
        "https://api.transferwise.com/v1/example",
        headers=client.headers,
        params={"a": 1},
        json=None,
    )
    assert client.headers["Authorization"] == "Bearer test-token"


def test_post_sends_json_body(client, mock_request):
    mock_request.return_value = make_response(200, {"id": 7})

    result = client._post("/v1/example", json={"x": "y"})

    assert result == {"id": 7}
    _, kwargs = mock_request.call_args
    assert kwargs["json"] == {"x": "y"}


def test_error_status_raises_with_api_details(client, mock_request):
    mock_request.return_value = make_response(
        422, {"errors": [{"code": "NOT_VALID", "message": "amount too low"}]}
    )

    with pytest.raises(Exception, match="NOT_VALID"):
        client._get("/v1/example")
