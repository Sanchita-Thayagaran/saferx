"""
orchestrator.py — SafeRx 6-step medicine verification reasoning chain.

Step 1  Input Processing       extract_medicine_info
Step 2  Foundry IQ Verification verify_drug (parallel knowledge-base queries)
Step 3  Anomaly Reasoning       assess_anomalies
Step 4  Risk Scoring            score + safety escalation rules
Step 5  Action Guidance         generate_action_guidance
Step 6  Reporting Loop          generate_regulatory_report (YELLOW/RED only)
"""
from __future__ import annotations

import os
import re
import time
import uuid
from typing import Optional

import structlog

from agent.foundry_client import FoundryAgentClient, FoundryIQClient
from agent.real_data_client import RealDataClient
from agent.models import (
    ActionGuidance,
    DatabaseMatch,
    ExtractedMedicineInfo,
    RegulatoryReport,
    RiskAssessment,
    RiskLevel,
    VerificationRequest,
    VerificationResponse,
)

log = structlog.get_logger(__name__)

_DISCLAIMER = (
    "SafeRx AI output is a decision-support tool only. "
    "It does not replace professional pharmaceutical judgement, "
    "regulatory authority guidance, or laboratory analysis. "
    "Always consult your national medicines authority for definitive verification."
)


# ── Risk-scoring helpers ──────────────────────────────────────────────────────

def _score_to_level(score: float) -> RiskLevel:
    """Map a normalised 0–1 risk score to GREEN / YELLOW / RED."""
    if score >= 0.7:
        return RiskLevel.RED
    if score >= 0.4:
        return RiskLevel.YELLOW
    return RiskLevel.GREEN


_CRITICAL_ALERT_TYPES = {"COUNTERFEIT_CONFIRMED", "CLASS_I_RECALL", "BATCH_RECALL"}

def _safety_escalate(level: RiskLevel, matches: list[DatabaseMatch]) -> RiskLevel:
    """
    Hard safety rule applied after LLM scoring.
    - Any match with a critical alert type (confirmed counterfeit / recall) → RED
    - Any match with a non-null alert_type + LLM said GREEN → floor to YELLOW
    Severity-aware: investigative alerts (SUSPECT_QUALITY, UNDER_INVESTIGATION)
    correctly produce YELLOW, not RED.
    """
    flagged  = [m for m in matches if m.matched and m.alert_type is not None]
    critical = [m for m in flagged  if m.alert_type in _CRITICAL_ALERT_TYPES]
    if critical:
        return RiskLevel.RED
    if flagged and level == RiskLevel.GREEN:
        return RiskLevel.YELLOW
    return level


# ── Orchestrator ──────────────────────────────────────────────────────────────

