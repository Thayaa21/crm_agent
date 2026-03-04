"""Supervisor Agent — produces final CX risk summary from all agent outputs."""
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.agents.state import AgentState
from app.config import get_settings
from app.db import data_store as db_store


def run_supervisor_final(state: AgentState) -> dict:
    """Produce final CX risk summary and update dashboard metrics."""
    findings = state.get("monitor_findings") or ""
    investigation = state.get("investigation_result") or ""
    actions = state.get("actions_taken") or ""
    metrics = db_store.load_metrics()
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=get_settings().openai_api_key,
        temperature=0,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the CX Supervisor. Summarize the full pipeline in 2-3 sentences: "
         "key risk, root cause, and actions taken. Then output a CX_HEALTH_SCORE (0-100) and one-sentence recommendation."),
        ("user", "Monitor: {findings}\n\nInvestigation: {investigation}\n\nActions: {actions}\n\nCurrent metrics: {metrics}"),
    ])
    chain = prompt | llm | StrOutputParser()
    summary = chain.invoke({
        "findings": findings,
        "investigation": investigation,
        "actions": actions,
        "metrics": str(metrics),
    })
    # Heuristic: if we had a P0, health drops
    health = max(0, min(100, 100 - (metrics.get("churn_risk", 0) * 0.5)))
    db_store.save_metrics({"cx_health_score": health})
    trace_entry = {
        "step": len(state.get("trace", [])) + 1,
        "agent": "supervisor",
        "action": "final_summary",
        "summary": summary,
        "timestamp": datetime.utcnow().isoformat(),
    }
    return {
        "final_summary": summary,
        "cx_risk_summary": {
            "summary": summary,
            "cx_health_score": health,
            "churn_risk": metrics.get("churn_risk", 0),
            "recommendation": summary.split(".")[-2] + "." if "." in summary else summary,
        },
        "trace": state.get("trace", []) + [trace_entry],
        "current_step": "supervisor",
    }
