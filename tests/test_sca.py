"""Tests for answering Strong Customer Authentication challenges."""

import base64

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from tests.conftest import make_response
from wise_mcp.api.sca import sign_one_time_token
from wise_mcp.api.wise_client import WiseSCARequiredError

CHALLENGE_HEADERS = {"x-2fa-approval-result": "REJECTED", "x-2fa-approval": "ott-123"}


@pytest.fixture
def rsa_key(tmp_path):
    """Write an unencrypted RSA private key to disk and return (path, public key)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path = tmp_path / "private.pem"
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return path, key.public_key()


def _verify(public_key, signature_b64: str, ott: str) -> None:
    public_key.verify(base64.b64decode(signature_b64), ott.encode(), padding.PKCS1v15(), hashes.SHA256())


def test_sign_one_time_token_produces_verifiable_signature(rsa_key):
    path, public_key = rsa_key

    _verify(public_key, sign_one_time_token("ott-123", str(path)), "ott-123")


def test_sign_one_time_token_with_passphrase(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path = tmp_path / "enc.pem"
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(b"secret"),
        )
    )

    _verify(key.public_key(), sign_one_time_token("ott-1", str(path), passphrase="secret"), "ott-1")


def test_challenge_is_retried_with_signed_token(client, mock_request, monkeypatch, rsa_key):
    path, public_key = rsa_key
    monkeypatch.setenv("WISE_PRIVATE_KEY_PATH", str(path))
    mock_request.side_effect = [
        make_response(403, headers=CHALLENGE_HEADERS),
        make_response(200, content=b"%PDF"),
    ]

    data = client.download_balance_statement("42", "7", "EUR", "a", "b")

    assert data == b"%PDF"
    assert mock_request.call_count == 2
    first, second = mock_request.call_args_list
    assert first.args[:2] == second.args[:2]
    assert first.kwargs["params"] == second.kwargs["params"]
    headers = second.kwargs["headers"]
    assert headers["x-2fa-approval"] == "ott-123"
    assert headers["Authorization"] == "Bearer test-token"
    _verify(public_key, headers["X-Signature"], "ott-123")


def test_challenge_without_key_raises_setup_instructions(client, mock_request, monkeypatch):
    monkeypatch.delenv("WISE_PRIVATE_KEY_PATH", raising=False)
    mock_request.return_value = make_response(403, headers=CHALLENGE_HEADERS)

    with pytest.raises(WiseSCARequiredError, match="WISE_PRIVATE_KEY_PATH") as excinfo:
        client._get("/v1/example")

    assert excinfo.value.one_time_token == "ott-123"
    assert mock_request.call_count == 1


def test_plain_403_is_not_treated_as_challenge(client, mock_request, monkeypatch):
    monkeypatch.delenv("WISE_PRIVATE_KEY_PATH", raising=False)
    mock_request.return_value = make_response(403, {"errors": [{"code": "FORBIDDEN", "message": "no"}]})

    with pytest.raises(Exception, match="FORBIDDEN"):
        client._get("/v1/example")
