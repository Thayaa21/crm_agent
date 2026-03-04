"""Dashboard summary and heatmap endpoints."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.db.data_store import load_tickets, load_metrics, load_reviews, load_alerts, reload_alerts_from_file
from app.models.schemas import DashboardSummary, HeatmapResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _now_utc():
    return datetime.now(timezone.utc)


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary():
    metrics = load_metrics()
    tickets = load_tickets()
    open_count = sum(1 for t in tickets if t.get("status") in ("open", "pending", "new"))
    # Top issues: by category or common theme (simplified: by category key)
    by_cat = defaultdict(int)
    for t in tickets:
        cat = t.get("category") or t.get("issue_type") or "Other"
        by_cat[cat] += 1
    top = [{"category": k, "count": v} for k, v in sorted(by_cat.items(), key=lambda x: -x[1])[:5]]
    return DashboardSummary(
        cx_health_score=metrics.get("cx_health_score", 85),
        churn_risk=metrics.get("churn_risk", 25),
        nps_score=metrics.get("nps_score", 42),
        open_issues_count=open_count,
        top_issues=top,
    )


@router.get("/heatmap", response_model=HeatmapResponse)
def dashboard_heatmap():
    tickets = load_tickets()
    reviews = load_reviews()
    # Build category x time matrix (last 7 days, 6h buckets)
    categories = set()
    bucket_hours = 6
    now = _now_utc()
    buckets = []
    for i in range(28):  # 7 days * 4 buckets per day (oldest first)
        start = now - timedelta(hours=bucket_hours * (28 - i))
        buckets.append(start.strftime("%m/%d %H:00"))
    matrix = defaultdict(lambda: defaultdict(int))

    def bucket_key(ts):
        if not ts:
            return None
        try:
            if isinstance(ts, datetime):
                dt = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
            else:
                s = str(ts)
                if "T" in s:
                    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            delta_h = (now - dt).total_seconds() / 3600
            if delta_h < 0 or delta_h > 7 * 24:
                return None
            # Recent events (small delta_h) -> last bucket; old events -> first buckets
            idx = min(len(buckets) - 1, max(0, int(delta_h // bucket_hours)))
            idx = len(buckets) - 1 - idx
            return buckets[min(idx, len(buckets) - 1)] if 0 <= idx < len(buckets) else None
        except Exception:
            return None

    for t in tickets:
        cat = t.get("category") or t.get("issue_type") or "Other"
        categories.add(cat)
        bk = bucket_key(t.get("created_at"))
        if bk:
            matrix[cat][bk] += 1
    for r in reviews:
        cat = "Reviews"
        categories.add(cat)
        bk = bucket_key(r.get("date"))
        if bk:
            matrix[cat][bk] += 1

    # Include agent-created alerts so "issues" show in the heatmap
    reload_alerts_from_file()
    alerts_list = load_alerts()
    for a in alerts_list:
        bk = bucket_key(a.get("created_at"))
        if not bk:
            bk = buckets[-1] if buckets else None  # fallback: show in most recent bucket
        if bk:
            categories.add("Alerts")
            matrix["Alerts"][bk] += 1

    categories = sorted(categories)
    matrix_list = [[matrix[cat].get(b, 0) for b in buckets] for cat in categories]
    return HeatmapResponse(
        categories=categories,
        time_buckets=buckets,
        matrix=matrix_list,
    )
