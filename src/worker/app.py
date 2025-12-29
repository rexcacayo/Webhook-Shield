import json
from common.logger import log

def handler(event, context):
    # SQS batch
    records = event.get("Records", [])
    for r in records:
        body = r.get("body", "{}")
        msg = json.loads(body)

        provider = msg.get("provider")
        event_id = msg.get("event_id")
        tenant = msg.get("tenant")

        # Simula downstream: si payload contiene {"fail": true} forzamos error
        payload = msg.get("payload", {})
        if isinstance(payload, dict) and payload.get("fail") is True:
            log("ERROR", "Downstream failure simulated", provider=provider, tenant=tenant, event_id=event_id)
            raise RuntimeError("Simulated downstream failure")

        log("INFO", "Processed webhook", provider=provider, tenant=tenant, event_id=event_id)
    return {"ok": True, "processed": len(records)}
