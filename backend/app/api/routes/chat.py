"""Chat Q&A with source citations."""
from fastapi import APIRouter

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.db.chroma import get_chroma_store
from app.config import get_settings
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    store = get_chroma_store()
    docs = store.similarity_search_with_score(req.message, k=5)
    context = "\n\n".join(
        f"[Source {i+1}] {d.page_content}"
        for i, (d, _) in enumerate(docs)
    )
    citations = [f"{d.metadata}" for d, _ in docs]
    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=get_settings().openai_api_key,
        temperature=0,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the user's question using ONLY the provided context. "
         "Cite sources by number [1], [2], etc. If the context does not contain the answer, say so."),
        ("user", "Context:\n{context}\n\nQuestion: {question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context, "question": req.message})
    return ChatResponse(
        answer=answer,
        sources=[{"index": i + 1, "metadata": docs[i][0].metadata} for i in range(len(docs))],
        citations=citations,
    )
