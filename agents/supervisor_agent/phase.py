"""
phase.py  —  Supervisor, stage 1: "Where are we now?"

It looks at what is already inside the state and returns the name of the phase.

Important difference from checks.py:
    In checks.py, a missing key is a BUG   -> we raise.
    Here, a missing key is INFORMATION      -> it tells us which step did not run yet.
    Example: no "draft" in the state means the Writer did not run yet.

The phases, in order:

    start  ->  analyzed  ->  ready_to_write  ->  drafted  ->  passed   ->  interviewing
                                                    ^            |
                                                    |            v
                                                    +------  rejected   (back to the Writer, max 3 rounds)
"""

from types import SimpleNamespace

# ---------------- Phase names (one place, so we never mistype them) ----------------

START = "start"                    # Profile and Job Intel did not finish yet
ANALYZED = "analyzed"              # we have profile + job, but no gap report yet
READY_TO_WRITE = "ready_to_write"  # we have the gap report, the Writer can start
DRAFTED = "drafted"                # the Writer made a draft, the Critic did not review it yet
PASSED = "passed"                  # the Critic accepted the draft -> ask the user to approve
REJECTED = "rejected"              # the Critic refused the draft -> back to the Writer or stop
INTERVIEWING = "interviewing"      # the mock interview has started


# ---------------- Helper ----------------

def has(state: dict, key: str) -> bool:
    """True if the key is in the state AND its value is not None."""
    return state.get(key) is not None


# ---------------- The main function ----------------

def detect_phase(state: dict) -> str:
    """Look at the state and return the current phase name."""

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
    #    Note: when the Supervisor sends the draft back to the Writer,
    #    actions.py will set "critique" to None, so we come back here.
    if not has(state, "critique"):
        return DRAFTED

    # 5) The interview started (this only happens after the user approved the CV)
    if has(state, "interview"):
        return INTERVIEWING

    # 6) The Critic gave its verdict
    critique = state["critique"]
    if not hasattr(critique, "passed"):
        raise AttributeError("state['critique'] has no 'passed'. Is it a Critique object?")

    if critique.passed:
        return PASSED
    return REJECTED


if __name__ == "__main__":
    # Quick manual test. Run it from the project root:
    #   python -m agents.supervisor_agent.phase
    #
    # The real objects (CandidateProfile, Critique, ...) do not exist yet,
    # so we use simple fake values. SimpleNamespace(passed=True) is just
    # a small object where  .passed  gives True.

    good_review = SimpleNamespace(passed=True)
    bad_review = SimpleNamespace(passed=False)

    # Each test: (name, fake state, the phase we expect)
    tests = [
        ("empty state",          {},                                                              START),
        ("only profile",         {"profile": "x"},                                                START),
        ("profile + job",        {"profile": "x", "job": "x"},                                    ANALYZED),
        ("+ gap",                {"profile": "x", "job": "x", "gap": "x"},                        READY_TO_WRITE),
        ("+ draft",              {"profile": "x", "job": "x", "gap": "x", "draft": "x"},          DRAFTED),
        ("critic said yes",      {"profile": "x", "job": "x", "gap": "x", "draft": "x",
                                  "critique": good_review},                                       PASSED),
        ("critic said no",       {"profile": "x", "job": "x", "gap": "x", "draft": "x",
                                  "critique": bad_review},                                        REJECTED),
        ("sent back to writer",  {"profile": "x", "job": "x", "gap": "x", "draft": "x",
                                  "critique": None},                                              DRAFTED),
        ("interview started",    {"profile": "x", "job": "x", "gap": "x", "draft": "x",
                                  "critique": good_review, "interview": []},                      INTERVIEWING),
    ]

    for name, state, expected in tests:
        result = detect_phase(state)
        mark = "OK " if result == expected else "BAD"
        print(f"[{mark}] {name:<20} -> {result:<15} (expected {expected})")