from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class NotebookCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    system_prompt: Optional[str] = ""


class NotebookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None


class NotebookResponse(BaseModel):
    id: int
    name: str
    description: str
    system_prompt: str
    created_at: str
    updated_at: str


class SourceResponse(BaseModel):
    id: int
    notebook_id: int
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    created_at: str


class ChatRequest(BaseModel):
    notebook_id: int
    message: str
    source_ids: list[int] = []
    model_key: Optional[str] = None


class Citation(BaseModel):
    index: int
    source_id: int
    filename: str
    chunk_id: str
    text: str
    page: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []


class SlideDeckRequest(BaseModel):
    notebook_id: int
    source_ids: list[int] = []
    instruction: Optional[str] = ""
    model_key: Optional[str] = None


class SlidePage(BaseModel):
    title: str
    bullet_points: list[str]
    notes: Optional[str] = ""


class SlideDeckResponse(BaseModel):
    title: str
    slides: list[SlidePage]


class InfographicRequest(BaseModel):
    notebook_id: int
    source_ids: list[int] = []
    chart_type: Literal["bento_grid", "timeline", "comparison"]
    instruction: Optional[str] = ""
    model_key: Optional[str] = None


class InfographicNode(BaseModel):
    id: str
    title: str
    content: str
    icon: Optional[str] = None
    color: Optional[str] = None
    position: Optional[dict] = None
    connections: list[str] = []


class InfographicResponse(BaseModel):
    chart_type: str
    title: str
    nodes: list[InfographicNode]


class DataTableRequest(BaseModel):
    notebook_id: int
    source_ids: list[int] = []
    instruction: Optional[str] = ""
    model_key: Optional[str] = None


class DataTableResponse(BaseModel):
    title: str
    columns: list[str]
    rows: list[list[str]]


class ModelConfigCreate(BaseModel):
    provider: str
    model_name: str
    display_name: Optional[str] = ""
    api_key: Optional[str] = ""
    base_url: Optional[str] = ""
    is_active: bool = True
    sort_order: int = 0


class ModelConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    display_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ModelConfigResponse(BaseModel):
    id: int
    provider: str
    model_name: str
    display_name: str
    api_key: str
    base_url: str
    is_active: bool
    sort_order: int
    created_at: str
