"""Tests for graph/fit_check.py (the temporary fit score)."""

import pytest

from graph import fit_check
from tests.helpers import analyzed_state, make_job, make_profile


def test_sample_cv_and_job_give_the_expected_score():
    update = fit_check.run(analyzed_state())
    # must: 7 of 8 matched (A/B testing missing); nice: 2 of 6 (FastAPI, Git)
    # 100 x (0.75 x 7/8 + 0.25 x 2/6) = 74.0
    assert update["fit_score"] == 74.0
    assert "A/B testing" in update["gap"].missing
    assert "Python" in update["gap"].matched


def test_no_skills_gives_zero():
    assert fit_check.run(analyzed_state(profile=make_profile(skills=[])))["fit_score"] == 0.0


def test_job_without_requirements_gives_full_score():
    assert fit_check.run(analyzed_state(job=make_job(requirements=[])))["fit_score"] == 100.0


def test_missing_profile_raises():
    with pytest.raises(KeyError, match="profile"):
        fit_check.run({"job": make_job()})
