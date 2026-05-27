import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.database import get_db
from app.services.literature_search import search_papers, fetch_full_text
from app.services.document_parser import parse_file
from app.services.vector_store import add_chunks
from app.config import UPLOADS_DIR

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search_literature(q: str, sources: str = "pmc,openalex,arxiv", page: int = 1, limit: int = 10):
    """Search across selected literature databases."""
    source_list = [s.strip() for s in sources.split(",") if s.strip()]
    if not source_list:
        raise HTTPException(status_code=400, detail="No sources specified")
    return search_papers(q, source_list, page, limit)


class ImportRequest(BaseModel):
    notebook_id: int
    paper_id: str
    title: str = ""


@router.post("/import")
def import_paper(req: ImportRequest):
    """Fetch full text of a paper and import it into a notebook."""
    full_text = fetch_full_text(req.paper_id)
    if not full_text or len(full_text) < 20:
        raise HTTPException(status_code=400, detail="Failed to fetch full text")

    safe_title = req.title.strip() or req.paper_id.replace(":", "_")
    safe_title = "".join(c for c in safe_title if c.isalnum() or c in "._- ")[:80]
    filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.txt"
    file_path = os.path.join(UPLOADS_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    chunks = parse_file(file_path)
    chunks = [{"text": c["text"], "metadata": c.get("metadata", {"source": filename})} for c in chunks]

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO sources (notebook_id, filename, file_type, file_size, file_path, chunk_count, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (req.notebook_id, filename, ".txt", len(full_text), file_path, len(chunks), "processing")
    )
    conn.commit()
    source_id = cursor.lastrowid

    try:
        added = add_chunks(req.notebook_id, source_id, chunks)
        conn.execute("UPDATE sources SET chunk_count = ?, status = 'ready' WHERE id = ?", (added, source_id))
        conn.commit()
    except Exception as e:
        conn.execute("UPDATE sources SET status = ? WHERE id = ?", (f"error: {str(e)}", source_id))
        conn.commit()

    row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    conn.close()
    return dict(row)
