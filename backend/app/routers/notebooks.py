from fastapi import APIRouter, HTTPException
from app.models.database import get_db
from app.models.schemas import NotebookCreate, NotebookUpdate, NotebookResponse
from app.services.vector_store import delete_collection

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])


@router.post("")
def create_notebook(data: NotebookCreate):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO notebooks (name, description, system_prompt) VALUES (?, ?, ?)",
        (data.name, data.description or "", data.system_prompt or "")
    )
    conn.commit()
    nb_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM notebooks WHERE id = ?", (nb_id,)).fetchone()
    conn.close()
    return dict(row)


@router.get("")
def list_notebooks():
    conn = get_db()
    rows = conn.execute("SELECT * FROM notebooks ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{notebook_id}")
def get_notebook(notebook_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM notebooks WHERE id = ?", (notebook_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return dict(row)


@router.put("/{notebook_id}")
def update_notebook(notebook_id: int, data: NotebookUpdate):
    conn = get_db()
    row = conn.execute("SELECT * FROM notebooks WHERE id = ?", (notebook_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Notebook not found")

    fields = []
    values = []
    for key in ["name", "description", "system_prompt"]:
        val = getattr(data, key)
        if val is not None:
            fields.append(f"{key} = ?")
            values.append(val)
    if fields:
        fields.append("updated_at = datetime('now')")
        values.append(notebook_id)
        conn.execute(f"UPDATE notebooks SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    row = conn.execute("SELECT * FROM notebooks WHERE id = ?", (notebook_id,)).fetchone()
    conn.close()
    return dict(row)


@router.delete("/{notebook_id}")
def delete_notebook(notebook_id: int):
    conn = get_db()
    conn.execute("DELETE FROM sources WHERE notebook_id = ?", (notebook_id,))
    conn.execute("DELETE FROM chat_history WHERE notebook_id = ?", (notebook_id,))
    conn.execute("DELETE FROM artifacts WHERE notebook_id = ?", (notebook_id,))
    conn.execute("DELETE FROM notebooks WHERE id = ?", (notebook_id,))
    conn.commit()
    conn.close()
    delete_collection(notebook_id)
    return {"status": "deleted"}
