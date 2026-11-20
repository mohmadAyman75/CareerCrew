"""Tests for agents/supervisor/checks.py: user problems return a message, our bugs raise."""

import pytest

from agents.supervisor.checks import (
    count_job_keywords,
    cv_is_clear,
    fit_is_high_enough,
    is_english,
    job_is_real,
    run_input_checks,
)
from tests.helpers import analyzed_state, inputs_state, make_job, make_profile


def test_sample_files_pass_all_input_checks():
    assert run_input_checks(inputs_state()) is None


def test_empty_cv_asks_for_a_text_pdf():
    assert "text-based PDF" in run_input_checks(inputs_state(cv_text=""))


def test_arabic_cv_is_rejected():
    assert "English" in run_input_checks(inputs_state(cv_text="سيرة ذاتية " * 50))


def test_short_job_text_is_rejected():
    assert "too short" in run_input_checks(inputs_state(job_text="Python job"))


def test_long_job_text_is_rejected():
    assert "too long" in run_input_checks(inputs_state(job_text="job skills " * 2000))


def test_text_that_is_not_a_job_is_rejected():
    assert "does not look like a job post" in run_input_checks(inputs_state(job_text="I like pizza and football. " * 20))


def test_missing_key_is_a_bug_and_raises():
    with pytest.raises(KeyError, match="job_text"):
        run_input_checks({"cv_text": "x" * 300})


def test_wrong_type_is_a_bug_and_raises():
    with pytest.raises(TypeError):
        run_input_checks(inputs_state(cv_text=123))


def test_pure_functions_validate_their_input():
    assert is_english("Hello world")
    assert count_job_keywords("Requirements and skills") == 2
    with pytest.raises(TypeError):
        is_english(None)
    with pytest.raises(TypeError):
        count_job_keywords(42)


def test_after_agent_checks():
    assert job_is_real(analyzed_state()) is None
    assert job_is_real(analyzed_state(job=make_job(is_valid_job_post=False))) is not None

    assert cv_is_clear(analyzed_state()) is None
    assert cv_is_clear(analyzed_state(profile=make_profile(parse_confidence=0.3))) is not None

    assert fit_is_high_enough({"fit_score": 74.0}) is None
    assert "20/100" in fit_is_high_enough({"fit_score": 20.0})
