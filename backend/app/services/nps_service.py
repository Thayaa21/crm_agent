"""NPS data service — used by nps_mcp and Monitor agent."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.db.data_store import load_nps


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_current_nps_score() -> float:
    nps_list = load_nps()
    if not nps_list:
        return 0.0
    # Use last 30 days
    cutoff = _now_utc() - timedelta(days=30)
    scores = [
        int(r.get("score", 0))
        for r in nps_list
        if _parse_ts(r.get("date")) and _parse_ts(r.get("date")) >= cutoff
    ]
    if not scores:
        return 0.0
    promoters = sum(1 for s in scores if s >= 9)
    detractors = sum(1 for s in scores if s <= 6)
    n = len(scores)
    return round(100 * (promoters - detractors) / n, 1) if n else 0.0


def get_nps_trend(days: int = 30, bucket_days: int = 7) -> list[dict]:
    nps_list = load_nps()
    cutoff = _now_utc() - timedelta(days=days)
    buckets: dict[str, list[int]] = {}
    for r in nps_list:
        ts = _parse_ts(r.get("date"))
        if ts is None or ts < cutoff:
            continue
        key = ts.strftime("%Y-%m-%d")[:10]
        # Group by week
        bucket = _week_bucket(ts)
        buckets.setdefault(bucket, []).append(int(r.get("score", 0)))
    return [
        {
            "bucket": k,
            "nps": round(100 * (_promoters(v) - _detractors(v)) / len(v), 1) if v else 0,
            "count": len(v),
        }
        for k, v in sorted(buckets.items())
    ]


def get_detractor_feedback(limit: int = 50) -> list[dict]:
    _min = datetime.min.replace(tzinfo=timezone.utc)
    nps_list = [r for r in load_nps() if int(r.get("score", 0)) <= 6 and r.get("feedback")]
    return sorted(nps_list, key=lambda r: _parse_ts(r.get("date", "")) or _min, reverse=True)[:limit]


def _parse_ts(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        if "T" in str(s):
            return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        dt = datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _week_bucket(ts: datetime) -> str:
    start = ts - timedelta(days=ts.weekday())
    return start.strftime("%Y-%m-%d")


def _promoters(scores: list[int]) -> float:
    return sum(1 for s in scores if s >= 9) / len(scores) if scores else 0


def _detractors(scores: list[int]) -> float:
    return sum(1 for s in scores if s <= 6) / len(scores) if scores else 0
