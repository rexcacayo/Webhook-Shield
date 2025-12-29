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

def is_duplicate(event_pk: str, ttl_seconds: int = 3600) -> bool:
    """
    Returns True if the event was already seen.
    Uses conditional put: if pk exists -> duplicate.
    """
    table = _ddb().Table(env("IDEMPOTENCY_TABLE"))
    now = int(time.time())
    ttl = now + ttl_seconds

    try:
        table.put_item(
            Item={"pk": event_pk, "created_at": now, "ttl": ttl},
            ConditionExpression="attribute_not_exists(pk)",
        )
        return False
    except Exception:
        # ConditionalCheckFailedException ends here too (botocore generic in localstack sometimes)
        return True
