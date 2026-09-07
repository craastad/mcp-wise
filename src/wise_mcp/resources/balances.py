"""
Wise API balance resources for the FastMCP server.
"""

from typing import List, Optional

from wise_mcp.app import mcp
from wise_mcp.api.types import WiseBalance
from wise_mcp.api.wise_client_helper import init_wise_client


@mcp.tool()
def get_balances(
    profile_type: str = "personal", currency: Optional[str] = None, profile_id: Optional[str] = None
) -> List[WiseBalance]:
    """
    Returns the balances held by the first profile of the given type, one entry per currency.
    Use this to check that a balance covers a payment before sending money.

    Args:
        profile_type: The type of profile to list balances for. One of [personal, business]
        profile_id: Optional. The ID of the profile to use; wins over profile_type. WISE_PROFILE_ID sets the default
        currency: Optional. Only return the balance for this currency code (e.g., 'EUR')

    Returns:
        List of balances with id, currency, available amount and reserved amount

    Raises:
        Exception: If the API request fails or no matching profile exists.
    """

    ctx = init_wise_client(profile_type, profile_id)

    return ctx.wise_api_client.list_balances(ctx.profile.profile_id, currency)
