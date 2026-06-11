from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.data_loader import load_campaign_reports, load_dmp_segments, load_report_summary, load_zones
from app.logic.brief_parser import parse_brief_mock
from app.logic.alert_builder import build_ao_alert
from app.logic.dmp_match import match_dmp_segments
from app.logic.invocation import run_invocation
from app.logic.report_analyzer import summarize_reports
from app.logic.setup_planner import build_setup_plan
from app.logic.zone_scoring import recommend_zones
from app.schemas import (
    AlertRequest,
    ApiResponse,
    BriefParseRequest,
    DmpMatchRequest,
    InvocationRequest,
    SetupPlanRequest,
    ZoneRecommendationRequest,
)


app = FastAPI(title="Camp Ads Agent", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/invocations", response_model=ApiResponse)
def invocations(payload: InvocationRequest) -> ApiResponse:
    return ApiResponse(
        data=run_invocation(
            message=payload.message,
            zones=load_zones(),
            dmp_segments=load_dmp_segments(),
            reports=load_campaign_reports(),
            creative=payload.creative,
            top_n=payload.top_n,
        )
    )


@app.post("/api/chat", response_model=ApiResponse)
def chat(payload: InvocationRequest) -> ApiResponse:
    return invocations(payload)


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


@app.get("/api/dmp/segments", response_model=ApiResponse)
def dmp_segments() -> ApiResponse:
    return ApiResponse(data=load_dmp_segments())


@app.post("/api/dmp/match", response_model=ApiResponse)
def dmp_match(payload: DmpMatchRequest) -> ApiResponse:
    return ApiResponse(data=match_dmp_segments(payload.target, load_dmp_segments()))


@app.post("/api/creative/inspect", response_model=ApiResponse)
async def creative_inspect(file: UploadFile = File(...)) -> ApiResponse:
    content = await file.read()
    return ApiResponse(
        data={
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(content),
            "status": "accepted" if len(content) > 0 else "empty",
        }
    )


@app.post("/api/setup/plan", response_model=ApiResponse)
def setup_plan(payload: SetupPlanRequest) -> ApiResponse:
    brief = parse_brief_mock(payload.brief_text)
    return ApiResponse(
        data=build_setup_plan(
            brief=brief,
            zones=load_zones(),
            dmp_segments=load_dmp_segments(),
            creative=payload.creative,
            top_n=payload.top_n,
        )
    )


@app.get("/api/reports/summary", response_model=ApiResponse)
def reports_summary() -> ApiResponse:
    return ApiResponse(data=load_report_summary())


@app.get("/api/reports/analyze", response_model=ApiResponse)
def reports_analyze() -> ApiResponse:
    return ApiResponse(data=summarize_reports(load_campaign_reports()))


@app.post("/api/alerts/ao", response_model=ApiResponse)
def ao_alert(payload: AlertRequest) -> ApiResponse:
    return ApiResponse(data=build_ao_alert(load_campaign_reports(), payload.max_items))


@app.post("/api/brief/parse", response_model=ApiResponse)
def brief_parse(payload: BriefParseRequest) -> ApiResponse:
    return ApiResponse(data=parse_brief_mock(payload.text).model_dump())
