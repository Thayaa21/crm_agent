"""LangGraph agent state."""
from typing import Annotated, Any, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    monitor_findings: Optional[str]
    investigation_result: Optional[str]
    actions_taken: Optional[str]
    final_summary: Optional[str]
    cx_risk_summary: Optional[dict]
    trace: Annotated[list[dict], lambda a, b: a + b]
    next_agent: Optional[Literal["monitor", "investigator", "action", "supervisor", "end"]]
    current_step: Optional[str]
