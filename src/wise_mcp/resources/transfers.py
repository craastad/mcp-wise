"""
Wise API transfer resources for the FastMCP server.
"""

from wise_mcp.app import mcp
from wise_mcp.api.types import WiseTransfer
from wise_mcp.api.wise_client import WiseApiClient


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
