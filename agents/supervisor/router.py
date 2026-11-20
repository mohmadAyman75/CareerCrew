"""
router.py  —  Supervisor, stage 3: "What runs next?"

Plain rules, no LLM: the same state always gives the same decision.
Each rule matches one row of the decision table in the Supervisor Guide.
"""

from agents.supervisor.checks import (
    SETTINGS,
    cv_is_clear,
    fit_is_high_enough,
    job_is_real,
    run_input_checks,
)
from agents.supervisor.phase import (
    ANALYZED,
    DONE,
    DRAFTED,
    INTERVIEWING,
    PASSED,
    READY_TO_WRITE,
    REJECTED,
    START,
    detect_phase,
)
from graph.validate import require_dict
from schemas.routing import Question, RoutingDecision

MAX_ROUNDS = SETTINGS["max_rounds"]


# ---------------- Small helpers to build a decision ----------------

def go(step: str, reason: str, instruction: str | None = None) -> RoutingDecision:
    """Send the session to one step."""
    return RoutingDecision(next_steps=[step], reason=reason, instruction=instruction)


def ask(kind: str, text: str, reason: str) -> RoutingDecision:
    """Pause and ask the user a question."""
    return RoutingDecision(next_steps=["ask_user"], reason=reason, question=Question(kind=kind, text=text))


# ---------------- The main function ----------------

def decide(state: dict) -> RoutingDecision:
    """Read the state and return where the session goes next."""
    require_dict(state, "decide")

    round_number = state.get("round", 0)
    if not isinstance(round_number, int) or not 0 <= round_number <= MAX_ROUNDS:
        raise ValueError(f"state['round'] must be an int from 0 to {MAX_ROUNDS}, got {round_number!r}")

    # 1) The user ended the session
    if state.get("stopped"):
        return go("end", "The user ended the session.")

    # 2) A problem in the user's input (empty CV, Arabic CV, not a job post, ...)
    problem = run_input_checks(state)
    if problem:
        return ask("fix_input", problem, reason="The input needs fixing before we start.")

    phase = detect_phase(state)

    # 3) Profile and Job Intel run first, at the same time
    if phase == START:
        missing = [step for step, key in (("profile", "profile"), ("job_intel", "job")) if state.get(key) is None]
        return RoutingDecision(next_steps=missing, reason="Read the CV and the job post.")

    # 4) Checks on what Profile and Job Intel found
    problem = job_is_real(state)
    if problem:
        return ask("not_a_job", problem, reason="Job Intel says this is not a real job post.")

    problem = cv_is_clear(state)
    if problem and not state.get("cv_confirmed"):
        return ask("unclear_cv", problem, reason="The CV was not read clearly.")

    # 5) The main flow
    if phase == ANALYZED:
        return go("fit_check", "Compare the CV with the job.")

    if phase == READY_TO_WRITE:
        problem = fit_is_high_enough(state)
        if problem and not state.get("continue_low_fit"):
            return ask("low_fit", problem, reason="The fit score is low.")
        return go("writer", "Write the first tailored draft.")

    if phase == DRAFTED:
        return go("critic", "Fact-check and score the draft.")

    if phase == REJECTED and round_number < MAX_ROUNDS:
        feedback = "\n".join(state["critique"].feedback)
        return go("writer", f"The critic rejected draft {round_number}. Send its feedback to the writer.", feedback)

    if phase in (PASSED, REJECTED):
        if state.get("approved"):
            return go("interview", "The user approved the CV. Start the mock interview.")
        return ask("approve", approval_question(phase), reason="Ask the user to approve the tailored CV.")

    if phase == INTERVIEWING:
        return go("interview", "Continue the mock interview.")

    if phase == DONE:
        return go("end", "The interview is finished.")

    raise ValueError(f"No routing rule for phase '{phase}'")


def approval_question(phase: str) -> str:
    """The text shown to the user before they approve the CV."""
    if phase == PASSED:
        return "Your tailored CV is ready. Do you approve it?"
    return (
        f"After {MAX_ROUNDS} rounds the critic still has notes (marked in the CV). "
        "Do you approve this best draft?"
    )
