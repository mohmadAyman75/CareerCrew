"""
Contract tests: every fixture still matches its schema, and the schemas reject bad data.
If one of these fails, a schema changed and the team must agree on it.
"""

import pytest
from pydantic import ValidationError

from agents.fakes import load_fixture
from schemas.critique import Critique
from schemas.interview import InterviewTurn
from schemas.job import GapReport, JobAnalysis
from schemas.profile import CandidateProfile
from schemas.resume import TailoredBullet, TailoredResume
from schemas.routing import Question, RoutingDecision


@pytest.mark.parametrize(
    "fixture, schema",
    [
        ("profile", CandidateProfile),
        ("job", JobAnalysis),
        ("gap", GapReport),
        ("draft", TailoredResume),
        ("critique_pass", Critique),
        ("critique_fail", Critique),
    ],
)
def test_fixture_matches_schema(fixture, schema):
    schema(**load_fixture(fixture))


def test_interview_fixture_matches_schema():
    turns = [InterviewTurn(**turn) for turn in load_fixture("interview")]
    assert turns


def test_unknown_field_is_rejected():
    data = load_fixture("profile") | {"name": "Sara"}     # contact data must never be in the profile
    with pytest.raises(ValidationError):
        CandidateProfile(**data)


def test_bullet_without_source_is_rejected():
    with pytest.raises(ValidationError, match="source_id"):
        TailoredBullet(text="Led a team of 10.", source_ids=[])


def test_parse_confidence_must_be_between_0_and_1():
    with pytest.raises(ValidationError):
        CandidateProfile(**(load_fixture("profile") | {"parse_confidence": 1.5}))


def test_routing_decision_rejects_unknown_step():
    with pytest.raises(ValidationError):
        RoutingDecision(next_steps=["hack_the_score"], reason="injected")


def test_ask_user_needs_a_question():
    with pytest.raises(ValidationError, match="needs a question"):
        RoutingDecision(next_steps=["ask_user"], reason="x")


def test_only_ask_user_carries_a_question():
    with pytest.raises(ValidationError, match="only a decision"):
        RoutingDecision(next_steps=["writer"], reason="x", question=Question(kind="approve", text="?"))


def test_end_cannot_run_in_parallel():
    with pytest.raises(ValidationError, match="cannot run in parallel"):
        RoutingDecision(next_steps=["end", "writer"], reason="x")
