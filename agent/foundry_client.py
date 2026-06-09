"""
foundry_client.py — Azure AI Search (Foundry IQ) + Azure AI Foundry (GPT-4o) clients.

Two clients are exposed:
  FoundryIQClient    — parallel knowledge-base queries via Azure AI Search
  FoundryAgentClient — LLM reasoning steps via AsyncAzureOpenAI
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import structlog

from agent.models import (
    ActionGuidance,
    AnomalyFlag,
    DatabaseMatch,
    ExtractedMedicineInfo,
    RegulatoryReport,
    RiskAssessment,
    RiskLevel,
    VerificationResponse,
)

log = structlog.get_logger(__name__)

# ── Credentials ───────────────────────────────────────────────────────────────

_FOUNDRY_ENDPOINT = os.getenv("AZURE_FOUNDRY_ENDPOINT", "")
_FOUNDRY_API_KEY  = os.getenv("AZURE_FOUNDRY_API_KEY", "")
_FOUNDRY_DEPLOY   = os.getenv("AZURE_FOUNDRY_DEPLOYMENT", "gpt-4o")
_FOUNDRY_VERSION  = os.getenv("AZURE_FOUNDRY_API_VERSION", "2024-08-01-preview")

_SEARCH_ENDPOINT  = os.getenv("AZURE_SEARCH_ENDPOINT", "")
_SEARCH_API_KEY   = os.getenv("AZURE_SEARCH_API_KEY", "")
_SEARCH_INDEX     = os.getenv("AZURE_SEARCH_INDEX_NAME", "saferx-medicines")

MOCK_MODE: bool = not all([_FOUNDRY_ENDPOINT, _FOUNDRY_API_KEY, _SEARCH_ENDPOINT, _SEARCH_API_KEY])

# Lazy-imported only when not in mock mode
if not MOCK_MODE:  # pragma: no cover
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents.aio import SearchClient as AzureSearchClient
    from openai import AsyncAzureOpenAI


# ── Mock data ─────────────────────────────────────────────────────────────────

_GREEN_MATCHES: list[DatabaseMatch] = [
    DatabaseMatch(
        source="WHO_GFMD",
        matched=True,
        record_id="WHO-2024-AMX-001",
        summary="Registered product — no active WHO alerts or quality complaints on file.",
        confidence=0.97,
    ),
    DatabaseMatch(
        source="FDA",
        matched=True,
        record_id="FDA-NDA-050716",
        summary="FDA-approved. Current GMP certificate valid. No recalls in last 5 years.",
        confidence=0.95,
    ),
    DatabaseMatch(source="EMA",          matched=False, confidence=0.0),
    DatabaseMatch(source="REGIONAL",     matched=False, confidence=0.0),
    DatabaseMatch(source="BATCH_ALERTS", matched=False, confidence=0.0),
]

_YELLOW_MATCHES: list[DatabaseMatch] = [
    DatabaseMatch(
        source="WHO_GFMD",
        matched=True,
        record_id="WHO-ALERT-2025-114",
        summary="Suspect packaging variant reported in West Africa — investigation open.",
        alert_type="SUSPECT_QUALITY",
        confidence=0.82,
    ),
    DatabaseMatch(source="FDA", matched=False, confidence=0.0),
    DatabaseMatch(source="EMA", matched=False, confidence=0.0),
    DatabaseMatch(
        source="REGIONAL",
        matched=True,
        record_id="NAFDAC-2025-0881",
        summary="NAFDAC issued quality query; product hold pending lab analysis.",
        alert_type="UNDER_INVESTIGATION",
        confidence=0.74,
    ),
    DatabaseMatch(source="BATCH_ALERTS", matched=False, confidence=0.0),
]

_RED_MATCHES: list[DatabaseMatch] = [
    DatabaseMatch(
        source="WHO_GFMD",
        matched=True,
        record_id="WHO-ALERT-2024-778",
        summary="CONFIRMED COUNTERFEIT. Product seized across 12 countries. Do not dispense.",
        alert_type="COUNTERFEIT_CONFIRMED",
        url="https://www.who.int/medicines/publications/drugalerts/alert_sample",
        confidence=0.99,
    ),
    DatabaseMatch(
        source="FDA",
        matched=True,
        record_id="FDA-RECALL-2024-112233",
        summary="Class I Recall: subpotent active ingredient confirmed. Immediate quarantine.",
        alert_type="CLASS_I_RECALL",
        confidence=0.98,
    ),
    DatabaseMatch(source="EMA", matched=False, confidence=0.0),
    DatabaseMatch(source="REGIONAL", matched=False, confidence=0.0),
    DatabaseMatch(
        source="BATCH_ALERTS",
        matched=True,
        record_id="BATCH-BX7741C",
        summary="Batch BX7741C in WHO Rapid Alert System — quarantine all units immediately.",
        alert_type="BATCH_RECALL",
        confidence=0.99,
    ),
]


def _mock_matches_for(drug_name: str, batch_number: Optional[str]) -> list[DatabaseMatch]:
    """Choose GREEN / YELLOW / RED mock set based on whole-word keyword matching."""
    text = f"{drug_name or ''} {batch_number or ''}".lower()

    def _has(keywords: tuple[str, ...]) -> bool:
        return any(re.search(rf"\b{re.escape(k)}\b", text) for k in keywords)

    if _has(("counterfeit", "fake", "seized", "red", "bx7741")):
        return _RED_MATCHES
    if _has(("suspect", "recall", "yellow", "query", "hold")):
        return _YELLOW_MATCHES
    return _GREEN_MATCHES


# ── FoundryIQClient ───────────────────────────────────────────────────────────

_SOURCES = ["WHO_GFMD", "FDA", "EMA", "REGIONAL", "BATCH_ALERTS"]


class FoundryIQClient:
    """
    Queries the saferx-medicines Azure AI Search index.
    Each source filter is queried in parallel; results are combined into
    a flat list of DatabaseMatch objects.
    """

    def __init__(self) -> None:
        self._mock = MOCK_MODE
        if not self._mock:  # pragma: no cover
            self._credential = AzureKeyCredential(_SEARCH_API_KEY)
        log.info("foundry_iq.init", mock=self._mock, index=_SEARCH_INDEX)

    def _make_search_client(self) -> "AzureSearchClient":  # pragma: no cover
        return AzureSearchClient(
            endpoint=_SEARCH_ENDPOINT,
            index_name=_SEARCH_INDEX,
            credential=self._credential,
        )

    async def _query_source(
        self,
        source: str,
        drug_name: str,
        manufacturer: Optional[str],
        batch_number: Optional[str],
        country: Optional[str],
    ) -> list[DatabaseMatch]:
        """Run one source-filtered search and map results to DatabaseMatch."""
        if self._mock:
            await asyncio.sleep(0)  # yield to event loop
            return []  # real selection happens in verify_drug for mock mode

        query_text = " ".join(filter(None, [drug_name, manufacturer, batch_number, country]))
        odata_filter = f"source eq '{source}'"

        try:  # pragma: no cover
            async with self._make_search_client() as client:
                results = await client.search(
                    search_text=query_text,
                    filter=odata_filter,
                    top=5,
                    select=["record_id", "source", "drug_name", "summary",
                            "alert_type", "url", "manufacturer", "batch_number"],
                )
                matches: list[DatabaseMatch] = []
                async for doc in results:
                    score = doc.get("@search.score", 0.0)
                    matches.append(
                        DatabaseMatch(
                            source=source,
                            matched=score > 0.5,
                            record_id=doc.get("record_id"),
                            summary=doc.get("summary"),
                            alert_type=doc.get("alert_type"),
                            url=doc.get("url"),
                            confidence=min(score / 10.0, 1.0),
                        )
                    )
                if not matches:
                    matches = [DatabaseMatch(source=source, matched=False, confidence=0.0)]
                log.debug("foundry_iq.source_result", source=source, hits=len(matches))
                return matches
        except Exception as exc:  # pragma: no cover
            log.warning("foundry_iq.source_error", source=source, error=str(exc))
            return [DatabaseMatch(source=source, matched=False, confidence=0.0)]

    async def verify_drug(
        self,
        drug_name: str,
        manufacturer: Optional[str] = None,
        batch_number: Optional[str] = None,
        country: Optional[str] = None,
        raw_input: Optional[str] = None,
    ) -> list[DatabaseMatch]:
        """
        Run all source queries in parallel and return a flat list of DatabaseMatch.
        One entry per source is guaranteed even on partial failure.
        raw_input is used in mock mode so keyword detection works against the full
        original text, not just the extracted drug_name / batch_number fields.
        """
        if self._mock:
            log.info("foundry_iq.mock_verify", drug=drug_name, batch=batch_number)
            return _mock_matches_for(raw_input or drug_name, batch_number)

        tasks = [  # pragma: no cover
            self._query_source(src, drug_name, manufacturer, batch_number, country)
            for src in _SOURCES
        ]
        results: list[list[DatabaseMatch]] = await asyncio.gather(*tasks, return_exceptions=False)
        flat = [match for group in results for match in group]
        log.info("foundry_iq.verify_done", drug=drug_name, total_matches=len(flat))
        return flat


# ── LLM prompt helpers ────────────────────────────────────────────────────────

_EXTRACT_SYSTEM = """\
You are a pharmaceutical data extraction assistant.
Extract structured information from the raw medicine text the user provides.
Return ONLY valid JSON — no markdown fences, no commentary — matching exactly:
{
  "drug_name": string | null,
  "active_ingredient": string | null,
  "manufacturer": string | null,
  "batch_number": string | null,
  "expiry_date": string | null,
  "dosage_form": string | null,
  "strength": string | null,
  "country_of_origin": string | null,
  "raw_input": string
}
Set a field to null if not present in the text."""

_ANOMALY_SYSTEM = """\
You are a pharmaceutical safety analyst specialising in counterfeit detection.
Given extracted medicine info and database search results, identify anomalies and assign a risk level.
Return ONLY valid JSON matching exactly:
{
  "level": "GREEN" | "YELLOW" | "RED",
  "score": 0.0-1.0,
  "reasoning": string,
  "flags": [{"flag_type": string, "description": string, "severity": "GREEN"|"YELLOW"|"RED"}],
  "citations": [string]
}
GREEN = verified safe. YELLOW = suspicious, needs investigation. RED = confirmed threat, do not dispense."""

_GUIDANCE_SYSTEM = """\
You are a pharmaceutical safety advisor writing for frontline healthcare workers.
Based on the risk assessment provided, generate clear, actionable guidance.
Respond in the language specified. Return ONLY valid JSON:
{
  "summary": string,
  "steps": [string],
  "contact_authority": string | null,
  "emergency": boolean
}"""

_REPORT_SYSTEM = """\
You are a regulatory affairs specialist.
Generate a formal verification report in Markdown and structured JSON.
Return ONLY valid JSON:
{
  "report_id": string,
  "generated_at": "ISO-8601 datetime",
  "markdown": string,
  "json_payload": object
}
The markdown should follow ICH E3 reporting conventions and include: Summary, Drug Details,
Database Findings, Risk Assessment, Recommended Actions, and Regulatory Contacts."""


# ── FoundryAgentClient ────────────────────────────────────────────────────────

class FoundryAgentClient:
    """
    Wraps AsyncAzureOpenAI for the 4 LLM reasoning steps.
    Falls back to rule-based mock implementations in development.
    """

    def __init__(self) -> None:
        self._mock = MOCK_MODE
        if not self._mock:  # pragma: no cover
            self._llm = AsyncAzureOpenAI(
                azure_endpoint=_FOUNDRY_ENDPOINT,
                api_key=_FOUNDRY_API_KEY,
                api_version=_FOUNDRY_VERSION,
            )
        log.info("foundry_agent.init", mock=self._mock, deployment=_FOUNDRY_DEPLOY)

    async def _chat_json(self, system: str, user: str, temperature: float = 0.1) -> dict[str, Any]:
        """Send a JSON-mode chat completion and parse the result."""
        response = await self._llm.chat.completions.create(  # pragma: no cover
            model=_FOUNDRY_DEPLOY,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)

    # ── Step 1: Extract ───────────────────────────────────────────────────────

    async def extract_medicine_info(self, raw_text: str) -> ExtractedMedicineInfo:
        log.info("agent.extract", chars=len(raw_text))
        if self._mock:
            return _mock_extract(raw_text)

        data = await self._chat_json(_EXTRACT_SYSTEM, raw_text)  # pragma: no cover
        data["raw_input"] = raw_text
        return ExtractedMedicineInfo(**data)

    # ── Step 3: Anomaly reasoning ─────────────────────────────────────────────

    async def assess_anomalies(
        self,
        extracted_info: ExtractedMedicineInfo,
        database_matches: list[DatabaseMatch],
    ) -> RiskAssessment:
        log.info("agent.assess", drug=extracted_info.drug_name)
        if self._mock:
            return _mock_assess(database_matches)

        user_payload = json.dumps(  # pragma: no cover
            {
                "extracted_info": extracted_info.model_dump(),
                "database_matches": [m.model_dump() for m in database_matches],
            },
            indent=2,
        )
        data = await self._chat_json(_ANOMALY_SYSTEM, user_payload)
        flags = [AnomalyFlag(**f) for f in data.pop("flags", [])]
        return RiskAssessment(**data, flags=flags)

    # ── Step 5: Action guidance ───────────────────────────────────────────────

    async def generate_action_guidance(
        self,
        risk_assessment: RiskAssessment,
        language: str = "en",
    ) -> ActionGuidance:
        log.info("agent.guidance", level=risk_assessment.level, lang=language)
        if self._mock:
            return _mock_guidance(risk_assessment.level)

        user_payload = json.dumps(  # pragma: no cover
            {"risk_assessment": risk_assessment.model_dump(), "language": language},
            indent=2,
        )
        data = await self._chat_json(_GUIDANCE_SYSTEM, user_payload)
        return ActionGuidance(**data)

    # ── Step 6: Regulatory report ─────────────────────────────────────────────

    async def generate_regulatory_report(
        self,
        verification_response: VerificationResponse,
    ) -> RegulatoryReport:
        log.info("agent.report", request_id=verification_response.request_id)
        if self._mock:
            return _mock_report(verification_response)

        user_payload = verification_response.model_dump_json(indent=2)  # pragma: no cover
        data = await self._chat_json(_REPORT_SYSTEM, user_payload, temperature=0.2)
        return RegulatoryReport(**data)


# ── Mock implementations ──────────────────────────────────────────────────────

def _mock_extract(raw_text: str) -> ExtractedMedicineInfo:
    """Simple regex-based extraction for development."""
    batch = re.search(r"\b([A-Z]{2}\d{4,}[A-Z]?)\b", raw_text)
    exp   = re.search(r"(?:exp(?:iry)?|best before)[:\s]*(\d{2}[/-]\d{4}|\d{4}[/-]\d{2})", raw_text, re.I)
    words = raw_text.split()
    return ExtractedMedicineInfo(
        drug_name=words[0] if words else None,
        manufacturer=next((w for w in words if w.istitle() and len(w) > 4), None),
        batch_number=batch.group(1) if batch else None,
        expiry_date=exp.group(1) if exp else None,
        raw_input=raw_text,
    )


def _mock_assess(matches: list[DatabaseMatch]) -> RiskAssessment:
    """Derive risk from database match alert types."""
    red_types   = {"COUNTERFEIT_CONFIRMED", "CLASS_I_RECALL", "BATCH_RECALL"}
    yellow_types = {"SUSPECT_QUALITY", "UNDER_INVESTIGATION"}

    flags: list[AnomalyFlag] = []
    citations: list[str] = []
    highest = RiskLevel.GREEN
    score = 0.1

    for m in matches:
        if not m.matched:
            continue
        if m.url:
            citations.append(m.url)
        if m.record_id:
            citations.append(m.record_id)
        if m.alert_type in red_types:
            highest = RiskLevel.RED
            score = max(score, 0.92)
            flags.append(AnomalyFlag(
                flag_type=m.alert_type or "UNKNOWN",
                description=m.summary or "Critical alert found.",
                severity=RiskLevel.RED,
            ))
        elif m.alert_type in yellow_types:
            if highest != RiskLevel.RED:
                highest = RiskLevel.YELLOW
            score = max(score, 0.55)
            flags.append(AnomalyFlag(
                flag_type=m.alert_type or "UNKNOWN",
                description=m.summary or "Suspicious record found.",
                severity=RiskLevel.YELLOW,
            ))

    reasoning_map = {
        RiskLevel.GREEN:  "All queried databases returned no alerts. Product appears legitimate.",
        RiskLevel.YELLOW: "One or more databases flagged this product for investigation. Do not dispense until cleared.",
        RiskLevel.RED:    "Critical alert confirmed. Product is associated with recalls or counterfeiting. Quarantine immediately.",
    }
    return RiskAssessment(
        level=highest,
        score=score,
        reasoning=reasoning_map[highest],
        flags=flags,
        citations=list(dict.fromkeys(citations)),
    )


def _mock_guidance(level: RiskLevel) -> ActionGuidance:
    if level == RiskLevel.GREEN:
        return ActionGuidance(
            summary="This medicine appears authentic and safe to dispense.",
            steps=[
                "Proceed with dispensing according to standard protocols.",
                "Retain batch documentation for routine audit trail.",
                "Report any patient-reported side effects through normal channels.",
            ],
            emergency=False,
        )
    if level == RiskLevel.YELLOW:
        return ActionGuidance(
            summary="This medicine is under investigation — do not dispense until cleared.",
            steps=[
                "Quarantine the product and do not dispense to patients.",
                "Record the batch number, manufacturer, and supplier details.",
                "Contact your national regulatory authority to report and seek guidance.",
                "Await official clearance before releasing stock.",
            ],
            contact_authority="Your national medicines regulatory authority (e.g. WHO GFMD: www.who.int/medicines)",
            emergency=False,
        )
    return ActionGuidance(
        summary="CRITICAL: This medicine is confirmed counterfeit or recalled. Do not dispense.",
        steps=[
            "Immediately quarantine ALL units from this batch.",
            "Do not dispense to any patients.",
            "Notify your supervisor and pharmacy manager now.",
            "Report to your national regulatory authority and WHO immediately.",
            "Preserve evidence (packaging, invoices, supplier records) for investigation.",
            "If patients have already received this product, contact them and their clinicians.",
        ],
        contact_authority="WHO Global Surveillance and Monitoring System: www.who.int/medicines/regulation/ssffc",
        emergency=True,
    )


def _mock_report(vr: VerificationResponse) -> RegulatoryReport:
    report_id = f"SAFERX-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    drug = vr.extracted_info.drug_name or "Unknown"
    level = vr.risk_level.value

    alert_rows = "\n".join(
        f"| {m.source} | {'Yes' if m.matched else 'No'} | {m.alert_type or '—'} | {m.summary or '—'} |"
        for m in vr.database_matches
    )

    md = f"""# SafeRx Verification Report
