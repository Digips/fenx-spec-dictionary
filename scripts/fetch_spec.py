from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fenx_spec_dictionary.spec_catalog import SpecSource, get_spec_sources

DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "raw"


def fetch_spec(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with urlopen(url) as response:  # nosec B310 - trusted URL input for this utility
        raw = response.read()

    spec = json.loads(raw.decode("utf-8"))

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch configured Swagger specs.")
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Filter fetch to one or more source IDs. Repeat this option for multiple values.",
    )
    return parser.parse_args()


def _fetch_source(source: SpecSource, output_dir: Path) -> tuple[str, str]:
    output_path = output_dir / source.raw_filename
    try:
        fetch_spec(source.source_url, output_path)
        return source.source_id, f"saved {output_path.name}"
    except Exception as exc:  # pragma: no cover - network failure branch
        return source.source_id, f"failed ({exc})"


if __name__ == "__main__":
    args = _parse_args()
    source_ids = set(args.source_id) if args.source_id else None
    sources = get_spec_sources(source_ids)

    if source_ids and not sources:
        print("No matching source IDs found in catalog.")
        raise SystemExit(1)

    print("Fetch summary:")
    failures = 0
    for source in sources:
        source_id, status = _fetch_source(source, DEFAULT_OUTPUT_DIR)
        print(f"- {source_id}: {status}")
        if status.startswith("failed"):
            failures += 1

    if failures:
        print(f"Completed with {failures} fetch failures.")
        raise SystemExit(2)

    print("All specs fetched successfully.")
