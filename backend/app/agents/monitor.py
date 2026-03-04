"""Monitor Agent — pulls from data sources via tools, detects anomalies."""
import json
from datetime import datetime

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.agents.tools import MONITOR_TOOLS
from app.agents.state import AgentState
from app.config import get_settings


def create_monitor_agent():
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=get_settings().openai_api_key,
        temperature=0,
    )
    return create_react_agent(llm, MONITOR_TOOLS)


def run_monitor(state: AgentState) -> dict:
    """Run Monitor agent and return updated state with monitor_findings and trace."""
    agent = create_monitor_agent()
    prompt = (
        "You are a CX Monitor Agent. Your job is to detect anomalies across customer feedback. "
        "Use the available tools to: (1) get recent reviews and sentiment trend, (2) get open tickets and ticket volume trend, "
        "(3) get NPS score and trend and detractor feedback. Look for: sentiment spikes (sudden drop), ticket volume spikes, "
        "escalation spikes, or NPS drops. Summarize your findings in a clear report: what anomalies you found, time windows, "
        "and severity. If you see a spike in tickets or negative reviews about the same topic (e.g. checkout failed, iOS), note it."
    )
    result = agent.invoke({"messages": [("user", prompt)]})
    last_message = result["messages"][-1]
    findings = last_message.content if hasattr(last_message, "content") else str(last_message)
    trace_entry = {
        "step": len(state.get("trace", [])) + 1,
        "agent": "monitor",
        "action": "anomaly_detection",
        "summary": findings[:500] + "..." if len(findings) > 500 else findings,
        "timestamp": datetime.utcnow().isoformat(),
    }
    return {
        "monitor_findings": findings,
        "trace": state.get("trace", []) + [trace_entry],
        "current_step": "monitor",
    }
