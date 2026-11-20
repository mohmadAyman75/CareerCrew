"""
run_session.py  —  run one full session in the terminal (owner: Member 1).

It uses the sample CV and job post, answers every question automatically,
and prints the timeline of what each agent did.

Run it from the project root:
    python -m scripts.run_session
    python -m scripts.run_session --scenario critic_rejects_once
    python -m scripts.run_session --scenario low_fit --cv my_cv.pdf --job my_job.txt
"""

import argparse

from agents.fakes import SCENARIOS
from graph.builder import build_graph
from graph.session import answer_question, get_session_state, start_session
from tools.document_parser import load_cv, load_job

# The answer this script gives to each kind of question
AUTO_ANSWERS = {
    "fix_input": {"stop": True},       # we cannot invent a new CV, so we stop
    "not_a_job": {"stop": True},
    "unclear_cv": {"confirmed": True},
    "low_fit": {"continue": True},
    "approve": {"approved": True},
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one CareerCrew session with the fake agents.")
    parser.add_argument("--scenario", default="happy", choices=SCENARIOS)
    parser.add_argument("--cv", default="data/samples/synthetic_cv_01.pdf")
    parser.add_argument("--job", default="data/samples/job_01.txt")
    args = parser.parse_args()

    graph = build_graph(scenario=args.scenario)
    session_id = f"demo-{args.scenario}"

    question = start_session(graph, session_id, load_cv(args.cv), load_job(args.job))
    while question is not None:
        answer = AUTO_ANSWERS[question["kind"]]
        print(f"\n  QUESTION ({question['kind']}): {question['text']}")
        print(f"  ANSWER: {answer}\n")
        question = answer_question(graph, session_id, answer)

    state = get_session_state(graph, session_id)
    print(f"\nTimeline ({args.scenario}):")
    for number, line in enumerate(state["events"], start=1):
        print(f"  {number:>2}. [{line['agent']:<10}] {line['message']}")

    print("\nResult:")
    print(f"  fit score : {state.get('fit_score')}")
    print(f"  rounds    : {state.get('round')}")
    print(f"  approved  : {state.get('approved', False)}")
    print(f"  stopped   : {state.get('stopped', False)}")


if __name__ == "__main__":
    main()
