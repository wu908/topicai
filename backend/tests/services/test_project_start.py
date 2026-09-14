"""「开始一条内容」的推断与建项目（创建流程重构 R1）。"""

import pytest

from app.models.v2.project_start import ProjectStartRequest
from app.services.project_start import ProjectStartService


class _StubLLM:
    model = "stub-intent-v1"

    def __init__(self, payload=None, error=None):
        self._payload = payload
        self._error = error
        self.calls = []

    def generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        if self._error is not None:
            raise self._error
        return schema.model_validate(self._payload)


def _payload(intent="share", question="这件事里哪一步最费劲？"):
    return {
        "intent": intent,
        "reason": "听起来是分享一段真实经历",
        "confidence": "medium",
        "next_question": question,
    }



async def _seed_user(db, user_id: str = "u1") -> None:
    """content_projects.owner_user_id 有外键约束，先建用户。"""
    await db.execute(
        "INSERT OR IGNORE INTO users (id,email,username,password_hash,ai_calls_today,"
        "ai_calls_reset_at,created_at) VALUES "
        "(:id,:email,:name,'hash',0,'','2026-06-03T00:00:00Z')",
        {"id": user_id, "email": f"{user_id}@test.com", "name": user_id},
    )

async def _seed_inbox(db, owner, suffix, content, *, consent="publishable", title=""):
    from app.models.v2.async_loop import InboxItemCreate
    from app.services.async_loop import InboxService

    item, _ = await InboxService(db).add(
        owner,
        InboxItemCreate(
            kind="text",
            title=title,
            content=content,
            consent=consent,
            idempotency_key=f"start-{suffix}",
        ),
    )
    return item


@pytest.mark.asyncio
async def test_start_from_one_sentence_infers_intent_without_asking(test_db):
    """一句话起步：AI 推断意图，用户不用先选分类，也不用先起标题。"""
    await _seed_user(test_db)
    llm = _StubLLM(payload=_payload("solve", "你试过哪一步？"))
    result = await ProjectStartService(test_db, llm=llm).start(
        "u1",
        ProjectStartRequest(
            raw_input="我修好了家里漏水的水管，想说说怎么判断漏点",
            idempotency_key="start-1",
        ),
    )

    assert llm.calls, "必须调用模型做推断"
    assert result.inference.intent == "solve"
    assert result.inference.intent_label == "解决"
    assert result.inference.source == "ai"
    assert result.inference.next_question == "你试过哪一步？"
    assert result.title, "标题由原料提炼，不让用户先起名"
    assert result.material_id is None


@pytest.mark.asyncio
async def test_start_from_inbox_item_attaches_material_for_provenance(test_db):
    """素材起步：素材挂到项目上，后续不必再向用户索要一遍。"""
    await _seed_user(test_db)
    item = await _seed_inbox(
        test_db, "u1", "inbox", "上周把系列停掉了，因为十二篇里九篇收藏两位数。",
        title="停掉系列",
    )
    await _seed_user(test_db)
    llm = _StubLLM(payload=_payload("share"))

    result = await ProjectStartService(test_db, llm=llm).start(
        "u1",
        ProjectStartRequest(inbox_item_id=item["id"], idempotency_key="start-2"),
    )

    assert result.material_id, "素材必须挂到项目上"
    material = await test_db.fetch_one(
        "SELECT content_text, privacy_level FROM materials WHERE id=:id",
        {"id": result.material_id},
    )
    assert "系列" in material["content_text"]
    # 素材默认私有：素材本身不公开，只有生成的内容面向读者
    assert material["privacy_level"] == "private"
    # 项目关联走 material_usages（这才是溯源链上真正被读取的关系）
    usage = await test_db.fetch_one(
        "SELECT project_id FROM material_usages WHERE material_id=:id",
        {"id": result.material_id},
    )
    assert usage is not None and usage["project_id"] == result.project_id
    assert result.title == "停掉系列"


@pytest.mark.asyncio
async def test_start_never_guesses_intent_when_model_fails(test_db):
    """模型不可用时**不猜意图**——留空交给确认步骤，而不是塞默认值。"""
    await _seed_user(test_db)
    llm = _StubLLM(error=RuntimeError("model down"))

    result = await ProjectStartService(test_db, llm=llm).start(
        "u1",
        ProjectStartRequest(raw_input="随便说点什么", idempotency_key="start-3"),
    )

    assert result.inference.intent is None
    assert result.inference.source == "deterministic_fallback"
    assert result.inference.confidence == "low"
    assert result.inference.next_question, "降级也要给一个能推进的问题"
    assert result.project_id


@pytest.mark.asyncio
async def test_start_requires_exactly_one_source(test_db):
    with pytest.raises(ValueError):
        ProjectStartRequest(raw_input="a", inbox_item_id="b", idempotency_key="k")
    with pytest.raises(ValueError):
        ProjectStartRequest(idempotency_key="k")


@pytest.mark.asyncio
async def test_start_rejects_unknown_or_foreign_inbox_item(test_db):
    await _seed_user(test_db)
    llm = _StubLLM(payload=_payload())
    with pytest.raises(ValueError):
        await ProjectStartService(test_db, llm=llm).start(
            "u1",
            ProjectStartRequest(inbox_item_id="nope", idempotency_key="start-4"),
        )
