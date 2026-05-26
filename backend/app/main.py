from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.database import init_db
from app.routers import notebooks, sources, chat, artifacts, models

init_db()

app = FastAPI(title="DrPaper API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notebooks.router)
app.include_router(sources.router)
app.include_router(chat.router)
app.include_router(artifacts.router)
app.include_router(models.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "DrPaper"}
