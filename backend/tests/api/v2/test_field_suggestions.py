"""候选端点契约（R9）：给可填字段提候选，AI 不可用时也必须有候选。"""

import pytest

from app.models.v2.field_suggestion import FieldSuggestionRequest
from app.services.field_suggestions import FieldSuggestionService


class _StubLLM:
    model = "stub-suggestion-v1"

    def __init__(self, payload=None, error=None):
        self._payload = payload
        self._error = error
        self.calls = []

    def is_available(self, capability: str = "text") -> bool:
        return True

    def generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        if self._error is not None:
            raise self._error
        return schema.model_validate(self._payload)


async def _seed_project(db, owner: str = "u1"):
    from app.models.v2.content_project import ContentProjectCreate
    from app.services.content_project import ContentProjectService

    session = await db.get_session()
    async with session:
        from sqlalchemy import text

        await session.execute(
            text(
                "INSERT OR IGNORE INTO users (id,email,username,password_hash,"
                "ai_calls_today,ai_calls_reset_at,created_at) VALUES "
                "(:id,:email,:name,'hash',0,'','2026-06-03T00:00:00Z')"
            ),
            {"id": owner, "email": f"{owner}@test.com", "name": owner},
        )
        await session.commit()
    project, _ = await ContentProjectService(db).create(
        owner,
        ContentProjectCreate(
            title="断更三周后我换了个选题方式",
            content_intent="share",
            audience_change="看完知道自己断更后可以怎么重启",
            idempotency_key="suggestion-project",
        ),
    )
    return project


@pytest.mark.asyncio
async def test_ai_candidates_use_project_material_and_stay_short(test_db):
    """AI 给的候选：按字段要求裁剪长度、去掉空候选、带一句推荐理由。"""
    project = await _seed_project(test_db)
    long_text = "看完能判断自己要不要重启" + "很长的补充" * 40
    llm = _StubLLM(
        payload={
            "candidates": [
                {"text": "看完能判断自己断更后该先做什么", "why": "贴着素材里的重启经历"},
                {"text": long_text, "why": ""},
                {"text": "   ", "why": "空候选会被丢掉"},
            ]
        }
    )
    view = await FieldSuggestionService(test_db, llm=llm).suggest(
        "u1",
        project["id"],
        FieldSuggestionRequest(field="audience_change", count=3),
    )

    assert view["source"] == "ai"
    assert [item["text"] for item in view["candidates"]][0] == "看完能判断自己断更后该先做什么"
    # audience_change 的字段上限是 80：模型给长了要截断，而不是原样塞进输入框
    assert all(len(item["text"]) <= 80 for item in view["candidates"])
    assert all(item["text"].strip() for item in view["candidates"])
    assert llm.calls, "必须真的调用模型"


@pytest.mark.asyncio
async def test_prompt_forbids_inventing_experience_without_material(test_db):
    """没有已确认素材时，提示词必须明确禁止编造经历。"""
    project = await _seed_project(test_db)
    llm = _StubLLM(payload={"candidates": [{"text": "写法骨架", "why": ""}]})
    await FieldSuggestionService(test_db, llm=llm).suggest(
        "u1", project["id"], FieldSuggestionRequest(field="answer")
    )

    prompt = llm.calls[0]["prompt"]
    assert "不要编造" in prompt
    assert "断更三周后我换了个选题方式" in prompt


@pytest.mark.asyncio
async def test_ai_failure_falls_back_to_candidates_with_a_reason(test_db):
    """AI 失败也要有候选，并说明这是通用方向——不能留空白让用户干瞪眼。"""
    project = await _seed_project(test_db)
    llm = _StubLLM(error=RuntimeError("boom"))
    view = await FieldSuggestionService(test_db, llm=llm).suggest(
        "u1", project["id"], FieldSuggestionRequest(field="audience_change")
    )

    assert view["source"] == "deterministic_fallback"
    assert view["candidates"], "降级不能返回空候选"
    assert any("AI 暂时不可用" in item for item in view["limitations"])


@pytest.mark.asyncio
async def test_no_llm_still_returns_a_usable_scaffold(test_db):
    """AI 关掉时，answer 字段给的是可照填的骨架，而不是编好的具体经历。"""
    project = await _seed_project(test_db)
    view = await FieldSuggestionService(test_db, llm=None).suggest(
        "u1", project["id"], FieldSuggestionRequest(field="answer")
    )

    assert view["source"] == "deterministic_fallback"
    assert view["candidates"]
    assert any("（" in item["text"] for item in view["candidates"]), "骨架要留出填写位置"


@pytest.mark.asyncio
async def test_other_users_project_is_not_readable(client, test_db):
    """候选会读到项目材料：别人的项目必须拒绝，且给能读懂的话。"""
    project = await _seed_project(test_db, owner="someone-else")

    response = await client.post(
        f"/api/v2/projects/{project['id']}/field-suggestions",
        json={"field": "answer"},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "找不到这条内容，刷新后再试。"


@pytest.mark.asyncio
async def test_unknown_field_is_rejected(client):
    project = await _seed_project_with_client(client)
    response = await client.post(
        f"/api/v2/projects/{project['id']}/field-suggestions",
        json={"field": "说说你今天的心情"},
    )
    assert response.status_code == 422


async def _seed_project_with_client(client):
    """HTTP 层用的最小项目（走真实端点，确保契约一致）。"""
    created = await client.post(
        "/api/v2/projects",
        json={"title": "候选字段契约", "idempotency_key": "suggestion-http"},
    )
    assert created.status_code == 201, created.text
    return created.json()["data"]
