import time
import boto3
from botocore.config import Config as BotoConfig
from .config import aws_endpoint_url, env

def _ddb():
    return boto3.resource(
        "dynamodb",
        endpoint_url=aws_endpoint_url(),
        config=BotoConfig(retries={"max_attempts": 3, "mode": "standard"}),
    )

def allow(key: str, limit: int = 30, window_seconds: int = 60) -> bool:
    """
    Simple fixed-window counter per key (provider or provider+tenant).
    Increments counter; denies if > limit.
    TTL ensures reset after window.
    """
    table = _ddb().Table(env("RATELIMIT_TABLE"))
    now = int(time.time())
    window = now // window_seconds
    pk = f"{key}#{window}"
    ttl = (window + 1) * window_seconds + 5

    # Read current count
    resp = table.get_item(Key={"pk": pk})
    item = resp.get("Item")
    count = int(item.get("count", 0)) if item else 0

    if count >= limit:
        return False

    # Write back (best-effort; for POC it's OK)
    table.put_item(Item={"pk": pk, "count": count + 1, "ttl": ttl})
    return True
