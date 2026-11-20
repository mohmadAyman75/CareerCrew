"""
agent.py  —  the Supervisor agent (Member 1).

After every step the graph comes back here. The Supervisor:
    1. finds the phase          (phase.py)
    2. checks for problems      (checks.py)
    3. decides the next step    (router.py)
    4. writes the decision      (actions.py)
"""

from agents.supervisor.actions import route_to
from agents.supervisor.router import decide
from graph.validate import require_dict


def run(state: dict) -> dict:
    """Graph node: read the state, return where the session goes next."""
    require_dict(state, "supervisor.run")

    decision = decide(state)
    return route_to(state, decision)
