"""HTTP adapters for the reference anchor (冷启动锚点 R7)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_db
from app.core.database import Database
from app.models.common import ApiResponse
from app.models.v2.reference_anchor import ReferenceAnchorUpdate, ReferenceAnchorView
from app.services.reference_anchor import ReferenceAnchorService

router = APIRouter(prefix="/reference-anchor", tags=["Reference anchor v2"])


@router.get("", response_model=ApiResponse[ReferenceAnchorView])
async def get_reference_anchor(
    user=Depends(get_current_user), db: Database = Depends(get_db)
):
    """从你贴的参考里读出来的「你想做成什么样」。

    参考集没变就返回上次的读数（不重复调用模型）；还没贴参考时返回空读数——
    那是正常状态，不是错误。
    """
    return ApiResponse[ReferenceAnchorView](
        data=await ReferenceAnchorService(db).get(user["id"])
    )


@router.put("", response_model=ApiResponse[ReferenceAnchorView])
async def update_reference_anchor(
    body: ReferenceAnchorUpdate,
    user=Depends(get_current_user),
    db: Database = Depends(get_db),
):
    """以你说的为准。改过之后，参考集再变化也不会自动覆盖你的判断。"""
    return ApiResponse[ReferenceAnchorView](
        data=await ReferenceAnchorService(db).update(user["id"], body)
    )
