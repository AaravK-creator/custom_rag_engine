from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


class SourceChunk(BaseModel):
    text: str
    source_file: str
    chunk_index: int
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    chunks: List[SourceChunk]
    session_id: str


class UploadResponse(BaseModel):
    filename: str
    chunks_created: int
    status: str


class DocumentInfo(BaseModel):
    filename: str
    chunk_count: int


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    sources: Optional[List[str]] = None
    timestamp: str


class ChatHistoryResponse(BaseModel):
    session_id: str
    history: List[ChatHistoryItem]
