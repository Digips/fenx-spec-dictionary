from __future__ import annotations

import csv
from pathlib import Path


def _normalize_value(value: object) -> object:
    if value is None:
        return ""

    if isinstance(value, str):
        # Keep one CSV record per physical line for easier downstream parsing in editors.
        return " ".join(value.splitlines())

    return value


def write_csv(rows: list[dict], path: str | Path, headers: list[str] | None = None) -> None:
    """Write dictionary rows to CSV using UTF-8 and creating parent folders automatically."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    fieldnames: list[str]
    if headers:
        fieldnames = headers
    elif rows:
        fieldnames = list(rows[0].keys())
        for row in rows[1:]:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
    else:
        fieldnames = []

    with target.open("w", encoding="utf-8", newline="") as f:
        if not fieldnames:
            return

        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for row in rows:
            writer.writerow({k: _normalize_value(row.get(k, "")) for k in fieldnames})
