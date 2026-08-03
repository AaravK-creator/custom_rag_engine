from app.core.retriever import (
    retrieve_relevant_chunks,
    retrieve_for_overview,
    retrieve_by_case_number,
    retrieve_by_labeled_id,
    retrieve_by_id_tokens,
    extract_case_number,
    extract_labeled_id,
    extract_id_tokens,
    is_broad_query,
)
from app.core.llm import generate_answer
from app.services import chat_history

NO_CONTEXT_MESSAGE = (
    "I don't have enough information in the uploaded documents to answer that."
)

NO_DOCUMENTS_MESSAGE = (
    "No documents have been uploaded yet, so I can't give you an overview."
)

NO_MATCHING_CASE_MESSAGE_TEMPLATE = (
    "I couldn't find Case No. {case_number} in the uploaded documents."
)

NO_MATCHING_ID_MESSAGE_TEMPLATE = (
    "I couldn't find a record matching {label} \"{id_value}\" in the uploaded documents."
)

PROMPT_TEMPLATE = """You are a helpful assistant. Answer the question using ONLY the context below.
If the answer is not contained in the context, say: "{no_context_message}"
Do not use any outside knowledge. Be concise and accurate.

Context:
{context}

Previous conversation:
{history}

Question: {question}
Answer:"""

OVERVIEW_PROMPT_TEMPLATE = """You are a helpful assistant. The excerpts below are samples taken from
across a document (beginning, middle, and end), not the full text. Based on these excerpts, give a
concise overview of what the document appears to cover: its main topic and the key sections/themes.
Be clear that this is based on sampled excerpts, not a read of the entire document.

Excerpts:
{context}

Question: {question}
Answer:"""


def build_prompt(context: str, question: str, history_text: str) -> str:
    return PROMPT_TEMPLATE.format(
        no_context_message=NO_CONTEXT_MESSAGE,
        context=context if context else "(no relevant context found)",
        history=history_text if history_text else "(no previous conversation)",
        question=question,
    )


def build_overview_prompt(context: str, question: str) -> str:
    return OVERVIEW_PROMPT_TEMPLATE.format(context=context, question=question)


def answer_query(query: str, session_id: str = "default") -> dict:
    # A question referencing a specific labeled ID (e.g. "HQ File Number
    # HQRNORM REVIW00002443AM25") needs exact text matching, same reasoning
    # as case numbers below - these are near-duplicate boilerplate records
    # distinguished mainly by an ID that similarity search can't reliably
    # tell apart. Checked first since it's the most specific pattern.
    label, id_value = extract_labeled_id(query)
    id_tokens = extract_id_tokens(query)

    if id_value or id_tokens:
        chunks = []

        # Try the labeled extraction first (it captures the exact ID
        # phrase after a recognized label like "HQ File Number").
        if id_value:
            chunks = retrieve_by_labeled_id(id_value)

        # Fall back to generic ID-token matching if the label-based
        # extraction didn't find anything - this covers cases where the
        # query uses different wording than any label we recognize (e.g.
        # "Norms Committee Decision File Number" instead of "HQ File
        # Number"), since the ID token itself is distinctive enough to
        # search for directly regardless of what precedes it.
        if not chunks and id_tokens:
            chunks = retrieve_by_id_tokens(id_tokens)

        if not chunks:
            shown_value = id_value or (id_tokens[0] if id_tokens else "")
            answer = NO_MATCHING_ID_MESSAGE_TEMPLATE.format(
                label=label or "ID", id_value=shown_value
            )
            chat_history.append_turn(session_id, query, answer, [])
            return {
                "answer": answer,
                "sources": [],
                "chunks": [],
                "session_id": session_id,
            }

        context = "\n\n---\n\n".join(c["text"] for c in chunks)
        history_text = chat_history.get_history_text(session_id)
        prompt = build_prompt(context, query, history_text)
        answer = generate_answer(prompt)

        source_files = sorted(set(c["source_file"] for c in chunks))
        chat_history.append_turn(session_id, query, answer, source_files)

        return {
            "answer": answer,
            "sources": source_files,
            "chunks": chunks,
            "session_id": session_id,
        }

    # A question referencing a specific case/record number (e.g. "Case No. 1")
    # needs exact text matching, not similarity search. Documents made of
    # many near-duplicate records (same boilerplate, different ID) defeat
    # semantic search, since every record's embedding looks about the same.
    case_number = extract_case_number(query)
    if case_number:
        chunks = retrieve_by_case_number(case_number)

        if not chunks:
            answer = NO_MATCHING_CASE_MESSAGE_TEMPLATE.format(case_number=case_number)
            chat_history.append_turn(session_id, query, answer, [])
            return {
                "answer": answer,
                "sources": [],
                "chunks": [],
                "session_id": session_id,
            }

        context = "\n\n---\n\n".join(c["text"] for c in chunks)
        history_text = chat_history.get_history_text(session_id)
        prompt = build_prompt(context, query, history_text)
        answer = generate_answer(prompt)

        source_files = sorted(set(c["source_file"] for c in chunks))
        chat_history.append_turn(session_id, query, answer, source_files)

        return {
            "answer": answer,
            "sources": source_files,
            "chunks": chunks,
            "session_id": session_id,
        }

    # Broad/meta questions ("what is this about") don't match well against
    # individual chunks via similarity search, since no single chunk
    # represents the document as a whole. Handle them with a sampled
    # overview instead of the normal retrieval path.
    if is_broad_query(query):
        chunks = retrieve_for_overview()

        if not chunks:
            answer = NO_DOCUMENTS_MESSAGE
            chat_history.append_turn(session_id, query, answer, [])
            return {
                "answer": answer,
                "sources": [],
                "chunks": [],
                "session_id": session_id,
            }

        context = "\n\n---\n\n".join(c["text"] for c in chunks)
        prompt = build_overview_prompt(context, query)
        answer = generate_answer(prompt)

        source_files = sorted(set(c["source_file"] for c in chunks))
        chat_history.append_turn(session_id, query, answer, source_files)

        return {
            "answer": answer,
            "sources": source_files,
            "chunks": chunks,
            "session_id": session_id,
        }

    chunks = retrieve_relevant_chunks(query)

    if not chunks:
        answer = NO_CONTEXT_MESSAGE
        chat_history.append_turn(session_id, query, answer, [])
        return {
            "answer": answer,
            "sources": [],
            "chunks": [],
            "session_id": session_id,
        }

    context = "\n\n---\n\n".join(c["text"] for c in chunks)
    history_text = chat_history.get_history_text(session_id)

    prompt = build_prompt(context, query, history_text)
    answer = generate_answer(prompt)

    source_files = sorted(set(c["source_file"] for c in chunks))
    chat_history.append_turn(session_id, query, answer, source_files)

    return {
        "answer": answer,
        "sources": source_files,
        "chunks": chunks,
        "session_id": session_id,
    }