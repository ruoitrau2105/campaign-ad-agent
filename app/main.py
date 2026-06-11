from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.data_loader import load_campaign_reports, load_report_summary, load_zones
from app.logic.brief_parser import parse_brief_mock
from app.logic.report_analyzer import summarize_reports
from app.logic.zone_scoring import recommend_zones
from app.schemas import ApiResponse, BriefParseRequest, ZoneRecommendationRequest


app = FastAPI(title="Camp Ads Agent", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/context", response_model=ApiResponse)
def context() -> ApiResponse:
    return ApiResponse(
        data={
            "project": "Camp Ads Agent",
            "mode": "mock-first",
            "framework": "FastAPI custom agent + deterministic workflow",
            "models": ["MiniMax M2.5", "Qwen 3.5 27B", "Gemma 4 31B-IT"],
            "baseline": load_report_summary()["total"],
        }
    )


@app.get("/api/zones", response_model=ApiResponse)
def zones() -> ApiResponse:
    return ApiResponse(data=load_zones())


@app.post("/api/zones/recommend", response_model=ApiResponse)
def zones_recommend(payload: ZoneRecommendationRequest) -> ApiResponse:
    return ApiResponse(
        data={
            "objective": payload.objective,
            "budget_vnd": payload.budget_vnd,
            "zones": recommend_zones(load_zones(), payload.objective, payload.top_n),
        }
    )


@app.get("/api/reports/summary", response_model=ApiResponse)
def reports_summary() -> ApiResponse:
    return ApiResponse(data=load_report_summary())


@app.get("/api/reports/analyze", response_model=ApiResponse)
def reports_analyze() -> ApiResponse:
    return ApiResponse(data=summarize_reports(load_campaign_reports()))


@app.post("/api/brief/parse", response_model=ApiResponse)
def brief_parse(payload: BriefParseRequest) -> ApiResponse:
    return ApiResponse(data=parse_brief_mock(payload.text).model_dump())
