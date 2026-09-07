"""
Signing of Wise Strong Customer Authentication one-time tokens with a private RSA key.
"""

import base64
import os
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def sign_one_time_token(ott: str, private_key_path: str, passphrase: Optional[str] = None) -> str:
    """Sign a one-time token with RSA SHA-256 (PKCS#1 v1.5) and return the base64 signature."""
    key_bytes = Path(private_key_path).expanduser().read_bytes()
    private_key = serialization.load_pem_private_key(
        key_bytes, password=passphrase.encode() if passphrase else None
    )
    signature = private_key.sign(ott.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode()


def private_key_path_from_env() -> Optional[str]:
    """Return WISE_PRIVATE_KEY_PATH, or None when it is unset or blank."""
    return os.getenv("WISE_PRIVATE_KEY_PATH", "").strip() or None


def private_key_passphrase_from_env() -> Optional[str]:
    """Return WISE_PRIVATE_KEY_PASSPHRASE, or None when it is unset or blank."""
    return os.getenv("WISE_PRIVATE_KEY_PASSPHRASE", "") or None
