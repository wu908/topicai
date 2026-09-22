"""从参考读出「你想做成什么样」（冷启动锚点 R7）。

这里守的规矩与 R4 是同一把尺子：结论的强度由**几条独立参考**支撑决定，
不由模型说得有多肯定；没有依据的结论宁可丢掉；以及——用户改过之后，
参考集再变化也不能覆盖他的判断。
"""

import json

import pytest

from app.core.exceptions import VersionConflictException
from app.models.v2.onboarding import HistoryImportCreate, ReferenceNoteInput
from app.models.v2.reference_anchor import ReferenceAnchorUpdate
from app.services.creator_profile_v2 import CreatorProfileV2Service
from app.services.history_import import HistoryImportService
from app.services.reference_anchor import ReferenceAnchorService

_REFERENCES = [
    {
        "title": "12 平的出租屋，我按动线重排了三次",
        "body_excerpt": "1. 先量尺寸 2. 拆掉一件家具 3. 按动线重排。结论先放前面。",
        "tags": ["租房", "收纳"],
        "source_handle": "@甲",
    },
    {
        "title": "租房第一年，我把预算降了两成",
        "body_excerpt": "1、记录每一笔 2、区分固定与浮动 3、每月复盘一次。",
        "tags": ["租房", "预算"],
        "source_handle": "@乙",
    },
    {
        "title": "搬了四次家之后，我只留这些东西",
        "body_excerpt": "1) 高频使用的 2) 有情感价值的，其余全部处理掉。",
        "tags": ["租房", "收纳"],
        "source_handle": "@丙",
    },
]


def _draft(topics, habits=(), audience=None) -> dict:
    return {
        "topics": [{"value": value, "evidence": evidence} for value, evidence in topics],
        "structure_habits": [
            {"value": value, "evidence": evidence} for value, evidence in habits
        ],
        "audience": (
            {"value": audience[0], "evidence": audience[1]} if audience else None
        ),
    }


class _StubLLM:
    model = "stub-anchor-v1"

    def __init__(self, payload=None, error=None):
        self._payload = payload
        self._error = error
        self.calls = 0

    def is_available(self, capability="text") -> bool:
        return True

    def generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return schema.model_validate(self._payload)


async def _insert_user(db) -> None:
    await db.insert(
        "users",
        {
            "id": "u1",
            "email": "u1@test.com",
            "username": "u1",
            "password_hash": "hash",
            "ai_calls_today": 0,
            "ai_calls_reset_at": "",
            "created_at": "2026-07-31T00:00:00Z",
        },
    )


async def _add_references(db, items=None, key: str = "refs-1") -> None:
    await HistoryImportService(db).import_items(
        "u1",
        HistoryImportCreate.model_validate(
            {
                "method": "manual",
                "items": items if items is not None else _REFERENCES,
                "idempotency_key": key,
            }
        ),
        origin="reference",
        item_model=ReferenceNoteInput,
    )


def _service(db, payload=None, error=None) -> tuple[ReferenceAnchorService, _StubLLM]:
    llm = _StubLLM(payload=payload, error=error)
    return ReferenceAnchorService(db, llm=llm), llm


@pytest.mark.asyncio
async def test_confidence_follows_the_number_of_supporting_references(test_db):
    """一条参考的结论是观察，两条是候选规律，三条才敢说稳定——与 R4 同一把尺子。"""
    await _insert_user(test_db)
    await _add_references(test_db)
    service, _ = _service(
        test_db,
        payload=_draft(
            topics=[("小户型收纳改造", [1]), ("低预算生活", [1, 2]), ("搬家取舍", [1, 2, 3])],
            habits=[("开头先给结论", [1, 2, 3])],
        ),
    )

    anchor = await service.get("u1")

    by_value = {item.value: item for item in anchor.topics}
    assert by_value["小户型收纳改造"].sample_count == 1
    assert by_value["小户型收纳改造"].confidence == "low"
    assert by_value["小户型收纳改造"].limitations  # 一条参考得出的结论要自己说清楚
    assert by_value["低预算生活"].confidence == "medium"
    assert by_value["搬家取舍"].confidence == "high"
    assert by_value["低预算生活"].evidence_refs  # 每条结论都指得出证据


@pytest.mark.asyncio
async def test_a_conclusion_without_valid_evidence_is_dropped(test_db):
    """模型编的编号对不上参考时，那条结论整个丢掉——不说没有依据的话。"""
    await _insert_user(test_db)
    await _add_references(test_db)
    service, _ = _service(
        test_db,
        payload=_draft(
            topics=[("有据可查的结论", [1, 2]), ("编出来的结论", [99])],
            habits=[("开头先给结论", [1])],
        ),
    )

    anchor = await service.get("u1")

    assert [item.value for item in anchor.topics] == ["有据可查的结论"]
    assert any("对不上你的参考" in line for line in anchor.limitations)


