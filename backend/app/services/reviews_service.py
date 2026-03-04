"""Review data service — used by reviews_mcp and Monitor agent."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.db.data_store import load_reviews


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_recent_reviews(limit: int = 50, hours: Optional[int] = None) -> list[dict]:
    reviews = load_reviews()
    if hours is not None:
        cutoff = _now_utc() - timedelta(hours=hours)
        reviews = [r for r in reviews if _parse_ts(r.get("date")) and _parse_ts(r.get("date")) >= cutoff]
    return sorted(reviews, key=lambda r: _parse_ts(r.get("date", "")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:limit]


def get_sentiment_trend(hours: int = 24, bucket_hours: int = 4) -> list[dict]:
    reviews = get_recent_reviews(limit=500, hours=hours)
    buckets: dict[str, list[float]] = {}
    now = _now_utc()
    for r in reviews:
        ts = _parse_ts(r.get("date"))
        if ts is None:
            continue
        bucket_key = _bucket_key(ts, now, bucket_hours)
        buckets.setdefault(bucket_key, []).append(float(r.get("sentiment", 0.5)))
    return [
        {"bucket": k, "avg_sentiment": sum(v) / len(v), "count": len(v)}
        for k, v in sorted(buckets.items())
    ]


def get_reviews_by_product(product_id: Optional[str] = None, product_name: Optional[str] = None) -> list[dict]:
    reviews = load_reviews()
    if product_id:
        reviews = [r for r in reviews if r.get("product_id") == product_id]
    if product_name:
        reviews = [r for r in reviews if (r.get("product_name") or "").lower() == product_name.lower()]
    return reviews


def _parse_ts(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        dt = datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _bucket_key(ts: datetime, now: datetime, bucket_hours: int) -> str:
    delta = (now - ts).total_seconds() // 3600
    bucket_start = int(delta // bucket_hours) * bucket_hours
    start_time = now - timedelta(hours=bucket_start)
    return start_time.strftime("%Y-%m-%d %H:00")
