import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models.database import get_db
from app.services.document_parser import parse_file, save_upload
from app.services.vector_store import add_chunks, delete_source_chunks

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.post("/upload")
def upload_source(notebook_id: int = Form(...), file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Save uploaded file
    content = file.file.read()
    file_path = save_upload(content, file.filename)
    file_size = len(content)

    # Get file type
    ext = os.path.splitext(file.filename)[1].lower()

    # Parse file into chunks
    chunks = parse_file(file_path)

    # Save source record
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO sources (notebook_id, filename, file_type, file_size, file_path, chunk_count, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (notebook_id, file.filename, ext, file_size, file_path, len(chunks), "processing")
    )
    conn.commit()
    source_id = cursor.lastrowid

    # Add chunks to vector store
    try:
        added = add_chunks(notebook_id, source_id, chunks)
        conn.execute("UPDATE sources SET chunk_count = ?, status = 'ready' WHERE id = ?", (added, source_id))
        conn.commit()
    except Exception as e:
        conn.execute("UPDATE sources SET status = ? WHERE id = ?", (f"error: {str(e)}", source_id))
        conn.commit()

    row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    conn.close()
    return dict(row)


@router.get("")
def list_sources(notebook_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sources WHERE notebook_id = ? ORDER BY created_at DESC",
        (notebook_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.delete("/{source_id}")
def delete_source(source_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Source not found")

    notebook_id = row["notebook_id"]
    file_path = row["file_path"]

    # Delete chunks from vector store
    delete_source_chunks(notebook_id, source_id)

    # Delete uploaded file
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}
