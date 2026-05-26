import os
import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import CHROMA_DIR

os.environ["ANONYMIZED_TELEMETRY"] = "False"

_client = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_or_create_collection(notebook_id: int):
    client = get_chroma_client()
    name = f"nb_{notebook_id}"
    try:
        return client.get_collection(name=name)
    except Exception:
        return client.create_collection(name=name, metadata={"hnsw:space": "cosine"})


def delete_collection(notebook_id: int):
    client = get_chroma_client()
    try:
        client.delete_collection(name=f"nb_{notebook_id}")
    except Exception:
        pass


def add_chunks(notebook_id: int, source_id: int, chunks: list[dict]) -> int:
    collection = get_or_create_collection(notebook_id)
    ids = []
    documents = []
    metadatas = []
    for chunk in chunks:
        cid = f"{source_id}_{uuid.uuid4().hex[:12]}"
        ids.append(cid)
        documents.append(chunk["text"])
        meta = dict(chunk.get("metadata", {}))
        meta["source_id"] = str(source_id)
        metadatas.append(meta)
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def delete_source_chunks(notebook_id: int, source_id: int):
    collection = get_or_create_collection(notebook_id)
    try:
        results = collection.get(where={"source_id": str(source_id)})
        if results and results["ids"]:
            collection.delete(ids=results["ids"])
    except Exception:
        pass


def query_chunks(notebook_id: int, query: str, source_ids: list[int] | None = None, n_results: int = 10):
    collection = get_or_create_collection(notebook_id)
    where_filter = None
    if source_ids:
        where_filter = {"source_id": {"$in": [str(sid) for sid in source_ids]}}
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )
        return results
    except Exception as e:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


def get_chunk_count(notebook_id: int) -> int:
    try:
        collection = get_or_create_collection(notebook_id)
        return collection.count()
    except Exception:
        return 0
