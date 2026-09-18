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
        "audience_change": "看完知道断更后可以先用零碎想法重启",
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
    assert result.inference.intent_label == "教方法"
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


# ==================== R2：推断必须被状态机用上，且可被一句话撤销 ====================


@pytest.mark.asyncio
async def test_inference_skips_the_duplicate_intent_confirmation(test_db):
    """有 AI 推断时不该再问一次「确认这是一条 X 内容吗」——那是重复提问。"""
    from app.services.intent_orchestrator import IntentOrchestratorService

    await _seed_user(test_db)
    llm = _StubLLM(payload=_payload("share", "这组插画里你最想先给大家看哪一张？"))
    started = await ProjectStartService(test_db, llm=llm).start(
        "u1",
        ProjectStartRequest(raw_input="我画了一组水彩插画想发出来", idempotency_key="r2-1"),
    )

    action = await IntentOrchestratorService(test_db).ensure_project_action("u1", started.project_id)
    assert action["action_type"] == "answer_key_question", "有推断就应直接进入取素材"
    assert action["title"] == "这组插画里你最想先给大家看哪一张？"
    assert "哪个瞬间" not in action["title"]


@pytest.mark.asyncio
async def test_dismissing_the_inference_restores_the_confirmation_step(test_db):
    """用户说「不对，我自己选」→ 清掉推断 → 回到既有的意图确认步骤。"""
    from app.services.content_project import ContentProjectService
    from app.services.intent_orchestrator import IntentOrchestratorService

    await _seed_user(test_db)
    llm = _StubLLM(payload=_payload("share"))
    started = await ProjectStartService(test_db, llm=llm).start(
        "u1",
        ProjectStartRequest(raw_input="随便说点什么", idempotency_key="r2-2"),
    )

    await ContentProjectService(test_db).dismiss_start_inference(
        "u1", started.project_id
    )

    action = await IntentOrchestratorService(test_db).ensure_project_action("u1", started.project_id)
    assert action["action_type"] == "confirm_intent", "撤销推断后必须回到用户自己定"


@pytest.mark.asyncio
async def test_no_inference_still_asks_the_user_to_confirm(test_db):
    """模型不可用（没有推断）时行为不变：仍然让用户确认意图。"""
    from app.services.intent_orchestrator import IntentOrchestratorService

    await _seed_user(test_db)
    llm = _StubLLM(error=RuntimeError("model down"))
    started = await ProjectStartService(test_db, llm=llm).start(
        "u1",
        ProjectStartRequest(raw_input="随便说点什么", idempotency_key="r2-3"),
    )

    action = await IntentOrchestratorService(test_db).ensure_project_action("u1", started.project_id)
    assert action["action_type"] == "confirm_intent"


# ==================== R3：读者变化由材料提炼，不再问用户 ====================


@pytest.mark.asyncio
async def test_inference_proposes_the_audience_change(test_db):
    """读者变化是生成候选的输入，应由材料提炼——不让用户凭空作答。"""
    await _seed_user(test_db)
    llm = _StubLLM(payload=_payload("share"))
    started = await ProjectStartService(test_db, llm=llm).start(
        "u1",
        ProjectStartRequest(raw_input="我画了一组水彩插画想发出来", idempotency_key="r3-1"),
    )

    project = await test_db.fetch_one(
        "SELECT audience_change FROM content_projects WHERE id=:id",
        {"id": started.project_id},
    )
    assert project["audience_change"] == "看完知道断更后可以先用零碎想法重启"
    assert started.inference.audience_change


@pytest.mark.asyncio
async def test_fallback_leaves_audience_change_for_the_confirmation_step(test_db):
    """模型不可用时不编读者变化——留空，由既有的确认步骤问用户。"""
    await _seed_user(test_db)
    llm = _StubLLM(error=RuntimeError("model down"))
    started = await ProjectStartService(test_db, llm=llm).start(
        "u1",
        ProjectStartRequest(raw_input="随便说说", idempotency_key="r3-2"),
    )

    project = await test_db.fetch_one(
        "SELECT audience_change FROM content_projects WHERE id=:id",
        {"id": started.project_id},
    )
    assert project["audience_change"] is None
    assert started.inference.audience_change is None


