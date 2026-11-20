"""
profile.py  —  output of the Profile agent (Member 2): the CV as structured data.

Every bullet has an ID (for example "exp1_b2"), so the Writer can link
each new bullet to the original line it came from.
"""

from pydantic import Field

from schemas.base import StrictBase


class Bullet(StrictBase):
    id: str                       # e.g. "exp1_b2"
    text: str


class Experience(StrictBase):
    id: str                       # e.g. "exp1"
    title: str
    organization: str
    start: str | None             # "2024-03"
    end: str | None               # None means "present"
    bullets: list[Bullet]


class Education(StrictBase):
    id: str
    degree: str
    institution: str
    start: str | None
    end: str | None


class Skill(StrictBase):
    raw: str                      # as written in the CV
    esco_id: str | None           # None means "not mapped yet"
    label: str | None             # the standard name
    evidence_ids: list[str]       # bullets that prove this skill


class CandidateProfile(StrictBase):
    headline: str | None
    summary: str | None
    experiences: list[Experience]
    projects: list[Experience]
    education: list[Education]
    skills: list[Skill]
    certifications: list[str]
    parse_confidence: float = Field(ge=0, le=1)   # 0 = unreadable, 1 = perfect
