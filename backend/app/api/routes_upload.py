import os
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.core.document_loader import load_document
from app.core.chunker import split_text
from app.core.vector_store import vector_store
from app.models.schemas import UploadResponse

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    save_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        text = load_document(save_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract text: {e}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found in file.")

    chunks = split_text(text)
    num_chunks = vector_store.add_chunks(file.filename, chunks)

    return UploadResponse(
        filename=file.filename,
        chunks_created=num_chunks,
        status="success",
    )
