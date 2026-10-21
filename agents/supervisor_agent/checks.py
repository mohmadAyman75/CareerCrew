"""
checks.py  —  Supervisor, stage 2: "Is there a problem?"

There are two kinds of problems, and we treat them differently:

1) A bug in OUR code (for example: the state has no "cv_text").
   -> We RAISE an error. This should never happen, a developer must fix it.

2) A problem in the USER's input (for example: the CV is in Arabic).
   -> We do NOT raise. We RETURN a message for the user,
      so the Supervisor can pause and ask them to fix it.

So every check returns:
    None   -> everything is fine
    str    -> the problem, written as a message for the user
"""

# ---------------- Settings (later they move to configs/supervisor.yaml) ----------------

MIN_CV_CHARS = 200           # a real CV is longer than this
MIN_JOB_CHARS = 200          # a real job post is longer than this
MAX_JOB_CHARS = 15_000       # protects the LLM from a huge pasted text
MAX_ARABIC_RATIO = 0.05      # more than 5% Arabic letters -> not an English CV
MIN_JOB_KEYWORDS = 2         # a job post has at least 2 of the words below
MIN_PARSE_CONFIDENCE = 0.6   # from the spec, table 3.2

JOB_KEYWORDS = [
    "responsibilities", "requirements", "qualifications", "experience",
    "skills", "role", "apply", "job", "position", "team",
]


# ---------------- Helper: read from the state safely ----------------

def get_from_state(state: dict, key: str, expected_type: type):
    """Return state[key]. Raise a clear error if it is missing or has the wrong type."""
    if key not in state:
        raise KeyError(f"The state has no '{key}'. Did the loader run before the Supervisor?")

    value = state[key]
    if not isinstance(value, expected_type):
        raise TypeError(
            f"state['{key}'] should be {expected_type.__name__}, "
            f"but it is {type(value).__name__}"
        )
    return value


# ---------------- Pure functions: they take a value, easy to test ----------------

def is_english(text: str) -> bool:
    """True if almost all the letters in the text are not Arabic."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False

    arabic_letters = [c for c in letters if "\u0600" <= c <= "\u06FF"]
    return len(arabic_letters) / len(letters) <= MAX_ARABIC_RATIO


def count_job_keywords(text: str) -> int:
    """How many words from JOB_KEYWORDS appear in the text."""
    text = text.lower()
    return sum(1 for word in JOB_KEYWORDS if word in text)


# ---------------- Checks: they take the state (this is what the Supervisor calls) ----------------

def cv_has_text(state: dict) -> str | None:
    cv_text = get_from_state(state, "cv_text", str)

    if len(cv_text.strip()) < MIN_CV_CHARS:
        return (
            "We could not read enough text from your CV. "
            "If it is a scanned image, please upload a text-based PDF."
        )
    return None


def cv_language_ok(state: dict) -> str | None:
    cv_text = get_from_state(state, "cv_text", str)

    if not is_english(cv_text):
        return "Only English CVs are supported for now. Please upload an English version of your CV."
    return None


def job_has_text(state: dict) -> str | None:
    job_text = get_from_state(state, "job_text", str)
    length = len(job_text.strip())

    if length < MIN_JOB_CHARS:
        return "The job description is too short. Please paste the full job post."
    if length > MAX_JOB_CHARS:
        return (
            f"The job description is too long ({length} characters). "
            f"Please paste only the job post (maximum {MAX_JOB_CHARS} characters)."
        )
    return None


def job_looks_like_job(state: dict) -> str | None:
    job_text = get_from_state(state, "job_text", str)

    if count_job_keywords(job_text) < MIN_JOB_KEYWORDS:
        return "This text does not look like a job post. Please paste the real job description."
    return None


def cv_is_clear(state: dict) -> str | None:
    """Runs only AFTER the Profile agent, because it needs state['profile']."""
    profile = state.get("profile")
    if profile is None:
        return None  # the Profile agent did not run yet, nothing to check

    if not hasattr(profile, "parse_confidence"):
        raise AttributeError("state['profile'] has no 'parse_confidence'. Is it a CandidateProfile?")

    if profile.parse_confidence < MIN_PARSE_CONFIDENCE:
        return (
            "Some parts of your CV were not clear to us. "
            "Please check the extracted sections and fix anything missing."
        )
    return None


# ---------------- Run all the input checks ----------------

# The order matters: we check that the text exists BEFORE checking its language,
# otherwise an empty CV would be reported as "not English".
INPUT_CHECKS = [cv_has_text, cv_language_ok, job_has_text, job_looks_like_job]


def run_input_checks(state: dict) -> str | None:
    """Run the input checks in order. Return the FIRST problem, or None if all pass."""
    for check in INPUT_CHECKS:
        problem = check(state)
        if problem is not None:
            return problem
    return None


"""if __name__ == "__main__":
    # Quick manual test. Run it from the project root:
    #   uv run python -m careercrew.agents.supervisor.checks
    from tools.document_parser import load_cv, load_job

    state = {
        "cv_text": load_cv("data/samples/Mohamed_Ayman_CV_Fixed.pdf"),
        "job_text": load_job("data/samples/job_01.txt"),
    }
    print("Real files  ->", run_input_checks(state))

    # Bad inputs, to see the messages
    arabic_cv = {"cv_text": "سيرة ذاتية " * 50, "job_text": state["job_text"]}
    print("Arabic CV   ->", run_input_checks(arabic_cv))

    not_a_job = {"cv_text": state["cv_text"], "job_text": "I like pizza and football. " * 20}
    print("Not a job   ->", run_input_checks(not_a_job))

    empty_cv = {"cv_text": "", "job_text": state["job_text"]}
    print("Empty CV    ->", run_input_checks(empty_cv))

    # A bug on purpose: the state has no "job_text" -> this one RAISES an error
    # A bug on purpose: the state has no "job_text" -> this one RAISES an error
    try:
        run_input_checks({"cv_text": state["cv_text"]})
    except KeyError as error:
        print("Missing key ->", error)"""


if __name__ == "__main__":
    import sys
    from tools.document_parser import load_cv, load_job

    # You can pass your own files:
    #   python -m agents.supervisor_agent.checks "D:/path/my_cv.pdf" "D:/path/my_job.txt"
    # If you pass nothing, it uses the sample files.
    if len(sys.argv) == 3:
        cv_path = sys.argv[1]
        job_path = sys.argv[2]
    else:
        cv_path = "data/samples/Mohamed_Ayman_CV_Fixed.pdf"
        job_path = "data/samples/job_01.txt"

    state = {
        "cv_text": load_cv(cv_path),
        "job_text": load_job(job_path),
    }

    print("CV file  :", cv_path, "->", len(state["cv_text"]), "characters")
    print("Job file :", job_path, "->", len(state["job_text"]), "characters")

    problem = run_input_checks(state)
    if problem is None:
        print("Result   : All checks passed")
    else:
        print("Result   :", problem)