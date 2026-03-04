"""Ticket data service — used by tickets_mcp and Monitor agent."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.db.data_store import load_tickets


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_open_tickets(limit: int = 100, priority: Optional[str] = None) -> list[dict]:
    tickets = [t for t in load_tickets() if t.get("status") in ("open", "pending", "new")]
    if priority:
        tickets = [t for t in tickets if t.get("priority") == priority]
    return sorted(tickets, key=lambda t: _parse_ts(t.get("created_at", "")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:limit]


def get_ticket_volume_trend(hours: int = 24, bucket_hours: int = 2) -> list[dict]:
    tickets = load_tickets()
    now = _now_utc()
    cutoff = now - timedelta(hours=hours)
    buckets: dict[str, int] = {}
    for t in tickets:
        ts = _parse_ts(t.get("created_at"))
        if ts is None or ts < cutoff:
            continue
        bucket_key = _bucket_key(ts, now, bucket_hours)
        buckets[bucket_key] = buckets.get(bucket_key, 0) + 1
    return [{"bucket": k, "count": v} for k, v in sorted(buckets.items())]


def get_escalated_tickets(limit: int = 50) -> list[dict]:
    tickets = [t for t in load_tickets() if t.get("escalated") is True]
    return sorted(tickets, key=lambda t: _parse_ts(t.get("created_at", "")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:limit]


def _parse_ts(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        if isinstance(s, datetime):
            return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
        if "T" in str(s):
            return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        dt = datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _bucket_key(ts: datetime, now: datetime, bucket_hours: int) -> str:
    delta = (now - ts).total_seconds() // 3600
    bucket_start = int(delta // bucket_hours) * bucket_hours
    start_time = now - timedelta(hours=bucket_start)
    return start_time.strftime("%Y-%m-%d %H:00")
