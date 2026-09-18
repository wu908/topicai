"""全模态（音/视频 → 文本）客户端：小米 MiMo 开放平台。

为什么单独一个客户端而不是扩展现有的 LLMClient：

- 它的 base_url、模型 id、计费与限流都与主 LLM 独立（主 LLM 可能是别的厂商）；
- 请求体是**内容数组**（`input_audio` / `video_url`），不是纯文本 prompt；
- 官方限制更硬：base64 ≤50MB、不支持本地直传、`thinking` 是非标准参数（须走
  `extra_body`）、结构化输出只有 `json_object`（没有 json_schema）。

接口事实（2026-09 调研，来源见 docs/reviews）：
- OpenAI 兼容：`POST {base}/chat/completions`，`Authorization: Bearer <key>`；
- 模型 id 是 **mimo-v2.5**；旧名 `mimo-v2-omni` 已于 2026-06-30 下线，
  写 `mimo-v2.5-omni` 这类不存在的 id 会被拒；
- 音频：mp3/wav/flac/m4a/ogg；视频：mp4/mov/avi/wmv（抽帧理解，fps 0.1–10）。
"""

from __future__ import annotations

import base64
from typing import Any, cast

from openai import OpenAI

from config.settings import get_settings


class OmniNotConfiguredException(Exception):
    """没有配置全模态模型：调用方要把这句话直接给用户看。"""


class OmniMediaRejectedException(Exception):
    """素材本身不符合对方接口的要求（太大/格式不支持），文案面向用户。"""


_MIME_BY_SUFFIX = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "ogg": "audio/ogg",
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "avi": "video/x-msvideo",
    "wmv": "video/x-ms-wmv",
}


class OmniClient:
    """按模态构造请求并把模型返回的文本拿回来。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = self.settings.omni_model
        self.client = (
            OpenAI(
                api_key=self.settings.omni_api_key,
                base_url=self.settings.omni_base_url,
                timeout=self.settings.omni_timeout_seconds,
            )
            if self.is_configured()
            else None
        )

    def is_configured(self) -> bool:
        return bool(
            self.settings.omni_enabled
            and self.settings.omni_api_key
            and self.settings.omni_base_url
            and self.settings.omni_model
        )

    def max_media_bytes(self) -> int:
        return self.settings.omni_max_media_bytes

    def describe_media(
        self,
        *,
        kind: str,
        mime_type: str | None,
        data: bytes,
        instruction: str,
        fps: float = 2.0,
    ) -> dict[str, Any]:
        """让全模态模型读一段音/视频，返回它的文本结论与用量。

        只支持 base64 内联（官方 base64 ≤50MB）：官方**不接受本地直传**，
        走 URL 需要素材有一个公网地址——那是产品侧的存储决策，不在这里偷偷做。
        """
        if not self.is_configured() or self.client is None:
            raise OmniNotConfiguredException(
                "音视频识别还没有开通：需要在服务端配置 OMNI_API_KEY 并打开 OMNI_ENABLED。"
            )
        if kind not in {"audio", "video"}:
            raise OmniMediaRejectedException("只有音频或视频素材需要全模态识别。")
        if not data:
            raise OmniMediaRejectedException("这条素材没有内容，无法识别。")
        if len(data) > self.max_media_bytes():
            raise OmniMediaRejectedException(
                f"这条素材有 {len(data) / 1_000_000:.1f}MB，"
                f"超过识别上限 {self.max_media_bytes() / 1_000_000:.0f}MB；"
                "可以先裁剪一段再传。"
            )

        # 官方只支持固定几种容器：按白名单判定，不能"只要有斜杠就放过"——
        # 传一个对方不认的 mime 会得到含糊的远端错误，不如在这里说清楚。
        suffix = (mime_type or "").split("/")[-1].lower().split(";")[0]
        known_suffixes = _MIME_BY_SUFFIX if kind == "audio" else {
            key: value for key, value in _MIME_BY_SUFFIX.items() if value.startswith("video/")
        }
        if "/" in (mime_type or ""):
            expected_prefix = "audio/" if kind == "audio" else "video/"
            if not mime_type.startswith(expected_prefix) or suffix not in known_suffixes:
                raise OmniMediaRejectedException(
                    "认不出这个文件的格式；支持 mp3/wav/flac/m4a/ogg（音频）与 mp4/mov/avi/wmv（视频）。"
                )
            mime = mime_type
        else:
            mime = known_suffixes.get(suffix, "")
        if not mime:
            raise OmniMediaRejectedException(
                "认不出这个文件的格式；支持 mp3/wav/flac/m4a/ogg（音频）与 mp4/mov/avi/wmv（视频）。"
            )

        encoded = base64.b64encode(data).decode("ascii")
        data_uri = f"data:{mime};base64,{encoded}"
        if kind == "audio":
            media_part: dict[str, Any] = {
                "type": "input_audio",
                "input_audio": {"data": data_uri},
            }
        else:
            media_part = {
                "type": "video_url",
                "video_url": {"url": data_uri},
                "fps": max(0.1, min(10.0, fps)),
                "media_resolution": "default",
            }

        # 多模态 content 数组是官方文档的线格式；当前 SDK 的 TypedDict 只建模了
        # 文本消息，所以这里显式声明成 Any（mypy 而不是运行时的问题）。
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [media_part, {"type": "text", "text": instruction}],
            }
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=cast(Any, messages),
                max_completion_tokens=4096,
                # 非标准参数，必须走 extra_body；理解类任务关掉思考以降低延迟与成本。
                extra_body={"thinking": {"type": "disabled"}},
            )
        except Exception as exc:  # 网络/限流/参数错误统一成一句可读的话
            raise OmniMediaRejectedException(
                "全模态模型这次没有返回结果（可能是网络、限流或素材格式问题），稍后再试。"
            ) from exc

        choice = response.choices[0] if response.choices else None
        text = (choice.message.content if choice and choice.message else "") or ""
        usage = getattr(response, "usage", None)
        return {
            "text": text.strip(),
            "model": getattr(response, "model", self.model),
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
        }
