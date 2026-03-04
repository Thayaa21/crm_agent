"""LangChain tools wrapping MCP data services (used by Monitor agent)."""
from langchain_core.tools import tool

from app.services import nps_service, reviews_service, tickets_service


@tool
def get_recent_reviews(limit: int = 50, hours: int | None = None) -> str:
    """Get most recent customer reviews. Use limit and optional hours to filter."""
    import json
    data = reviews_service.get_recent_reviews(limit=limit, hours=hours)
    return json.dumps(data, default=str)


@tool
def get_sentiment_trend(hours: int = 24, bucket_hours: int = 4) -> str:
    """Get average sentiment trend over time buckets."""
    import json
    data = reviews_service.get_sentiment_trend(hours=hours, bucket_hours=bucket_hours)
    return json.dumps(data, default=str)


@tool
def get_reviews_by_product(product_id: str | None = None, product_name: str | None = None) -> str:
    """Get reviews filtered by product_id or product_name."""
    import json
    data = reviews_service.get_reviews_by_product(product_id=product_id, product_name=product_name)
    return json.dumps(data, default=str)


@tool
def get_open_tickets(limit: int = 100, priority: str | None = None) -> str:
    """Get open support tickets, optionally by priority (P0, P1, P2)."""
    import json
    data = tickets_service.get_open_tickets(limit=limit, priority=priority)
    return json.dumps(data, default=str)


@tool
def get_ticket_volume_trend(hours: int = 24, bucket_hours: int = 2) -> str:
    """Get ticket volume over time buckets."""
    import json
    data = tickets_service.get_ticket_volume_trend(hours=hours, bucket_hours=bucket_hours)
    return json.dumps(data, default=str)


@tool
def get_escalated_tickets(limit: int = 50) -> str:
    """Get escalated tickets."""
    import json
    data = tickets_service.get_escalated_tickets(limit=limit)
    return json.dumps(data, default=str)


@tool
def get_current_nps_score() -> str:
    """Get current NPS score (last 30 days)."""
    return str(nps_service.get_current_nps_score())


@tool
def get_nps_trend(days: int = 30, bucket_days: int = 7) -> str:
    """Get NPS trend over time."""
    import json
    data = nps_service.get_nps_trend(days=days, bucket_days=bucket_days)
    return json.dumps(data, default=str)


@tool
def get_detractor_feedback(limit: int = 50) -> str:
    """Get feedback from detractors (score <= 6)."""
    import json
    data = nps_service.get_detractor_feedback(limit=limit)
    return json.dumps(data, default=str)


MONITOR_TOOLS = [
    get_recent_reviews,
    get_sentiment_trend,
    get_reviews_by_product,
    get_open_tickets,
    get_ticket_volume_trend,
    get_escalated_tickets,
    get_current_nps_score,
    get_nps_trend,
    get_detractor_feedback,
]
