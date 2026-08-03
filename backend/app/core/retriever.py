import re

from app.core.vector_store import vector_store
from app.config import settings

# Below this similarity score, we treat a chunk as "not relevant enough"
MIN_SCORE_THRESHOLD = 0.15

# Phrases that signal a broad/meta question about the document as a whole,
# rather than a question about a specific fact or section. Similarity
# search performs poorly on these because no single chunk represents
# "the document as a whole" - so we handle them with a different strategy.
BROAD_QUERY_PHRASES = [
    "what is this document about",
    "what is this pdf about",
    "what is this file about",
    "what does this document cover",
    "summarize this document",
    "summarise this document",
    "summarize the document",
    "give me an overview",
    "give an overview",
    "what topics are covered",
    "what is in this document",
    "what's this about",
    "tl;dr",
]

# Matches phrasings like "Case No. 1", "case number 47", "case #12", "Case 3"
# Captures the numeric ID so we can build an exact-match search string.
CASE_NUMBER_PATTERN = re.compile(
    r"case\s*(?:no\.?|number|#)?\s*(\d+)\b", re.IGNORECASE
)


# Field labels used to reference a specific record by an identifier other
# than its case number - e.g. "HQ File Number HQRNORM REVIW00002443AM25".
# These IDs are exact strings, not something similarity search can find
# reliably in a document full of near-duplicate boilerplate records.
ID_FIELD_LABELS = [
    "hq file number",
    "ra file number",
    "licence no and date",
    "licence no",
    "license no and date",
    "license no",
    "udin",
]


# A run of 4+ consecutive digits, used to detect whether a whitespace-
# separated token is likely to be a document-specific ID (as opposed to
# a short number like a case number or a year). This is checked as a
# substring anywhere in the token, not just at a fixed position, since
# real-world IDs vary in shape - some start with letters ("REVIW00002443AM25"),
# others start with digits ("03AX04004787"), and both need to be caught.
DIGIT_RUN_PATTERN = re.compile(r"\d{4,}")

# Trailing/leading punctuation to strip off a token before treating it as
# a candidate ID (so "AM26?" or "(AM26)" don't carry punctuation into the
# search string).
TOKEN_STRIP_CHARS = "?.,;:()[]{}\"'"


def is_broad_query(query: str) -> bool:
    """Heuristic check for meta/summary-style questions."""
    q = query.lower().strip()
    return any(phrase in q for phrase in BROAD_QUERY_PHRASES)


def extract_case_number(query: str) -> str | None:
    """
    Pull a case/record number out of a query like "Case No. 1" or
    "case number 47". Returns None if no such reference is found.
    """
    match = CASE_NUMBER_PATTERN.search(query)
    return match.group(1) if match else None


def extract_labeled_id(query: str) -> tuple[str, str] | tuple[None, None]:
    """
    Detect a query referencing a specific record by a labeled identifier,
    e.g. "case status of HQ File Number HQRNORM REVIW00002443AM25".
    Returns (label, id_value) or (None, None) if no such reference is found.

    Takes everything after the label as the identifier value, since these
    IDs are alphanumeric codes that don't follow a single fixed pattern
    (unlike case numbers, which are plain digits).
    """
    q_lower = query.lower()

    # Check longer/more specific labels first so "licence no and date"
    # isn't shadowed by the shorter "licence no".
    for label in sorted(ID_FIELD_LABELS, key=len, reverse=True):
        idx = q_lower.find(label)
        if idx == -1:
            continue

        value = query[idx + len(label):].strip(" :\u2013\u2014-?.\n\t")
        if value:
            return label, value

    return None, None


def extract_id_tokens(query: str) -> list[str]:
    """
    Fallback ID detection that doesn't depend on a label at all - neither
    a recognized label phrase (extract_labeled_id) nor any particular
    position of digits within the token. Splits the query on whitespace
    and keeps any token containing a run of 4+ digits anywhere in it,
    since that's distinctive enough to be a document-specific ID whether
    it's shaped like "REVIW00002443AM25" (letters first) or "03AX04004787"
    (digits first) or something else entirely.
    """
    candidates = []
    for raw_token in query.split():
        token = raw_token.strip(TOKEN_STRIP_CHARS)
        if DIGIT_RUN_PATTERN.search(token):
            candidates.append(token)
    return candidates


def retrieve_relevant_chunks(query: str, top_k: int = None) -> list[dict]:
    """
    Retrieve the top_k most relevant chunks for a query, filtering out
    chunks that fall below a minimum similarity threshold.
    """
    k = top_k or settings.TOP_K
    results = vector_store.query(query, top_k=k)
    return [r for r in results if r["score"] >= MIN_SCORE_THRESHOLD]


def retrieve_for_overview(max_chunks: int = 12) -> list[dict]:
    """Retrieve a representative spread of chunks for broad/meta questions."""
    return vector_store.get_overview_chunks(max_chunks=max_chunks)


def retrieve_by_case_number(case_number: str) -> list[dict]:
    """
    Retrieve chunks for a specific case/record number via exact text match.
    Used when a document contains many near-duplicate records that
    similarity search can't reliably tell apart (e.g. a table of cases
    that all share the same boilerplate decision text, differing mainly
    by an ID number).
    """
    # Matches the document's literal format: "Case No. 1 /". The trailing
    # "/" (or end-of-token) prevents "Case No. 1" from matching "Case No. 10",
    # "Case No. 100", etc.
    pattern = f"Case No. {case_number} /"
    results = vector_store.find_by_exact_text(pattern)

    if not results:
        # Fall back to a looser pattern in case formatting differs slightly
        # (e.g. no space before the slash, or a different separator).
        pattern = f"Case No. {case_number}"
        results = vector_store.find_by_exact_text(pattern)
        # Filter out false positives like matching "1" inside "10", "11", etc.
        results = [
            r for r in results
            if re.search(rf"case no\.?\s*{re.escape(case_number)}\b(?!\d)", r["text"], re.IGNORECASE)
        ]

    return results


def retrieve_by_labeled_id(id_value: str) -> list[dict]:
    """
    Retrieve chunks containing a specific labeled identifier (HQ File
    Number, RA File Number, Licence No, UDIN, etc.) via exact text match.
    Same rationale as retrieve_by_case_number: these are near-duplicate
    boilerplate records distinguished mainly by an ID, which similarity
    search can't reliably tell apart.
    """
    return vector_store.find_by_exact_text(id_value)


def retrieve_by_id_tokens(tokens: list[str]) -> list[dict]:
    """
    Retrieve chunks matching any of the given ID-like tokens via exact
    text match. Tries the longest token first (most specific/least likely
    to have false positives), then falls back to shorter ones if nothing
    matches.
    """
    for token in sorted(tokens, key=len, reverse=True):
        results = vector_store.find_by_exact_text(token)
        if results:
            return results
    return []