class VerificationOrchestrator:

    def __init__(self) -> None:
        self._iq    = FoundryIQClient()
        self._agent = FoundryAgentClient()
        self.real_data_client = RealDataClient()
        self.use_real_data = os.getenv("USE_REAL_DATA", "true").lower() == "true"

    async def verify(self, request: VerificationRequest) -> VerificationResponse:
        request_id = str(uuid.uuid4())
        start      = time.perf_counter()
        trace: list[str] = []

        bound = log.bind(request_id=request_id, session_id=request.session_id)
        bound.info("verification.start", input_chars=len(request.input_text))

        if not _is_sufficient_input(request.input_text):
            elapsed_ms = (time.perf_counter() - start) * 1000
            bound.info("verification.insufficient_input", input=request.input_text)
            return _insufficient_response(request, request_id, elapsed_ms)

        try:
            return await self._run_chain(request, request_id, start, trace, bound)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            bound.exception("verification.error", error=str(exc), elapsed_ms=round(elapsed_ms, 2))
            return _error_response(request, request_id, exc, elapsed_ms, trace)

    # ── Chain ─────────────────────────────────────────────────────────────────

    async def _run_chain(
        self,
        request: VerificationRequest,
        request_id: str,
        start: float,
        trace: list[str],
        bound: structlog.typing.FilteringBoundLogger,
    ) -> VerificationResponse:

        # ── Step 1: Input Processing ──────────────────────────────────────────
        extracted_info: ExtractedMedicineInfo = await self._agent.extract_medicine_info(
            request.input_text
        )
        bound.info(
            "step_1.complete",
            drug_name=extracted_info.drug_name,
            batch=extracted_info.batch_number,
            manufacturer=extracted_info.manufacturer,
        )
        trace.append(
            f"Step 1 — Extracted: drug='{extracted_info.drug_name}', "
            f"batch='{extracted_info.batch_number}', "
            f"manufacturer='{extracted_info.manufacturer}'."
        )

        # ── Step 2: Foundry IQ Verification ──────────────────────────────────
        # Always runs even if extraction was partial — fall back to raw input_text.
        drug_name_for_query = extracted_info.drug_name or request.input_text

        if self.use_real_data:
            bound.info("step_2.real_data_used", used=True)
            real_result = await self.real_data_client.verify_drug_realworld(
                drug_name_for_query, extracted_info.batch_number
            )
            foundry_matches = await self._iq.verify_drug(
                drug_name=drug_name_for_query,
                manufacturer=extracted_info.manufacturer,
                batch_number=extracted_info.batch_number,
                country=extracted_info.country_of_origin,
                raw_input=request.input_text,
            )
            database_matches = real_result["matches"] + foundry_matches
        else:
            bound.info("step_2.real_data_used", used=False)
            database_matches = await self._iq.verify_drug(
                drug_name=drug_name_for_query,
                manufacturer=extracted_info.manufacturer,
                batch_number=extracted_info.batch_number,
                country=extracted_info.country_of_origin,
                raw_input=request.input_text,
            )

        sources_checked = sorted({m.source for m in database_matches})
        matched_count   = sum(1 for m in database_matches if m.matched)
        bound.info(
            "step_2.complete",
            matched_count=matched_count,
            sources_checked=sources_checked,
            real_data_used=self.use_real_data,
        )
        trace.append(
            f"Step 2 — Queried {len(sources_checked)} source(s) "
            f"({', '.join(sources_checked)}); {matched_count} matching record(s) found."
            + (" [live data]" if self.use_real_data else " [mock data]")
        )

        # ── Step 3: Anomaly Reasoning ─────────────────────────────────────────
        risk_assessment: RiskAssessment = await self._agent.assess_anomalies(
            extracted_info, database_matches
        )
        anomaly_count = len(risk_assessment.flags)
        bound.info(
            "step_3.complete",
            anomaly_count=anomaly_count,
            risk_score=risk_assessment.score,
            llm_level=risk_assessment.level.value,
        )
        trace.append(
            f"Step 3 — Anomaly reasoning: score={risk_assessment.score:.2f}, "
            f"flags={anomaly_count}, LLM verdict={risk_assessment.level.value}."
        )

        # ── Step 4: Risk Scoring ──────────────────────────────────────────────
        score_level = _score_to_level(risk_assessment.score)
        final_level = _safety_escalate(score_level, database_matches)

        if final_level != risk_assessment.level:
            risk_assessment = risk_assessment.model_copy(update={"level": final_level})
            trace.append(
                f"Step 4 — Safety escalation: "
                f"{score_level.value} → {final_level.value} "
                f"(flagged database records triggered hard safety rule)."
            )
        else:
            trace.append(
                f"Step 4 — Risk level confirmed: {final_level.value} "
                f"(score={risk_assessment.score:.2f}, no escalation needed)."
            )

        bound.info(
            "step_4.complete",
            score_level=score_level.value,
            final_level=final_level.value,
            escalated=final_level != score_level,
        )

        # ── Step 5: Action Guidance ───────────────────────────────────────────
        action_guidance: ActionGuidance = await self._agent.generate_action_guidance(
            risk_assessment, request.locale
        )
        bound.info(
            "step_5.complete",
            emergency=action_guidance.emergency,
            step_count=len(action_guidance.steps),
        )
        trace.append(
            f"Step 5 — Action guidance: emergency={action_guidance.emergency}, "
            f"{len(action_guidance.steps)} recommended step(s)."
        )

        # ── Step 6: Reporting Loop ────────────────────────────────────────────
        report: Optional[RegulatoryReport] = None

        if final_level in (RiskLevel.YELLOW, RiskLevel.RED):
            # Build a complete-enough response so the report has full context.
            partial = VerificationResponse(
                request_id=request_id,
                session_id=request.session_id,
                extracted_info=extracted_info,
                database_matches=database_matches,
                risk_assessment=risk_assessment,
                action_guidance=action_guidance,
                risk_level=final_level,
                verified=False,
                reasoning_trace=list(trace),
                disclaimer=_DISCLAIMER,
            )
            report = await self._agent.generate_regulatory_report(partial)
            bound.info("step_6.complete", report_id=report.report_id, generated=True)
            trace.append(f"Step 6 — Regulatory report generated: id={report.report_id}.")
        else:
            bound.info("step_6.complete", generated=False, reason="GREEN — report not required")
            trace.append("Step 6 — Report skipped (GREEN risk; no regulatory action required).")

        # ── Final Assembly ────────────────────────────────────────────────────
        elapsed_ms = (time.perf_counter() - start) * 1000
        verified   = (
            final_level == RiskLevel.GREEN
            and matched_count > 0
            and extracted_info.drug_name is not None
        )

        response = VerificationResponse(
            request_id=request_id,
            session_id=request.session_id,
            extracted_info=extracted_info,
            database_matches=database_matches,
            risk_assessment=risk_assessment,
            action_guidance=action_guidance,
            report=report,
            risk_level=final_level,
            verified=verified,
            processing_time_ms=round(elapsed_ms, 2),
            reasoning_trace=trace,
            disclaimer=_DISCLAIMER,
        )

        bound.info(
            "verification.complete",
            request_id=request_id,
            risk_level=final_level.value,
            verified=verified,
            processing_time_ms=response.processing_time_ms,
        )
        return response


