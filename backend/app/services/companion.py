"""Companion companion-ask service: real-model answers for the floating ball.

UX 审计 2026-09-13 (P0-A1): the companion dialog used to reply with a canned
demo string while the sidebar claimed "AI 正常". This service wires the ask
path to the provider-neutral LLM client with product-persona constraints.
"""

from typing import Any

from app.core.llm import LLMClient, wrap_user_input


class CompanionService:
    def __init__(self, db: Any = None, llm: LLMClient | None = None):
        self._db = db
        self._llm = llm

    async def answer(self, context: str, question: str) -> str:
        """Answer one companion question.

        The system prompt carries the product persona and honesty rules; the
        user question is wrapped as untrusted input (prompt-injection guard,
        same as the other AI services). Synchronous generate() matches the
        existing service pattern.
        """
        llm = self._llm or LLMClient()
        system_prompt = (
            "你是 TopicAI 的创作伙伴。TopicAI 是一个小红书内容操作系统："
            "异步循环（收件箱素材 → 消化 → 产出架拾取 → 发布 → 复盘）"
            "加养成系信任机制（AI 只提议，决定权在用户）。\n"
            f"当前界面上下文：{context}\n"
            "规则：\n"
            "1. 只提议；拾取、发布、公开范围等决策永远属于用户。\n"
            "2. 不编造用户的事实、数据和经历；缺少信息时先问一个最关键的问题。\n"
            "3. 回答不超过 160 字，直接、具体、不套话。"
        )
        return llm.generate(
            wrap_user_input(question),
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=400,
        )
