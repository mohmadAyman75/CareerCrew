"""
actions.py  —  Supervisor, stage 4: "Do it."

route_to()      turns a RoutingDecision into a state update
ask_user()      a graph node: pauses the graph and waits for the user's answer
apply_answer()  turns the user's answer into a state update
"""

from langgraph.types import interrupt

from graph.validate import require, require_dict
from schemas.routing import Question, RoutingDecision

# Questions answered with yes / no: kind -> (answer key, state key set to True on "yes")
YES_NO_QUESTIONS = {
    "unclear_cv": ("confirmed", "cv_confirmed"),
    "low_fit": ("continue", "continue_low_fit"),
    "approve": ("approved", "approved"),
}

# Questions answered with new text: kind -> nothing else needed
NEW_INPUT_QUESTIONS = ("fix_input", "not_a_job")

# When the user sends a new CV or job post, every result built from the old one is cleared.
RESET_RESULTS = {
    "profile": None,
    "job": None,
    "gap": None,
    "fit_score": None,
    "draft": None,
    "critique": None,
    "interview": None,
    "round": 0,
    "instruction": None,
    "cv_confirmed": False,
    "continue_low_fit": False,
    "approved": False,
}


def event(message: str, agent: str = "supervisor") -> dict:
    """One line for the UI timeline."""
    return {"agent": agent, "message": message}


# ---------------- Routing ----------------

def route_to(state: dict, decision: RoutingDecision) -> dict:
    """Return the state update that sends the session where the decision says."""
    require_dict(state, "route_to")
    if not isinstance(decision, RoutingDecision):
        raise TypeError(f"route_to() needs a RoutingDecision, got {type(decision).__name__}")

    update = {
        "next_steps": list(decision.next_steps),
        "instruction": decision.instruction,
        "question": decision.question,
        "events": [event(decision.reason)],
    }

    # Every trip to the Writer is a new round, and the new draft needs a new review.
    if decision.next_steps == ["writer"]:
        update["round"] = state.get("round", 0) + 1
        update["critique"] = None

    return update


# ---------------- Asking the user ----------------

def ask_user(state: dict) -> dict:
    """
    Graph node. Pauses the graph with LangGraph's interrupt() until the user answers.
    The API resumes the graph with the answer (see graph/session.py).
    """
    question = require(state, "question", Question)

    answer = interrupt({"kind": question.kind, "text": question.text})

    update = apply_answer(question.kind, answer)
    update["question"] = None
    update["events"] = [event(f"Answered: {question.kind}", agent="user")]
    return update


def apply_answer(kind: str, answer: dict) -> dict:
    """
    Turn the user's answer into a state update.

    Answers:
        any question            {"stop": True}                      -> end the session
        fix_input, not_a_job    {"cv_text": "...", "job_text": "..."} (one or both)
        unclear_cv              {"confirmed": True / False}  or a new {"cv_text": "..."}
        low_fit                 {"continue": True / False}
        approve                 {"approved": True / False}
    """
    if not isinstance(answer, dict):
        raise TypeError(f"The answer must be a dict, got {type(answer).__name__}")

    if answer.get("stop") is True:
        return {"stopped": True}

    if kind in NEW_INPUT_QUESTIONS or (kind == "unclear_cv" and "cv_text" in answer):
        return new_inputs(answer)

    if kind in YES_NO_QUESTIONS:
        answer_key, state_key = YES_NO_QUESTIONS[kind]
        if not isinstance(answer.get(answer_key), bool):
            raise ValueError(f"The answer to '{kind}' needs '{answer_key}': true or false, got {answer}")
        if answer[answer_key]:
            return {state_key: True}
        return {"stopped": True}          # "no" ends the session for now (chat edits come later)

    raise ValueError(f"Unknown question kind: '{kind}'")


def new_inputs(answer: dict) -> dict:
    """The user sent a new CV and/or job text: keep them and clear the old results."""
    texts = {key: answer[key] for key in ("cv_text", "job_text") if key in answer}
    if not texts:
        raise ValueError(f"The answer needs 'cv_text' or 'job_text', got {answer}")
    for key, value in texts.items():
        if not isinstance(value, str):
            raise TypeError(f"answer['{key}'] must be a string, got {type(value).__name__}")

    return {**RESET_RESULTS, **texts}
