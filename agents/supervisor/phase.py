"""
phase.py  —  Supervisor, stage 1: "Where are we now?"

It looks at what is already inside the state and returns the name of the phase.

Important difference from checks.py:
    In checks.py, a missing key is a BUG   -> we raise.
    Here, a missing key is INFORMATION      -> it tells us which step did not run yet.
    Example: no "draft" in the state means the Writer did not run yet.

The phases, in order:

    start -> analyzed -> ready_to_write -> drafted -> passed   -> interviewing -> done
                                              ^          |
                                              |          v
                                              +------ rejected   (back to the Writer, max 3 rounds)
"""

from graph.validate import require_dict
from schemas.critique import Critique
from schemas.interview import InterviewTurn

# ---------------- Phase names (one place, so we never mistype them) ----------------

START = "start"                    # Profile and Job Intel did not finish yet
ANALYZED = "analyzed"              # we have profile + job, but no gap report yet
READY_TO_WRITE = "ready_to_write"  # we have the gap report, the Writer can start
DRAFTED = "drafted"                # the Writer made a draft, the Critic did not review it yet
PASSED = "passed"                  # the Critic accepted the draft -> ask the user to approve
REJECTED = "rejected"              # the Critic refused the draft -> back to the Writer or ask the user
INTERVIEWING = "interviewing"      # the mock interview has started
DONE = "done"                      # every interview answer is scored


def has(state: dict, key: str) -> bool:
    """True if the key is in the state AND its value is not None."""
    return state.get(key) is not None


def detect_phase(state: dict) -> str:
    """Look at the state and return the current phase name."""
    require_dict(state, "detect_phase")

    # 1) The two parallel agents must both finish first
    if not has(state, "profile") or not has(state, "job"):
        return START

    # 2) Both finished, but the gap report is not built yet
    if not has(state, "gap"):
        return ANALYZED

    # 3) Gap report is ready, but the Writer did not write yet
    if not has(state, "draft"):
        return READY_TO_WRITE

    # 4) There is a draft, but no review for it yet.
    #    When the Supervisor sends a draft back to the Writer, it sets "critique" to None,
    #    so after the Writer runs again we come back here.
    if not has(state, "critique"):
        return DRAFTED

    # 5) The interview started (this only happens after the user approved the CV)
    if has(state, "interview"):
        turns = state["interview"]
        if not isinstance(turns, list) or not all(isinstance(t, InterviewTurn) for t in turns):
            raise TypeError("state['interview'] must be a list of InterviewTurn")
        if turns and all(turn.score is not None for turn in turns):
            return DONE
        return INTERVIEWING

    # 6) The Critic gave its verdict
    critique = state["critique"]
    if not isinstance(critique, Critique):
        raise TypeError(f"state['critique'] must be a Critique, got {type(critique).__name__}")

    return PASSED if critique.passed else REJECTED
