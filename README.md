# CareerCrew — Multi-Agent Job Application Assistant

> Six AI agents that tailor your CV to any job, and refuse to lie for you.

CareerCrew takes a CV and a job description, tailors the CV to the job **without inventing anything**,
explains the skill gap, and runs a mock interview for that exact job. Six LLM-powered agents work as one
team, coordinated by **LangGraph**. DEPI graduation project — 6 members, 1 agent each.

The full design is in [`CareerCrew — Multi-Agent Job Application Assistant (Project Spec).docx`](<CareerCrew — Multi-Agent Job Application Assistant (Project Spec).docx>).

![Runtime pipeline](careercrew_runtime_pipeline.png)

## The agents

| # | Agent | Job | Owner |
|---|---|---|---|
| 1 | Supervisor | checks the inputs and decides which agent runs next | Member 1 |
| 2 | Profile | CV file → structured candidate profile | Member 2 |
| 3 | Job Intelligence | job post → requirements + gap report | Member 3 |
| 4 | Resume Writer | tailored CV, every bullet linked to its source | Member 4 |
| 5 | Critic | fact-checks the draft and computes the Match Score | Member 5 |
| 6 | Interview Coach | job-specific mock interview with scored feedback | Member 6 |

## Status

Work in progress. Done so far:
- `tools/document_parser.py`: reads a PDF CV and a `.txt` job post
- `agents/supervisor_agent/checks.py`: input checks (CV text, English only, real job post)
- `agents/supervisor_agent/phase.py`: detects the current phase from the shared state

## Setup

Requires Python 3.11 (3.10 also works).

```bash
python -m venv venv
venv\Scripts\activate            # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # Mac/Linux: cp .env.example .env
```

Then open `.env` and paste your free Groq API key (from https://console.groq.com/keys).
Never commit `.env`.

## Run

From the project root:

```bash
python -m tools.document_parser
python -m agents.supervisor_agent.checks
python -m agents.supervisor_agent.phase
```

`checks` also accepts your own files:

```bash
python -m agents.supervisor_agent.checks path/to/cv.pdf path/to/job.txt
```

## Project structure (current)

```
agents/
  supervisor_agent/      Member 1: checks.py, phase.py, prompts/
tools/
  document_parser.py     load_cv(), load_job()
schema/                  shared schemas and configs
data/
  samples/               synthetic CV + job post for demos and tests
  raw/, processed/       datasets (git-ignored, rebuilt by scripts)
tests/
UI/
app/
eval/
```

The target structure (src layout, one folder per agent) is in section 10 of the spec.

## Data rules

- **No real CV or personal data in Git** (spec section 7.4). Use the synthetic samples in `data/samples/`.
- Keep real CVs in `data/private/` on your machine. That folder is git-ignored.
- `.env`, `data/raw/` and processed Parquet files are git-ignored.
- Notebooks and quick experiments go in `scratch/`, which is git-ignored.
