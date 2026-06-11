from typing import Any, Literal

from pydantic import BaseModel, Field


Objective = Literal["awareness", "consideration", "conversion", "retention"]


class BriefTarget(BaseModel):
    age: str | None = None
    gender: str | None = None
    location: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    behaviors: list[str] = Field(default_factory=list)


class CampaignBrief(BaseModel):
    brand: str
    objective: str
    funnel_stage: Objective
    target: BriefTarget = Field(default_factory=BriefTarget)
    budget_vnd: int | None = None
    flight: str | None = None
    kpi: list[str] = Field(default_factory=list)
    formats: list[str] = Field(default_factory=list)


class BriefParseRequest(BaseModel):
    text: str


class ZoneRecommendationRequest(BaseModel):
    objective: Objective
    budget_vnd: int | None = None
    top_n: int = Field(default=5, ge=1, le=10)


class DmpMatchRequest(BaseModel):
    target: BriefTarget


class SetupPlanRequest(BaseModel):
    brief_text: str
    creative: dict[str, Any] | None = None
    top_n: int = Field(default=5, ge=1, le=10)


class AlertRequest(BaseModel):
    max_items: int = Field(default=8, ge=1, le=20)


class ApiResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: Any
