"""Agent run and status endpoints."""
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.db.data_store import get_job, save_job
from app.agents.graph import run_agent_graph
from app.models.schemas import (
    AgentRunRequest,
    AgentRunResponse,
    AgentStatus,
    JobStatus,
    TraceStep,
)

router = APIRouter(prefix="/agent", tags=["agent"])
executor = ThreadPoolExecutor(max_workers=2)


def _run_agent_sync(job_id: str) -> None:
    try:
        run_agent_graph(job_id)
    except Exception as e:
        from app.db.data_store import save_job
        from datetime import datetime
        save_job(job_id, {"status": "failed", "error": str(e), "completed_at": datetime.utcnow().isoformat()})


@router.post("/run", response_model=AgentRunResponse)
def agent_run(req: AgentRunRequest):
    job_id = str(uuid.uuid4())
    save_job(job_id, {"status": "pending"})
    executor.submit(_run_agent_sync, job_id)
    return AgentRunResponse(job_id=job_id, status=JobStatus.PENDING, message="Agent run started")


@router.get("/status/{job_id}", response_model=AgentStatus)
def agent_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    status = JobStatus(job.get("status", "pending"))
    return AgentStatus(
        job_id=job_id,
        status=status,
        progress=job.get("current_step"),
        current_step=job.get("current_step"),
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        result=job.get("result"),
        error=job.get("error"),
    )


@router.get("/trace/{job_id}")
def agent_trace(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    trace = job.get("trace", [])
    return {"job_id": job_id, "trace": trace}
