from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fenx_spec_dictionary.exporter import write_csv
from fenx_spec_dictionary.extractor import (
    extract_endpoints,
    extract_parameters,
    extract_responses,
    extract_schema_properties,
    extract_schemas,
)
from fenx_spec_dictionary.loader import load_json
from fenx_spec_dictionary.spec_catalog import SpecSource, get_spec_sources

OUT_DIR = REPO_ROOT / "data" / "dictionary"
RAW_DIR = REPO_ROOT / "data" / "raw"

SOURCE_HEADERS = [
    "source_id",
    "api_name",
    "api_mode",
    "api_version",
    "source_url",
]


OUTPUTS: list[tuple[str, list[str], Callable[[dict, dict[str, str] | None], list[dict]]]] = [
    (
        "endpoints.csv",
        SOURCE_HEADERS
        + [
            "path",
            "method",
            "operation_id",
            "summary",
            "description",
            "tags",
            "deprecated",
        ],
        extract_endpoints,
    ),
    (
        "parameters.csv",
        SOURCE_HEADERS
        + [
            "path",
            "method",
            "operation_id",
            "name",
            "in",
            "required",
            "type",
            "description",
        ],
        extract_parameters,
    ),
    (
        "responses.csv",
        SOURCE_HEADERS
        + [
            "path",
            "method",
            "operation_id",
            "status_code",
            "description",
            "content_type",
            "schema_ref",
            "schema_type",
        ],
        extract_responses,
    ),
    (
        "schemas.csv",
        SOURCE_HEADERS
        + [
            "schema_name",
            "type",
            "description",
            "property_count",
            "required_count",
        ],
        extract_schemas,
    ),
    (
        "schema_properties.csv",
        SOURCE_HEADERS
        + [
            "schema_name",
            "property_path",
            "payload_json_path",
            "json_pointer",
            "property_name",
            "type",
            "format",
            "required",
            "nullable",
            "description",
            "enum",
            "ref",
            "item_type",
            "item_ref",
            "example",
        ],
        extract_schema_properties,
    ),
]


def _source_metadata(source: SpecSource) -> dict[str, str]:
    return {
        "source_id": source.source_id,
        "api_name": source.api_name,
        "api_mode": source.api_mode,
        "api_version": source.api_version,
        "source_url": source.source_url,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build dictionary CSVs from all configured specs.")
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Filter build to one or more source IDs. Repeat this option for multiple values.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    source_ids = set(args.source_id) if args.source_id else None
    sources = get_spec_sources(source_ids)

    if source_ids and not sources:
        print("No matching source IDs found in catalog.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    merged_rows: dict[str, list[dict]] = {file_name: [] for file_name, _headers, _extractor in OUTPUTS}

    print("Dictionary build summary:")
    for source in sources:
        raw_path = RAW_DIR / source.raw_filename
        if not raw_path.exists():
            print(f"- {source.source_id}: skipped (missing raw file {raw_path.name})")
            continue

        spec = load_json(raw_path)
        source_meta = _source_metadata(source)
        per_source_dir = OUT_DIR / source.source_id

        source_total = 0
        for file_name, headers, extractor in OUTPUTS:
            rows = extractor(spec, source_meta)
            source_total += len(rows)
            merged_rows[file_name].extend(rows)
            write_csv(rows, per_source_dir / file_name, headers=headers)

        print(f"- {source.source_id}: {source_total} rows")

    for file_name, headers, _extractor in OUTPUTS:
        rows = merged_rows[file_name]
        out_path = OUT_DIR / file_name
        write_csv(rows, out_path, headers=headers)
        print(f"  merged {file_name}: {len(rows)} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
