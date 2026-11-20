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

The numbers live in configs/supervisor.yaml.
"""

from config import load_yaml
from graph.validate import require, require_dict
from schemas.job import JobAnalysis
from schemas.profile import CandidateProfile

SETTINGS = load_yaml("supervisor.yaml")


# ---------------- Pure functions: they take a value, easy to test ----------------

def is_english(text: str) -> bool:
    """True if almost all the letters in the text are not Arabic."""
    if not isinstance(text, str):
        raise TypeError(f"is_english() needs a string, got {type(text).__name__}")

    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False

    arabic_letters = [c for c in letters if "\u0600" <= c <= "\u06FF"]
    return len(arabic_letters) / len(letters) <= SETTINGS["max_arabic_ratio"]


def count_job_keywords(text: str) -> int:
    """How many words from the job keyword list appear in the text."""
    if not isinstance(text, str):
        raise TypeError(f"count_job_keywords() needs a string, got {type(text).__name__}")

    text = text.lower()
    return sum(1 for word in SETTINGS["job_keywords"] if word in text)


# ---------------- Input checks: they run before any agent ----------------

def cv_has_text(state: dict) -> str | None:
    cv_text = require(state, "cv_text", str)

    if len(cv_text.strip()) < SETTINGS["min_cv_chars"]:
        return (
            "We could not read enough text from your CV. "
            "If it is a scanned image, please upload a text-based PDF."
        )
    return None


def cv_language_ok(state: dict) -> str | None:
    cv_text = require(state, "cv_text", str)

    if not is_english(cv_text):
        return "Only English CVs are supported for now. Please upload an English version of your CV."
    return None


def job_has_text(state: dict) -> str | None:
    job_text = require(state, "job_text", str)
    length = len(job_text.strip())

    if length < SETTINGS["min_job_chars"]:
        return "The job description is too short. Please paste the full job post."
    if length > SETTINGS["max_job_chars"]:
        return (
            f"The job description is too long ({length} characters). "
            f"Please paste only the job post (maximum {SETTINGS['max_job_chars']} characters)."
        )
    return None


def job_looks_like_job(state: dict) -> str | None:
    job_text = require(state, "job_text", str)

    if count_job_keywords(job_text) < SETTINGS["min_job_keywords"]:
        return "This text does not look like a job post. Please paste the real job description."
    return None


# The order matters: we check that the text exists BEFORE checking its language,
# otherwise an empty CV would be reported as "not English".
INPUT_CHECKS = [cv_has_text, cv_language_ok, job_has_text, job_looks_like_job]


def run_input_checks(state: dict) -> str | None:
    """Run the input checks in order. Return the FIRST problem, or None if all pass."""
    require_dict(state, "run_input_checks")

    for check in INPUT_CHECKS:
        problem = check(state)
        if problem is not None:
            return problem
    return None


# ---------------- Checks after an agent ran ----------------

def job_is_real(state: dict) -> str | None:
    """After Job Intel: did the LLM decide the text is a real job post?"""
    job = require(state, "job", JobAnalysis)

    if not job.is_valid_job_post:
        return "This text does not look like a real job post. Please paste the full job description."
    return None


def cv_is_clear(state: dict) -> str | None:
    """After Profile: was the CV read with enough confidence?"""
    profile = require(state, "profile", CandidateProfile)

    if profile.parse_confidence < SETTINGS["min_parse_confidence"]:
        return (
            "Some parts of your CV were not clear to us. "
            "Please check the extracted sections and confirm, or upload a clearer CV."
        )
    return None


def fit_is_high_enough(state: dict) -> str | None:
    """After fit_check: is the CV close enough to the job to be worth tailoring?"""
    fit_score = require(state, "fit_score", (int, float))

    if fit_score < SETTINGS["min_fit_score"]:
        return (
            f"Your CV matches this job at only {fit_score:.0f}/100. "
            "See the gap report. Do you want to tailor the CV anyway?"
        )
    return None


if __name__ == "__main__":
    import sys

    from tools.document_parser import load_cv, load_job

    # You can pass your own files:
    #   python -m agents.supervisor.checks "D:/path/my_cv.pdf" "D:/path/my_job.txt"
    # If you pass nothing, it uses the sample files.
    if len(sys.argv) == 3:
        cv_path, job_path = sys.argv[1], sys.argv[2]
    else:
        cv_path, job_path = "data/samples/synthetic_cv_01.pdf", "data/samples/job_01.txt"

    state = {"cv_text": load_cv(cv_path), "job_text": load_job(job_path)}

    print("CV file  :", cv_path, "->", len(state["cv_text"]), "characters")
    print("Job file :", job_path, "->", len(state["job_text"]), "characters")

    problem = run_input_checks(state)
    print("Result   :", "All checks passed" if problem is None else problem)