**Report ID:** {report_id}
**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}
**Request ID:** {vr.request_id}

---

## 1. Summary

**Risk Level: {level}**
{vr.action_guidance.summary}

---

## 2. Drug Details

| Field | Value |
|---|---|
| Drug Name | {vr.extracted_info.drug_name or '—'} |
| Active Ingredient | {vr.extracted_info.active_ingredient or '—'} |
| Manufacturer | {vr.extracted_info.manufacturer or '—'} |
| Batch Number | {vr.extracted_info.batch_number or '—'} |
| Expiry Date | {vr.extracted_info.expiry_date or '—'} |
| Dosage Form | {vr.extracted_info.dosage_form or '—'} |
| Strength | {vr.extracted_info.strength or '—'} |
| Country of Origin | {vr.extracted_info.country_of_origin or '—'} |

---

## 3. Database Findings

| Source | Match | Alert Type | Summary |
|---|---|---|---|
{alert_rows}

---

## 4. Risk Assessment

**Level:** {vr.risk_assessment.level.value}
**Score:** {vr.risk_assessment.score:.2f}
**Reasoning:** {vr.risk_assessment.reasoning}

{"### Anomaly Flags" if vr.risk_assessment.flags else ""}
{"".join(f"- **{f.flag_type}** ({f.severity.value}): {f.description}" + chr(10) for f in vr.risk_assessment.flags)}

---

## 5. Recommended Actions

{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(vr.action_guidance.steps))}

{f"**Contact:** {vr.action_guidance.contact_authority}" if vr.action_guidance.contact_authority else ""}

---

*This report was generated by SafeRx AI. It is intended to support — not replace — professional regulatory judgement.*
"""

    return RegulatoryReport(
        report_id=report_id,
        generated_at=now,
        markdown=md.strip(),
        json_payload={
            "request_id": vr.request_id,
            "drug": vr.extracted_info.model_dump(),
            "risk": vr.risk_assessment.model_dump(mode="json"),
            "matches": [m.model_dump() for m in vr.database_matches],
            "guidance": vr.action_guidance.model_dump(),
        },
    )