# ── Input validation ─────────────────────────────────────────────────────────

def _is_sufficient_input(text: str) -> bool:
    """
    Reject inputs that clearly cannot describe a medicine.
    Requires at least 2 words, at least one >= 4 alphabetic characters.
    Prevents nonsense like "papa" or "ok" from returning VERIFIED SAFE.
    """
    words = text.strip().split()
    if len(words) < 2:
        return False
    has_drug_like_word = any(
        len(re.sub(r"[^a-zA-Z]", "", w)) >= 4 for w in words
    )
    return has_drug_like_word


def _insufficient_response(
    request: VerificationRequest,
    request_id: str,
    elapsed_ms: float,
) -> VerificationResponse:
    """Return YELLOW when the input is too vague to verify."""
    return VerificationResponse(
        request_id=request_id,
        session_id=request.session_id,
        extracted_info=ExtractedMedicineInfo(raw_input=request.input_text),
        database_matches=[],
        risk_assessment=RiskAssessment(
            level=RiskLevel.YELLOW,
            score=0.5,
            reasoning=(
                "Input does not contain enough information to verify this medicine. "
                "Please provide the medicine name, manufacturer, and batch number."
            ),
            flags=[],
            citations=[],
        ),
        action_guidance=ActionGuidance(
            summary="More information needed — this medicine cannot be verified.",
            steps=[
                "Check the medicine packaging for the full drug name.",
                "Look for the manufacturer name and country of origin.",
                "Find the batch number (usually printed near the expiry date).",
                "Re-enter the details and try again.",
                "If packaging is unclear or missing, do not dispense — consult a pharmacist.",
            ],
            emergency=False,
        ),
        risk_level=RiskLevel.YELLOW,
        verified=False,
        processing_time_ms=round(elapsed_ms, 2),
        reasoning_trace=["Input rejected: insufficient medicine information provided."],
        disclaimer=_DISCLAIMER,
    )


# ── Error fallback ────────────────────────────────────────────────────────────

def _error_response(
    request: VerificationRequest,
    request_id: str,
    exc: Exception,
    elapsed_ms: float,
    trace: list[str],
) -> VerificationResponse:
    """Return a safe RED response so the API layer never surfaces a raw exception."""
    trace.append(f"ERROR — verification chain failed at step above: {exc!s}")
    return VerificationResponse(
        request_id=request_id,
        session_id=request.session_id,
        extracted_info=ExtractedMedicineInfo(raw_input=request.input_text),
        database_matches=[],
        risk_assessment=RiskAssessment(
            level=RiskLevel.RED,
            score=1.0,
            reasoning=(
                "Verification system error — defaulting to RED for patient safety. "
                f"Error: {exc!s}"
            ),
            flags=[],
            citations=[],
        ),
        action_guidance=ActionGuidance(
            summary="VERIFICATION ERROR — treat this medicine as unverified.",
            steps=[
                "Do NOT dispense this medicine until manual verification is complete.",
                "Contact your pharmacy supervisor or regulatory officer immediately.",
                "Verify manually via WHO GFMD or your national regulatory authority.",
            ],
            contact_authority=(
                "WHO Global Surveillance and Monitoring System: "
                "www.who.int/medicines/regulation/ssffc"
            ),
            emergency=True,
        ),
        risk_level=RiskLevel.RED,
        verified=False,
        processing_time_ms=round(elapsed_ms, 2),
        reasoning_trace=trace,
        disclaimer=_DISCLAIMER,
    )
