"""Seed a temp account with 2 projects, then shoot /content at 1280/390."""
from __future__ import annotations

import json
import secrets
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://1.13.251.252:8081/api/v2"
STATE = Path(r"G:\codex_project\topicAI\mvp\scripts\.content-visual-state.json")


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
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw or b"null")
        except json.JSONDecodeError:
            return exc.code, {"_raw": raw[:120].decode("utf-8", "replace")}


def main() -> int:
    suffix = secrets.token_hex(4)
    email = f"content-vis-{suffix}@example.com"
    username = f"cvis{suffix}"
    password = f"Content-Vis-Pw-{suffix}"
    code, reg = req("POST", "/auth/register", body={"email": email, "username": username, "password": password})
    print("register", code)
    if code != 201:
        print(reg)
        return 1
    token = reg["data"]["access_token"]
    user_id = reg["data"]["user"]["id"]

    projects = []
    for i, raw in enumerate(
        [
            "番茄钟别在下班后补，改到第二天早上更容易坚持",
            "阳台辣椒终于结果了，记录第一次收成",
        ]
    ):
        code, started = req(
            "POST",
            "/projects/start",
            token=token,
            body={"raw_input": raw, "idempotency_key": f"vis-start-{suffix}-{i}"},
        )
        print("start", code, (started or {}).get("data", {}).get("project_id"))
        if code < 300:
            projects.append(started["data"]["project_id"])

    STATE.write_text(
        json.dumps(
            {
                "user_id": user_id,
                "email": email,
                "username": username,
                "password": password,
                "access_token": token,
                "idempotency_suffix": suffix,
                "projects": projects,
            }
        )
    )
    print("SEED_OK", projects)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
