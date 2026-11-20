"""Tests for graph/registry.py and agents/fakes.py."""

import pytest

from agents.fakes import get_fake
from graph.registry import get_agent
from tests.helpers import inputs_state

ALL_FAKE = {"profile": "fake", "job_intel": "fake", "writer": "fake", "critic": "fake", "interview": "fake"}


def test_fake_mode_returns_a_working_fake():
    run = get_agent("profile", modes=ALL_FAKE)
    update = run(inputs_state())
    assert set(update) == {"profile", "events"}          # only the keys it owns


def test_fake_checks_its_input_like_the_real_agent():
    with pytest.raises(KeyError, match="cv_text"):
        get_fake("profile")({})


def test_unknown_agent_raises():
    with pytest.raises(ValueError, match="Unknown agent"):
        get_agent("hacker", modes=ALL_FAKE)


def test_bad_mode_raises():
    with pytest.raises(ValueError, match="'fake' or 'real'"):
        get_agent("profile", modes=ALL_FAKE | {"profile": "maybe"})


def test_real_agent_that_does_not_exist_yet_raises():
    with pytest.raises(ModuleNotFoundError):
        get_agent("profile", modes=ALL_FAKE | {"profile": "real"})


def test_unknown_scenario_raises():
    with pytest.raises(ValueError, match="scenario"):
        get_fake("profile", scenario="everything_breaks")
