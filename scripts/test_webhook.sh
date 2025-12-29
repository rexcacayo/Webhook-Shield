BODY='{"type":"invoice.paid","id":"evt_fail_2","fail":true}'
SECRET='dev_stripe_secret'
EVENT_ID="evt_fail_2"
TENANT="acme"

SIG=$(BODY="$BODY" SECRET="$SECRET" python - <<'PY'
import hmac, hashlib, os
body = os.environ["BODY"].encode("utf-8")
secret = os.environ["SECRET"].encode("utf-8")
print(hmac.new(secret, body, hashlib.sha256).hexdigest())
PY
)

curl -s -X POST "$API_URL/webhooks/stripe" \
  -H "content-type: application/json" \
  -H "x-webhook-signature: $SIG" \
  -H "x-event-id: $EVENT_ID" \
  -H "x-tenant-id: $TENANT" \
  -d "$BODY" | jq .
