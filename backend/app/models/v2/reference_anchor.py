"""「你想做成什么样」的契约（冷启动锚点 R7）。

与 CreatorProfileResult 形状上有意相似（每条结论都带证据、样本数、置信度、局限），
但语义不同：画像说的是"你是谁"（由你自己的作品推断），锚点说的是"你想成为谁"
（由你贴的参考推断）。两者的结论不互相写入。
"""

from typing import Literal

from pydantic import Field

from app.models.v2.intent_actions import StrictModel

#: 结论由几条参考支撑——不是"结论有多可信"，而是"有几条独立观察"（R4 同一把尺子：
#: 1 条是观察，2 条是候选规律，3 条才当稳定结论）。
AnchorConfidence = Literal["low", "medium", "high"]


class AnchorItem(StrictModel):
    """一条关于"你想做成什么样"的结论，连同它的证据。"""

    value: str = Field(min_length=1, max_length=200)
    #: 支撑这条结论的参考样本（imported_notes.id）。
    evidence_refs: list[str] = Field(default_factory=list)
    sample_count: int = Field(ge=0)
    confidence: AnchorConfidence
    limitations: list[str] = Field(default_factory=list)


class ReferenceAnchorView(StrictModel):
    """锚点的完整读数。

    reference_count == 0 时其余字段为空列表——"还没贴参考"是正常状态，不是错误。
    """

    reference_count: int = Field(ge=0)
    source_handles: list[str] = Field(default_factory=list)
    topics: list[AnchorItem] = Field(default_factory=list)
    structure_habits: list[AnchorItem] = Field(default_factory=list)
    audience: AnchorItem | None = None
    #: 用户否证过的结论。被否证的不再出现，但记录保留——否则用户会看到同一个
    #: 错误结论反复出现，每次都得再否一次。
    rejected: list[str] = Field(default_factory=list)
    capability: Literal["structured_llm", "deterministic_fallback", "user_edited"] = (
        "deterministic_fallback"
    )
    limitations: list[str] = Field(default_factory=list)
    version: int = Field(ge=1)
    updated_at: str


class ReferenceAnchorUpdate(StrictModel):
    """改锚点。两种意图刻意分开，因为它们的后果不同：

    - **只否证**（只填 rejected）：这条结论不再出现，但系统继续从参考里读——
      下次参考集变化时会重推，且被否证的结论不会再回来。
    - **自己重写**（填了 topics / structure_habits / audience 中的任一）：以你说的为准，
      此后参考集再怎么变化都不覆盖你的判断。

    混成一种会导致"只想否掉一条"顺手把整个锚点冻死，那用户就再也拿不到重读了。
    """

    #: 否证掉的结论。累计保留——否则用户每次重推都要再否一次。
    rejected: list[str] = Field(default_factory=list, max_length=20)
    #: 自己重写的内容。留空表示"只是否证了几条，继续让参考说话"。
    topics: list[str] | None = Field(default=None, max_length=5)
    structure_habits: list[str] | None = Field(default=None, max_length=5)
    audience: str | None = Field(default=None, max_length=200)
    expected_version: int = Field(ge=1)
