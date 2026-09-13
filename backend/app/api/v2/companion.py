"""Companion ask endpoint (real-model answers for the floating ball)."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, field_validator

from app.api.deps import get_current_user
from app.models.common import ApiResponse
from app.services.companion import CompanionService

router = APIRouter(prefix="/companion", tags=["Companion"])


class CompanionAskRequest(BaseModel):
    context: str = Field(default="全局", max_length=120)
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value


@router.post("/ask", response_model=ApiResponse)
async def ask(
    req: Request,
    body: CompanionAskRequest,
    user: dict = Depends(get_current_user),
):
    service = CompanionService(db=req.app.state.db)
    answer = await service.answer(context=body.context, question=body.question)
    return {
        "code": 200,
        "data": {"answer": answer},
        "message": "success",
        "meta": {},
    }
