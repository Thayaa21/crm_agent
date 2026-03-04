"""Action Agent — drafts alerts, response templates, updates churn risk, routes to team."""
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.agents.state import AgentState
from app.config import get_settings
from app.db.data_store import save_alert, save_metrics


def run_action(state: AgentState) -> dict:
    """Produce P0/P1/P2 alert, customer response template, route, and update churn risk."""
    findings = state.get("monitor_findings") or ""
    investigation = state.get("investigation_result") or ""
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=get_settings().openai_api_key,
        temperature=0,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a CX Action Agent. Given monitor findings and investigation report, produce:\n"
         "1. SEVERITY: P0 (critical), P1 (high), or P2 (medium). Use P0 for widespread checkout/outage issues.\n"
         "2. ALERT_TITLE: Short title for the alert.\n"
         "3. ALERT_BODY: 2-3 sentence description.\n"
         "4. CUSTOMER_RESPONSE_TEMPLATE: A short template support can use to reply to affected customers.\n"
         "5. ROUTE_TO: Which team (e.g. Engineering, Support, Product).\n"
         "6. CHURN_RISK_DELTA: A number to add to current churn risk (e.g. +40 for P0 crisis).\n"
         "Output in this exact format:\nSEVERITY: ...\nALERT_TITLE: ...\nALERT_BODY: ...\nCUSTOMER_RESPONSE_TEMPLATE: ...\nROUTE_TO: ...\nCHURN_RISK_DELTA: ..."),
        ("user", "Findings:\n{findings}\n\nInvestigation:\n{investigation}"),
    ])
    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke({"findings": findings, "investigation": investigation})
    # Parse structured output
    severity = "P1"
    title = "CX Anomaly Detected"
    body = raw
    template = ""
    route_to = "Support"
    churn_delta = 20
    for line in raw.split("\n"):
        line = line.strip()
        if line.upper().startswith("SEVERITY:"):
            severity = line.split(":", 1)[1].strip()[:10] or "P1"
        elif line.upper().startswith("ALERT_TITLE:"):
            title = line.split(":", 1)[1].strip()
        elif line.upper().startswith("ALERT_BODY:"):
            body = line.split(":", 1)[1].strip()
        elif line.upper().startswith("CUSTOMER_RESPONSE_TEMPLATE:"):
            template = line.split(":", 1)[1].strip()
        elif line.upper().startswith("ROUTE_TO:"):
            route_to = line.split(":", 1)[1].strip()
        elif line.upper().startswith("CHURN_RISK_DELTA:"):
            try:
                churn_delta = int(line.split(":", 1)[1].strip().replace("+", "").strip() or "0")
            except ValueError:
                churn_delta = 20
    # Persist alert
    from app.db.data_store import load_metrics
    metrics = load_metrics()
    new_churn = min(100, metrics.get("churn_risk", 25) + churn_delta)
    save_alert({
        "severity": severity,
        "title": title,
        "body": body,
        "routed_to": route_to,
        "metadata": {"customer_response_template": template, "investigation": investigation[:300]},
    })
    save_metrics({"churn_risk": new_churn})
    actions_taken = (
        f"Created {severity} alert: {title}. Routed to {route_to}. "
        f"Churn risk updated to {new_churn}%. Customer response template: {template[:100]}..."
    )
    trace_entry = {
        "step": len(state.get("trace", [])) + 1,
        "agent": "action",
        "action": "alert_and_route",
        "summary": actions_taken,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {"severity": severity, "route_to": route_to, "churn_risk": new_churn},
    }
    return {
        "actions_taken": actions_taken,
        "trace": state.get("trace", []) + [trace_entry],
        "current_step": "action",
    }
