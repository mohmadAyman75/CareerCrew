"""Tests for agents/supervisor/phase.py: one test per phase."""

import pytest

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
from tests.helpers import (
    analyzed_state,
    drafted_state,
    inputs_state,
    make_interview,
    make_profile,
    ready_to_write_state,
    reviewed_state,
)


def test_phases_in_order():
    assert detect_phase(inputs_state()) == START
    assert detect_phase(inputs_state(profile=make_profile())) == START
    assert detect_phase(analyzed_state()) == ANALYZED
    assert detect_phase(ready_to_write_state()) == READY_TO_WRITE
    assert detect_phase(drafted_state()) == DRAFTED
    assert detect_phase(reviewed_state(passed=True)) == PASSED
    assert detect_phase(reviewed_state(passed=False)) == REJECTED


def test_draft_sent_back_to_writer_is_drafted_again():
    assert detect_phase(reviewed_state(passed=False, critique=None)) == DRAFTED


def test_interview_phases():
    turns = make_interview()
    assert detect_phase(reviewed_state(passed=True, interview=turns)) == DONE

    unscored = [turns[0].model_copy(update={"score": None})]
    assert detect_phase(reviewed_state(passed=True, interview=unscored)) == INTERVIEWING


def test_bad_values_raise():
    with pytest.raises(TypeError):
        detect_phase("not a state")
    with pytest.raises(TypeError, match="Critique"):
        detect_phase(drafted_state(critique="looks good"))
    with pytest.raises(TypeError, match="InterviewTurn"):
        detect_phase(reviewed_state(passed=True, interview=["question 1"]))
