"""Tests for balance statements."""

from datetime import datetime, timezone

from tests.conftest import make_response
from wise_mcp.api.types import WiseTransaction
from wise_mcp.resources.statements import _parse_timestamp

CREDIT = {
    "type": "CREDIT",
    "date": "2026-01-05T10:00:00Z",
    "amount": {"value": 49.99, "currency": "EUR"},
    "runningBalance": {"value": 1049.99, "currency": "EUR"},
    "referenceNumber": "TRANSFER-1",
    "details": {
        "type": "DEPOSIT",
        "description": "Received money from A Sender with reference Order 1",
        "senderName": "A Sender",
        "senderAccount": "DE00 0000 0000 0000 0000 00",
        "paymentReference": "Order 1",
    },
}

DEBIT = {
    "type": "DEBIT",
    "date": "2026-01-04T10:00:00Z",
    "amount": {"value": -300.0, "currency": "EUR"},
    "runningBalance": {"value": 1000.0, "currency": "EUR"},
    "referenceNumber": "TRANSFER-2",
    "details": {
        "type": "TRANSFER",
        "description": "Sent money to A Supplier",
        "paymentReference": "Invoice 7",
        "recipient": {"name": "A Supplier", "bankAccount": "DE11"},
    },
}


def test_get_balance_statement_passes_window_and_type(client, mock_request):
    mock_request.return_value = make_response(200, {"transactions": [CREDIT, DEBIT]})

    statement = client.get_balance_statement(
        "42", "7", "EUR", "2026-01-01T00:00:00.000Z", "2026-01-31T00:00:00.000Z"
    )

    assert len(statement["transactions"]) == 2
    args, kwargs = mock_request.call_args
    assert args[1].endswith("/v1/profiles/42/balance-statements/7/statement.json")
    assert kwargs["params"] == {
        "currency": "EUR",
        "intervalStart": "2026-01-01T00:00:00.000Z",
        "intervalEnd": "2026-01-31T00:00:00.000Z",
        "type": "COMPACT",
    }


def test_transaction_flattens_credit_details():
    transaction = WiseTransaction.from_api(CREDIT)

    assert transaction.type == "CREDIT"
    assert transaction.amount == 49.99
    assert transaction.running_balance == 1049.99
    assert transaction.sender_name == "A Sender"
    assert transaction.payment_reference == "Order 1"
    assert transaction.recipient_name is None


def test_transaction_flattens_debit_recipient():
    transaction = WiseTransaction.from_api(DEBIT)

    assert transaction.amount == -300.0
    assert transaction.recipient_name == "A Supplier"
    assert transaction.sender_name is None


def test_parse_timestamp_accepts_zulu_and_naive():
    assert _parse_timestamp("2026-01-01T00:00:00Z") == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert _parse_timestamp("2026-01-01T00:00:00") == datetime(2026, 1, 1, tzinfo=timezone.utc)
