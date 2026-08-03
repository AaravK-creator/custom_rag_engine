import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 800))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 120))

    TOP_K: int = int(os.getenv("TOP_K", 5))

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    CHROMA_DIR: str = os.getenv("CHROMA_DIR", "./data/chroma_db")
    SQLITE_DB: str = os.getenv("SQLITE_DB", "./data/chat_history.db")

    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "*")


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_DIR, exist_ok=True)
