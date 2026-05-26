from fastapi import APIRouter, HTTPException
from app.models.schemas import ModelConfigCreate, ModelConfigUpdate
from app.services.model_hub import (
    get_all_models, get_model_by_id, create_model, update_model, delete_model
)

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_models():
    return get_all_models()


@router.get("/{model_id}")
def get_model(model_id: int):
    model = get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("")
def add_model(data: ModelConfigCreate):
    mid = create_model(data.model_dump())
    return get_model_by_id(mid)


@router.put("/{model_id}")
def edit_model(model_id: int, data: ModelConfigUpdate):
    update_model(model_id, data.model_dump(exclude_none=True))
    return get_model_by_id(model_id)


@router.delete("/{model_id}")
def remove_model(model_id: int):
    delete_model(model_id)
    return {"status": "deleted"}
