import json
import boto3
from botocore.config import Config as BotoConfig
from .config import aws_endpoint_url

def _sqs():
    return boto3.client(
        "sqs",
        endpoint_url=aws_endpoint_url(),
        config=BotoConfig(retries={"max_attempts": 3, "mode": "standard"}),
    )

def send(queue_url: str, message: dict, group_id: str | None = None):
    body = json.dumps(message)
    params = {"QueueUrl": queue_url, "MessageBody": body}
    # (FIFO not used in this POC; kept for future)
    if group_id:
        params["MessageGroupId"] = group_id
    return _sqs().send_message(**params)
