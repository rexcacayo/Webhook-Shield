import hmac
import hashlib

def hmac_sha256_hex(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

def verify_hmac_signature(secret: str, payload: bytes, provided_hex: str) -> bool:
    if not provided_hex:
        return False
    expected = hmac_sha256_hex(secret, payload)
    return hmac.compare_digest(expected, provided_hex)
