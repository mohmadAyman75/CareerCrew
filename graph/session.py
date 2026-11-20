"""
session.py  —  start a session, answer the Supervisor's questions, read the result.

The API and scripts/run_session.py use these three functions,
so they never talk to LangGraph directly.

A session ends in one of two ways:
    it pauses on a question  -> the functions return the question as a dict {"kind", "text"}
    it finishes              -> the functions return None
"""

from langgraph.types import Command


def _config(session_id: str) -> dict:
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id must be a non-empty string")
    return {"configurable": {"thread_id": session_id}}


def start_session(graph, session_id: str, cv_text: str, job_text: str) -> dict | None:
    """Run a new session until it pauses or finishes. Return the open question, or None."""
    if not isinstance(cv_text, str) or not isinstance(job_text, str):
        raise TypeError("cv_text and job_text must be strings")

    first_state = {"session_id": session_id, "cv_text": cv_text, "job_text": job_text, "round": 0}
    graph.invoke(first_state, _config(session_id))
    return open_question(graph, session_id)


def answer_question(graph, session_id: str, answer: dict) -> dict | None:
    """Resume a paused session with the user's answer. Return the next question, or None."""
    if not isinstance(answer, dict):
        raise TypeError(f"answer must be a dict, got {type(answer).__name__}")
    if open_question(graph, session_id) is None:
        raise RuntimeError(f"Session '{session_id}' is not waiting for an answer")

    graph.invoke(Command(resume=answer), _config(session_id))
    return open_question(graph, session_id)


def open_question(graph, session_id: str) -> dict | None:
    """The question the session is waiting on, or None."""
    snapshot = graph.get_state(_config(session_id))
    if not snapshot.interrupts:
        return None
    return snapshot.interrupts[0].value


def get_session_state(graph, session_id: str) -> dict:
    """The full state of the session right now."""
    return graph.get_state(_config(session_id)).values
