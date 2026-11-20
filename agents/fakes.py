"""
fakes.py  —  fake versions of the 5 worker agents (owner: Member 1).

Each fake has the same shape as the real agent: it takes the state and
returns only the keys it owns. Instead of calling an LLM, it loads a
ready-made sample from tests/fixtures/.

This lets us build and test the whole graph before the real agents exist.

A "scenario" changes the samples a little, so we can test every route:
    happy                  everything goes well
    not_a_job              Job Intel says the text is not a job post
    unclear_cv             Profile has a low parse confidence
    low_fit                the candidate has none of the job's skills
    critic_rejects_once    the Critic rejects round 1, then accepts
    critic_rejects_always  the Critic rejects every round
"""

import json
from collections.abc import Callable

from config import ROOT
from graph.validate import require
from schemas.critique import Critique
from schemas.interview import InterviewTurn
from schemas.job import GapReport, JobAnalysis
from schemas.profile import CandidateProfile
from schemas.resume import TailoredResume

FIXTURES_DIR = ROOT / "tests" / "fixtures"

SCENARIOS = (
    "happy",
    "not_a_job",
    "unclear_cv",
    "low_fit",
    "critic_rejects_once",
    "critic_rejects_always",
)

UNCLEAR_PARSE_CONFIDENCE = 0.4   # below the 0.6 limit in configs/supervisor.yaml


# ---------------- Helpers ----------------

def load_fixture(name: str):
    """Read tests/fixtures/<name>.json and return its content."""
    path = FIXTURES_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def event(agent: str, message: str) -> dict:
    """One line for the UI timeline."""
    return {"agent": agent, "message": message}


# ---------------- The 5 fake agents ----------------

def fake_profile(state: dict, scenario: str) -> dict:
    require(state, "cv_text", str)

    profile = CandidateProfile(**load_fixture("profile"))
    if scenario == "unclear_cv":
        profile = profile.model_copy(update={"parse_confidence": UNCLEAR_PARSE_CONFIDENCE})
    if scenario == "low_fit":
        profile = profile.model_copy(update={"skills": []})

    return {"profile": profile, "events": [event("profile", "Fake profile loaded")]}


def fake_job_intel(state: dict, scenario: str) -> dict:
    require(state, "job_text", str)

    job = JobAnalysis(**load_fixture("job"))
    if scenario == "not_a_job":
        job = job.model_copy(update={"is_valid_job_post": False})

    return {"job": job, "events": [event("job_intel", "Fake job analysis loaded")]}


def fake_writer(state: dict, scenario: str) -> dict:
    require(state, "profile", CandidateProfile)
    require(state, "gap", GapReport)
    round_number = require(state, "round", int)

    draft = TailoredResume(**load_fixture("draft"))
    draft = draft.model_copy(update={"version": round_number})

    return {"draft": draft, "events": [event("writer", f"Fake draft v{round_number} written")]}


def fake_critic(state: dict, scenario: str) -> dict:
    require(state, "draft", TailoredResume)
    round_number = require(state, "round", int)

    rejects = scenario == "critic_rejects_always" or (
        scenario == "critic_rejects_once" and round_number == 1
    )
    critique = Critique(**load_fixture("critique_fail" if rejects else "critique_pass"))

    verdict = "rejected" if rejects else "accepted"
    return {"critique": critique, "events": [event("critic", f"Fake critic {verdict} draft v{round_number}")]}


def fake_interview(state: dict, scenario: str) -> dict:
    require(state, "draft", TailoredResume)
    require(state, "job", JobAnalysis)

    turns = [InterviewTurn(**turn) for turn in load_fixture("interview")]

    return {"interview": turns, "events": [event("interview", f"Fake interview with {len(turns)} questions")]}


FAKE_AGENTS = {
    "profile": fake_profile,
    "job_intel": fake_job_intel,
    "writer": fake_writer,
    "critic": fake_critic,
    "interview": fake_interview,
}


def get_fake(name: str, scenario: str = "happy") -> Callable[[dict], dict]:
    """Return the fake agent `name`, ready to use as a graph node: run(state) -> dict."""
    if name not in FAKE_AGENTS:
        raise ValueError(f"No fake for '{name}'. Fakes exist for: {list(FAKE_AGENTS)}")
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Choose one of: {list(SCENARIOS)}")

    fake = FAKE_AGENTS[name]

    def run(state: dict) -> dict:
        return fake(state, scenario)

    run.__name__ = f"fake_{name}"
    return run
