"""Delete the last OMNI e2e temp account via privacy gate. Reads .omni-e2e-last.json."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://1.13.251.252:8081/api/v2"
state = json.loads(Path(r"G:\codex_project\topicAI\mvp\scripts\.omni-e2e-last.json").read_text())
token = state["access_token"]
suffix = state["idempotency_suffix"]


def req(method: str, path: str, body: dict | None = None):
    data = None
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read()
            code = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        code = exc.code
    if not raw:
        return code, None
    try:
        return code, json.loads(raw)
    except json.JSONDecodeError:
        return code, {"_raw_bytes": len(raw)}


code, gate = req("POST", "/account/deletion:request", body={"idempotency_key": f"del-{suffix}"})
print("deletion_request", code)
if code not in (200, 201):
    print(gate)
    raise SystemExit(1)
gate_id = gate["data"]["id"]
code, decided = req(
    "POST",
    f"/human-gates/{gate_id}:decide",
    body={
        "decision": "confirm",
        "decision_payload": {},
        "expected_gate_version": gate["data"]["version"],
        "idempotency_key": f"dec-{suffix}",
    },
)
print("gate_decide", code)
print("decided_body", decided)
code, deleted = req("DELETE", f"/account?gate_id={gate_id}")
print("account_delete", code)
print("deleted_body", deleted)
Path(r"G:\codex_project\topicAI\mvp\scripts\.omni-e2e-last.json").unlink(missing_ok=True)
print("STATE_CLEANED")


