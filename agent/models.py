from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class VerificationRequest(BaseModel):
    input_text: str = Field(
        ...,
        description="Free-text input: medicine name, description, batch number, or photo OCR output.",
        min_length=1,
        max_length=2000,
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional client session ID for audit logging.",
    )
    locale: str = Field(
        default="en",
        description="BCP-47 locale for action guidance language (e.g. 'en', 'fr', 'ar').",
    )


class ExtractedMedicineInfo(BaseModel):
    drug_name: Optional[str] = None
    active_ingredient: Optional[str] = None
    manufacturer: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    country_of_origin: Optional[str] = None
    raw_input: str


class DatabaseMatch(BaseModel):
    source: str = Field(
        ...,
        description="Database source: 'WHO', 'FDA', 'EMA', 'regional', or 'batch_alert'.",
    )
    matched: bool
    record_id: Optional[str] = None
    summary: Optional[str] = None
    alert_type: Optional[str] = None
    url: Optional[str] = None
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Retrieval confidence score from Azure AI Search (0-1).",
    )


class AnomalyFlag(BaseModel):
    flag_type: str
    description: str
    severity: RiskLevel


class RiskAssessment(BaseModel):
    level: RiskLevel
    score: float = Field(ge=0.0, le=1.0, description="Normalised risk score (0 = safest, 1 = highest risk).")
    reasoning: str
    flags: list[AnomalyFlag] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)


class ActionGuidance(BaseModel):
    summary: str = Field(description="One-sentence plain-language verdict.")
    steps: list[str] = Field(description="Ordered list of recommended next steps.")
    contact_authority: Optional[str] = None
    emergency: bool = Field(default=False, description="True if immediate action is required.")


class RegulatoryReport(BaseModel):
    report_id: str
    generated_at: datetime
    markdown: str = Field(description="Full report in Markdown for download/print.")
    json_payload: dict = Field(description="Machine-readable version of the report.")


class VerificationResponse(BaseModel):
    request_id: str
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    extracted_info: ExtractedMedicineInfo
    database_matches: list[DatabaseMatch]
    risk_assessment: RiskAssessment
    action_guidance: ActionGuidance
    report: Optional[RegulatoryReport] = None

    risk_level: RiskLevel
    verified: bool = Field(description="True only when risk is GREEN and at least one DB match confirmed.")

    processing_time_ms: Optional[float] = None
    reasoning_trace: list[str] = Field(
        default_factory=list,
        description="Human-readable log of each step's decision, for transparency.",
    )
    disclaimer: str = Field(
        default="",
        description="Regulatory disclaimer — always surfaced to the end user.",
    )
