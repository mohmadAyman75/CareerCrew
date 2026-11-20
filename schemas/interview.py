"""
interview.py  —  output of the Interview Coach agent (Member 6).

One InterviewTurn = one question, the candidate's answer, and its score.
"""

from typing import Literal

from pydantic import Field

from schemas.base import StrictBase


class AnswerScore(StrictBase):
    relevance: int = Field(ge=1, le=5)
    depth: int = Field(ge=1, le=5)
    structure: int = Field(ge=1, le=5)        # STAR structure
    evidence: int = Field(ge=1, le=5)
    feedback: str
    better_answer_outline: list[str]


class InterviewTurn(StrictBase):
    question: str
    kind: Literal["technical", "behavioral", "role"]
    answer: str | None
    follow_up: str | None
    score: AnswerScore | None                  # None until the answer is scored
