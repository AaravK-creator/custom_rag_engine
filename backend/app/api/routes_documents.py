import os
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.vector_store import vector_store
from app.models.schemas import DocumentInfo

router = APIRouter()


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    docs = vector_store.list_documents()
    return [DocumentInfo(filename=d["filename"], chunk_count=d["chunk_count"]) for d in docs]


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    vector_store.delete_document(filename)

    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    return {"status": "deleted", "filename": filename}
