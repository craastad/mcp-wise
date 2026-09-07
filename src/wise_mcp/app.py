"""
FastMCP server initialization.
"""

import os
from fastmcp import FastMCP

def create_app():
    """Create and configure the MCP application."""
    return FastMCP("WiseMcp")

mcp = create_app()

from wise_mcp.resources import balances, profiles, recipients, statements, transfers, send_money