"""Tests for transfer lookups on WiseApiClient."""

from tests.conftest import make_response

TRANSFER = {
    "id": 123456,
    "status": "outgoing_payment_sent",
    "sourceCurrency": "EUR",
    "sourceValue": 300.0,
    "targetCurrency": "EUR",
    "targetValue": 300.0,
    "rate": 1.0,
    "details": {"reference": "Invoice 42"},
    "targetAccount": 987,
    "created": "2026-01-02 03:04:05",
    "customerTransactionId": "abc-123",
    "hasActiveIssues": False,
}


def test_get_transfer_maps_fields(client, mock_request):
    mock_request.return_value = make_response(200, TRANSFER)

    transfer = client.get_transfer("123456")

    assert transfer.id == "123456"
    assert transfer.status == "outgoing_payment_sent"
    assert transfer.source_value == 300.0
    assert transfer.reference == "Invoice 42"
    assert transfer.recipient_id == "987"
    assert transfer.has_active_issues is False
    args, _ = mock_request.call_args
    assert args == ("GET", "https://api.transferwise.com/v1/transfers/123456")


def test_download_transfer_receipt_returns_pdf_bytes(client, mock_request):
    mock_request.return_value = make_response(200, content=b"%PDF-1.4 fake")

    pdf = client.download_transfer_receipt("123456")

    assert pdf.startswith(b"%PDF")
    args, _ = mock_request.call_args
    assert args == ("GET", "https://api.transferwise.com/v1/transfers/123456/receipt.pdf")
