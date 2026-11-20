"""Tests for agents/supervisor/actions.py: route_to() and apply_answer()."""

import pytest

from agents.supervisor.actions import apply_answer, route_to
from agents.supervisor.router import ask, go
from tests.helpers import reviewed_state


def test_route_to_writer_starts_a_new_round_and_clears_the_review():
    update = route_to(reviewed_state(passed=False, round_number=1), go("writer", "retry", "fix bullet 2"))
    assert update["next_steps"] == ["writer"]
    assert update["round"] == 2
    assert update["critique"] is None
    assert update["instruction"] == "fix bullet 2"


def test_route_to_other_step_keeps_round_and_review():
    update = route_to(reviewed_state(passed=True), go("interview", "go"))
    assert "round" not in update
    assert "critique" not in update


def test_route_to_writes_the_question_and_a_timeline_event():
    update = route_to({}, ask("approve", "Approve?", reason="ask"))
    assert update["question"].kind == "approve"
    assert update["events"] == [{"agent": "supervisor", "message": "ask"}]


def test_route_to_validates_input():
    with pytest.raises(TypeError):
        route_to({}, {"next_steps": ["writer"]})


def test_yes_answers_set_their_flag():
    assert apply_answer("approve", {"approved": True}) == {"approved": True}
    assert apply_answer("low_fit", {"continue": True}) == {"continue_low_fit": True}
    assert apply_answer("unclear_cv", {"confirmed": True}) == {"cv_confirmed": True}


def test_no_or_stop_ends_the_session():
    assert apply_answer("approve", {"approved": False}) == {"stopped": True}
    assert apply_answer("fix_input", {"stop": True}) == {"stopped": True}


def test_new_text_clears_old_results():
    update = apply_answer("not_a_job", {"job_text": "new job post"})
    assert update["job_text"] == "new job post"
    assert update["job"] is None
    assert update["round"] == 0


def test_bad_answers_raise():
    with pytest.raises(TypeError):
        apply_answer("approve", "yes")
    with pytest.raises(ValueError, match="approved"):
        apply_answer("approve", {"approved": "yes"})
    with pytest.raises(ValueError, match="cv_text"):
        apply_answer("fix_input", {})
    with pytest.raises(TypeError):
        apply_answer("fix_input", {"cv_text": 42})
    with pytest.raises(ValueError, match="Unknown question"):
        apply_answer("hello", {})
