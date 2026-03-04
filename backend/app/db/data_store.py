"""In-memory / file-backed store for tickets, NPS, reviews, and alerts. Shared by MCP and API."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import get_settings


def _data_path(name: str) -> Path:
    return Path(get_settings().data_dir) / f"{name}.json"


def _load(name: str, default: Any) -> Any:
    p = _data_path(name)
    if not p.exists():
        return default
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return default


def _save(name: str, data: Any) -> None:
    p = _data_path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(data, f, indent=2, default=str)


# --- Tickets ---
_tickets: list[dict] = []
_tickets_loaded = False


def load_tickets() -> list[dict]:
    global _tickets, _tickets_loaded
    if not _tickets_loaded:
        _tickets = _load("tickets", [])
        _tickets_loaded = True
    return _tickets


def save_tickets(tickets: list[dict]) -> None:
    global _tickets
    _tickets = tickets
    _save("tickets", tickets)


# --- NPS ---
_nps: list[dict] = []
_nps_loaded = False


def load_nps() -> list[dict]:
    global _nps, _nps_loaded
    if not _nps_loaded:
        _nps = _load("nps", [])
        _nps_loaded = True
    return _nps


def save_nps(nps: list[dict]) -> None:
    global _nps
    _nps = nps
    _save("nps", nps)


# --- Reviews ---
_reviews: list[dict] = []
_reviews_loaded = False


def load_reviews() -> list[dict]:
    global _reviews, _reviews_loaded
    if not _reviews_loaded:
        _reviews = _load("reviews", [])
        _reviews_loaded = True
    return _reviews


def save_reviews(reviews: list[dict]) -> None:
    global _reviews
    _reviews = reviews
    _save("reviews", reviews)


# --- Alerts (agent-generated) ---
_alerts: list[dict] = []
_alerts_loaded = False


def load_alerts() -> list[dict]:
    global _alerts, _alerts_loaded
    if not _alerts_loaded:
        _alerts = _load("alerts", [])
        _alerts_loaded = True
    return _alerts


def save_alert(alert: dict) -> None:
    alerts = load_alerts()
    alert.setdefault("id", f"alert-{len(alerts) + 1}")
    alert.setdefault("created_at", datetime.utcnow().isoformat())
    alerts.insert(0, alert)
    _save("alerts", alerts)
    global _alerts
    _alerts = alerts


def reload_alerts_from_file() -> None:
    """Reload alerts from disk so GET /alerts always returns latest (e.g. after agent run)."""
    global _alerts
    _alerts = _load("alerts", [])


# --- Agent jobs (status, trace) ---
_jobs: dict[str, dict] = {}
_jobs_loaded = False


def _jobs_path() -> Path:
    return _data_path("jobs")


def load_jobs() -> dict[str, dict]:
    global _jobs, _jobs_loaded
    if not _jobs_loaded:
        _jobs = _load("jobs", {})
        _jobs_loaded = True
    return _jobs


def save_job(job_id: str, data: dict) -> None:
    jobs = load_jobs()
    jobs[job_id] = {**jobs.get(job_id, {}), **data}
    _save("jobs", jobs)
    global _jobs
    _jobs = jobs


def get_job(job_id: str) -> dict | None:
    return load_jobs().get(job_id)


# --- Dashboard metrics (updated by agent) ---
_metrics: dict = {}
_metrics_loaded = False


def load_metrics() -> dict:
    global _metrics, _metrics_loaded
    if not _metrics_loaded:
        _metrics = _load("metrics", {
            "cx_health_score": 85.0,
            "churn_risk": 25.0,
            "nps_score": 42.0,
            "open_issues_count": 0,
        })
        _metrics_loaded = True
    return _metrics


def save_metrics(metrics: dict) -> None:
    global _metrics
    current = load_metrics()
    current.update(metrics)
    _metrics = current
    _save("metrics", current)


def get_data_store():
    """Return a simple namespace for use in dependency injection."""
    class Store:
        tickets = property(lambda _: load_tickets())
        nps = property(lambda _: load_nps())
        reviews = property(lambda _: load_reviews())
        alerts = property(lambda _: load_alerts())
        jobs = property(lambda _: load_jobs())
        metrics = property(lambda _: load_metrics())
        save_tickets = staticmethod(save_tickets)
        save_nps = staticmethod(save_nps)
        save_reviews = staticmethod(save_reviews)
        save_alert = staticmethod(save_alert)
        save_job = staticmethod(save_job)
        save_metrics = staticmethod(save_metrics)
        get_job = staticmethod(get_job)
    return Store()
