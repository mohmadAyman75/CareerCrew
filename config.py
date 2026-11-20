"""
config.py  —  SHARED

One place to find the project folder and to read the YAML files in configs/.
Every number the code uses lives in configs/, not inside the code.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
CONFIGS_DIR = ROOT / "configs"


def load_yaml(file_name: str) -> dict:
    """Read configs/<file_name> and return it as a dict."""
    if not isinstance(file_name, str) or not file_name.endswith(".yaml"):
        raise ValueError(f"file_name must be a '.yaml' file name, got: {file_name!r}")

    path = CONFIGS_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping (key: value lines)")
    return data
