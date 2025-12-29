import json

def ok(body: dict, status_code: int = 200):
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }

def err(code: str, message: str, status_code: int = 400):
    return ok({"error": {"code": code, "message": message}}, status_code=status_code)
