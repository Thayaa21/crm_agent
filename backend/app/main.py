"""FastAPI application for CRM Agent."""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env from project root so OPENAI_API_KEY is set when running from backend/
_root = Path(__file__).resolve().parent.parent.parent  # backend/app -> backend -> project root
load_dotenv(_root / ".env")

from app.config import get_settings, ensure_dirs
from app.api.routes import agent, dashboard, alerts, chat, data_upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs(get_settings())
    yield


# CORS: local dev + deployed frontend (set FRONTEND_URL on the host, e.g. https://your-app.onrender.com)
_cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if os.getenv("FRONTEND_URL"):
    _cors_origins.append(os.getenv("FRONTEND_URL").rstrip("/"))

app = FastAPI(
    title="CRM Agent",
    description="Enterprise Customer Experience Intelligence Agent",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(dashboard.router)
app.include_router(alerts.router)
app.include_router(chat.router)
app.include_router(data_upload.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "CRM Agent API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
