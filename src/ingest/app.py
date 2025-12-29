import base64
import json
from urllib.parse import unquote

from common.config import env, provider_secrets
from common.logger import log
from common.response import ok, err
from common.security import verify_hmac_signature
from common.idempotency import is_duplicate
from common.ratelimit import allow
from common.sqs import send

def _raw_body(event: dict) -> bytes:
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        return base64.b64decode(body)
    return body.encode("utf-8")

def _headers(event: dict) -> dict:
    h = event.get("headers") or {}
    return {k.lower(): v for k, v in h.items() if isinstance(k, str)}

def handler(event, context):
    provider = (event.get("pathParameters") or {}).get("provider", "").lower()
    provider = unquote(provider).strip()

    if not provider:
        return err("BAD_REQUEST", "Missing provider in path", 400)

    secrets = provider_secrets()
    secret = secrets.get(provider)
    if not secret:
        return err("UNKNOWN_PROVIDER", f"Provider '{provider}' is not configured", 400)

    headers = _headers(event)
    payload = _raw_body(event)

    # Signature header convention for this POC:
    # x-webhook-signature: <hex_hmac_sha256(payload)>
    provided_sig = (headers.get("x-webhook-signature") or "").strip().lower()
    if not verify_hmac_signature(secret, payload, provided_sig):
        log("WARN", "Invalid signature", provider=provider)
        return err("UNAUTHORIZED", "Invalid signature", 401)

    # Identify event id
    # Convention: x-event-id header (or derive from payload hash)
    event_id = (headers.get("x-event-id") or "").strip()
    if not event_id:
        # fallback: hash payload to reduce duplicates
        import hashlib
        event_id = hashlib.sha256(payload).hexdigest()

    # Rate limiting key (provider + optional tenant)
    tenant = (headers.get("x-tenant-id") or "public").strip()
    rl_key = f"{provider}:{tenant}"
    if not allow(rl_key, limit=30, window_seconds=60):
        log("WARN", "Rate limit exceeded", provider=provider, tenant=tenant)
        return err("RATE_LIMITED", "Too many requests", 429)

    # Idempotency
    pk = f"{provider}:{tenant}:{event_id}"
    if is_duplicate(pk, ttl_seconds=3600):
        log("INFO", "Duplicate event ignored", provider=provider, tenant=tenant, event_id=event_id)
        return ok({"status": "duplicate_ignored", "event_id": event_id}, status_code=200)

    # Normalize event
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except Exception:
        parsed = {"raw": payload.decode("utf-8", errors="replace")}

    message = {
        "provider": provider,
        "tenant": tenant,
        "event_id": event_id,
        "headers": {k: v for k, v in headers.items() if k.startswith("x-")},
        "payload": parsed,
    }

    queue_url = env("QUEUE_URL")
    send(queue_url, message)

    log("INFO", "Webhook accepted", provider=provider, tenant=tenant, event_id=event_id)
    return ok({"status": "accepted", "event_id": event_id}, status_code=202)
