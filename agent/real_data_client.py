"""
real_data_client.py — live pharmaceutical safety data from public sources.

Two sources, queried independently so one outage never blocks the other:
  openFDA Drug Enforcement API  — live recall/enforcement records, no auth required
  WHO Medical Product Alerts    — scraped + in-memory cached (1h TTL)

Standalone module: not wired into VerificationOrchestrator. The orchestrator
still runs on FoundryIQClient (mock or Azure AI Search). This client is for
callers that explicitly want a live, real-data cross-check.

Note on field mapping: DatabaseMatch (agent/models.py) doesn't have separate
match_type / details / citation_url / flagged fields — it uses alert_type,
summary, url, and matched. Records here are "flagged" by setting alert_type
to a non-None value (the convention orchestrator._safety_escalate relies on);
unflagged matches keep alert_type=None.
"""
from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Optional

import httpx
import structlog

from agent.models import DatabaseMatch

log = structlog.get_logger(__name__)

FDA_API_BASE = "https://api.fda.gov"
_FDA_ENFORCEMENT_PATH = "/drug/enforcement.json"

WHO_ALERTS_URL = (
    "https://www.who.int/teams/regulation-prequalification/incidents-and-SF/"
    "full-list-of-who-medical-product-alerts"
)

HTTP_TIMEOUT = 5.0
WHO_CACHE_TTL_SECONDS = 3600

# ── FDA classification → risk mapping ──────────────────────────────────────────

_FDA_CONFIDENCE_BY_CLASS = {"Class I": 0.95, "Class II": 0.75, "Class III": 0.5}
_FDA_ALERT_TYPE_BY_CLASS = {
    "Class I": "CLASS_I_RECALL",
    "Class II": "CLASS_II_RECALL",
    "Class III": "CLASS_III_RECALL",
}
_FDA_FLAGGED_CLASSES = {"Class I", "Class II"}

_FDA_CITATION_URL = "https://www.accessdata.fda.gov/scripts/enforcement/enforce_rpt-Product-Tabs.cfm"


def _map_fda_result(result: dict[str, Any]) -> DatabaseMatch:
    classification = result.get("classification", "")
    product_description = result.get("product_description", "—")
    reason = result.get("reason_for_recall", "—")
    status = result.get("status", "—")
    flagged = classification in _FDA_FLAGGED_CLASSES

    return DatabaseMatch(
        source="FDA_ENFORCEMENT",
        matched=True,
        record_id=result.get("recall_number"),
        summary=f"{product_description} - {reason} - Status: {status}",
        alert_type=_FDA_ALERT_TYPE_BY_CLASS.get(classification) if flagged else None,
        url=_FDA_CITATION_URL,
        confidence=_FDA_CONFIDENCE_BY_CLASS.get(classification, 0.3),
    )


async def _fetch_fda(client: httpx.AsyncClient, search_query: str, limit: int) -> list[dict[str, Any]]:
    """Run one openFDA search. Returns [] on any failure or zero-result 404."""
    try:
        resp = await client.get(
            f"{FDA_API_BASE}{_FDA_ENFORCEMENT_PATH}",
            params={"search": search_query, "limit": limit},
            timeout=HTTP_TIMEOUT,
        )
        if resp.status_code == 404:
            # openFDA returns 404 (not an empty array) when nothing matches.
            return []
        resp.raise_for_status()
        return resp.json().get("results", [])
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        log.warning("fda.fetch_error", query=search_query, error=str(exc))
        return []


async def search_fda_recalls(drug_name: str) -> list[DatabaseMatch]:
    """Search openFDA enforcement records by product description, falling back to recalling firm."""
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        results = await _fetch_fda(client, f'product_description:"{drug_name}"', limit=10)
        if not results:
            results = await _fetch_fda(client, f'recalling_firm:"{drug_name}"', limit=10)
    log.info("fda.search_recalls", drug=drug_name, hits=len(results))
    return [_map_fda_result(r) for r in results]


async def search_fda_by_batch(batch_number: str) -> list[DatabaseMatch]:
    """Search openFDA enforcement records by lot/batch number."""
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        results = await _fetch_fda(client, f'lot_number:"{batch_number}"', limit=5)
    log.info("fda.search_by_batch", batch=batch_number, hits=len(results))
    return [_map_fda_result(r) for r in results]


# ── WHO Medical Product Alerts (scraped + cached) ──────────────────────────────

