"""Pydantic schemas for API and agent state."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


# --- Agent API ---
class AgentRunRequest(BaseModel):
    pass


class AgentRunResponse(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.PENDING
    message: str = "Agent run started"


class AgentStatus(BaseModel):
    job_id: str
    status: JobStatus
    progress: Optional[str] = None
    current_step: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error: Optional[str] = None


class TraceStep(BaseModel):
    step: int
    agent: str
    action: str
    summary: str
    timestamp: datetime
    payload: Optional[dict] = None


# --- Dashboard ---
class DashboardSummary(BaseModel):
    cx_health_score: float = Field(ge=0, le=100)
    churn_risk: float = Field(ge=0, le=100)
    nps_score: float
    open_issues_count: int
    top_issues: list[dict] = []


class HeatmapBucket(BaseModel):
    category: str
    time_bucket: str
    count: int


class HeatmapResponse(BaseModel):
    categories: list[str]
    time_buckets: list[str]
    matrix: list[list[int]]


# --- Alerts ---
class AlertResponse(BaseModel):
    id: str
    severity: Severity
    title: str
    body: str
    created_at: datetime
    routed_to: Optional[str] = None
    metadata: Optional[dict] = None


# --- Chat ---
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    citations: list[str] = []
