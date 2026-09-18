"""音视频素材识别（全模态）契约。

这几条测试守住的是"这条链路怎么坏都不该坏"的部分：未配置时给人话、敏感素材不外发、
识别结果落到素材上并标出来源、载荷按官方格式拼（这是集成的核心，写错了线上才发现）。
"""

import base64

import pytest

from app.core.omni import (
    OmniClient,
    OmniMediaRejectedException,
    OmniNotConfiguredException,
)
from app.models.v2.material import MaterialCreate
from app.services.material import MaterialService
from app.services.material_analysis import MaterialAnalysisService


class _StubOmni:
    def __init__(self, *, text="【内容摘要】断更两周后换了选题方式。", model="mimo-v2.5"):
        self.instructions: list[str] = []
        self._text = text
        self._model = model

    def describe_media(self, *, kind, mime_type, data, instruction, fps=2.0):  # noqa: ANN001
        self.instructions.append(instruction)
        return {
            "text": self._text,
            "model": self._model,
            "usage": {"prompt_tokens": 1200, "completion_tokens": 88, "total_tokens": 1288},
        }


async def _seed_user(db, owner="u1"):
    from sqlalchemy import text

    session = await db.get_session()
    async with session:
        await session.execute(
            text(
                "INSERT OR IGNORE INTO users (id,email,username,password_hash,"
                "ai_calls_today,ai_calls_reset_at,created_at) VALUES "
                "(:id,:email,:name,'hash',0,'','2026-06-03T00:00:00Z')"
            ),
            {"id": owner, "email": f"{owner}@test.com", "name": owner},
        )
        await session.commit()


@pytest.mark.asyncio
async def test_audio_material_is_analyzed_and_marks_its_source(test_db, tmp_path):
    """识别结果写回素材文本，并带上来源——界面才能说清"这是模型读出来的"。"""
    from app.core.storage import LocalObjectStorage

    await _seed_user(test_db)
    storage = LocalObjectStorage(tmp_path)
    material, _ = await MaterialService(test_db, storage=storage).create(
        "u1",
        MaterialCreate(
            kind="audio",
            title="复更那天的口述",
            content_base64=base64.b64encode(b"fake-mp3-bytes").decode(),
            mime_type="audio/mpeg",
            idempotency_key="audio-1",
        ),
    )

    omni = _StubOmni()
    view = await MaterialAnalysisService(test_db, storage=storage, omni=omni).analyze(
        "u1", material["id"]
    )

    assert view["content"].startswith("【内容摘要】")
    assert view["analysis"]["source"] == "omni"
    assert view["analysis"]["model"] == "mimo-v2.5"
    assert view["analysis"]["usage"]["total_tokens"] == 1288
    assert "未能确认" in omni.instructions[0], "提示词必须要求标出不确定的地方"

    # 轨迹可查：这条素材被外部模型读过，必须留痕
    trace = await test_db.fetch_one(
        "SELECT task_type,capability,model_identifier FROM ai_traces_v2 "
        "WHERE owner_user_id='u1' AND task_type='material_analysis'"
    )
    assert trace["capability"] == "omni_media"
    assert trace["model_identifier"] == "mimo-v2.5"


@pytest.mark.asyncio
async def test_sensitive_material_is_never_sent_out(test_db, tmp_path):
    """标着敏感的素材不外发：给用户可执行的下一步，而不是静默失败。"""
    from app.core.exceptions import UserActionRequiredException
    from app.core.storage import LocalObjectStorage

    await _seed_user(test_db)
    storage = LocalObjectStorage(tmp_path)
    material, _ = await MaterialService(test_db, storage=storage).create(
        "u1",
        MaterialCreate(
            kind="video",
            title="家里的片段",
            content_base64=base64.b64encode(b"fake-mp4").decode(),
            mime_type="video/mp4",
            privacy_level="sensitive",
            idempotency_key="video-sensitive",
        ),
    )
    omni = _StubOmni()

    with pytest.raises(UserActionRequiredException, match="敏感"):
        await MaterialAnalysisService(test_db, storage=storage, omni=omni).analyze(
            "u1", material["id"]
        )

    assert omni.instructions == [], "敏感素材绝不能被发出去"


@pytest.mark.asyncio
async def test_text_material_does_not_need_recognition(test_db):
    await _seed_user(test_db)
    material, _ = await MaterialService(test_db).create(
        "u1",
        MaterialCreate(
            kind="text", title="一句素材", content="已经是一句话了",
            idempotency_key="text-1",
        ),
    )

    from app.core.exceptions import UserActionRequiredException

    with pytest.raises(UserActionRequiredException, match="只有音频或视频"):
        await MaterialAnalysisService(test_db, omni=_StubOmni()).analyze("u1", material["id"])


