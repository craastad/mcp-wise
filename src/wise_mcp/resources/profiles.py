"""
Wise API profile resources for the FastMCP server.
"""

from typing import List

from wise_mcp.app import mcp
from wise_mcp.api.types import WiseProfileSummary
from wise_mcp.api.wise_client import WiseApiClient
from wise_mcp.api.wise_client_helper import default_profile_id


@mcp.tool()
def list_profiles() -> List[WiseProfileSummary]:
    """
    Returns every profile the API token can see (personal and business), with id, type and name.
    The one WISE_PROFILE_ID points to is marked is_default; pass profile_id to other tools to
    use a different one.

    Returns:
        List of profiles with profile_id, type, name and is_default

    Raises:
        Exception: If the API request fails
    """

    default_id = default_profile_id()

    return [WiseProfileSummary.from_api(p, default_id) for p in WiseApiClient().list_profiles()]
