"""Tests for WiseApiClient.list_balances."""

from tests.conftest import make_response

BALANCES = [
    {"id": 1, "currency": "EUR", "amount": {"value": 1234.5, "currency": "EUR"},
     "reservedAmount": {"value": 10, "currency": "EUR"}, "name": None},
    {"id": 2, "currency": "USD", "amount": {"value": 20, "currency": "USD"},
     "reservedAmount": {"value": 0, "currency": "USD"}, "name": "Travel"},
]


def test_list_balances_returns_all_currencies(client, mock_request):
    mock_request.return_value = make_response(200, BALANCES)

    balances = client.list_balances("42")

    assert [b.currency for b in balances] == ["EUR", "USD"]
    assert balances[0].amount == 1234.5
    assert balances[0].reserved_amount == 10
    assert balances[1].name == "Travel"
    _, kwargs = mock_request.call_args
    assert kwargs["params"] == {"types": "STANDARD"}


def test_list_balances_filters_by_currency_case_insensitively(client, mock_request):
    mock_request.return_value = make_response(200, BALANCES)

    balances = client.list_balances("42", currency="usd")

    assert [b.currency for b in balances] == ["USD"]
