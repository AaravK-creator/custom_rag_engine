from app.db import session_store


def append_turn(session_id: str, query: str, answer: str, sources: list[str]):
    session_store.add_message(session_id, "user", query)
    session_store.add_message(session_id, "assistant", answer, sources)


def get_session_history(session_id: str) -> list[dict]:
    return session_store.get_history(session_id)


def get_history_text(session_id: str) -> str:
    return session_store.format_history_for_prompt(session_id)
