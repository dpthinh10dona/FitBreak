"""Request-scoped diagnostics for the opt-in live evaluation endpoint."""

from contextvars import ContextVar

trace: ContextVar[dict | None] = ContextVar("live_eval_trace", default=None)
force_gemini_failure: ContextVar[bool] = ContextVar("live_eval_force_gemini_failure", default=False)


def record_model(provider: str, model: str, outcome: str, error_type: str | None = None) -> None:
    current = trace.get()
    if current is not None:
        current["model_events"].append({
            "provider": provider, "model": model, "outcome": outcome,
            "error_type": error_type,
        })


def record_chunks(origin: str, chunks: list[dict], approved: dict) -> None:
    current = trace.get()
    if current is None:
        return
    current["retrieval_origin"] = origin
    current["retrieved_rag_chunks"] = [
        {
            "source_document": approved[chunk["source_id"]]["title"],
            "source_id": chunk["source_id"],
            "chunk_id": chunk.get("chunk_id", chunk.get("id")),
            "similarity_score": chunk.get("similarity"),
            "heading_path": chunk.get("heading_path", chunk.get("title")),
            "page_or_section": chunk.get("page_or_section"),
            "content": chunk.get("content", ""),
        }
        for chunk in chunks
    ]
