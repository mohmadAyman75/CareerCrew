"""
routing.py  —  output of the Supervisor agent (Member 1).

RoutingDecision = where the graph goes next, and why.
"""

from typing import Literal

from pydantic import model_validator

from schemas.base import StrictBase

# Every place the Supervisor may send the session. Nothing else is allowed,
# so a prompt injection inside a CV can never invent a new route.
NextStep = Literal[
    "profile", "job_intel", "fit_check", "writer", "critic", "ask_user", "interview", "end",
]

# The questions the Supervisor may ask the user.
QuestionKind = Literal["fix_input", "not_a_job", "unclear_cv", "low_fit", "approve"]


class Question(StrictBase):
    kind: QuestionKind
    text: str                                  # shown to the user


class RoutingDecision(StrictBase):
    next_steps: list[NextStep]                 # more than one = run in parallel
    reason: str                                # shown on the UI timeline
    instruction: str | None = None             # extra note for the next agent (e.g. critic feedback)
    question: Question | None = None           # needed when next_steps is ["ask_user"]

    @model_validator(mode="after")
    def check_consistency(self) -> "RoutingDecision":
        if not self.next_steps:
            raise ValueError("next_steps cannot be empty")
        if len(self.next_steps) != len(set(self.next_steps)):
            raise ValueError(f"next_steps has duplicates: {self.next_steps}")

        asks_user = "ask_user" in self.next_steps
        if asks_user and self.question is None:
            raise ValueError("a decision that goes to 'ask_user' needs a question")
        if not asks_user and self.question is not None:
            raise ValueError("only a decision that goes to 'ask_user' may carry a question")
        if (asks_user or "end" in self.next_steps) and len(self.next_steps) > 1:
            raise ValueError("'ask_user' and 'end' cannot run in parallel with other steps")
        return self
