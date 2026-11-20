"""
base.py  —  the parent class of every schema.

extra="forbid" means: an unknown field is an error, not silently ignored.
Groq's strict mode needs this for every schema an LLM fills (spec, section 9.4).
"""

from pydantic import BaseModel, ConfigDict


class StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
