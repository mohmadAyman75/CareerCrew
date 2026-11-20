"""
state.py  —  SHARED: the one dictionary every agent reads and writes.

Rule: each key has ONE owner. Only the owner writes it.
Everyone may read every key.
"""

import operator
from typing import Annotated, TypedDict

from schemas.critique import Critique
from schemas.interview import InterviewTurn
from schemas.job import GapReport, JobAnalysis
from schemas.profile import CandidateProfile
from schemas.resume import TailoredResume
from schemas.routing import Question


class GraphState(TypedDict, total=False):
    # ---- Inputs (owner: API) ----
    session_id: str
    cv_text: str                     # contact block already removed
    job_text: str

    # ---- Agent outputs (owner: the agent named on the right) ----
    profile: CandidateProfile | None          # Profile agent
    job: JobAnalysis | None                   # Job Intel agent
    gap: GapReport | None                     # fit_check
    fit_score: float | None                   # fit_check (0 to 100)
    draft: TailoredResume | None              # Writer
    critique: Critique | None                 # Critic
    interview: list[InterviewTurn] | None     # Interview Coach

    # ---- Routing (owner: Supervisor) ----
    next_steps: list[str]            # where the graph goes next
    instruction: str | None          # note for the next agent (e.g. the critic's feedback)
    question: Question | None        # the open question for the user
    round: int                       # writer rounds done, max 3

    # ---- User answers (owner: Supervisor, written by ask_user) ----
    cv_confirmed: bool               # user says the unclear CV is fine
    continue_low_fit: bool           # user wants to tailor even with a low fit
    approved: bool                   # user approved the tailored CV
    stopped: bool                    # user ended the session

    # ---- Shared by everyone (add only, never replace) ----
    events: Annotated[list[dict], operator.add]   # lines for the UI timeline
