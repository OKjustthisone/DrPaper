import json
from app.models.database import get_db
from app.services.vector_store import query_chunks
from app.services.model_hub import resolve_llm
from langchain_core.messages import HumanMessage, SystemMessage


def _get_sources_context(notebook_id: int, source_ids: list[int] | None = None) -> str:
    """Get aggregated text from sources for artifact generation."""
    results = query_chunks(notebook_id, "summary overview key findings methodology results conclusion", source_ids or None, n_results=30)
    if not results or not results["documents"] or not results["documents"][0]:
        return ""
    parts = []
    for i, doc in enumerate(results["documents"][0], 1):
        meta = results["metadatas"][0][i-1] if results["metadatas"] else {}
        src = meta.get("source", "unknown")
        page = meta.get("page", "")
        parts.append(f"[Chunk {i}] {src} (Page {page}):\n{doc}")
    return "\n\n".join(parts)


def generate_slide_deck(notebook_id: int, source_ids: list[int] | None, instruction: str, model_key: str | None) -> dict:
    context = _get_sources_context(notebook_id, source_ids)
    if not context:
        return {"title": "No content", "slides": []}

    llm = resolve_llm(model_key)

    prompt = f"""Based on the provided research sources, create a presentation slide deck.

{instruction if instruction else "Focus on the key findings, methodology, and conclusions."}

SOURCES:
{context}

Generate a structured slide deck in JSON format. The response must be pure JSON:
{{
  "title": "Presentation Title",
  "slides": [
    {{
      "title": "Slide Title",
      "bullet_points": ["Point 1", "Point 2", "Point 3"],
      "notes": "Optional speaker notes"
    }}
  ]
}}

Rules:
- 6-10 slides
- Each slide has 3-5 bullet points
- Include: Title slide, Background/Motivation, Methods, Key Results, Discussion, Conclusions
- Bullet points should be concise and data-rich
- Return ONLY JSON, no other text."""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        text = response.content
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3].strip()
            else:
                text = text.rsplit("\n```", 1)[0].strip()
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {
            "title": "Slide Deck",
            "slides": [
                {"title": "Parsing Error", "bullet_points": ["AI response could not be parsed as JSON.", response.content[:500]], "notes": ""}
            ]
        }

    conn = get_db()
    conn.execute(
        "INSERT INTO artifacts (notebook_id, artifact_type, title, data_json) VALUES (?, ?, ?, ?)",
        (notebook_id, "slide_deck", result.get("title", "Slide Deck"), json.dumps(result))
    )
    conn.commit()
    conn.close()

    return result


def generate_infographic(notebook_id: int, source_ids: list[int] | None, chart_type: str, instruction: str, model_key: str | None) -> dict:
    context = _get_sources_context(notebook_id, source_ids)
    if not context:
        return {"chart_type": chart_type, "title": "No content", "nodes": []}

    llm = resolve_llm(model_key)

    chart_configs = {
        "bento_grid": "Bento Grid layout: Organize key findings into visually distinct card-like nodes. Each node should be a key insight or data point.",
        "timeline": "Timeline layout: Arrange research developments, experimental steps, or findings in chronological order.",
        "comparison": "Comparison layout: Create a side-by-side comparison of different methods, compounds, studies, or approaches.",
    }

    prompt = f"""Based on the provided research sources, create an infographic in '{chart_type}' style.

{chart_configs.get(chart_type, "")}

{instruction if instruction else ""}

SOURCES:
{context}

Generate a structured infographic in JSON format. The response must be pure JSON:
{{
  "title": "Infographic Title",
  "nodes": [
    {{
      "id": "node_1",
      "title": "Node Title",
      "content": "Detailed content for this node",
      "icon": "flask" | "chart" | "brain" | "dna" | "pill" | "microscope" | "target" | "lightbulb",
      "color": "#hexcolor",
      "connections": ["node_2", "node_3"]
    }}
  ]
}}

Rules:
- 5-10 nodes
- Choose meaningful icons from: flask, chart, brain, dna, pill, microscope, target, lightbulb, document, beaker
- Assign distinct colors to each node
- For timeline: connections show chronological flow
- For comparison: each node is a comparison item
- For bento: nodes are standalone insight cards
- Return ONLY JSON, no other text."""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3].strip()
            else:
                text = text.rsplit("\n```", 1)[0].strip()
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {
            "chart_type": chart_type,
            "title": "Infographic",
            "nodes": [{"id": "err", "title": "Error", "content": response.content[:300], "icon": "brain", "color": "#FF6B6B", "connections": []}]
        }

    conn = get_db()
    conn.execute(
        "INSERT INTO artifacts (notebook_id, artifact_type, title, data_json) VALUES (?, ?, ?, ?)",
        (notebook_id, f"infographic_{chart_type}", result.get("title", "Infographic"), json.dumps(result))
    )
    conn.commit()
    conn.close()

    return result


def generate_data_table(notebook_id: int, source_ids: list[int] | None, instruction: str, model_key: str | None) -> dict:
    context = _get_sources_context(notebook_id, source_ids)
    if not context:
        return {"title": "No content", "columns": [], "rows": []}

    llm = resolve_llm(model_key)

    prompt = f"""Based on the provided research sources, extract and organize data into a structured comparison table.

{instruction if instruction else "Extract all quantitative data points and create a comprehensive comparison table."}

SOURCES:
{context}

Generate a structured data table in JSON format. The response must be pure JSON:
{{
  "title": "Table Title",
  "columns": ["Column1", "Column2", "Column3", ...],
  "rows": [
    ["Row1Value1", "Row1Value2", "Row1Value3", ...],
    ["Row2Value1", "Row2Value2", "Row2Value3", ...]
  ]
}}

Rules:
- Columns should include: Study/Compound/Method names, numerical values, units
- Extract exact numbers from the sources where possible
- 5-20 rows depending on available data
- Include units in column headers
- Return ONLY JSON, no other text."""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3].strip()
            else:
                text = text.rsplit("\n```", 1)[0].strip()
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {
            "title": "Data Table",
            "columns": ["Error"],
            "rows": [[response.content[:500]]]
        }

    conn = get_db()
    conn.execute(
        "INSERT INTO artifacts (notebook_id, artifact_type, title, data_json) VALUES (?, ?, ?, ?)",
        (notebook_id, "data_table", result.get("title", "Data Table"), json.dumps(result))
    )
    conn.commit()
    conn.close()

    return result


def get_artifacts(notebook_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM artifacts WHERE notebook_id = ? ORDER BY created_at DESC",
        (notebook_id,)
    ).fetchall()
    conn.close()
    return [{"id": r["id"], "type": r["artifact_type"], "title": r["title"], "data": json.loads(r["data_json"]), "created_at": r["created_at"]} for r in rows]


def export_table_to_csv(artifact_id: int) -> tuple[str, str]:
    conn = get_db()
    row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    conn.close()
    if not row:
        raise ValueError("Artifact not found")
    data = json.loads(row["data_json"])
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(data.get("columns", []))
    for r in data.get("rows", []):
        writer.writerow(r)
    return row["title"], output.getvalue()
