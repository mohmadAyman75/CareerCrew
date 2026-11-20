# Supervisor agent (Member 1)

The team leader. After every step the graph comes back here, and the Supervisor decides what runs next.
It never calls an LLM for clear transitions: plain rules, so the same state always gives the same decision.

## How it works

```
agent.run(state)
  1. phase.py    detect_phase()      where are we now?
  2. checks.py   run_input_checks()  is there a problem in the user's input?
  3. router.py   decide()            what runs next?  -> RoutingDecision
  4. actions.py  route_to()          write the decision into the state
```

`actions.ask_user` is its own graph node: it pauses the graph with `interrupt()` until the user answers.

## Inputs and outputs

| Reads | Writes |
|---|---|
| everything in the state | `next_steps`, `instruction`, `question`, `round`, `critique` (set to None before a new round), `events` |

`ask_user` writes the user's answers: `cv_confirmed`, `continue_low_fit`, `approved`, `stopped`, or new `cv_text` / `job_text`.

## Decision table

| Situation | Next step |
|---|---|
| user stopped | end |
| bad input | ask_user (`fix_input`) |
| no profile or no job | profile + job_intel (parallel) |
| not a real job post | ask_user (`not_a_job`) |
| CV parse confidence < 0.6, not confirmed | ask_user (`unclear_cv`) |
| no gap | fit_check |
| fit score < 40, user did not say continue | ask_user (`low_fit`) |
| no draft | writer |
| draft, no critique | critic |
| critic failed, round < 3 | writer (round + 1, critic feedback as `instruction`) |
| critic passed, or round = 3 | ask_user (`approve`) |
| approved | interview |
| interview finished | end |

The numbers (0.6, 40, 3) are in `configs/supervisor.yaml`.

## Answers the user can send

| Question | Answer |
|---|---|
| any | `{"stop": true}` |
| `fix_input`, `not_a_job` | `{"cv_text": "..."}` and/or `{"job_text": "..."}` |
| `unclear_cv` | `{"confirmed": true}` or a new `{"cv_text": "..."}` |
| `low_fit` | `{"continue": true}` |
| `approve` | `{"approved": true}` |

## How to test

```bash
python -m pytest tests/test_router.py tests/test_phase.py tests/test_checks.py tests/test_actions.py
python -m agents.supervisor.checks              # input checks on the sample files
python -m scripts.run_session --scenario happy  # a full session with fake agents
```

## Still to do

- `chat_router.py` + `prompts/chat_route.md`: map chat messages ("make it shorter") to an agent with the LLM.
- SQLite checkpointer instead of the in-memory one, so sessions survive a restart.
- Daily quota guard: finish early when the model quota is almost used.
