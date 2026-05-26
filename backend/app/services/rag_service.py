import json
from app.models.database import get_db
from app.services.vector_store import query_chunks
from app.services.model_hub import resolve_llm
from langchain_core.messages import HumanMessage, SystemMessage


def grounded_chat(notebook_id: int, message: str, source_ids: list[int] | None = None, model_key: str | None = None) -> dict:
    # 1. Get notebook system prompt
    conn = get_db()
    nb = conn.execute("SELECT * FROM notebooks WHERE id = ?", (notebook_id,)).fetchone()
    conn.close()
    if not nb:
        raise ValueError("Notebook not found")

    system_prompt = nb["system_prompt"] or "You are a helpful research assistant. Answer questions based on the provided sources."

    # 2. Retrieve relevant chunks
    results = query_chunks(notebook_id, message, source_ids or None, n_results=15)

    retrieved_chunks = []
    if results and results["documents"] and results["documents"][0]:
        for i in range(len(results["ids"][0])):
            retrieved_chunks.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            })

    # 3. Build context
    if not retrieved_chunks:
        answer = "No relevant information found in the selected sources. Please check your source selection or upload relevant documents."
        return {"answer": answer, "citations": []}

    context_parts = []
    citation_map = []
    for idx, chunk in enumerate(retrieved_chunks, 1):
        source_id = chunk["metadata"].get("source_id", "unknown")
        filename = chunk["metadata"].get("source", "unknown")
        page = chunk["metadata"].get("page", None)
        context_parts.append(f"[{idx}] Source: {filename} (Page {page})\n{chunk['text']}")
        citation_map.append({
            "index": idx,
            "source_id": int(source_id) if source_id and source_id != "unknown" else 0,
            "filename": filename,
            "chunk_id": chunk["id"],
            "text": chunk["text"][:300],
            "page": int(page) if page else None,
        })

    context = "\n\n".join(context_parts)

    # 4. Call LLM
    llm = resolve_llm(model_key)

    full_system_prompt = f"""{system_prompt}

IMPORTANT RULES:
1. Only answer based on the provided sources below. Do NOT use outside knowledge.
2. When you use information from a source, cite it with its citation number in brackets like [1], [2], etc.
3. Every factual claim must have a citation.
4. If the sources don't contain the answer, say "No relevant information found in the current sources."
5. Be precise and quote key data points from the sources.

SOURCES:
{context}"""

    messages = [
        SystemMessage(content=full_system_prompt),
        HumanMessage(content=message),
    ]
    response = llm.invoke(messages)

    # 5. Save to chat history
    conn = get_db()
    conn.execute(
        "INSERT INTO chat_history (notebook_id, role, content, citations_json) VALUES (?, ?, ?, ?)",
        (notebook_id, "user", message, "[]")
    )
    conn.execute(
        "INSERT INTO chat_history (notebook_id, role, content, citations_json) VALUES (?, ?, ?, ?)",
        (notebook_id, "assistant", response.content, json.dumps(citation_map))
    )
    conn.commit()
    conn.close()

    return {"answer": response.content, "citations": citation_map}


def get_chat_history(notebook_id: int, limit: int = 50):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM chat_history WHERE notebook_id = ? ORDER BY created_at DESC LIMIT ?",
        (notebook_id, limit)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"], "citations": json.loads(r["citations_json"] or "[]"), "time": r["created_at"]} for r in reversed(rows)]
