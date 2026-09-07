"""
Helper functions for working with the Wise API client.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .wise_client import WiseApiClient
from .types import WiseProfile
from .types.profile import profile_display_name


@dataclass
class WiseClientContext:
    """
    Context class that contains the Wise API client and the matched profile.
    """
    wise_api_client: WiseApiClient
    profile: WiseProfile


def default_profile_id() -> Optional[str]:
    """Return the profile id pinned by WISE_PROFILE_ID, or None when it is unset or blank."""
    value = os.getenv("WISE_PROFILE_ID", "").strip()
    return value or None


def init_wise_client(profile_type: str = "personal", profile_id: Optional[str] = None) -> WiseClientContext:
    """
    Build a client bound to one profile: the explicit profile_id, else WISE_PROFILE_ID,
    else the first profile whose type matches profile_type (case-insensitive).
    """
    api_client = WiseApiClient()

    resolved_id = (profile_id or "").strip() or default_profile_id()
    if resolved_id:
        return WiseClientContext(api_client, WiseProfile(profile_id=str(resolved_id)))

    profiles = api_client.list_profiles()

    if not profiles:
        raise Exception("No profiles found. Please create a profile in Wise first.")

    matching_profile = find_profile_by_type(profiles, profile_type)

    if not matching_profile:
        raise Exception(
            f"No profile found with type '{profile_type}'. Available profiles: "
            f"{describe_profiles(profiles)}. Pass profile_id or set WISE_PROFILE_ID to pick one."
        )

    return WiseClientContext(api_client, WiseProfile(profile_id=str(matching_profile["id"])))


def find_profile_by_type(profiles: List[Dict[str, Any]], profile_type: str) -> Optional[Dict[str, Any]]:
    """Return the first raw profile whose type equals profile_type, ignoring case."""
    wanted = (profile_type or "").strip().lower()
    for profile in profiles:
        if str(profile.get("type", "")).lower() == wanted:
            return profile
    return None


def describe_profiles(profiles: List[Dict[str, Any]]) -> str:
    """Render raw profiles as 'id (TYPE, name)' entries for error messages."""
    return ", ".join(
        f"{p.get('id')} ({str(p.get('type', 'unknown')).upper()}, {profile_display_name(p) or 'unnamed'})"
        for p in profiles
    )
