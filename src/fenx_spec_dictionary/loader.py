from __future__ import annotations

import json
from pathlib import Path


def load_json(path: str | Path) -> dict:
    """Load a JSON file and return its parsed dictionary."""
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    if not file_path.is_file():
        raise FileNotFoundError(f"Path is not a file: {file_path}")

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse JSON file {file_path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Failed to read JSON file {file_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object in {file_path}")

    return data
