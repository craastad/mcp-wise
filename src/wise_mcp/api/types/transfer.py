"""
Type definitions for Wise transfers, fund responses and SCA handling.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class WiseFundResponse:
    type: str
    status: str
    error_code: Optional[str] = None


@dataclass
class WiseScaResponse:
    one_time_token: str


@dataclass
class WiseFundWithScaResponse:
    """Combined response for fund transfer with SCA challenge."""
    fund_response: Optional[WiseFundResponse] = None
    sca_response: Optional[WiseScaResponse] = None

@dataclass
class WiseTransfer:
    """The fields of a transfer that matter when tracking or reconciling a payment."""
    id: str
    status: str
    source_currency: str
    source_value: Optional[float]
    target_currency: str
    target_value: Optional[float]
    rate: Optional[float]
    reference: Optional[str]
    recipient_id: Optional[str]
    created: Optional[str]
    customer_transaction_id: Optional[str]
    has_active_issues: bool = False

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "WiseTransfer":
        """Build a WiseTransfer from a raw transfer object returned by the Wise API."""
        details = data.get("details") or {}
        target_account = data.get("targetAccount")
        return cls(
            id=str(data.get("id", "")),
            status=data.get("status", ""),
            source_currency=data.get("sourceCurrency", ""),
            source_value=data.get("sourceValue"),
            target_currency=data.get("targetCurrency", ""),
            target_value=data.get("targetValue"),
            rate=data.get("rate"),
            reference=details.get("reference") or data.get("reference"),
            recipient_id=str(target_account) if target_account is not None else None,
            created=data.get("created"),
            customer_transaction_id=data.get("customerTransactionId"),
            has_active_issues=bool(data.get("hasActiveIssues", False)),
        )
