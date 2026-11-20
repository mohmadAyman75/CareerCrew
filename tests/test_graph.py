"""
Full sessions with the fake agents: one test per scenario.
These prove the agents are linked correctly, from START to END.
"""

import pytest

from graph.builder import build_graph
from graph.session import answer_question, get_session_state, start_session
from tests.helpers import CV_TEXT, JOB_TEXT


def start(scenario: str) -> tuple:
    graph = build_graph(scenario=scenario)
    question = start_session(graph, scenario, CV_TEXT, JOB_TEXT)
    return graph, question


def agents_that_ran(graph, session_id: str) -> list[str]:
    return [line["agent"] for line in get_session_state(graph, session_id)["events"] if line["agent"] != "supervisor"]


def test_happy_path_runs_from_start_to_end():
    graph, question = start("happy")
    assert question["kind"] == "approve"

    assert answer_question(graph, "happy", {"approved": True}) is None      # finished

    state = get_session_state(graph, "happy")
    assert state["round"] == 1
    assert state["fit_score"] == 74.0
    assert len(state["interview"]) == 2
    ran = agents_that_ran(graph, "happy")
    assert set(ran[:2]) == {"profile", "job_intel"}                        # ran in parallel
    assert ran[2:] == ["fit_check", "writer", "critic", "user", "interview"]


def test_not_a_job_pauses_and_can_stop():
    graph, question = start("not_a_job")
    assert question["kind"] == "not_a_job"

    assert answer_question(graph, "not_a_job", {"stop": True}) is None
    state = get_session_state(graph, "not_a_job")
    assert state["stopped"] is True
    assert state.get("draft") is None                                      # the writer never ran


def test_unclear_cv_continues_after_the_user_confirms():
    graph, question = start("unclear_cv")
    assert question["kind"] == "unclear_cv"

    question = answer_question(graph, "unclear_cv", {"confirmed": True})
    assert question["kind"] == "approve"


def test_low_fit_asks_then_tailors_anyway():
    graph, question = start("low_fit")
    assert question["kind"] == "low_fit"

    question = answer_question(graph, "low_fit", {"continue": True})
    assert question["kind"] == "approve"


def test_low_fit_can_stop():
    graph, _ = start("low_fit")
    assert answer_question(graph, "low_fit", {"continue": False}) is None
    assert get_session_state(graph, "low_fit")["stopped"] is True


def test_critic_rejects_once_then_accepts():
    graph, question = start("critic_rejects_once")
    assert question["kind"] == "approve"
    state = get_session_state(graph, "critic_rejects_once")
    assert state["round"] == 2
    assert state["critique"].passed is True


def test_critic_rejects_three_times_then_asks_the_user():
    graph, question = start("critic_rejects_always")
    assert question["kind"] == "approve"
    assert "still has notes" in question["text"]

    state = get_session_state(graph, "critic_rejects_always")
    assert state["round"] == 3                                             # stopped at the limit
    assert agents_that_ran(graph, "critic_rejects_always").count("writer") == 3


def test_answer_without_open_question_raises():
    graph, _ = start("happy")
    answer_question(graph, "happy", {"approved": True})
    with pytest.raises(RuntimeError, match="not waiting"):
        answer_question(graph, "happy", {"approved": True})
