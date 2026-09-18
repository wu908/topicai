"""音视频素材识别：把一段音频/视频交给全模态模型，读回来的文字写回素材。

三条产品约束（与前几轮一致）：

1. **不外发敏感素材**：素材的 privacy_level 是 sensitive 时拒绝（要用户自己先改级别）。
2. **不编造**：提示词要求"听不清/看不清就写未能确认"，并要求列出"无法确认"的部分。
3. **来源可见**：识别结果落库时记下模型与时间（analysis_json），界面据此说明
   「这段文字是模型读出来的」，而不是把它伪装成作者自己写的素材。
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.core.exceptions import UserActionRequiredException
from app.core.omni import (
    OmniClient,
    OmniMediaRejectedException,
    OmniNotConfiguredException,
)
from app.models.v2.action_domain import AITraceCreate
from app.services.ai_trace import AITraceService
from app.services.material import MaterialService
from app.services.v2_utils import now

#: 让模型说人话、说清楚哪里不确定——它的输出会直接变成素材文本。
ANALYSIS_INSTRUCTION = (
    "请读这段素材，只输出下面四段，用中文，不要用 Markdown 代码块：\n"
    "【内容摘要】两三句话，说清这段素材里发生了什么。\n"
    "【关键原话】最重要的两三句原话（听不清就写「未能确认」）。\n"
    "【可用细节】可以直接写进内容的 2–3 个具体细节（时间、数字、动作、结果）。\n"
    "【无法确认】你从这段素材里确认不了的信息。\n"
    "只写素材里真实出现的内容；听不清、看不清、没提到的一律写「未能确认」，不要推测。"
)


class MaterialAnalysisService:
    def __init__(
        self,
        db: Any,
        *,
        storage: Any | None = None,
        omni: OmniClient | None = None,
    ):
        self.db = db
        self.materials = MaterialService(db, storage=storage)
        self.omni = omni

    async def analyze(self, owner: str, material_id: str) -> dict[str, Any]:
        try:
            material = await self.materials.get(owner, material_id)
        except ValueError as exc:
            # 别人的素材、或已删除：给一句用户能照做的话（而不是 404 + 英文）。
            raise UserActionRequiredException("找不到这条素材，刷新后再试。") from exc
        kind = material["kind"]
        if kind not in {"audio", "video"}:
            raise UserActionRequiredException(
                "只有音频或视频素材需要识别；文字和图片素材不用这一步。"
            )
        if material["privacy_level"] == "sensitive":
            raise UserActionRequiredException(
                "这条素材标着「敏感」。识别会把它发给外部模型，"
                "要先在素材里把隐私级别改成「私密」或「公开」。"
            )

        client = self.omni or OmniClient()
        try:
            payload, mime_type = await self.materials.content_bytes(owner, material_id)
            result = client.describe_media(
                kind=kind,
                mime_type=mime_type,
                data=payload,
                instruction=ANALYSIS_INSTRUCTION,
            )
        except (OmniNotConfiguredException, OmniMediaRejectedException) as exc:
            raise UserActionRequiredException(str(exc)) from exc

        text = (result.get("text") or "").strip()
        if not text:
            raise UserActionRequiredException(
                "模型这次没有读出内容（可能是素材太短或格式问题），可以换个片段再试。"
            )

        analysis = {
            "source": "omni",
            "model": result.get("model"),
            "analyzed_at": now(),
            "usage": result.get("usage") or {},
        }
        await self.materials.store_analysis(owner, material_id, text, analysis)
        await self._trace(owner, material_id, kind, result)
        return await self.materials.get(owner, material_id)

    async def _trace(self, owner: str, material_id: str, kind: str, result: dict[str, Any]) -> None:
        session = await self.db.get_session()
        async with session:
            async with session.begin():
                await AITraceService.create(
                    session,
                    owner,
                    AITraceCreate(
                        id=str(uuid.uuid4()),
                        task_type="material_analysis",
                        input_refs=[f"material:{material_id}", f"kind:{kind}"],
                        evidence_refs=[],
                        policy_version="material-analysis-v1",
                        model_identifier=str(result.get("model") or ""),
                        capability="omni_media",
                        visibility_boundary={
                            # 素材内容离开本服务去外部模型：这是可见边界的一部分，
                            # 写进轨迹以便日后回答"这条素材被谁读过"。
                            "allowed": ["owner_uploaded_media"],
                            "forbidden": ["sensitive_material", "other_users"],
                            "actual": ["owner_uploaded_media", "external_model_read"],
                        },
                        contamination_check={
                            "status": "clean",
                            "unexpected_classes": [],
                            "missing_classes": [],
                        },
                        calibration_state="insufficient",
                        limitations=[
                            "识别结果由外部全模态模型生成，可能听错或漏读；"
                            "「未能确认」的部分需要作者自己核对",
                        ],
                        output_ref=f"material:{material_id}",
                        generated_at=now(),
                        confidence_label="medium",
                        outcome="success",
                        user_decision="pending",
                    ),
                )


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)
