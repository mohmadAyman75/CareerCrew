"""
Tests for agents/supervisor/router.py: one test per row of the decision table.
"""

import pytest

from agents.supervisor.router import MAX_ROUNDS, decide
from tests.helpers import (
    analyzed_state,
    drafted_state,
    inputs_state,
    make_interview,
    make_job,
    make_profile,
    ready_to_write_state,
    reviewed_state,
)


def asks(state: dict) -> str:
    """Return the kind of question the Supervisor asks, and check it really asks."""
    decision = decide(state)
    assert decision.next_steps == ["ask_user"]
    return decision.question.kind


def goes_to(state: dict) -> list[str]:
    return decide(state).next_steps


def test_stopped_session_ends():
    assert goes_to(inputs_state(stopped=True)) == ["end"]


def test_bad_input_asks_the_user_to_fix_it():
    assert asks(inputs_state(cv_text="")) == "fix_input"


def test_start_runs_profile_and_job_intel_in_parallel():
    assert goes_to(inputs_state()) == ["profile", "job_intel"]


def test_start_runs_only_the_missing_agent():
    assert goes_to(inputs_state(profile=make_profile())) == ["job_intel"]


def test_not_a_real_job_asks_the_user():
    assert asks(analyzed_state(job=make_job(is_valid_job_post=False))) == "not_a_job"


def test_unclear_cv_asks_the_user():
    assert asks(analyzed_state(profile=make_profile(parse_confidence=0.3))) == "unclear_cv"


def test_unclear_cv_confirmed_goes_on():
    assert goes_to(analyzed_state(profile=make_profile(parse_confidence=0.3), cv_confirmed=True)) == ["fit_check"]


def test_no_gap_runs_fit_check():
    assert goes_to(analyzed_state()) == ["fit_check"]


def test_low_fit_asks_the_user():
    assert asks(ready_to_write_state(fit_score=20.0)) == "low_fit"


def test_low_fit_with_user_ok_goes_to_writer():
    assert goes_to(ready_to_write_state(fit_score=20.0, continue_low_fit=True)) == ["writer"]


def test_good_fit_goes_to_writer():
    assert goes_to(ready_to_write_state()) == ["writer"]


def test_draft_goes_to_critic():
    assert goes_to(drafted_state()) == ["critic"]


def test_rejected_draft_goes_back_to_writer_with_feedback():
    decision = decide(reviewed_state(passed=False, round_number=1))
    assert decision.next_steps == ["writer"]
    assert "Remove the A/B testing claim" in decision.instruction


def test_rejected_at_last_round_asks_for_approval():
    decision = decide(reviewed_state(passed=False, round_number=MAX_ROUNDS))
    assert decision.next_steps == ["ask_user"]
    assert decision.question.kind == "approve"
    assert "still has notes" in decision.question.text


def test_passed_draft_asks_for_approval():
    assert asks(reviewed_state(passed=True)) == "approve"


def test_approved_cv_starts_the_interview():
    assert goes_to(reviewed_state(passed=True, approved=True)) == ["interview"]


def test_finished_interview_ends():
    assert goes_to(reviewed_state(passed=True, approved=True, interview=make_interview())) == ["end"]


def test_bad_state_raises():
    with pytest.raises(TypeError):
        decide(None)
    with pytest.raises(ValueError, match="round"):
        decide(inputs_state(round=MAX_ROUNDS + 1))
