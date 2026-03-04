"""Investigator Agent — cross-references across channels using ChromaDB, finds root cause."""
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.agents.state import AgentState
from app.config import get_settings
from app.db.chroma import get_chroma_store


def run_investigator(state: AgentState) -> dict:
    """Use ChromaDB retrieval to find root cause from monitor findings."""
    findings = state.get("monitor_findings") or "No findings yet."
    store = get_chroma_store()
    # Retrieve relevant docs based on monitor findings (query = key terms from findings)
    query = findings[:500]  # use start of findings as query
    try:
        docs = store.similarity_search_with_score(query, k=15)
        context = "\n\n".join(
            f"[{i+1}] {d.page_content} (metadata: {d.metadata})"
            for i, (d, _) in enumerate(docs)
        )
    except Exception:
        context = "No relevant documents in vector store."
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=get_settings().openai_api_key,
        temperature=0,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a CX Investigator. Given monitor findings and retrieved evidence from tickets/reviews/NPS, "
         "identify the root cause: same version (e.g. iOS v2.3.1), region (e.g. West Coast), time window. "
         "Output a concise investigation report with: root cause hypothesis, supporting evidence, and confidence."),
        ("user", "Monitor findings:\n{findings}\n\nRetrieved evidence:\n{context}"),
    ])
    chain = prompt | llm | StrOutputParser()
    report = chain.invoke({"findings": findings, "context": context})
    trace_entry = {
        "step": len(state.get("trace", [])) + 1,
        "agent": "investigator",
        "action": "root_cause_analysis",
        "summary": report[:500] + "..." if len(report) > 500 else report,
        "timestamp": datetime.utcnow().isoformat(),
    }
    return {
        "investigation_result": report,
        "trace": state.get("trace", []) + [trace_entry],
        "current_step": "investigator",
    }
