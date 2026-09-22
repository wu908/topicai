"""Seed a temp production account with audio/video materials for visual pass.

Creates:
- audio A: unanalyzed (shows 识别内容 + external-model helper)
- audio B: analyzed (shows 重新识别 + provenance note)
- video V: unanalyzed
Saves state to scripts/.omni-visual-state.json for shots + cleanup.
"""
from __future__ import annotations

import base64
import json
import secrets
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://1.13.251.252:8081/api/v2"
AUDIO = Path(r"G:\codex_project\topicAI\mvp\scripts\omni-test-audio.wav")
STATE = Path(r"G:\codex_project\topicAI\mvp\scripts\.omni-visual-state.json")


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
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw or b"null")
        except json.JSONDecodeError:
            return exc.code, {"_raw": raw[:200].decode("utf-8", "replace")}


def main() -> int:
    suffix = secrets.token_hex(4)
    email = f"omni-vis-{suffix}@example.com"
    username = f"omnivis{suffix}"
    password = f"Omni-Vis-Pw-{suffix}"
    code, reg = req("POST", "/auth/register", body={"email": email, "username": username, "password": password})
    print("register", code)
    if code != 201:
        print(reg)
        return 1
    token = reg["data"]["access_token"]
    user_id = reg["data"]["user"]["id"]

    audio_b64 = base64.b64encode(AUDIO.read_bytes()).decode("ascii")

    # tiny silent-ish wav still works as a "video" is harder; use the same wav as video? No.
    # Create a minimal mp4 via empty bytes won't work. Use a tiny real-ish mp4 header.
    # For visual pass of the video *entry* (button/helper), a tiny valid-enough mp4 is enough
    # if analyze is NOT run on it — we only need the unanalyzed video row UI.
    mp4 = bytes.fromhex(
        "00000018667479706d703432000000006d7034326d703431"
        "0000000866726565"
    ) + b"\x00" * 256

    created = {}
    code, a1 = req(
        "POST",
        "/materials",
        token=token,
        body={
            "kind": "audio",
            "title": "口播草稿：阳台香草养护",
            "content_base64": audio_b64,
            "mime_type": "audio/wav",
            "privacy_level": "private",
            "idempotency_key": f"vis-a1-{suffix}",
        },
    )
    print("audio_unanalyzed", code)
    created["audio_unanalyzed"] = a1["data"]["id"] if code == 201 else None

    code, a2 = req(
        "POST",
        "/materials",
        token=token,
        body={
            "kind": "audio",
            "title": "访谈片段：读者怎么找养护方法",
            "content_base64": audio_b64,
            "mime_type": "audio/wav",
            "privacy_level": "private",
            "idempotency_key": f"vis-a2-{suffix}",
        },
    )
    print("audio_for_analyze", code)
    a2_id = a2["data"]["id"] if code == 201 else None
    created["audio_analyzed"] = a2_id
    if a2_id:
        code, analyzed = req("POST", f"/materials/{a2_id}:analyze", token=token)
        print("analyze", code, "model", (analyzed or {}).get("data", {}).get("analysis", {}).get("model"))
        if code != 200:
            print(analyzed)

    code, v1 = req(
        "POST",
        "/materials",
        token=token,
        body={
            "kind": "video",
            "title": "过程片段：换盆延时",
            "content_base64": base64.b64encode(mp4).decode("ascii"),
            "mime_type": "video/mp4",
            "privacy_level": "private",
            "idempotency_key": f"vis-v1-{suffix}",
        },
    )
    print("video_unanalyzed", code)
    created["video_unanalyzed"] = v1["data"]["id"] if code == 201 else None
    if code != 201:
        print(v1)

    STATE.write_text(
        json.dumps(
            {
                "user_id": user_id,
                "email": email,
                "username": username,
                "password": password,
                "access_token": token,
                "idempotency_suffix": suffix,
                "materials": created,
            }
        )
    )
    print("STATE", json.dumps(created))
    print("SEED_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
