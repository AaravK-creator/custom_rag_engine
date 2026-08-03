from sentence_transformers import SentenceTransformer
from app.config import settings


class EmbeddingService:
    """
    Thin wrapper around SentenceTransformer so the rest of the app
    doesn't need to know which embedding model is being used.
    """

    _instance = None

    def __new__(cls):
        # Singleton so the model is loaded into memory only once.
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return cls._instance

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


embedding_service = EmbeddingService()
