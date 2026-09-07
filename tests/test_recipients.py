"""Tests for recipient listing on WiseApiClient."""

from unittest.mock import patch

from tests.conftest import make_response

RECIPIENT = {
    "id": 40000000,
    "profileId": 30000000,
    "name": {"fullName": "John Doe"},
    "currency": "GBP",
    "country": "GB",
    "accountSummary": "(04-00-75) 37778842",
}


def test_list_recipients_maps_profile_id(client):
    with patch("wise_mcp.api.wise_client.requests.get") as mocked:
        mocked.return_value = make_response(200, {"content": [RECIPIENT]})

        recipients = client.list_recipients("30000000", currency="GBP")

    assert len(recipients) == 1
    assert recipients[0].id == "40000000"
    assert recipients[0].profile_id == "30000000"
    assert recipients[0].full_name == "John Doe"
    args, kwargs = mocked.call_args
    assert args[0] == "https://api.wise.com/2026Q3/accounts"
    assert kwargs["params"] == {"profileId": "30000000", "currency": "GBP"}


def test_list_recipients_accepts_legacy_profile_key(client):
    with patch("wise_mcp.api.wise_client.requests.get") as mocked:
        mocked.return_value = make_response(200, {"content": [{**RECIPIENT, "profileId": None, "profile": 1}]})

        recipients = client.list_recipients("1")

    assert recipients[0].profile_id == "1"
