"""
Wise API balance statement resources for the FastMCP server.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastmcp.exceptions import ToolError

from wise_mcp.app import mcp
from wise_mcp.api.types import WiseTransaction
from wise_mcp.api.wise_client_helper import init_wise_client

# Wise expects statement interval bounds in this exact UTC format.
WISE_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"


@mcp.tool()
def list_balance_transactions(
    currency: str,
    profile_type: str = "personal",
    days: int = 30,
    interval_start: Optional[str] = None,
    interval_end: Optional[str] = None,
    transaction_type: Optional[str] = None,
    sender_name: Optional[str] = None,
) -> List[WiseTransaction]:
    """
    Returns the transactions of a balance in a time window, newest first, for reconciling
    incoming payments (CREDIT) and outgoing transfers (DEBIT). Wise may require Strong Customer
    Authentication for statements on some accounts; the API error says so if it does.

    Args:
        currency: Currency code of the balance to read (e.g., 'EUR')
        profile_type: The type of profile that holds the balance. One of [personal, business]
        days: Number of days to look back when interval_start is not given. Default: 30
        interval_start: Optional. Start of the window as an ISO 8601 timestamp (e.g., '2026-01-01T00:00:00Z')
        interval_end: Optional. End of the window as an ISO 8601 timestamp. Default: now
        transaction_type: Optional. Only return 'CREDIT' or 'DEBIT' transactions
        sender_name: Optional. Only return transactions whose sender name contains this text (case-insensitive)

    Returns:
        List of transactions with date, type, amount, running balance, reference and counterparty

    Raises:
        Exception: If the API request fails or no balance exists for the currency
    """

    if transaction_type and transaction_type.upper() not in ("CREDIT", "DEBIT"):
        raise ToolError("transaction_type must be 'CREDIT' or 'DEBIT'")

    ctx = init_wise_client(profile_type)

    balances = ctx.wise_api_client.list_balances(ctx.profile.profile_id, currency)
    if not balances:
        raise ToolError(f"No {currency.upper()} balance found for the {profile_type} profile")

    end = _parse_timestamp(interval_end) if interval_end else datetime.now(timezone.utc)
    start = _parse_timestamp(interval_start) if interval_start else end - timedelta(days=days)

    statement = ctx.wise_api_client.get_balance_statement(
        profile_id=ctx.profile.profile_id,
        balance_id=balances[0].id,
        currency=currency.upper(),
        interval_start=start.strftime(WISE_TIMESTAMP_FORMAT),
        interval_end=end.strftime(WISE_TIMESTAMP_FORMAT),
    )

    transactions = [WiseTransaction.from_api(t) for t in statement.get("transactions", [])]

    if transaction_type:
        transactions = [t for t in transactions if t.type == transaction_type.upper()]

    if sender_name:
        needle = sender_name.lower()
        transactions = [t for t in transactions if needle in (t.sender_name or "").lower()]

    return transactions


def _parse_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp, treating a missing zone as UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
