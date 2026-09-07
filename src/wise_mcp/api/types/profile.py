"""
Type definitions for Wise Profiles.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class WiseProfile:
    profile_id: str


@dataclass
class WiseProfileSummary:
    """A profile as shown to the client: its id, type, display name and whether it is the default."""
    profile_id: str
    type: str
    name: str
    is_default: bool = False

    @classmethod
    def from_api(cls, data: Dict[str, Any], default_profile_id: str | None = None) -> "WiseProfileSummary":
        """Build a summary from a raw profile object; the name is businessName or fullName, else first+last."""
        profile_id = str(data.get("id", ""))
        return cls(
            profile_id=profile_id,
            type=str(data.get("type", "")).upper(),
            name=profile_display_name(data),
            is_default=default_profile_id is not None and profile_id == str(default_profile_id),
        )


def profile_display_name(data: Dict[str, Any]) -> str:
    """Return the businessName or fullName of a raw profile, falling back to first + last name."""
    name = data.get("businessName") or data.get("fullName")
    if name:
        return str(name)
    parts = [data.get("firstName"), data.get("lastName")]
    return " ".join(str(p) for p in parts if p)
