"""Upload user data (CSV/JSON) to replace or append tickets, reviews, or NPS."""
import csv
import io
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.db.data_store import (
    load_tickets,
    load_nps,
    load_reviews,
    save_tickets,
    save_nps,
    save_reviews,
)

router = APIRouter(prefix="/data", tags=["data"])

DataKind = Literal["tickets", "reviews", "nps"]
Mode = Literal["replace", "append"]


def _norm_date(v: str) -> str:
    """Normalise date string to ISO-like for storage."""
    if not v or not str(v).strip():
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = str(v).strip()
    if "T" in s or " " in s:
        return s.replace(" ", "T")[:19] + ("Z" if "Z" not in s and "+" not in s else "")
    if len(s) >= 10:
        return s[:10] + "T00:00:00Z"
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm_num(v, default=0):
    try:
        return float(v) if v is not None and str(v).strip() != "" else default
    except (TypeError, ValueError):
        return default


def _get(r: dict, *keys, default=""):
    for k in keys:
        for alias in (k, k.lower(), k.replace("_", " "), k.replace(" ", "_")):
            if isinstance(r, dict) and alias in r and r[alias] is not None:
                return str(r[alias]).strip()
    return default


def parse_tickets(rows: list[dict]) -> list[dict]:
    out = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        r = {k.strip().lower().replace(" ", "_"): v for k, v in row.items()}
        if not r:
            continue
        subject = _get(r, "subject", "title", "summary") or f"Ticket {i+1}"
        body = _get(r, "body", "description", "content") or subject
        out.append({
            "id": _get(r, "id") or f"TKT-U{10000 + i}",
            "subject": subject,
            "body": body,
            "category": _get(r, "category", "issue_type", "type") or "Other",
            "status": _get(r, "status") or "open",
            "priority": _get(r, "priority") or "P2",
            "region": _get(r, "region", "location") or "Unknown",
            "created_at": _norm_date(_get(r, "created_at", "date", "created")),
            "escalated": _get(r, "escalated", "priority") in ("1", "true", "True", "P0", "P1", "yes"),
            "metadata": {},
        })
    return out


def parse_reviews(rows: list[dict]) -> list[dict]:
    out = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        r = {k.strip().lower().replace(" ", "_"): v for k, v in row.items()}
        if not r:
            continue
        text = _get(r, "text", "body", "review_body", "content", "review") or _get(r, "comment") or ""
        if not text:
            continue
        sent = _get(r, "sentiment", "rating", "score")
        out.append({
            "id": _get(r, "id") or f"REV-U{20000 + i}",
            "text": text[:2000],
            "sentiment": _norm_num(sent, 0.5) if sent else 0.5,
            "product_name": _get(r, "product_name", "product") or "Unknown",
            "product_id": _get(r, "product_id") or f"prod-{i}",
            "date": _norm_date(_get(r, "date", "created_at", "created")),
            "region": _get(r, "region", "location") or "Unknown",
        })
    return out


def parse_nps(rows: list[dict]) -> list[dict]:
    out = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        r = {k.strip().lower().replace(" ", "_"): v for k, v in row.items()}
        if not r:
            continue
        score_str = _get(r, "score", "nps", "rating")
        score = int(_norm_num(score_str, 0))
        if score < 0 or score > 10:
            score = 0
        out.append({
            "id": _get(r, "id") or f"NPS-U{30000 + i}",
            "score": score,
            "feedback": _get(r, "feedback", "comment", "text", "body") or "",
            "date": _norm_date(_get(r, "date", "created_at", "created")),
            "region": _get(r, "region", "location") or "Unknown",
        })
    return out


@router.post("/upload")
async def upload_data(
    kind: DataKind = Form(...),
    mode: Mode = Form("replace"),
    file: UploadFile = File(...),
):
    """Upload CSV or JSON file for tickets, reviews, or NPS. mode: replace (default) or append."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    raw = await file.read()
    try:
        raw_str = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text (CSV or JSON).")
    rows: list[dict] = []
    if file.filename.lower().endswith(".json") or raw_str.startswith("["):
        try:
            data = json.loads(raw_str)
            rows = data if isinstance(data, list) else data.get("data", data.get("rows", [data]))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    else:
        try:
            reader = csv.DictReader(io.StringIO(raw_str))
            rows = list(reader)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV: {e}")
    if not rows:
        raise HTTPException(status_code=400, detail="No rows in file.")
    if kind == "tickets":
        parsed = parse_tickets(rows)
        existing = load_tickets() if mode == "append" else []
        save_tickets(existing + parsed)
        return {"ok": True, "kind": "tickets", "rows_uploaded": len(parsed), "total_now": len(existing) + len(parsed)}
    if kind == "reviews":
        parsed = parse_reviews(rows)
        existing = load_reviews() if mode == "append" else []
        save_reviews(existing + parsed)
        return {"ok": True, "kind": "reviews", "rows_uploaded": len(parsed), "total_now": len(existing) + len(parsed)}
    if kind == "nps":
        parsed = parse_nps(rows)
        existing = load_nps() if mode == "append" else []
        save_nps(existing + parsed)
        return {"ok": True, "kind": "nps", "rows_uploaded": len(parsed), "total_now": len(existing) + len(parsed)}
    raise HTTPException(status_code=400, detail=f"Unknown kind: {kind}")


@router.get("/formats")
def get_formats():
    """Return expected column names and types for each data kind (for UI help)."""
    return {
        "tickets": {
            "required": ["subject or title", "body or description"],
            "optional": ["id", "category", "status", "priority", "region", "created_at", "escalated"],
            "note": "CSV or JSON. Headers can vary (e.g. title→subject, description→body).",
        },
        "reviews": {
            "required": ["text or body or review_body"],
            "optional": ["id", "sentiment", "product_name", "product_id", "date", "region"],
            "note": "CSV or JSON. sentiment 0–1 optional.",
        },
        "nps": {
            "required": ["score (0–10)"],
            "optional": ["id", "feedback", "date", "region"],
            "note": "CSV or JSON.",
        },
    }
