"""Alerts endpoint."""
from fastapi import APIRouter

from app.db.data_store import load_alerts, reload_alerts_from_file
from app.models.schemas import AlertResponse, Severity

router = APIRouter(tags=["alerts"])


@router.get("/alerts")
def get_alerts():
    from datetime import datetime
    reload_alerts_from_file()  # always serve latest (e.g. after agent run)
    alerts = load_alerts()[:20]
    out = []
    for a in alerts:
        ca = a.get("created_at")
        if isinstance(ca, str) and "T" in ca:
            try:
                ca = datetime.fromisoformat(ca.replace("Z", "+00:00"))
            except Exception:
                pass
        out.append(
            AlertResponse(
                id=a.get("id", ""),
                severity=Severity(a.get("severity", "P2")),
                title=a.get("title", ""),
                body=a.get("body", ""),
                created_at=ca,
                routed_to=a.get("routed_to"),
                metadata=a.get("metadata"),
            )
        )
    return out
