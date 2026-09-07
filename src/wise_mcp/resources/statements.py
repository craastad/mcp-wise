"""
Wise API balance statement resources for the FastMCP server.
"""

import calendar
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from fastmcp.exceptions import ToolError

from wise_mcp.app import mcp
from wise_mcp.api.types import WiseTransaction
from wise_mcp.api.wise_client_helper import init_wise_client

# Wise expects statement interval bounds in this exact UTC format.
WISE_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"
# Longest window Wise accepts for one statement.
MAX_STATEMENT_DAYS = 469


@mcp.tool()
def list_balance_transactions(
    currency: str,
    profile_type: str = "personal",
    days: int = 30,
    interval_start: Optional[str] = None,
    interval_end: Optional[str] = None,
    transaction_type: Optional[str] = None,
    sender_name: Optional[str] = None,
    profile_id: Optional[str] = None,
) -> List[WiseTransaction]:
    """
    Returns the transactions of a balance in a time window, newest first, for reconciling
    incoming payments (CREDIT) and outgoing transfers (DEBIT). Wise may require Strong Customer
    Authentication for statements on some accounts; the API error says so if it does.

    Args:
        currency: Currency code of the balance to read (e.g., 'EUR')
        profile_type: The type of profile that holds the balance. One of [personal, business]
        profile_id: Optional. The ID of the profile to use; wins over profile_type. WISE_PROFILE_ID sets the default
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

    ctx = init_wise_client(profile_type, profile_id)

    balances = ctx.wise_api_client.list_balances(ctx.profile.profile_id, currency)
    if not balances:
        raise ToolError(f"No {currency.upper()} balance found for profile {ctx.profile.profile_id}")

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


@mcp.tool()
def download_balance_statement(
    currency: str,
    output_path: str,
    month: Optional[str] = None,
    interval_start: Optional[str] = None,
    interval_end: Optional[str] = None,
    format: str = "pdf",
    statement_type: str = "COMPACT",
    profile_type: str = "personal",
    profile_id: Optional[str] = None,
) -> str:
    """
    Saves the statement of a balance as a PDF, CSV, XLSX or JSON file on the machine running this
    server, for bookkeeping. Give either a month or an explicit interval. Some accounts need Strong
    Customer Authentication for statements; the error explains how to set up signing if so.

    Args:
        currency: Currency code of the balance (e.g., 'USD')
        output_path: File path to write to; parent directories are created as needed
        month: Optional. Calendar month as 'YYYY-MM', covering its first to last day in UTC
        interval_start: Start of the window as 'YYYY-MM-DD' or an ISO 8601 timestamp; required without month
        interval_end: End of the window as 'YYYY-MM-DD' (inclusive) or an ISO 8601 timestamp; required without month
        format: File format, one of [pdf, csv, xlsx, json]. Default: "pdf"
        statement_type: 'COMPACT' (one line per transaction) or 'FLAT' (fees as separate lines). Default: "COMPACT"
        profile_type: The type of profile that holds the balance. One of [personal, business]
        profile_id: Optional. The ID of the profile to use; wins over profile_type. WISE_PROFILE_ID sets the default

    Returns:
        String message with the path written, file size, profile, balance and interval

    Raises:
        Exception: If the API request fails, no balance exists for the currency, or the window is invalid
    """

    try:
        start, end = resolve_statement_interval(month, interval_start, interval_end)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc

    ctx = init_wise_client(profile_type, profile_id)

    balances = ctx.wise_api_client.list_balances(ctx.profile.profile_id, currency)
    if not balances:
        raise ToolError(f"No {currency.upper()} balance found for profile {ctx.profile.profile_id}")

    try:
        data = ctx.wise_api_client.download_balance_statement(
            profile_id=ctx.profile.profile_id,
            balance_id=balances[0].id,
            currency=currency.upper(),
            interval_start=start,
            interval_end=end,
            fmt=format,
            statement_type=statement_type,
        )
    except ValueError as exc:
        raise ToolError(str(exc)) from exc

    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

    return (
        f"Statement written to {path} ({len(data)} bytes) for profile {ctx.profile.profile_id}, "
        f"balance {balances[0].id} ({currency.upper()}), {start} to {end}"
    )


def resolve_statement_interval(
    month: Optional[str], interval_start: Optional[str], interval_end: Optional[str]
) -> Tuple[str, str]:
    """
    Turn a month or a start/end pair into Wise-formatted interval bounds, rejecting windows
    longer than MAX_STATEMENT_DAYS.
    """
    if month:
        start, end = month_bounds(month)
    elif interval_start and interval_end:
        start = _parse_interval_bound(interval_start, end_of_day=False)
        end = _parse_interval_bound(interval_end, end_of_day=True)
    else:
        raise ValueError("Give either month (YYYY-MM) or both interval_start and interval_end")

    if end <= start:
        raise ValueError("interval_end must be after interval_start")
    if end - start > timedelta(days=MAX_STATEMENT_DAYS):
        raise ValueError(f"Statement window must not exceed {MAX_STATEMENT_DAYS} days")

    return format_interval_bound(start), format_interval_bound(end)


def month_bounds(month: str) -> Tuple[datetime, datetime]:
    """Return the first instant and the last millisecond of a 'YYYY-MM' month in UTC."""
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError(f"month must be formatted as YYYY-MM, got '{month}'")
    year, month_number = int(month[:4]), int(month[5:])
    if not 1 <= month_number <= 12:
        raise ValueError(f"month must be formatted as YYYY-MM, got '{month}'")
    last_day = calendar.monthrange(year, month_number)[1]
    start = datetime(year, month_number, 1, tzinfo=timezone.utc)
    end = datetime(year, month_number, last_day, 23, 59, 59, 999000, tzinfo=timezone.utc)
    return start, end


def format_interval_bound(value: datetime) -> str:
    """Format a UTC datetime the way Wise expects, keeping millisecond precision."""
    return value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{value.microsecond // 1000:03d}Z"


def _parse_interval_bound(value: str, end_of_day: bool) -> datetime:
    """Parse 'YYYY-MM-DD' as the start or last millisecond of that UTC day, or any ISO timestamp."""
    if len(value) == 10:
        try:
            day = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError as exc:
            raise ValueError(f"Dates must be formatted as YYYY-MM-DD, got '{value}'") from exc
        if end_of_day:
            return day.replace(hour=23, minute=59, second=59, microsecond=999000)
        return day
    try:
        return _parse_timestamp(value)
    except ValueError as exc:
        raise ValueError(f"Could not parse timestamp '{value}'") from exc

