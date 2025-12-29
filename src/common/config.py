import json
import os

def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)

def provider_secrets() -> dict[str, str]:
    raw = env("PROVIDER_SECRETS_JSON", "{}")
    try:
        return json.loads(raw)
    except Exception:
        return {}

def aws_endpoint_url() -> str | None:
    v = env("AWS_ENDPOINT_URL", "").strip()
    return v or None
