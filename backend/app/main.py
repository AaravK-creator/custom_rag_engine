from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session_store import init_db
from app.api import routes_upload, routes_chat, routes_documents

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN] if settings.FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
async def root():
    return {"status": "ok", "message": "RAG Chatbot API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(routes_upload.router, tags=["Upload"])
app.include_router(routes_chat.router, tags=["Chat"])
app.include_router(routes_documents.router, tags=["Documents"])
