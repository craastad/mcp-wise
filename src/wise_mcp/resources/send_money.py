"""
Wise API send money resource for the FastMCP server.
"""

import uuid
from typing import Dict, Any, Optional

from wise_mcp.app import mcp
from wise_mcp.api.wise_client_helper import init_wise_client
from wise_mcp.resources.transfers import describe_fund_result


@mcp.tool()
def send_money(
    profile_type: str,
    source_currency: str,
    source_amount: float,
    recipient_id: str,
    payment_reference: Optional[str] = None,
    source_of_funds: Optional[str] = None,
    profile_id: Optional[str] = None,
) -> str:
    """
    Send money to a recipient using the Wise API.

    Args:
        profile_type: The type of profile to use (personal or business)
        profile_id: Optional. The ID of the profile to use; wins over profile_type. WISE_PROFILE_ID sets the default
        source_currency: Source currency code (e.g., 'USD')
        source_amount: Amount in source currency to send
        recipient_id: The ID of the recipient to send money to
        payment_reference: Optional. Reference message for the transfer (defaults to "money")
        source_of_funds: Optional. Source of the funds (e.g., "salary", "savings")

    Returns:
        String message with transfer status or SCA challenge details

    Raises:
        Exception: If any API request fails during the process
    """

    ctx = init_wise_client(profile_type, profile_id)
    
    customer_transaction_id = str(uuid.uuid4())
    
    reference = payment_reference or "money"
    
    # 1. Create a quote
    quote = ctx.wise_api_client.create_quote(
        profile_id=ctx.profile.profile_id,
        source_currency=source_currency,
        target_currency=source_currency,
        source_amount=source_amount,
        recipient_id=recipient_id
    )
    
    # 2. Create a transfer
    transfer_params = {
        "recipient_id": recipient_id,
        "quote_uuid": quote["id"],
        "reference": reference,
        "customer_transaction_id": customer_transaction_id
    }
    
    # Add source of funds if provided
    if source_of_funds:
        transfer_params["source_of_funds"] = source_of_funds
    
    transfer = ctx.wise_api_client.create_transfer(**transfer_params)
    transfer_id = transfer["id"]
    
    # 3. Fund the transfer (may trigger SCA)
    fund_result = ctx.wise_api_client.fund_transfer(
        profile_id=ctx.profile.profile_id,
        transfer_id=transfer_id,
        type="BALANCE"
    )

    return describe_fund_result(transfer_id, fund_result)
