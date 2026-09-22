"""Smoke-test OmniClient with a local audio file. Prints only non-secret fields."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "/app")

from app.core.omni import OmniClient, OmniMediaRejectedException, OmniNotConfiguredException  # noqa: E402

audio_path = Path(sys.argv[1])
data = audio_path.read_bytes()
client = OmniClient()
print("is_configured", client.is_configured())
print("model", client.model)
print("audio_bytes", len(data))
try:
    result = client.describe_media(
        kind="audio",
        mime_type="audio/wav",
        data=data,
        instruction="请转写这段音频的说话内容，并用一句话概括主题。听不清的部分写「未能确认」。",
    )
except OmniNotConfiguredException as exc:
    print("NOT_CONFIGURED", exc)
    sys.exit(2)
except OmniMediaRejectedException as exc:
    print("REJECTED", exc)
    sys.exit(3)
except Exception as exc:  # noqa: BLE001
    print("ERROR", type(exc).__name__, exc)
    sys.exit(4)

text = result.get("text") or ""
print("text_len", len(text))
print("text_head", text[:200].replace("\n", " / "))
print("model_returned", result.get("model"))
print("usage", result.get("usage"))
print("SMOKE_OK")
