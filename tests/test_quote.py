"""Tests for the WiseQuote summary."""

from wise_mcp.api.types import WiseQuote

QUOTE = {
    "id": "q-1",
    "sourceCurrency": "EUR",
    "targetCurrency": "USD",
    "sourceAmount": 100.0,
    "targetAmount": 108.0,
    "rate": 1.1,
    "expirationTime": "2026-01-02T03:34:05Z",
    "paymentOptions": [
        {"payIn": "BANK_TRANSFER", "payOut": "BANK_TRANSFER", "fee": {"total": 2.0},
         "sourceAmount": 100.0, "targetAmount": 107.8, "disabled": False},
        {"payIn": "BALANCE", "payOut": "BANK_TRANSFER", "fee": {"total": 0.5},
         "sourceAmount": 100.0, "targetAmount": 109.45, "disabled": False,
         "estimatedDelivery": "2026-01-02T10:00:00Z"},
    ],
}


def test_quote_summarises_balance_payment_option():
    quote = WiseQuote.from_api(QUOTE)

    assert quote.id == "q-1"
    assert quote.fee == 0.5
    assert quote.target_amount == 109.45
    assert quote.pay_out == "BANK_TRANSFER"
    assert quote.estimated_delivery == "2026-01-02T10:00:00Z"
    assert quote.expiration_time == "2026-01-02T03:34:05Z"


def test_quote_without_balance_option_falls_back_to_top_level_amounts():
    data = {**QUOTE, "paymentOptions": [QUOTE["paymentOptions"][0]]}

    quote = WiseQuote.from_api(data)

    assert quote.fee is None
    assert quote.target_amount == 108.0
    assert quote.pay_out is None
