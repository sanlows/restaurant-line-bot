import base64
import hashlib
import hmac

from services.line_service import is_valid_signature


def test_is_valid_signature_accepts_matching_signature():
    secret = "channel-secret"
    body = b'{"events":[]}'
    signature = base64.b64encode(
        hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    ).decode("utf-8")

    assert is_valid_signature(secret, body, signature)


def test_is_valid_signature_strips_accidental_whitespace():
    secret = "channel-secret"
    body = b'{"events":[]}'
    signature = base64.b64encode(
        hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    ).decode("utf-8")

    assert is_valid_signature(f" {secret}\n", body, f" {signature}\n")
