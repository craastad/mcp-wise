"""Tests for balance statements."""

from datetime import datetime, timezone

import pytest

from tests.conftest import make_response
from wise_mcp.api.types import WiseTransaction
from wise_mcp.resources.statements import _parse_timestamp, resolve_statement_interval

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


def test_download_balance_statement_requests_pdf(client, mock_request):
    mock_request.return_value = make_response(200, content=b"%PDF-1.4")

    data = client.download_balance_statement(
        "42", "7", "EUR", "2026-01-01T00:00:00.000Z", "2026-01-31T23:59:59.999Z", locale="de"
    )

    assert data == b"%PDF-1.4"
    args, kwargs = mock_request.call_args
    assert args[1].endswith("/v1/profiles/42/balance-statements/7/statement.pdf")
    assert kwargs["params"] == {
        "currency": "EUR",
        "intervalStart": "2026-01-01T00:00:00.000Z",
        "intervalEnd": "2026-01-31T23:59:59.999Z",
        "type": "COMPACT",
        "statementLocale": "de",
    }
    assert kwargs["headers"]["Accept"] == "application/pdf"
    assert kwargs["headers"]["Authorization"] == "Bearer test-token"
    assert "Content-Type" not in kwargs["headers"]


def test_download_balance_statement_rejects_unknown_format(client, mock_request):
    with pytest.raises(ValueError, match="fmt must be one of"):
        client.download_balance_statement("42", "7", "EUR", "a", "b", fmt="docx")
    with pytest.raises(ValueError, match="statement_type must be one of"):
        client.download_balance_statement("42", "7", "EUR", "a", "b", statement_type="WIDE")
    mock_request.assert_not_called()


def test_month_expands_to_full_calendar_month():
    assert resolve_statement_interval("2025-02", None, None) == (
        "2025-02-01T00:00:00.000Z",
        "2025-02-28T23:59:59.999Z",
    )


def test_month_handles_leap_year():
    assert resolve_statement_interval("2024-02", None, None) == (
        "2024-02-01T00:00:00.000Z",
        "2024-02-29T23:59:59.999Z",
    )


def test_date_only_bounds_cover_whole_days():
    assert resolve_statement_interval(None, "2025-08-01", "2025-08-31") == (
        "2025-08-01T00:00:00.000Z",
        "2025-08-31T23:59:59.999Z",
    )


def test_full_timestamps_are_kept():
    assert resolve_statement_interval(None, "2025-08-01T12:00:00Z", "2025-08-02T12:30:00+02:00") == (
        "2025-08-01T12:00:00.000Z",
        "2025-08-02T10:30:00.000Z",
    )


def test_interval_over_limit_is_rejected():
    with pytest.raises(ValueError, match="469 days"):
        resolve_statement_interval(None, "2024-01-01", "2025-06-30")


def test_missing_bounds_and_bad_month_are_rejected():
    with pytest.raises(ValueError, match="either month"):
        resolve_statement_interval(None, "2024-01-01", None)
    with pytest.raises(ValueError, match="YYYY-MM"):
        resolve_statement_interval("2024-1", None, None)
