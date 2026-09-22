"""Full OMNI product E2E: register → material → analyze → print ids → pause for DB check.

Does NOT auto-delete; call omni_e2e_cleanup.py after DB verification.
"""
from __future__ import annotations

import base64
import json
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://1.13.251.252:8081/api/v2"
AUDIO = Path(sys.argv[1] if len(sys.argv) > 1 else r"G:\codex_project\topicAI\mvp\scripts\omni-test-audio.wav")
STATE_PATH = Path(r"G:\codex_project\topicAI\mvp\scripts\.omni-e2e-last.json")


def req(method: str, path: str, *, token: str | None = None, body: dict | None = None):
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=180) as resp:
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


def main() -> int:
    suffix = secrets.token_hex(4)
    email = f"omni-e2e-{suffix}@example.com"
    username = f"omniae2e{suffix}"
    password = f"Omni-E2e-Pw-{suffix}"
    print("REGISTERING", email)

    code, reg = req("POST", "/auth/register", body={"email": email, "username": username, "password": password})
    print("register", code)
    if code != 201:
        print(reg)
        return 1
    token = reg["data"]["access_token"]
    user_id = reg["data"]["user"]["id"]

    audio_b64 = base64.b64encode(AUDIO.read_bytes()).decode("ascii")
    code, created = req(
        "POST",
        "/materials",
        token=token,
        body={
            "kind": "audio",
            "title": "OMNI 端到端测试音频",
            "content_base64": audio_b64,
            "mime_type": "audio/wav",
            "privacy_level": "private",
            "idempotency_key": f"omni-e2e-{suffix}",
        },
    )
    print("create_material", code)
    if code != 201:
        print(created)
        return 1
    material_id = created["data"]["id"]
    print("material_id", material_id)

    code, analyzed = req("POST", f"/materials/{material_id}:analyze", token=token)
    print("analyze", code)
    if code != 200:
        print(analyzed)
        return 1
    view = analyzed["data"]
    content = (view.get("content") or "").strip()
    analysis = view.get("analysis")
    print("content_len", len(content))
    print("content_head", content[:180].replace("\n", " / "))
    print("analysis", json.dumps(analysis, ensure_ascii=False) if analysis else None)
    ok = bool(content) and analysis and analysis.get("source") == "omni"
    print("MATERIAL_ID", material_id)
    print("USER_ID", user_id)
    print("E2E_OK" if ok else "E2E_FAIL")
    STATE_PATH.write_text(
        json.dumps(
            {
                "user_id": user_id,
                "material_id": material_id,
                "email": email,
                "username": username,
                "password": password,
                "access_token": token,
                "idempotency_suffix": suffix,
            }
        )
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