@pytest.mark.asyncio
async def test_confident_inference_is_settled_so_later_steps_can_run(test_db):
    """R8：高/中置信度的推断在创建时就落成"已确认的工作意图"。

    在此之前，状态机凭"有推断记录"跳过了意图确认步骤（R2：再问一次是重复
    提问），却从未把意图落定——intent_status 一直停在 candidate，而发布判断
    锁定、观点提炼、系列发现都要求 working_confirmed。用户会一路走到"锁定
    发布判断"才撞上 400，生产环境还会把它换成通用的「请求参数无效」。
    """
    from app.services.content_project import ContentProjectService
    from app.services.intent_orchestrator import IntentOrchestratorService

    await _seed_user(test_db)
    llm = _StubLLM(payload=_payload("share", "你拿它试的第一件真实任务是什么？"))
    result = await ProjectStartService(test_db, llm=llm).start(
        "u1",
        ProjectStartRequest(
            raw_input="试了三天智能体，想说说值不值得试",
            idempotency_key="start-settled-1",
        ),
    )

    project = await ContentProjectService(test_db).get("u1", result.project_id)
    assert project["intent_status"] == "working_confirmed"
    assert project["content_intent"] == "share"
    # 推断没给读者变化时用 rubric 的通用方向兜底，而不是留下空值。
    assert project["audience_change"] == "看完知道断更后可以先用零碎想法重启"

    # 意图已定：状态机不再问一次，直接进入取素材那一步。
    action = await IntentOrchestratorService(test_db).ensure_project_action(
        "u1", dict(project)
    )
    assert action["action_type"] == "answer_key_question"


@pytest.mark.asyncio
async def test_low_confidence_inference_still_asks_the_user(test_db):
    """低置信度推断**不**落成已确认：AI 自己都不确定时，该问一次。"""
    from app.services.content_project import ContentProjectService
    from app.services.intent_orchestrator import IntentOrchestratorService

    await _seed_user(test_db)
    payload = {**_payload("share", "这件事里哪一步最费劲？"), "confidence": "low"}
    result = await ProjectStartService(test_db, llm=_StubLLM(payload=payload)).start(
        "u1",
        ProjectStartRequest(raw_input="随手记一下今天的事", idempotency_key="start-low-1"),
    )

    project = await ContentProjectService(test_db).get("u1", result.project_id)
    assert project["intent_status"] == "candidate"
    action = await IntentOrchestratorService(test_db).ensure_project_action(
        "u1", dict(project)
    )
    assert action["action_type"] == "confirm_intent"


@pytest.mark.asyncio
async def test_dismissing_the_inference_reopens_the_intent_question(test_db):
    """「不对，我自己选」必须真的把决定权还回来。

    推断现在会落成已确认，所以撤销动作必须同时把意图状态退回 candidate，
    否则状态机认为意图已定，用户没有任何入口改回自己的判断。
    """
    from app.services.content_project import ContentProjectService
    from app.services.intent_orchestrator import IntentOrchestratorService

    await _seed_user(test_db)
    result = await ProjectStartService(test_db, llm=_StubLLM(payload=_payload("share"))).start(
        "u1",
        ProjectStartRequest(raw_input="讲一段经历", idempotency_key="start-dismiss-1"),
    )
    await ContentProjectService(test_db).dismiss_start_inference("u1", result.project_id)

    project = await ContentProjectService(test_db).get("u1", result.project_id)
    assert project["intent_status"] == "candidate"
    action = await IntentOrchestratorService(test_db).ensure_project_action(
        "u1", dict(project)
    )
    assert action["action_type"] == "confirm_intent"
