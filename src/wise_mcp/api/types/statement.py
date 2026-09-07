"""
Type definitions for Wise balance statements.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class WiseTransaction:
    """One line of a balance statement, flattened for reconciliation."""
    date: str
    type: str
    amount: float
    currency: str
    running_balance: Optional[float]
    reference_number: Optional[str]
    description: Optional[str]
    transaction_type: Optional[str]
    payment_reference: Optional[str]
    sender_name: Optional[str] = None
    sender_account: Optional[str] = None
    recipient_name: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "WiseTransaction":
        """Build a WiseTransaction from a raw statement transaction."""
        details = data.get("details") or {}
        recipient = details.get("recipient") or {}
        amount = data.get("amount") or {}
        running_balance = data.get("runningBalance") or {}
        return cls(
            date=data.get("date", ""),
            type=data.get("type", ""),
            amount=float(amount.get("value", 0)),
            currency=amount.get("currency", ""),
            running_balance=running_balance.get("value"),
            reference_number=data.get("referenceNumber"),
            description=details.get("description"),
            transaction_type=details.get("type"),
            payment_reference=details.get("paymentReference"),
            sender_name=details.get("senderName"),
            sender_account=details.get("senderAccount"),
            recipient_name=recipient.get("name"),
        )
