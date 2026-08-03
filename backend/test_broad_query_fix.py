"""
Before/after test: does the broad-query fallback actually fix retrieval
for meta/summary-style questions?

Run this from inside backend/ with your venv activated:
    python test_broad_query_fix.py

It uses your already-uploaded documents in ChromaDB (no re-upload needed),
so run it after you've uploaded at least one document through the app.
"""

from app.core.vector_store import vector_store
from app.core.retriever import retrieve_relevant_chunks, retrieve_for_overview, is_broad_query

# Add/edit these to match questions relevant to whatever you've uploaded
TEST_QUERIES = [
    "what is this document about",
    "summarize this document",
    "give me an overview",
    "what topics are covered",
    "what is this pdf about",
    "what does this document cover",
    "tl;dr",
    "what's in this file",
]


def old_behavior(query: str) -> bool:
    """Simulates the OLD code path: plain top-k similarity search only."""
    chunks = retrieve_relevant_chunks(query)
    return len(chunks) > 0  # True = got an answer, False = "not enough info"


def new_behavior(query: str) -> bool:
    """Simulates the NEW code path: broad-query detection + overview fallback."""
    if is_broad_query(query):
        chunks = retrieve_for_overview()
    else:
        chunks = retrieve_relevant_chunks(query)
    return len(chunks) > 0


def main():
    docs = vector_store.list_documents()
    if not docs:
        print("No documents found in ChromaDB. Upload a document through the app first, then re-run this.")
        return

    print(f"Testing against {len(docs)} indexed document(s): {[d['filename'] for d in docs]}\n")

    old_pass, new_pass = 0, 0
    print(f"{'Query':<45} {'OLD':<8} {'NEW':<8}")
    print("-" * 65)

    for q in TEST_QUERIES:
        old_ok = old_behavior(q)
        new_ok = new_behavior(q)
        old_pass += old_ok
        new_pass += new_ok
        print(f"{q:<45} {'PASS' if old_ok else 'FAIL':<8} {'PASS' if new_ok else 'FAIL':<8}")

    total = len(TEST_QUERIES)
    print("-" * 65)
    print(f"\nOLD behavior: {old_pass}/{total} broad queries returned results ({100*old_pass/total:.0f}%)")
    print(f"NEW behavior: {new_pass}/{total} broad queries returned results ({100*new_pass/total:.0f}%)")

    if old_pass < new_pass:
        fixed = new_pass - old_pass
        print(f"\n-> Fallback fixed {fixed} previously-failing quer{'y' if fixed==1 else 'ies'} "
              f"out of {total} tested ({100*fixed/total:.0f}% improvement in coverage).")


if __name__ == "__main__":
    main()