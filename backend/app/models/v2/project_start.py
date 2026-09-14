"""Contracts for the conversational project start (创建流程重构 R1).

「开始一条内容」不再让用户先填表、先选意图分类，而是：给一句话或选一条
已有素材 → AI 推断意图与下一步问题 → 创建项目。意图由模型推断，用户只需
在不对时一句话纠正。
"""

from typing import Literal

from pydantic import Field, model_validator

from app.models.v2.intent_actions import StrictModel

ContentIntentValue = Literal["solve", "share", "record"]


class ProjectStartRequest(StrictModel):
    """两种起点：给一句话，或指定一条收件箱素材。二者必居其一。"""

    raw_input: str | None = Field(default=None, min_length=1, max_length=2000)
    inbox_item_id: str | None = Field(default=None, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def exactly_one_source(self) -> "ProjectStartRequest":
        provided = [value for value in (self.raw_input, self.inbox_item_id) if value]
        if len(provided) != 1:
            raise ValueError("provide exactly one of raw_input or inbox_item_id")
        return self


class ProjectStartInference(StrictModel):
    """AI 的推断结果——呈现给用户，用户可一句话纠正。"""

    intent: ContentIntentValue | None
    intent_label: str
    #: 为什么这么判断（用户看得懂的一句话，不是内部术语）
    reason: str
    #: high | medium | low —— 低置信度时前端应弱化呈现，避免误导
    confidence: Literal["high", "medium", "low"]
    #: 只问一个：当前最缺、且答了会改变产出的那个信息
    next_question: str
    #: 推断来源：模型或降级（降级时 intent 为 None，交给后续确认步骤）
    source: Literal["ai", "deterministic_fallback"]


class ProjectStartView(StrictModel):
    project_id: str
    title: str
    inference: ProjectStartInference
    #: 从收件箱素材起步时，素材已挂到项目上（溯源链）
    material_id: str | None = None
