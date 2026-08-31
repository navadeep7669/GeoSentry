from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, reports, risk_zones, alerts


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm up ML model
    from app.services.ml_service import ml_service
    ml_service.load_model()
    yield
    # Shutdown: nothing needed


app = FastAPI(
    title="GeoSentry",
    summary="GeoSentry — AI Landslide Early Warning & Dynamic Risk Prioritization Platform",
    description=(
        "**GeoSentry** is an AI-powered landslide early warning and emergency risk prioritization platform. "
        "It continuously integrates live weather, terrain DEM, soil moisture, satellite Earth observation changes, "
        "historical susceptibility, and verified field reports to compute dynamic risk and exposure-based prioritization.\n\n"
        "**Core Principles:** Dynamic Risk, Not a Painted Danger Zone.\n\n"
        "**Roles:** `citizen` (field reporter) | `validator` (field verifier) | `authority` (emergency manager)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS: restrict this in production
origins = ["http://localhost:3000", "http://localhost:8000"]
if settings.APP_ENV == "development":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(risk_zones.router, prefix="/risk-zones", tags=["Risk Zones & Dynamic Evaluation"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts & Notifications"])


from pathlib import Path
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _serve_template(filename: str, fallback_title: str):
    f = TEMPLATES_DIR / filename
    if f.exists():
        return FileResponse(f)
    return HTMLResponse(f"<h1>{fallback_title}</h1><p><a href='/'>&larr; Back to Directory</a></p>")


# ── Web Pages & Dedicated Feature Routes ────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["Web Portal"])
async def web_portal_directory():
    """Main API & Service Mapping Directory."""
    return _serve_template("index.html", "GeoSentry Directory")


@app.get("/analytics", response_class=HTMLResponse, tags=["Web Portal"])
async def page_analytics():
    """Dedicated Analytics Dashboard, Regional Breakdown & Trends."""
    return _serve_template("analytics.html", "Analytics Dashboard")


@app.get("/risk-evaluation", response_class=HTMLResponse, tags=["Web Portal"])
async def page_risk_evaluation():
    """Dedicated Dynamic Landslide Risk Engine Calculator."""
    return _serve_template("risk_evaluation.html", "Risk Evaluation Page")


@app.get("/risk-zones-view", response_class=HTMLResponse, tags=["Web Portal"])
async def page_risk_zones():
    """Dedicated Active Risk Zones GIS Map."""
    return _serve_template("risk_zones.html", "Risk Zones Map")


@app.get("/risk-priority", response_class=HTMLResponse, tags=["Web Portal"])
async def page_risk_priority():
    """Dedicated Emergency Risk Prioritization Hotspots."""
    return _serve_template("risk_priority.html", "Priority Hotspots")


@app.get("/field-reports", response_class=HTMLResponse, tags=["Web Portal"])
async def page_field_reports():
    """Dedicated Citizen Incident Field Submission."""
    return _serve_template("field_reports.html", "Field Reports")


@app.get("/reports-review", response_class=HTMLResponse, tags=["Web Portal"])
async def page_reports_review():
    """Dedicated Middleman Field Validator Console."""
    return _serve_template("reports_review.html", "Validator Review Console")


@app.get("/alert-dispatch", response_class=HTMLResponse, tags=["Web Portal"])
async def page_alert_dispatch():
    """Dedicated Emergency Multi-Channel Alert Dispatcher."""
    return _serve_template("alert_dispatch.html", "Alert Dispatch Center")


@app.get("/system-health", response_class=HTMLResponse, tags=["Web Portal"])
async def page_system_health():
    """Dedicated Operational Health & Diagnostics."""
    return _serve_template("system_health.html", "System Health Diagnostics")


@app.get("/auth/login-page", response_class=HTMLResponse, tags=["Web Portal"])
async def page_login():
    """Dedicated Account Authentication Page."""
    return _serve_template("login.html", "Account Login")


@app.get("/auth/register-page", response_class=HTMLResponse, tags=["Web Portal"])
async def page_register():
    """Dedicated User Account Registration Page."""
    return _serve_template("register.html", "User Registration")


@app.get("/stakeholders", response_class=HTMLResponse, tags=["Web Portal"])
async def page_stakeholders():
    """Dedicated Stakeholder & Persona Verification Gateway."""
    return _serve_template("stakeholders.html", "Stakeholders Verification Gateway")


# ── System Endpoints ────────────────────────────────────────────────────────

@app.get("/api/info", tags=["System"])
async def system_info():
    return {
        "app": "GeoSentry",
        "tagline": "AI Landslide Early Warning & Dynamic Risk Prioritization Platform",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "app": "GeoSentry",
        "env": settings.APP_ENV,
    }


@app.get("/api/health", tags=["System"])
async def api_health_check():
    return {
        "status": "ok",
        "service": "geosentry-api",
    }



from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.chat_service import chat_service

class ChatRequest(BaseModel):
    message: str
    language: str = "en"
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    language: str
    status: str = "success"

@app.post("/api/chat", response_model=ChatResponse, tags=["AI Assistant"])
async def chat_with_assistant(req: ChatRequest):
    """
    Multilingual AI early-warning voice & chat assistant powered by Gemini API / NLP domain engine.
    """
    reply = chat_service.generate_response(
        message=req.message,
        language=req.language,
        context=req.context
    )
    return ChatResponse(reply=reply, language=req.language)


