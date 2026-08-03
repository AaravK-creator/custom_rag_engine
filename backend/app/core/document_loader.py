import os
from pypdf import PdfReader
import docx


def load_pdf(filepath: str) -> str:
    """Extract text from a PDF file, page by page."""
    reader = PdfReader(filepath)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)
    return "\n".join(text_parts)


def load_docx(filepath: str) -> str:
    """Extract text from a Word (.docx) file."""
    document = docx.Document(filepath)
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def load_txt(filepath: str) -> str:
    """Extract text from a plain text file."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_document(filepath: str) -> str:
    """
    Route to the correct loader based on file extension.
    Returns the full extracted text as a single string.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return load_pdf(filepath)
    elif ext == ".docx":
        return load_docx(filepath)
    elif ext == ".txt":
        return load_txt(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported types: .pdf, .docx, .txt")
