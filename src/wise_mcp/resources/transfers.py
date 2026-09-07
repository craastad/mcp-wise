"""
Wise API transfer resources for the FastMCP server.
"""

import uuid
from typing import Optional

from wise_mcp.app import mcp
from wise_mcp.api.types import WiseQuote, WiseTransfer
from wise_mcp.api.wise_client import WiseApiClient
from wise_mcp.api.wise_client_helper import init_wise_client


@mcp.tool()
def create_quote(
    source_currency: str,
    target_currency: str,
    source_amount: float,
    recipient_id: Optional[str] = None,
    profile_type: str = "personal",
) -> WiseQuote:
    """
    Creates a quote and returns the rate, fee and target amount for paying it from the balance.
    Creating a quote moves no money, so use it to preview a payment before send_money, or as
    the first step of the create_transfer / fund_transfer flow. Pass recipient_id to get the
    exact fee for that recipient's account type.

    Args:
        source_currency: Source currency code (e.g., 'EUR')
        target_currency: Target currency code (e.g., 'USD'); same as source for a same-currency transfer
        source_amount: Amount in source currency to send
        recipient_id: Optional. The ID of the recipient the quote is for
        profile_type: The type of profile to use. One of [personal, business]. Default: "personal"

    Returns:
        The quote with id, amounts, rate, fee, estimated delivery and expiry

    Raises:
        Exception: If the API request fails
    """

    ctx = init_wise_client(profile_type)

    quote = ctx.wise_api_client.create_quote(
        profile_id=ctx.profile.profile_id,
        source_currency=source_currency,
        target_currency=target_currency,
        source_amount=source_amount,
        recipient_id=recipient_id,
    )

    return WiseQuote.from_api(quote)


@mcp.tool()
def create_transfer(
    recipient_id: str,
    quote_id: str,
    payment_reference: str,
    source_of_funds: Optional[str] = None,
) -> WiseTransfer:
    """
    Creates a transfer from a quote. The transfer is not paid until fund_transfer is called,
    so this is the point to review the amounts and reference before any money moves.
    Prefer send_money when no review step is needed.

    Args:
        recipient_id: The ID of the recipient to send money to
        quote_id: The ID of a quote from create_quote for this recipient and amount
        payment_reference: Reference message shown to the recipient
        source_of_funds: Optional. Source of the funds (e.g., "salary", "savings")

    Returns:
        The created transfer, with status 'incoming_payment_waiting' until it is funded

    Raises:
        Exception: If the API request fails or the quote has expired
    """

    transfer = WiseApiClient().create_transfer(
        recipient_id=recipient_id,
        quote_uuid=quote_id,
        reference=payment_reference,
        customer_transaction_id=str(uuid.uuid4()),
        source_of_funds=source_of_funds,
    )

    return WiseTransfer.from_api(transfer)


@mcp.tool()
def get_transfer(transfer_id: str) -> WiseTransfer:
    """
    Returns the current status and amounts of a transfer. Use it to follow a payment after
    send_money: a SEPA transfer normally moves from 'processing' to 'outgoing_payment_sent'.
    Transfers are looked up by ID and do not depend on a profile.

    Args:
        transfer_id: The ID of the transfer, as returned by send_money

    Returns:
        The transfer with id, status, source/target amounts, rate, reference and recipient id

    Raises:
        Exception: If the API request fails or the transfer does not exist.
    """

    return WiseApiClient().get_transfer(transfer_id)
