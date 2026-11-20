"""
builder.py  —  builds the LangGraph graph (owner: Member 1).

The shape is a hub and spoke:
    START -> supervisor -> (one or more steps) -> supervisor -> ... -> END

Every step returns to the Supervisor, and only the Supervisor decides what runs next.
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph

from agents.supervisor import agent as supervisor
from agents.supervisor.actions import ask_user
from graph import fit_check
from graph.registry import WORKER_AGENTS, get_agent
from graph.state import GraphState
from graph.validate import require

# Every step the Supervisor may choose, except "end"
STEPS = (*WORKER_AGENTS, "fit_check", "ask_user")

# Supervisor's choice -> graph node
PATH_MAP = {step: step for step in STEPS} | {"end": END}

# The schema objects the checkpointer may save and load back.
# A new schema stored in the state must be added here.
SAVED_SCHEMAS = [
    ("schemas.profile", "CandidateProfile"),
    ("schemas.job", "JobAnalysis"),
    ("schemas.job", "GapReport"),
    ("schemas.resume", "TailoredResume"),
    ("schemas.critique", "Critique"),
    ("schemas.interview", "InterviewTurn"),
    ("schemas.routing", "Question"),
]


def build_graph(scenario: str = "happy", modes: dict | None = None, checkpointer=None):
    """
    Build and compile the graph.

    scenario      used by the fake agents (see agents/fakes.py)
    modes         {"profile": "fake", ...}; read from configs/agents.yaml when not given
    checkpointer  saves the state between pauses; in memory when not given
                  (a SQLite checkpointer comes later, so sessions survive a restart)
    """
    graph = StateGraph(GraphState)

    graph.add_node("supervisor", supervisor.run)
    graph.add_node("fit_check", fit_check.run)
    graph.add_node("ask_user", ask_user)
    for name in WORKER_AGENTS:
        graph.add_node(name, get_agent(name, scenario, modes))

    graph.add_edge(START, "supervisor")
    for step in STEPS:
        graph.add_edge(step, "supervisor")          # always come back to the Supervisor

    graph.add_conditional_edges("supervisor", next_steps, PATH_MAP)

    if checkpointer is None:
        checkpointer = InMemorySaver(serde=JsonPlusSerializer(allowed_msgpack_modules=SAVED_SCHEMAS))
    return graph.compile(checkpointer=checkpointer)


def next_steps(state: dict) -> list[str]:
    """Read the Supervisor's decision from the state."""
    steps = require(state, "next_steps", list)
    unknown = [step for step in steps if step not in PATH_MAP]
    if unknown:
        raise ValueError(f"The Supervisor chose unknown steps: {unknown}")
    return steps
