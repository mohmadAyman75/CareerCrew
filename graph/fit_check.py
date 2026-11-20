"""
fit_check.py  —  graph node: compare the CV with the job (owner: Member 1).

It runs after Profile and Job Intel, because it needs BOTH results.
It writes the gap report and the first fit score (0 to 100).

TEMPORARY: this is a simple exact-name match. When the shared tools are ready,
compute_gap() will come from Member 3 and compute_fit_score() from
tools/match_score.py (Member 5). The node's inputs and outputs stay the same.
"""

from config import load_yaml
from graph.validate import require
from schemas.job import GapReport, JobAnalysis, SkillRequirement
from schemas.profile import CandidateProfile

WEIGHTS = load_yaml("supervisor.yaml")["fit_score_weights"]


def run(state: dict) -> dict:
    """Graph node: build the gap report and the fit score."""
    profile = require(state, "profile", CandidateProfile)
    job = require(state, "job", JobAnalysis)

    gap = compute_gap(profile, job)
    score = compute_fit_score(gap, job)

    return {
        "gap": gap,
        "fit_score": score,
        "events": [{"agent": "fit_check", "message": f"Fit score {score:.0f}/100, {len(gap.missing)} skills missing"}],
    }


def skill_key(label: str | None, raw: str) -> str:
    """The name we compare: the standard label if we have one, else the raw text."""
    if not isinstance(raw, str):
        raise TypeError(f"raw must be a string, got {type(raw).__name__}")
    return (label or raw).strip().lower()


def compute_gap(profile: CandidateProfile, job: JobAnalysis) -> GapReport:
    """Split the job's skills into matched and missing."""
    if not isinstance(profile, CandidateProfile):
        raise TypeError("compute_gap() needs a CandidateProfile")
    if not isinstance(job, JobAnalysis):
        raise TypeError("compute_gap() needs a JobAnalysis")

    candidate_skills = {skill_key(skill.label, skill.raw) for skill in profile.skills}

    matched, missing = [], []
    for requirement in job.requirements:
        name = requirement.label or requirement.raw
        if skill_key(requirement.label, requirement.raw) in candidate_skills:
            matched.append(name)
        else:
            missing.append(name)

    return GapReport(matched=matched, partial=[], missing=missing, learning_plan=[])


def compute_fit_score(gap: GapReport, job: JobAnalysis) -> float:
    """Score = 100 x (must weight x must coverage + nice weight x nice coverage)."""
    if not isinstance(gap, GapReport):
        raise TypeError("compute_fit_score() needs a GapReport")
    if not isinstance(job, JobAnalysis):
        raise TypeError("compute_fit_score() needs a JobAnalysis")

    matched = {name.strip().lower() for name in gap.matched}
    must = [r for r in job.requirements if r.importance == "must"]
    nice = [r for r in job.requirements if r.importance != "must"]   # "nice" and "implied"

    score = 100 * (WEIGHTS["must"] * coverage(must, matched) + WEIGHTS["nice"] * coverage(nice, matched))
    return round(score, 1)


def coverage(requirements: list[SkillRequirement], matched: set[str]) -> float:
    """Share of the requirements the candidate has (0 to 1). No requirements = full coverage."""
    if not requirements:
        return 1.0
    hits = sum(1 for r in requirements if skill_key(r.label, r.raw) in matched)
    return hits / len(requirements)
