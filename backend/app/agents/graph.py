"""LangGraph pipeline: Monitor -> Investigator -> Action -> Supervisor."""
from typing import Literal

from langgraph.graph import StateGraph, END, START

from app.agents.state import AgentState
from app.agents.monitor import run_monitor
from app.agents.investigator import run_investigator
from app.agents.action import run_action
from app.agents.supervisor import run_supervisor_final


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("monitor", run_monitor)
    graph.add_node("investigator", run_investigator)
    graph.add_node("action", run_action)
    graph.add_node("supervisor", run_supervisor_final)
    graph.add_edge(START, "monitor")
    graph.add_edge("monitor", "investigator")
    graph.add_edge("investigator", "action")
    graph.add_edge("action", "supervisor")
    graph.add_edge("supervisor", END)
    return graph.compile()


_agent_graph = None


def get_agent_graph():
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = build_graph()
    return _agent_graph


def run_agent_graph(job_id: str, trace_callback=None) -> dict:
    """Run full pipeline and return final state. Optional trace_callback(step_dict) for live trace."""
    from app.db.data_store import save_job
    from datetime import datetime

    save_job(job_id, {"status": "running", "started_at": datetime.utcnow().isoformat()})
    graph = get_agent_graph()
    initial: AgentState = {
        "messages": [],
        "trace": [],
        "current_step": None,
    }
    final_state = None
    try:
        for event in graph.stream(initial, stream_mode="values"):
            final_state = event
            if isinstance(event, dict):
                save_job(job_id, {"current_step": event.get("current_step"), "trace": event.get("trace", [])})
                if trace_callback and event.get("trace"):
                    for step in event["trace"]:
                        trace_callback(step)
        save_job(
            job_id,
            {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "result": final_state,
                "trace": final_state.get("trace", []) if final_state else [],
            },
        )
    except Exception as e:
        save_job(job_id, {"status": "failed", "error": str(e), "completed_at": datetime.utcnow().isoformat()})
        raise
    return final_state or initial
