from app.config import settings

# Ordered from "biggest" boundary to smallest. The splitter tries each
# separator in turn, only falling back to a harder cut when a piece is
# still too big to fit in one chunk.
DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def _split_on_separator(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Recursively split text using the first separator that produces
    pieces small enough to work with, falling back to the next separator
    (or a hard character cut) when needed."""
    if len(text) <= chunk_size:
        return [text]

    if not separators:
        # No more separators to try: hard-cut by character count.
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep, rest_separators = separators[0], separators[1:]
    parts = text.split(sep) if sep else list(text)

    pieces = []
    for part in parts:
        if sep:
            part = part + sep
        if len(part) > chunk_size:
            pieces.extend(_split_on_separator(part, rest_separators, chunk_size))
        else:
            pieces.append(part)
    return pieces


def _merge_with_overlap(pieces: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    """Greedily pack small pieces into chunks close to chunk_size,
    carrying a bit of overlap forward between consecutive chunks."""
    chunks = []
    current = ""

    for piece in pieces:
        if len(current) + len(piece) <= chunk_size:
            current += piece
        else:
            if current:
                chunks.append(current)
            # Start the next chunk with overlap from the end of the previous one
            overlap_text = current[-chunk_overlap:] if chunk_overlap else ""
            current = overlap_text + piece

    if current:
        chunks.append(current)

    return chunks


def split_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> list[str]:
    """
    Split raw text into overlapping chunks suitable for embedding.
    Tries to break on paragraph/sentence boundaries before falling back
    to hard character cuts, and keeps a small overlap between chunks so
    context isn't lost at chunk boundaries.
    """
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

    if not text or not text.strip():
        return []

    pieces = _split_on_separator(text, DEFAULT_SEPARATORS, size)
    chunks = _merge_with_overlap(pieces, size, overlap)

    return [c.strip() for c in chunks if c.strip()]
