"""
main.py — SafeRx FastAPI application entry point.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from agent.models import VerificationRequest, VerificationResponse
from agent.orchestrator import VerificationOrchestrator

log = structlog.get_logger(__name__)

_VERSION = "1.0.0"
_APP_ENV  = os.getenv("APP_ENV", "development")
_APP_PORT = int(os.getenv("APP_PORT", "8000"))
_CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]

# ── Demo scenarios ────────────────────────────────────────────────────────────

_DEMO_INPUTS: dict[str, str] = {
    "green":  "Paracetamol 500mg GlaxoSmithKline batch PAR-2024-001",
    "yellow": "Amoxicillin 250mg suspect batch recall AMX-HOLD-99",
    "red":    "Artesunate 50mg fake seized counterfeit batch BX7741",
}

# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("saferx.startup", env=_APP_ENV, port=_APP_PORT, cors_origins=_CORS_ORIGINS)
    app.state.orchestrator = VerificationOrchestrator()
    yield
    log.info("saferx.shutdown")

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SafeRx API",
    description="AI Medicine Verification Agent — powered by Azure AI Foundry and Foundry IQ.",
    version=_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root() -> str:
    return """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>SafeRx API</title>
<style>body{font-family:system-ui,sans-serif;max-width:600px;margin:4rem auto;padding:0 1rem;color:#1a1a1a}
a{color:#0066cc}</style></head>
<body>
<h1>SafeRx API</h1>
<p>SafeRx is an AI-powered medicine verification agent that cross-references WHO, FDA, and EMA
databases to detect counterfeit or recalled medicines in real time.</p>
<p><a href="/docs">Interactive API docs (Swagger UI)</a> &nbsp;|&nbsp;
<a href="/redoc">ReDoc</a></p>
</body>
</html>"""


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "SafeRx", "version": _VERSION}


@app.post("/verify", response_model=VerificationResponse)
async def verify(request: VerificationRequest) -> VerificationResponse:
    try:
        return await app.state.orchestrator.verify(request)
    except Exception as exc:
        log.exception("verify.unhandled_error", error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Verification service encountered an unexpected error. Please try again.",
        ) from exc


@app.post("/verify/demo", response_model=VerificationResponse)
async def verify_demo(
    scenario: str = Query(default="red", pattern="^(green|yellow|red)$"),
) -> VerificationResponse:
    """
    Pre-loads one of three demonstration scenarios.
    Use ?scenario=green|yellow|red (default: red — most impactful for live demos).
    """
    input_text = _DEMO_INPUTS[scenario]
    log.info("verify.demo", scenario=scenario, input_text=input_text)
    request = VerificationRequest(input_text=input_text)
    try:
        return await app.state.orchestrator.verify(request)
    except Exception as exc:
        log.exception("verify_demo.unhandled_error", scenario=scenario, error=str(exc))
        raise HTTPException(
            status_code=500,
            detail="Demo verification encountered an unexpected error.",
        ) from exc


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "agent.main:app",
        host="0.0.0.0",
        port=_APP_PORT,
        reload=_APP_ENV == "development",
        log_level="info",
    )
