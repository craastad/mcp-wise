"""
Type definitions for Wise Quotes.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

# fund_transfer only supports paying from the balance, so quotes are summarised for that option.
BALANCE_PAY_IN = "BALANCE"


@dataclass
class WiseQuote:
    """A quote summarised for the balance payment option that send_money funds with."""
    id: str
    source_currency: str
    target_currency: str
    source_amount: Optional[float]
    target_amount: Optional[float]
    rate: Optional[float]
    fee: Optional[float]
    pay_out: Optional[str]
    estimated_delivery: Optional[str]
    expiration_time: Optional[str]

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "WiseQuote":
        """Build a WiseQuote from a raw quote object returned by the Wise API."""
        option = next(
            (o for o in data.get("paymentOptions", [])
             if o.get("payIn") == BALANCE_PAY_IN and not o.get("disabled")),
            {},
        )
        return cls(
            id=str(data.get("id", "")),
            source_currency=data.get("sourceCurrency", ""),
            target_currency=data.get("targetCurrency", ""),
            source_amount=option.get("sourceAmount", data.get("sourceAmount")),
            target_amount=option.get("targetAmount", data.get("targetAmount")),
            rate=data.get("rate"),
            fee=(option.get("fee") or {}).get("total"),
            pay_out=option.get("payOut"),
            estimated_delivery=option.get("estimatedDelivery"),
            expiration_time=data.get("expirationTime"),
        )