@pytest.mark.asyncio
async def test_unconfigured_model_says_what_to_do(test_db, tmp_path):
    """没配 key 时给出可执行的话（而不是 500 或静默无结果）。"""
    from app.core.exceptions import UserActionRequiredException
    from app.core.storage import LocalObjectStorage

    await _seed_user(test_db)
    storage = LocalObjectStorage(tmp_path)
    material, _ = await MaterialService(test_db, storage=storage).create(
        "u1",
        MaterialCreate(
            kind="audio",
            title="口述",
            content_base64=base64.b64encode(b"bytes").decode(),
            mime_type="audio/wav",
            idempotency_key="audio-unconfigured",
        ),
    )

    with pytest.raises(UserActionRequiredException, match="OMNI_API_KEY"):
        await MaterialAnalysisService(test_db, storage=storage, omni=OmniClient()).analyze(
            "u1", material["id"]
        )


def test_omni_payload_matches_the_official_shape(monkeypatch):
    """载荷必须按官方格式拼：它会直接决定线上能不能读出内容。"""
    captured: dict = {}

    class _Completions:
        def create(self, **kwargs):  # noqa: ANN003
            captured.update(kwargs)

            class _Message:
                content = "读出来的文本"

            class _Choice:
                message = _Message()

            class _Usage:
                prompt_tokens, completion_tokens, total_tokens = 10, 20, 30

            class _Response:
                choices = [_Choice()]
                model = "mimo-v2.5"
                usage = _Usage()

            return _Response()

    class _Client:
        chat = type("_Chat", (), {"completions": _Completions()})()

    client = OmniClient()
    monkeypatch.setattr(client, "is_configured", lambda: True)
    client.client = _Client()  # type: ignore[assignment]

    result = client.describe_media(
        kind="video",
        mime_type="video/mp4",
        data=b"0123456789",
        instruction="读它",
        fps=3.0,
    )

    payload = captured
    part = payload["messages"][0]["content"][0]
    assert part["type"] == "video_url"
    assert part["video_url"]["url"].startswith("data:video/mp4;base64,")
    assert part["fps"] == 3.0
    assert part["media_resolution"] == "default"
    assert payload["messages"][0]["content"][1]["text"] == "读它"
    # thinking 是非标准参数，必须走 extra_body；否则服务端会忽略/报错
    assert payload["extra_body"] == {"thinking": {"type": "disabled"}}
    assert result["text"] == "读出来的文本"
    assert result["usage"]["total_tokens"] == 30


def test_oversized_and_unknown_formats_are_rejected_with_plain_words(monkeypatch):
    client = OmniClient()
    monkeypatch.setattr(client, "is_configured", lambda: True)
    # 尺寸/格式校验发生在发请求之前，所以这里不需要真的客户端；
    # 但客户端为 None 会先被"未配置"拦住，所以要给个占位。
    client.client = object()  # type: ignore[assignment]
    monkeypatch.setattr(client, "max_media_bytes", lambda: 10)

    with pytest.raises(OmniMediaRejectedException, match="超过识别上限"):
        client.describe_media(kind="audio", mime_type="audio/wav", data=b"x" * 50, instruction="读")

    monkeypatch.setattr(client, "max_media_bytes", lambda: 10_000)
    with pytest.raises(OmniMediaRejectedException, match="认不出这个文件的格式"):
        client.describe_media(kind="audio", mime_type="application/x-weird", data=b"x", instruction="读")


def test_unconfigured_client_refuses_before_building_a_request():
    client = OmniClient()
    with pytest.raises(OmniNotConfiguredException):
        client.describe_media(kind="audio", mime_type="audio/wav", data=b"x", instruction="读")


@pytest.mark.asyncio
async def test_analysis_is_owner_scoped(client, test_db, tmp_path):
    """别人的素材读不到——识别结果是素材内容的一部分。"""
    from app.core.storage import LocalObjectStorage

    await _seed_user(test_db, owner="someone-else")
    storage = LocalObjectStorage(tmp_path)
    material, _ = await MaterialService(test_db, storage=storage).create(
        "someone-else",
        MaterialCreate(
            kind="audio",
            title="别人的口述",
            content_base64=base64.b64encode(b"bytes").decode(),
            mime_type="audio/mpeg",
            idempotency_key="audio-other",
        ),
    )

    response = await client.post(f"/api/v2/materials/{material['id']}:analyze")

    assert response.status_code == 400
    assert "找不到这条素材" in response.json()["message"]