@pytest.mark.asyncio
async def test_without_a_model_it_only_says_what_it_can_count(test_db):
    """模型不可用：只数标签，读者留空——不猜。"""
    await _insert_user(test_db)
    await _add_references(test_db)
    service, _ = _service(test_db, error=RuntimeError("model is down"))

    anchor = await service.get("u1")

    assert anchor.capability == "deterministic_fallback"
    # 「租房」出现在 3 条里，「收纳」2 条，「预算」1 条。
    by_value = {item.value: item for item in anchor.topics}
    assert by_value["租房"].sample_count == 3
    assert by_value["收纳"].sample_count == 2
    assert by_value["预算"].confidence == "low"
    assert anchor.audience is None
    assert any("读者" in line for line in anchor.limitations)
    # 只看得出篇幅与清单这类表面特征，且必须说明这一点。
    assert anchor.structure_habits
    assert any("没有理解语义" in line for item in anchor.structure_habits for line in item.limitations)


# 回归：F25（用户验收测试 2026-09-19）。
# 真实前端 parseReferences 给每一条参考都写 tags: []（它不猜标签），
# 而 _REFERENCES 这个夹具三条都带标签——于是「模型不可用 + 参考没有标签」
# 这条真实路径从来没有被测过。实测它会在降级里构造出 topics=[] 的
# _AnchorDraft，触发 pydantic min_length 校验，异常一路冒到 HTTP 层，
# 用户看到一段英文 pydantic 原文。降级路径本身必须是合法的。
_UNTAGGED_REFERENCES = [
    {
        "title": "12 平的出租屋，我按动线重排了三次",
        "body_excerpt": "1. 先量尺寸 2. 拆掉一件家具 3. 按动线重排。结论先放前面。",
        "tags": [],
        "source_handle": "@甲",
    },
    {
        "title": "租房第一年，我把预算降了两成",
        "body_excerpt": "1、记录每一笔 2、区分固定与浮动 3、每月复盘一次。",
        "tags": [],
        "source_handle": "@乙",
    },
]


@pytest.mark.asyncio
async def test_without_a_model_and_without_tags_the_fallback_still_returns_a_valid_anchor(
    test_db,
):
    """F25：参考没有标签时，降级也必须产出合法读数，而不是抛校验异常。"""
    await _insert_user(test_db)
    await _add_references(test_db, items=_UNTAGGED_REFERENCES, key="refs-untagged")
    service, _ = _service(test_db, error=RuntimeError("model is down"))

    anchor = await service.get("u1")

    assert anchor.capability == "deterministic_fallback"
    # 没有标签时，仍然能从「参考本身」读出可数的东西：条数。
    assert len(anchor.topics) >= 1
    assert all(item.evidence_refs for item in anchor.topics)
    assert anchor.audience is None


@pytest.mark.asyncio
async def test_the_fallback_never_leaks_a_validation_error_to_the_caller(test_db):
    """F25：降级路径不得把 pydantic 原文当成用户可见错误抛出去。"""
    await _insert_user(test_db)
    await _add_references(test_db, items=_UNTAGGED_REFERENCES, key="refs-untagged-2")
    service, _ = _service(test_db, error=RuntimeError("model is down"))

    # 只要不抛异常即为通过；上面的用例断言了内容合法性。
    anchor = await service.get("u1")
    assert anchor.reference_count == 2


@pytest.mark.asyncio
async def test_the_anchor_is_not_recomputed_until_the_references_change(test_db):
    """参考集没变就不重推：不重复调用模型，读数是稳定的。"""
    await _insert_user(test_db)
    await _add_references(test_db)
    service, llm = _service(test_db, payload=_draft(topics=[("小户型收纳改造", [1, 2])]))

    first = await service.get("u1")
    second = await service.get("u1")

    assert llm.calls == 1
    assert second.version == first.version
    assert [item.value for item in second.topics] == ["小户型收纳改造"]

    await _add_references(
        test_db,
        items=[{**_REFERENCES[0], "title": "又一条参考", "external_key": "ref-4"}],
        key="refs-2",
    )
    third = await service.get("u1")

    assert llm.calls == 2
    assert third.version == first.version + 1
    assert third.reference_count == 4


