"""
resume.py  —  output of the Resume Writer agent (Member 4).

The zero-fabrication rule: every bullet must point to at least one
original bullet in the CandidateProfile (source_ids).
"""

from pydantic import field_validator

from schemas.base import StrictBase


class TailoredBullet(StrictBase):
    text: str
    source_ids: list[str]

    @field_validator("source_ids")
    @classmethod
    def must_have_a_source(cls, source_ids: list[str]) -> list[str]:
        # Checked in Python, not with min_length, because Groq's strict mode
        # does not support size limits (spec, section 9.4).
        if not source_ids:
            raise ValueError("every tailored bullet needs at least one source_id")
        return source_ids


class TailoredSection(StrictBase):
    title: str                                 # e.g. "Experience"
    bullets: list[TailoredBullet]


class TailoredResume(StrictBase):
    version: int                               # 1, 2, 3: one per writer round
    summary: TailoredBullet
    sections: list[TailoredSection]
