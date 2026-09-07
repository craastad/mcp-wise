"""
Type definitions for Wise Balances.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class WiseBalance:
    id: str
    currency: str
    amount: float
    reserved_amount: float = 0.0
    name: Optional[str] = None
