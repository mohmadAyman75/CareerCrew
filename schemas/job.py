"""
job.py  —  output of the Job Intelligence agent (Member 3) and of fit_check.

JobAnalysis = what the job asks for.
GapReport   = what the candidate has, partly has, and misses.
"""

from typing import Literal

from schemas.base import StrictBase


class SkillRequirement(StrictBase):
    raw: str                                   # as written in the job post
    esco_id: str | None
    label: str | None
    importance: Literal["must", "nice", "implied"]


class JobAnalysis(StrictBase):
    is_valid_job_post: bool
    title: str
    seniority: Literal["intern", "junior", "mid", "senior", "lead"]
    min_years: int | None
    requirements: list[SkillRequirement]
    responsibilities: list[str]


class LearningItem(StrictBase):
    skill: str
    suggestion: str                            # how to learn it


class GapReport(StrictBase):
    matched: list[str]
    partial: list[str]
    missing: list[str]
    learning_plan: list[LearningItem]