@pytest.mark.asyncio
async def test_the_users_own_word_wins_permanently(test_db):
    """用户改过之后，新增参考也不覆盖他的判断。"""
    await _insert_user(test_db)
    await _add_references(test_db)
    service, llm = _service(test_db, payload=_draft(topics=[("系统读出来的", [1, 2])]))
    derived = await service.get("u1")

    edited = await service.update(
        "u1",
        ReferenceAnchorUpdate(
            topics=["我自己定的方向"],
            structure_habits=["我想要的开头方式"],
            audience="我想写给刚毕业的自己",
            rejected=["系统读出来的"],
            expected_version=derived.version,
        ),
    )
    assert edited.capability == "user_edited"
    assert [item.value for item in edited.topics] == ["我自己定的方向"]
    # 用户自己写的结论不能挂参考证据——那会让"有依据"变成假话。
    assert edited.topics[0].evidence_refs == []

    await _add_references(
        test_db,
        items=[{**_REFERENCES[1], "title": "再加一条", "external_key": "ref-5"}],
        key="refs-3",
    )
    after = await service.get("u1")

    assert llm.calls == 1  # 用户改过之后不再调用模型
    assert [item.value for item in after.topics] == ["我自己定的方向"]
    assert after.audience is not None and after.audience.value == "我想写给刚毕业的自己"


@pytest.mark.asyncio
async def test_a_rejected_conclusion_does_not_come_back(test_db):
    """否证一条不等于冻死锚点：立刻消失，且重推时不再出现，但记录保留。"""
    await _insert_user(test_db)
    await _add_references(test_db)
    service, llm = _service(
        test_db, payload=_draft(topics=[("我说不对的方向", [1, 2]), ("留着的那条", [1, 2])])
    )
    derived = await service.get("u1")

    edited = await service.update(
        "u1",
        ReferenceAnchorUpdate(rejected=["我说不对的方向"], expected_version=derived.version),
    )

    assert [item.value for item in edited.topics] == ["留着的那条"]
    # 只否证没有重写，所以锚点还是活的——参考集变化仍会重推。
    assert edited.capability == "structured_llm"

    await _add_references(
        test_db,
        items=[{**_REFERENCES[2], "title": "第三条", "external_key": "ref-6"}],
        key="refs-4",
    )
    refreshed = await service.get("u1")

    assert llm.calls == 2  # 确实重推了
    assert "我说不对的方向" in refreshed.rejected
    assert "我说不对的方向" not in [item.value for item in refreshed.topics]
    assert "留着的那条" in [item.value for item in refreshed.topics]


@pytest.mark.asyncio
async def test_no_references_is_an_empty_reading_not_an_error(test_db):
    await _insert_user(test_db)
    service, llm = _service(test_db, payload=_draft(topics=[("不该出现", [1])]))

    anchor = await service.get("u1")

    assert anchor.reference_count == 0
    assert anchor.topics == [] and anchor.structure_habits == []
    assert anchor.audience is None
    assert llm.calls == 0


@pytest.mark.asyncio
async def test_the_anchor_never_writes_into_the_creator_profile(test_db):
    """R7b 新引入的风险：锚点自己也不许把"你想成为谁"写进"你是谁"。"""
    await _insert_user(test_db)
    await _add_references(test_db)
    service, _ = _service(
        test_db,
        payload=_draft(
            topics=[("小户型收纳改造", [1, 2, 3])],
            habits=[("开头先给结论", [1, 2, 3])],
            audience=("正在租房的年轻人", [1, 2, 3]),
        ),
    )

    anchor = await service.get("u1")
    profile = await CreatorProfileV2Service(test_db).get_or_build("u1")

    assert anchor.audience is not None
    assert profile["attributes"]["target_audience"]["value"] == ""
    assert profile["attributes"]["niche"]["value"] == ""
    assert profile["attributes"]["content_pillars"] == []


@pytest.mark.asyncio
async def test_the_trace_says_what_the_reference_content_may_be_used_for(test_db):
    await _insert_user(test_db)
    await _add_references(test_db)
    service, _ = _service(test_db, payload=_draft(topics=[("小户型收纳改造", [1, 2])]))

    await service.get("u1")

    row = await test_db.fetch_one(
        "SELECT * FROM ai_traces_v2 WHERE task_type='reference_anchor'"
    )
    boundary = json.loads(row["visibility_boundary_json"])
    assert boundary["actual"] == ["owner_supplied_reference_content"]
    assert "verbatim_reuse" in boundary["forbidden"]
    assert row["capability"] == "structured_llm"
    assert row["outcome"] == "success"


@pytest.mark.asyncio
async def test_updating_with_a_stale_version_conflicts(test_db):
    await _insert_user(test_db)
    await _add_references(test_db)
    service, _ = _service(test_db, payload=_draft(topics=[("小户型收纳改造", [1, 2])]))
    derived = await service.get("u1")

    with pytest.raises(VersionConflictException):
        await service.update(
            "u1",
            ReferenceAnchorUpdate(topics=["改一下"], expected_version=derived.version + 5),
        )
