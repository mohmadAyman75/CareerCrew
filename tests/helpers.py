"""
helpers.py  —  build test states from the fixtures, so every test stays short.

Each make_*() function returns a real schema object. Pass keyword arguments
to change a field, for example make_profile(parse_confidence=0.3).
"""

from agents.fakes import load_fixture
from config import ROOT
from schemas.critique import Critique
from schemas.interview import InterviewTurn
from schemas.job import GapReport, JobAnalysis
from schemas.profile import CandidateProfile
from schemas.resume import TailoredResume
from tools.document_parser import load_cv, load_job

CV_TEXT = load_cv(ROOT / "data" / "samples" / "synthetic_cv_01.pdf")
JOB_TEXT = load_job(ROOT / "data" / "samples" / "job_01.txt")


def make_profile(**changes) -> CandidateProfile:
    return CandidateProfile(**load_fixture("profile")).model_copy(update=changes)


def make_job(**changes) -> JobAnalysis:
    return JobAnalysis(**load_fixture("job")).model_copy(update=changes)


def make_gap() -> GapReport:
    return GapReport(**load_fixture("gap"))


def make_draft() -> TailoredResume:
    return TailoredResume(**load_fixture("draft"))


def make_critique(passed: bool) -> Critique:
    return Critique(**load_fixture("critique_pass" if passed else "critique_fail"))


def make_interview() -> list[InterviewTurn]:
    return [InterviewTurn(**turn) for turn in load_fixture("interview")]


# Each helper adds its defaults FIRST, so a value passed by the test always wins.

def inputs_state(**changes) -> dict:
    """A state with only the inputs, as the API creates it."""
    return {"cv_text": CV_TEXT, "job_text": JOB_TEXT, "round": 0, **changes}


def analyzed_state(**changes) -> dict:
    """Profile and Job Intel are done."""
    return inputs_state(**{"profile": make_profile(), "job": make_job(), **changes})


def ready_to_write_state(**changes) -> dict:
    """fit_check is done, with a good fit score."""
    return analyzed_state(**{"gap": make_gap(), "fit_score": 74.0, **changes})


def drafted_state(round_number: int = 1, **changes) -> dict:
    """The Writer made a draft; the Critic did not review it yet."""
    return ready_to_write_state(**{"draft": make_draft(), "round": round_number, **changes})


def reviewed_state(passed: bool, round_number: int = 1, **changes) -> dict:
    """The Critic reviewed the draft."""
    return drafted_state(round_number, **{"critique": make_critique(passed), **changes})
