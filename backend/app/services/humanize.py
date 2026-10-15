"""人话化 post-process（P2-B1 / P2-F3）。

默认开、可关、失败静默回退原文——绝不因改写丢事实或卡住主流程。
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.llm import LLMClient
from app.prompts.humanize import HUMANIZE_SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class HumanizeService:
    """把 AI 腔草稿改得更像人话；只改说法，不改事实。"""

    def __init__(self, llm: LLMClient | None = None, enabled: bool | None = None):
        self._llm = llm
        # None / True → 默认开；显式 False 才关
        self.enabled = True if enabled is None else bool(enabled)

    def rewrite(self, text: str) -> str:
        """改写一段正文。空文/关掉/无模型/出错 → 原样返回。"""
        if not self.enabled:
            return text
        if not text or not text.strip():
            return text

        llm = self._llm or LLMClient()
        if not getattr(llm, "is_available", lambda _c="text": True)("text"):
            return text

        try:
            out = llm.generate(
                build_user_prompt(text),
                system_prompt=HUMANIZE_SYSTEM_PROMPT,
                temperature=0.5,
                max_tokens=2000,
            )
        except Exception:  # noqa: BLE001 — 改写失败绝不影响主流程
            logger.warning("humanize rewrite failed; keeping original", exc_info=True)
            return text

        result = (out or "").strip()
        if not result:
            return text
        return result


def humanize_enabled_from_prefs(product_prefs: Any) -> bool:
    """从 product_prefs 读开关；缺省 True（默认开）。"""
    if product_prefs is None:
        return True
    if isinstance(product_prefs, dict):
        val = product_prefs.get("humanize_enabled")
    else:
        val = getattr(product_prefs, "humanize_enabled", None)
    return True if val is None else bool(val)