_who_cache: dict[str, Any] = {"data": None, "fetched_at": 0.0}

_LINK_PATTERN = re.compile(r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>[^<]+)</a>', re.IGNORECASE)
_DATE_PATTERN = re.compile(r"\b(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{4})\b")


def _parse_who_html(html: str) -> list[dict[str, Any]]:
    """
    Best-effort regex scrape of the WHO alerts listing page.
    Skips anything that doesn't look like an alert link rather than raising —
    the page markup is not a stable contract.
    """
    alerts: list[dict[str, Any]] = []
    for match in _LINK_PATTERN.finditer(html):
        title = match.group("title").strip()
        href = match.group("href").strip()
        if len(title) < 8:
            continue
        if "alert" not in href.lower() and "alert" not in title.lower():
            continue
        date_match = _DATE_PATTERN.search(title)
        url = href if href.startswith("http") else f"https://www.who.int{href}"
        alerts.append({
            "drug_name": title,
            "alert_type": "medical_product_alert",
            "date": date_match.group(0) if date_match else None,
            "url": url,
        })
    return alerts


async def _fetch_who_alerts() -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(WHO_ALERTS_URL)
            resp.raise_for_status()
            html = resp.text
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        log.warning("who.fetch_error", error=str(exc))
        return []
    return _parse_who_html(html)


async def get_who_alerts_cached() -> list[dict[str, Any]]:
    """In-memory cache of the WHO alerts list, refreshed at most once per hour."""
    now = time.time()
    if _who_cache["data"] is not None and (now - _who_cache["fetched_at"]) < WHO_CACHE_TTL_SECONDS:
        return _who_cache["data"]

    alerts = await _fetch_who_alerts()
    _who_cache["data"] = alerts
    _who_cache["fetched_at"] = now
    log.info("who.cache_refreshed", alert_count=len(alerts))
    return alerts


async def search_who_alerts(drug_name: str) -> list[DatabaseMatch]:
    """Filter the cached WHO alert list for titles mentioning drug_name."""
    alerts = await get_who_alerts_cached()
    name_lower = drug_name.lower()

    matches: list[DatabaseMatch] = []
    for alert in alerts:
        if name_lower not in alert["drug_name"].lower():
            continue
        summary = alert["drug_name"]
        if alert.get("date"):
            summary = f"{summary} ({alert['date']})"
        matches.append(DatabaseMatch(
            source="WHO_GFMD",
            matched=True,
            record_id=None,
            summary=summary,
            alert_type="WHO_PRODUCT_ALERT",
            url=alert["url"],
            confidence=0.98,
        ))

    log.info("who.search_alerts", drug=drug_name, hits=len(matches))
    return matches


# ── Combined ────────────────────────────────────────────────────────────────────

async def verify_drug_realworld(drug_name: str, batch_number: Optional[str] = None) -> dict[str, Any]:
    """
    Query openFDA and WHO in parallel (plus a batch-number lookup if provided).
    A single source failing never blocks the others — failures degrade to
    empty results, logged as warnings.
    """
    log.info("realworld.verify.start", drug=drug_name, batch=batch_number)

    tasks = [search_fda_recalls(drug_name), search_who_alerts(drug_name)]
    query_count = 2
    if batch_number:
        tasks.append(search_fda_by_batch(batch_number))
        query_count += 1

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_matches: list[DatabaseMatch] = []
    for result in results:
        if isinstance(result, Exception):
            log.warning("realworld.verify.task_error", error=str(result))
            continue
        all_matches.extend(result)

    log.info("realworld.verify.complete", drug=drug_name, total_matches=len(all_matches))
    return {
        "matches": all_matches,
        "sources_checked": ["FDA Enforcement", "WHO GFMD"],
        "real_data": True,
        "query_count": query_count,
    }


class RealDataClient:
    """Instance wrapper around the module-level openFDA/WHO query functions, for orchestrator use."""

    async def search_fda_recalls(self, drug_name: str) -> list[DatabaseMatch]:
        return await search_fda_recalls(drug_name)

    async def search_fda_by_batch(self, batch_number: str) -> list[DatabaseMatch]:
        return await search_fda_by_batch(batch_number)

    async def search_who_alerts(self, drug_name: str) -> list[DatabaseMatch]:
        return await search_who_alerts(drug_name)

    async def verify_drug_realworld(self, drug_name: str, batch_number: Optional[str] = None) -> dict[str, Any]:
        return await verify_drug_realworld(drug_name, batch_number)
