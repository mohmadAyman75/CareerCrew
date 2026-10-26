"""
document_parser.py

Reads the CV and the job description from files and returns plain text.

This file only READS. It does not decide if the text is good or bad.
That is the job of agents/supervisor/checks.py.
"""

from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


def load_cv(cv_path: str | Path) -> str:
    """Read a PDF CV and return its text, page by page."""
    cv_path = Path(cv_path)

    # 1) The file must exist
    if not cv_path.exists():
        raise FileNotFoundError(f"CV file not found: {cv_path}")

    # 2) Only PDF for now (DOCX can be added later)
    if cv_path.suffix.lower() != ".pdf":
        raise ValueError(f"Only PDF CVs are supported for now, got: '{cv_path.suffix}'")

    # 3) Open the PDF (a broken file raises PdfReadError)
    try:
        reader = PdfReader(cv_path)
    except PdfReadError as error:
        raise ValueError(f"Could not open the PDF, the file may be broken: {cv_path}") from error

    # 4) Extract the text of every page
    extracted_text = ""
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            extracted_text += f"--- Page {page_num} ---\n" + text + "\n"

    # If the PDF is a scanned image, extracted_text will be empty.
    # We do NOT raise here: checks.py will notice it and ask the user.
    return extracted_text


def load_job(job_path: str | Path) -> str:
    """Read the job description from a .txt file."""
    job_path = Path(job_path)

    if not job_path.exists():
        raise FileNotFoundError(f"Job file not found: {job_path}")

    if job_path.suffix.lower() != ".txt":
        raise ValueError(f"The job description must be a .txt file, got: '{job_path.suffix}'")

    return job_path.read_text(encoding="utf-8")


if __name__ == "__main__":
    # Quick manual test. Run it from the project root:
    #   uv run python -m careercrew.tools.document_parser
    cv_text = load_cv("data/samples/synthetic_cv_01.pdf")
    job_text = load_job("data/samples/job_01.txt")

    print(cv_text[:500])
    print("-" * 40)
    print(job_text[:500])