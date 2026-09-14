"""从参考样本读出「你想做成什么样」（冷启动锚点 R7）。

用户说不出自己是谁，但能指出"我想做成这样"。这个服务把那些参考读成三件事：
**选题范围**（这个内容空间在讲什么）、**结构习惯**（这类内容通常怎么写）、
**读者**（谁在看这类内容），每条结论都带证据与样本数。

边界（与 R4 同一把尺子）：
- 结论的置信度取决于**几条独立参考**支撑它，不取决于模型说得有多肯定。1 条是观察，
  2 条是候选规律，3 条才当稳定结论——与 creator_state 的洞察分级共用阈值。
- 模型引用的参考编号一律校验，越界的丢弃；一条结论若没有任何有效证据，整条丢弃。
  宁可少说，不说没有依据的话。
- 参考是别人的作品：只提取方向与写法，**不复制原文**，也不把别人的数据当你的基线
  （见 trace 的 visibility_boundary）。
- 读不出读者就不写读者，并把这件事说清楚，而不是猜一个填上去。
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Literal

from pydantic import Field

from app.core.exceptions import VersionConflictException
from app.models.v2.action_domain import AITraceCreate
from app.models.v2.intent_actions import StrictModel
from app.models.v2.reference_anchor import AnchorItem, ReferenceAnchorUpdate, ReferenceAnchorView
from app.services.ai_trace import AITraceService
from app.services.creator_state import CreatorStateService
from app.services.v2_utils import now

logger = logging.getLogger(__name__)

#: 与 R4 的洞察分级共用同一组阈值：样本数是信号强度的代理指标。
_EVIDENCE_FOR_CROSS_CONTENT = CreatorStateService.EVIDENCE_FOR_CROSS_CONTENT
_EVIDENCE_FOR_SETTLED = CreatorStateService.EVIDENCE_FOR_SETTLED

#: 参考条数上限：读 2–3 条就够看出方向，读 20 条只会让结论更泛。
_MAX_REFERENCES = 12
#: 正文片段截断长度——够读开头与结构，不必把别人的全文塞进提示词。
_EXCERPT_CHARS = 600

_NOT_ENOUGH_EVIDENCE = "这条由 1 条参考得出，只是观察，不代表规律"
_FALLBACK_STRUCTURE_LIMITATION = "写法是从文本表面特征读出来的（篇幅、有没有清单），没有理解语义"
_FALLBACK_NO_AUDIENCE = "从参考里看不出读者是谁——这条需要你自己定"
_NO_VERBATIM = "参考是别人的作品：只提取方向与写法，不复制原文，也不用别人的数据当你的基线"


class _DraftItem(StrictModel):
    """模型必须给出证据编号：没有依据的结论会被丢掉。"""

    value: str = Field(min_length=1, max_length=120)
    #: 参考编号，从 1 开始（与提示词里给的编号一致）。
    evidence: list[int] = Field(min_length=1, max_length=_MAX_REFERENCES)


class _AnchorDraft(StrictModel):
    #: 选题必须有：一条都读不出来的话，这次读数就算失败（宁可退回数标签）。
    topics: list[_DraftItem] = Field(min_length=1, max_length=5)
    #: 写法可以没有：全是散文、没有明显结构的参考是常见的，这不是模型的错。
    #: 空着时由 _surface_habits 用文本表面特征补，而不是让整份读数作废。
    structure_habits: list[_DraftItem] = Field(default_factory=list, max_length=4)
    audience: _DraftItem | None = None


_ANCHOR_SYSTEM_PROMPT = (
    "你是内容创作助手的参考解读模块。用户会给你几条**别人**的内容（他想做成那样），"
    "你要读出这个内容空间的三件事，并且每一条都必须指出它来自哪几条参考。\n"
    "1. topics：这个空间在讲什么（选题范围）。用中文短语，2–5 条，彼此不重叠。\n"
    "2. structure_habits：这类内容通常怎么写（开头怎么起、篇幅、有没有清单、怎么收尾）。"
    "1–4 条，只描述从文本里看得出来的写法。\n"
    "3. audience：谁在看这类内容。看不出来就输出 null——不要猜。\n"
    "规则：\n"
    "- evidence 里填参考编号（数组），只能填给你的编号，不要编。\n"
    "- 不要复制参考里的原句，不要引用它们的点赞数。\n"
    "- 看不出结论参考的是哪条，就不要写这条结论。\n"
    "只输出一个 JSON 对象，不要解释、不要 Markdown 代码块。字段严格如下：\n"
    '{"topics":[{"value":"小户型收纳改造","evidence":[1,2]}],'
    '"structure_habits":[{"value":"开头先给结论再讲过程","evidence":[1,3]}],'
    '"audience":{"value":"正在租房、预算有限的年轻人","evidence":[1,2]}}'
)


def _confidence_for(sample_count: int) -> Literal["low", "medium", "high"]:
    """样本数决定置信度——不是模型的口气决定。"""
    if sample_count >= _EVIDENCE_FOR_SETTLED:
        return "high"
    if sample_count >= _EVIDENCE_FOR_CROSS_CONTENT:
        return "medium"
    return "low"


class ReferenceAnchorService:
    def __init__(self, db: Any, llm: Any = None):
        self.db = db
        self.llm = llm

    # ==================== 读 ====================

    async def get(self, owner: str) -> ReferenceAnchorView:
        """返回锚点；参考集变了（或还没有）就重读一次。

        用户改过（capability='user_edited'）就不再自动覆盖——参考样本可以影响
        "你想成为谁"，但用户说什么就是什么。
        """
        stored = await self.db.fetch_one(
            "SELECT * FROM reference_anchors WHERE owner_user_id=:owner", {"owner": owner}
        )
        if stored and stored["capability"] == "user_edited":
            return self._view(stored)
        references = await self._references(owner)
        if stored and stored["reference_note_count"] == len(references):
            return self._view(stored)
        return await self._derive(owner, references, stored)

    async def _references(self, owner: str) -> list[dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM imported_notes WHERE owner_user_id=:owner AND origin='reference' "
            "ORDER BY rowid LIMIT :limit",
            {"owner": owner, "limit": _MAX_REFERENCES},
        )
        return [dict(row) for row in rows]

    def _view(self, row: dict[str, Any]) -> ReferenceAnchorView:
        audience = json.loads(row["audience_json"]) if row.get("audience_json") else None
        return ReferenceAnchorView(
            reference_count=row["reference_note_count"],
            source_handles=json.loads(row["source_handles_json"]),
            topics=[AnchorItem.model_validate(item) for item in json.loads(row["topics_json"])],
            structure_habits=[
                AnchorItem.model_validate(item)
                for item in json.loads(row["structure_habits_json"])
            ],
            audience=AnchorItem.model_validate(audience) if audience else None,
            rejected=json.loads(row["rejected_json"]),
            capability=row["capability"],
            limitations=json.loads(row["limitations_json"]),
            version=row["version"],
            updated_at=row["updated_at"],
        )

    # ==================== 推断 ====================

    async def _derive(
        self, owner: str, references: list[dict[str, Any]], stored: dict[str, Any] | None
    ) -> ReferenceAnchorView:
        rejected = json.loads(stored["rejected_json"]) if stored else []
        handles = sorted(
            {row["source_handle"] for row in references if row.get("source_handle")}
        )
        if not references:
            # 还没有参考样本：写一条空的，不猜任何东西（reference_count=0 就是
            # "还没贴参考"，不需要额外说明）。
            topics: list[AnchorItem] = []
            habits: list[AnchorItem] = []
            audience: AnchorItem | None = None
            capability = "deterministic_fallback"
            limitations = []
            trace_refs: list[str] = []
        else:
            draft, capability, limitations, trace_refs = await self._read_references(references)
            topics = self._items(draft.topics, references, rejected)
            habits = self._items(draft.structure_habits, references, rejected)
            audience = self._one(draft.audience, references, rejected)
            if not habits:
                # 模型没给出写法时，退回只看文本表面特征；只看得出什么说什么。
                habits, habit_limitations = self._surface_habits(references)
                limitations = [*limitations, *habit_limitations]
        limitations = [*limitations, _NO_VERBATIM]

        trace_id = None
        if references:
            trace_id = await self._trace(
                owner, references, trace_refs, capability, limitations
            )
        timestamp = now()
        fields = {
            "topics_json": json.dumps(
                [item.model_dump(mode="json") for item in topics], ensure_ascii=False
            ),
            "structure_habits_json": json.dumps(
                [item.model_dump(mode="json") for item in habits], ensure_ascii=False
            ),
            "audience_json": (
                json.dumps(audience.model_dump(mode="json"), ensure_ascii=False)
                if audience
                else None
            ),
            "source_handles_json": json.dumps(handles, ensure_ascii=False),
            "reference_note_count": len(references),
            "capability": capability,
            "limitations_json": json.dumps(limitations, ensure_ascii=False),
            "ai_trace_id": trace_id,
            "updated_at": timestamp,
        }
        if stored:
            fields["version"] = stored["version"] + 1
            await self.db.update(
                "reference_anchors", fields, {"owner_user_id": owner}
            )
        else:
            await self.db.insert(
                "reference_anchors",
                {
                    "id": str(uuid.uuid4()),
                    "owner_user_id": owner,
                    "rejected_json": json.dumps(rejected, ensure_ascii=False),
                    "version": 1,
                    "created_at": timestamp,
                    **fields,
                },
            )
        return self._view(
            await self.db.fetch_one(
                "SELECT * FROM reference_anchors WHERE owner_user_id=:owner",
                {"owner": owner},
            )
        )

    async def _read_references(
        self, references: list[dict[str, Any]]
    ) -> tuple[_AnchorDraft, str, list[str], list[str]]:
        """读参考：模型可用就用模型，不可用则退回确定性读法。"""
        from app.core.llm import LLMClient, wrap_user_input

        llm = self.llm or LLMClient()
        listing = "\n\n".join(
            f"[{index}] 来源：{row.get('source_handle') or '未标注'}\n"
            f"标题：{row['title']}\n"
            f"正文片段：{(row.get('body_excerpt') or '')[: _EXCERPT_CHARS]}"
            for index, row in enumerate(references, start=1)
        )
        try:
            if self.llm is None and not llm.is_available("text"):
                raise RuntimeError("text capability is not available")
            draft = await asyncio.to_thread(
                llm.generate_structured,
                f"用户贴的参考内容：\n{wrap_user_input(listing)}",
                _AnchorDraft,
                _ANCHOR_SYSTEM_PROMPT,
                temperature=0.3,
            )
            limitations: list[str] = []
            used = sorted(
                {
                    index
                    for item in [*draft.topics, *draft.structure_habits]
                    + ([draft.audience] if draft.audience else [])
                    for index in item.evidence
                    if 1 <= index <= len(references)
                }
            )
            dropped = _count_invalid_indices(draft, len(references))
            if dropped:
                limitations.append(
                    f"模型给出的 {dropped} 处依据对不上你的参考，已丢弃——只保留有据可查的结论"
                )
            return draft, "structured_llm", limitations, [
                _reference_ref(references[index - 1]) for index in used
            ]
        except Exception:
            logger.warning("Reference anchor read failed; falling back", exc_info=True)
            draft, limitation = self._read_deterministically(references)
            return draft, "deterministic_fallback", limitation, [
                _reference_ref(row) for row in references
            ]

    @staticmethod
    def _read_deterministically(
        references: list[dict[str, Any]],
    ) -> tuple[_AnchorDraft, list[str]]:
        """没有模型时的读法：只数得出来的东西。

        标签词频就是"可数的选题信号"，这是画像推断已经用过的机制（creator_profile_v2），
        在这里复用而不是另发明一套。读者读不出来，所以留空——不猜。
        """
        counts: dict[str, list[int]] = {}
        for index, row in enumerate(references, start=1):
            for tag in dict.fromkeys(json.loads(row.get("tags_json") or "[]")):
                counts.setdefault(str(tag), []).append(index)
        ranked = sorted(counts.items(), key=lambda item: (-len(item[1]), item[0]))[:5]
        return (
            _AnchorDraft(
                topics=[_DraftItem(value=tag, evidence=indices) for tag, indices in ranked],
                structure_habits=[],
                audience=None,
            ),
            [
                "模型不可用，当前只用了可数的信号（参考里的标签），没有读懂内容本身",
                _FALLBACK_NO_AUDIENCE,
            ],
        )

    @staticmethod
    def _surface_habits(
        references: list[dict[str, Any]],
    ) -> tuple[list[AnchorItem], list[str]]:
        """结构习惯的兜底读法：只看篇幅与有没有清单。

        只断言文本表面显示出来的事，并把"这没读懂语义"写进局限里。
        """
        excerpts = [(row.get("body_excerpt") or "") for row in references]
        refs = [_reference_ref(row) for row in references]
        medians = sorted(len(text) for text in excerpts)[len(excerpts) // 2]
        habits: list[AnchorItem] = []
        if medians and medians <= 120:
            habits.append(
                AnchorItem(
                    value="篇幅偏短、段落碎",
                    evidence_refs=refs,
                    sample_count=len(refs),
                    confidence=_confidence_for(len(refs)),
                    limitations=[_FALLBACK_STRUCTURE_LIMITATION],
                )
            )
        elif medians >= 300:
            habits.append(
                AnchorItem(
                    value="篇幅较长、信息密度高",
                    evidence_refs=refs,
                    sample_count=len(refs),
                    confidence=_confidence_for(len(refs)),
                    limitations=[_FALLBACK_STRUCTURE_LIMITATION],
                )
            )
        listed = [
            _reference_ref(row)
            for row in references
            if any(mark in (row.get("body_excerpt") or "") for mark in ("1.", "1、", "①", "- "))
        ]
        if len(listed) * 2 >= len(references):
            habits.append(
                AnchorItem(
                    value="常用清单或分点来组织内容",
                    evidence_refs=listed,
                    sample_count=len(listed),
                    confidence=_confidence_for(len(listed)),
                    limitations=[_FALLBACK_STRUCTURE_LIMITATION],
                )
            )
        return habits, [_FALLBACK_STRUCTURE_LIMITATION] if habits else []

    # ==================== 落盘 ====================

    async def update(
        self, owner: str, body: ReferenceAnchorUpdate
    ) -> ReferenceAnchorView:
        """改锚点：只否证 vs 自己重写，两种意图后果不同（见契约注释）。"""
        stored = await self.db.fetch_one(
            "SELECT * FROM reference_anchors WHERE owner_user_id=:owner", {"owner": owner}
        )
        if stored is None:
            raise ValueError("reference anchor not found")
        if stored["version"] != body.expected_version:
            raise VersionConflictException(stored["version"], body.expected_version)

        rejected = sorted(set(json.loads(stored["rejected_json"])) | set(body.rejected))
        current = self._view(stored)
        rewrote = any(
            value is not None
            for value in (body.topics, body.structure_habits, body.audience)
        )
        if rewrote:
            # 以用户说的为准：此后再不自动重推。
            references = await self._references(owner)
            refs = [_reference_ref(row) for row in references]
            topics = [self._user_item(value, refs) for value in body.topics or []]
            habits = [
                self._user_item(value, refs) for value in body.structure_habits or []
            ]
            audience = self._user_item(body.audience, refs) if body.audience else None
            capability = "user_edited"
        else:
            # 只否证：把这几条从当前读数里去掉，但继续让参考说话。
            topics = [item for item in current.topics if item.value not in rejected]
            habits = [
                item for item in current.structure_habits if item.value not in rejected
            ]
            audience = (
                current.audience
                if current.audience and current.audience.value not in rejected
                else None
            )
            capability = stored["capability"]

        timestamp = now()
        await self.db.update(
            "reference_anchors",
            {
                "topics_json": json.dumps(
                    [item.model_dump(mode="json") for item in topics], ensure_ascii=False
                ),
                "structure_habits_json": json.dumps(
                    [item.model_dump(mode="json") for item in habits], ensure_ascii=False
                ),
                "audience_json": (
                    json.dumps(audience.model_dump(mode="json"), ensure_ascii=False)
                    if audience
                    else None
                ),
                "rejected_json": json.dumps(rejected, ensure_ascii=False),
                "capability": capability,
                "version": stored["version"] + 1,
                "updated_at": timestamp,
            },
            {"owner_user_id": owner},
        )
        return self._view(
            await self.db.fetch_one(
                "SELECT * FROM reference_anchors WHERE owner_user_id=:owner", {"owner": owner}
            )
        )

    @staticmethod
    def _user_item(value: str, refs: list[str]) -> AnchorItem:
        """用户自己写的结论：不挂证据、标为用户来源。

        给它挂参考 id 会让"这条结论有依据"变成假话——依据是用户，不是参考。
        """
        return AnchorItem(
            value=value,
            evidence_refs=[],
            sample_count=0,
            confidence="high",
            limitations=["这是你自己定的，不是从参考里读出来的"],
        )

    # ==================== 辅助 ====================

    def _items(
        self,
        draft: list[_DraftItem],
        references: list[dict[str, Any]],
        rejected: list[str],
    ) -> list[AnchorItem]:
        items: list[AnchorItem] = []
        for entry in draft:
            value = entry.value.strip()
            if not value or value in rejected:
                continue
            refs = [
                _reference_ref(references[index - 1])
                for index in dict.fromkeys(entry.evidence)
                if 1 <= index <= len(references)
            ]
            if not refs:
                # 没有有效证据的结论直接丢弃：宁可少说，不说没依据的话。
                continue
            items.append(
                AnchorItem(
                    value=value,
                    evidence_refs=refs,
                    sample_count=len(refs),
                    confidence=_confidence_for(len(refs)),
                    limitations=[_NOT_ENOUGH_EVIDENCE] if len(refs) < 2 else [],
                )
            )
        return items

    def _one(
        self,
        draft: _DraftItem | None,
        references: list[dict[str, Any]],
        rejected: list[str],
    ) -> AnchorItem | None:
        if draft is None:
            return None
        items = self._items([draft], references, rejected)
        return items[0] if items else None

    async def _trace(
        self,
        owner: str,
        references: list[dict[str, Any]],
        used_refs: list[str],
        capability: str,
        limitations: list[str],
    ) -> str:
        trace_id = str(uuid.uuid4())
        timestamp = now()
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await AITraceService.create(
                    session,
                    owner,
                    AITraceCreate(
                        id=trace_id,
                        task_type="reference_anchor",
                        input_refs=[_reference_ref(row) for row in references],
                        evidence_refs=used_refs,
                        policy_version="reference-anchor-v1",
                        capability=capability,
                        visibility_boundary={
                            "allowed": ["owner_supplied_reference_content"],
                            # 别人的作品：可以读方向，不可以搬原文，也不拿它的数据
                            # 当用户的基线。
                            "forbidden": [
                                "verbatim_reuse",
                                "reference_metrics",
                                "other_users",
                            ],
                            "actual": ["owner_supplied_reference_content"],
                        },
                        contamination_check={"status": "clean", "unexpected_classes": []},
                        calibration_state="insufficient",
                        limitations=limitations,
                        output_ref=f"reference-anchor:{owner}",
                        generated_at=timestamp,
                        confidence_label="low",
                        outcome=(
                            "success" if capability == "structured_llm" else "fallback"
                        ),
                    ),
                )
        return trace_id


def _reference_ref(row: dict[str, Any]) -> str:
    return f"reference_note:{row['id']}"


def _count_invalid_indices(draft: _AnchorDraft, size: int) -> int:
    entries: list[_DraftItem] = [*draft.topics, *draft.structure_habits]
    if draft.audience:
        entries.append(draft.audience)
    return sum(
        1 for item in entries for index in item.evidence if not 1 <= index <= size
    )
