"""
registry.py  —  gives the graph the fake or the real version of each agent.

configs/agents.yaml says "fake" or "real" for each agent.
When a teammate finishes an agent, they change one word there. Nothing else changes.
"""

import importlib
from collections.abc import Callable

from agents.fakes import get_fake
from config import load_yaml

WORKER_AGENTS = ("profile", "job_intel", "writer", "critic", "interview")


def get_agent(name: str, scenario: str = "happy", modes: dict | None = None) -> Callable[[dict], dict]:
    """
    Return the run(state) function of agent `name`.

    scenario  only used by fake agents (see agents/fakes.py)
    modes     {"profile": "fake", ...}; read from configs/agents.yaml when not given
    """
    if name not in WORKER_AGENTS:
        raise ValueError(f"Unknown agent '{name}'. Known agents: {list(WORKER_AGENTS)}")

    if modes is None:
        modes = load_yaml("agents.yaml")
    if name not in modes:
        raise KeyError(f"configs/agents.yaml has no line for '{name}'")

    mode = modes[name]
    if mode == "fake":
        return get_fake(name, scenario)
    if mode == "real":
        return _load_real_agent(name)
    raise ValueError(f"configs/agents.yaml: '{name}' must be 'fake' or 'real', got '{mode}'")


def _load_real_agent(name: str) -> Callable[[dict], dict]:
    """Import agents/<name>/agent.py and return its run function."""
    module = importlib.import_module(f"agents.{name}.agent")
    run = getattr(module, "run", None)
    if not callable(run):
        raise AttributeError(f"agents/{name}/agent.py must define a function run(state) -> dict")
    return run
