from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from app.models.schemas import SlideDeckRequest, InfographicRequest, DataTableRequest
from app.services.artifact_service import (
    generate_slide_deck, generate_infographic, generate_data_table,
    get_artifacts, export_table_to_csv
)

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.post("/slide-deck")
def create_slide_deck(request: SlideDeckRequest):
    return generate_slide_deck(
        notebook_id=request.notebook_id,
        source_ids=request.source_ids or None,
        instruction=request.instruction or "",
        model_key=request.model_key,
    )


@router.post("/infographic")
def create_infographic(request: InfographicRequest):
    return generate_infographic(
        notebook_id=request.notebook_id,
        source_ids=request.source_ids or None,
        chart_type=request.chart_type,
        instruction=request.instruction or "",
        model_key=request.model_key,
    )


@router.post("/data-table")
def create_data_table(request: DataTableRequest):
    return generate_data_table(
        notebook_id=request.notebook_id,
        source_ids=request.source_ids or None,
        instruction=request.instruction or "",
        model_key=request.model_key,
    )


@router.get("/{notebook_id}")
def list_artifacts(notebook_id: int):
    return get_artifacts(notebook_id)


@router.get("/export-csv/{artifact_id}")
def export_csv(artifact_id: int):
    title, csv_content = export_table_to_csv(artifact_id)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={title}.csv"}
    )
