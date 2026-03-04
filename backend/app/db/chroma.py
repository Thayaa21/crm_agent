"""ChromaDB vector store for CX documents (tickets, reviews, NPS)."""
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings

COLLECTION_NAME = "cx_intelligence"
EMBEDDING_MODEL = "text-embedding-3-small"


def get_chroma_client():
    settings = get_settings()
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_embeddings():
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=get_settings().openai_api_key)


def get_chroma_store():
    """LangChain Chroma wrapper for retrieval."""
    client = get_chroma_client()
    embeddings = get_embeddings()
    return Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )


def get_raw_collection():
    """Raw Chroma collection for adding documents with metadata."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "CX intelligence documents"},
    )
