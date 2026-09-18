"""契约：给可填字段的 AI 候选（R9）。

用户的原话：所有需要填的内容都应该先由 AI 给出候选选项、由 AI 推荐，推荐不对
也要支持自定义。所以候选不是"选项墙"——点一下填进输入框，文字仍然可以任意改；
AI 不可用时也必须给出候选（基于项目自身数据或通用方向），不留空白。
"""

from typing import Any, Literal

from pydantic import Field

from app.models.v2.intent_actions import StrictModel

#: 需要候选的字段。命名与发布判断契约里的字段名一致，避免又一套叫法。
SuggestionField = Literal[
    "answer",
    "audience_change",
    "audience_problem",
    "reader_promise",
    "viewpoint_anchor",
    "continuation_promise",
]


class FieldSuggestionRequest(StrictModel):
    field: SuggestionField
    #: 正在回答的那个问题（answer 字段用它来对准问题，其他字段可空）
    question: str | None = Field(default=None, max_length=1000)
    #: 用户已经写下的内容：给了就按它改进，而不是另起一句
    current_text: str | None = Field(default=None, max_length=2000)
    count: int = Field(default=3, ge=1, le=5)


class FieldSuggestionCandidate(StrictModel):
    text: str
    #: 为什么推荐这一条（一句话，给用户判断用）
    why: str = ""


class FieldSuggestionsView(StrictModel):
    field: SuggestionField
    candidates: list[FieldSuggestionCandidate]
    source: Literal["ai", "deterministic_fallback"]
    #: 降级原因等；前端据此说明"这些是通用方向"
    limitations: list[str] = Field(default_factory=list)
    context_refs: list[str] = Field(default_factory=list)


class _CandidateDraft(StrictModel):
    text: str
    why: str = ""


class _SuggestionDraft(StrictModel):
    """模型必须返回的结构（字段名会随骨架一起发进系统提示）。"""

    candidates: list[_CandidateDraft]


class _SuggestionPayload(StrictModel):
    """内部使用：字段规格。"""

    meaning: str
    hint: str
    max_length: int
    context: dict[str, Any] = Field(default_factory=dict)
