import json
import boto3
from botocore.config import Config as BotoConfig
from common.config import aws_endpoint_url, env
from common.logger import log
from common.response import ok, err

def _sqs():
    return boto3.client(
        "sqs",
        endpoint_url=aws_endpoint_url(),
        config=BotoConfig(retries={"max_attempts": 3, "mode": "standard"}),
    )

def handler(event, context):
    provider = (event.get("pathParameters") or {}).get("provider", "any").lower()

    dlq_url = env("DLQ_URL")
    main_url = env("MAIN_QUEUE_URL")

    sqs = _sqs()
    moved = 0
    max_to_move = 25

    # Pull a batch from DLQ and push to main
    resp = sqs.receive_message(
        QueueUrl=dlq_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=0,
    )
    msgs = resp.get("Messages", [])
    if not msgs:
        return ok({"status": "nothing_to_replay", "moved": 0})

    for m in msgs[:max_to_move]:
        body = m["Body"]
        # Optional filter by provider
        try:
            parsed = json.loads(body)
            if provider != "any" and parsed.get("provider") != provider:
                continue
        except Exception:
            pass

        sqs.send_message(QueueUrl=main_url, MessageBody=body)
        sqs.delete_message(QueueUrl=dlq_url, ReceiptHandle=m["ReceiptHandle"])
        moved += 1

    log("INFO", "Replay completed", provider=provider, moved=moved)
    return ok({"status": "replayed", "provider": provider, "moved": moved})
