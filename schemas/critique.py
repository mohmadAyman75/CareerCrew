"""
critique.py  —  output of the Critic agent (Member 5).

passed = True only when there are zero unsupported claims
and the Match Score is high enough.
"""

from typing import Literal

from pydantic import Field

from schemas.base import StrictBase


class ClaimCheck(StrictBase):
    bullet_text: str
    verdict: Literal["supported", "partial", "unsupported"]
    reason: str


class Critique(StrictBase):
    match_score: float = Field(ge=0, le=100)
    score_breakdown: dict[str, float]
    claim_checks: list[ClaimCheck]
    feedback: list[str]                        # numbered notes for the Writer
    passed: bool
