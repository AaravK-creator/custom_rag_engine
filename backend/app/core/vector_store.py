import re

import chromadb
from app.config import settings
from app.core.embeddings import embedding_service

COLLECTION_NAME = "documents"


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, filename: str, chunks: list[str]):
        """Embed and store chunks for a given source file."""
        if not chunks:
            return 0

        embeddings = embedding_service.embed(chunks)
        ids = [f"{filename}__chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"source_file": filename, "chunk_index": i} for i in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def query(self, query_text: str, top_k: int) -> list[dict]:
        """Return top_k most similar chunks with metadata and distance scores."""
        query_embedding = embedding_service.embed_one(query_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        chunks = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                chunks.append(
                    {
                        "text": doc,
                        "source_file": meta.get("source_file", "unknown"),
                        "chunk_index": meta.get("chunk_index", -1),
                        # Convert cosine distance to a similarity-like score (0-1, higher is better)
                        "score": max(0.0, 1 - distance),
                    }
                )
        return chunks

    def list_documents(self) -> list[dict]:
        """Return distinct source filenames with their chunk counts."""
        data = self.collection.get()
        counts: dict[str, int] = {}
        for meta in data.get("metadatas", []):
            source = meta.get("source_file", "unknown")
            counts[source] = counts.get(source, 0) + 1
        return [{"filename": f, "chunk_count": c} for f, c in counts.items()]

    def get_overview_chunks(self, max_chunks: int = 12) -> list[dict]:
        """
        Return a representative spread of chunks across all stored documents,
        in original document order. Used for broad/meta questions like
        "what is this document about" where similarity search against a
        single chunk doesn't work well, since no single chunk represents
        the document as a whole.
        """
        data = self.collection.get()
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])

        # Sort by (source_file, chunk_index) so we read each doc in order
        combined = sorted(
            zip(documents, metadatas),
            key=lambda pair: (pair[1].get("source_file", ""), pair[1].get("chunk_index", 0)),
        )

        if len(combined) <= max_chunks:
            sampled = combined
        else:
            # Evenly sample across the full document rather than just
            # taking the first N, so the overview covers beginning,
            # middle, and end.
            step = len(combined) / max_chunks
            indices = [int(i * step) for i in range(max_chunks)]
            sampled = [combined[i] for i in indices]

        return [
            {
                "text": doc,
                "source_file": meta.get("source_file", "unknown"),
                "chunk_index": meta.get("chunk_index", -1),
                "score": 1.0,  # not similarity-ranked; included by design
            }
            for doc, meta in sampled
        ]

    def find_by_exact_text(self, pattern: str, include_neighbors: bool = True) -> list[dict]:
        """
        Find chunks containing an exact literal substring (case-insensitive,
        whitespace-normalized), bypassing embedding similarity entirely.

        This matters for documents made of many near-duplicate records
        (e.g. a table of near-identical case entries where only an ID
        differs) - semantic search can't reliably distinguish "Case No. 1"
        from "Case No. 47" because the surrounding boilerplate text is
        almost the same, so their embeddings end up nearly identical too.
        An exact substring match is the correct tool here, not similarity.

        Whitespace is normalized (runs of whitespace collapsed to a single
        space) before comparison, since a user-typed or copy-pasted ID may
        have different spacing than the original extracted PDF text.

        If include_neighbors is True, also pulls the immediately preceding
        and following chunk from the same document, since a chunk boundary
        may fall in the middle of a single record (e.g. splitting the
        header from its decision paragraph).
        """
        data = self.collection.get()
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])

        pattern_norm = re.sub(r"\s+", " ", pattern).strip().lower()
        matched_keys = set()  # (source_file, chunk_index) already included
        results = []

        # Index everything by (source_file, chunk_index) for neighbor lookup
        by_key = {
            (meta.get("source_file", ""), meta.get("chunk_index", -1)): doc
            for doc, meta in zip(documents, metadatas)
        }

        for doc, meta in zip(documents, metadatas):
            doc_norm = re.sub(r"\s+", " ", doc).lower()
            if pattern_norm in doc_norm:
                source = meta.get("source_file", "unknown")
                idx = meta.get("chunk_index", -1)

                candidate_indices = [idx]
                if include_neighbors:
                    candidate_indices = [idx - 1, idx, idx + 1]

                for ci in candidate_indices:
                    key = (source, ci)
                    if key in by_key and key not in matched_keys:
                        matched_keys.add(key)
                        results.append(
                            {
                                "text": by_key[key],
                                "source_file": source,
                                "chunk_index": ci,
                                "score": 1.0,  # exact match, not similarity-ranked
                            }
                        )

        # Keep results in document order for readability
        results.sort(key=lambda r: (r["source_file"], r["chunk_index"]))
        return results

    def delete_document(self, filename: str):
        """Delete all chunks belonging to a given source file."""
        self.collection.delete(where={"source_file": filename})


vector_store = VectorStore()