from __future__ import annotations

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

RAW_SPEC = REPO_ROOT / "data" / "raw" / "policyquery.swagger.json"
OUT_DIR = REPO_ROOT / "data" / "dictionary"


OUTPUTS: list[tuple[str, list[str], Callable[[dict], list[dict]]]] = [
    (
        "endpoints.csv",
        [
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
        [
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
        [
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
        [
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
        [
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


def main() -> int:
    spec = load_json(RAW_SPEC)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Dictionary build summary:")
    for file_name, headers, extractor in OUTPUTS:
        rows = extractor(spec)
        out_path = OUT_DIR / file_name
        write_csv(rows, out_path, headers=headers)
        print(f"- {file_name}: {len(rows)} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
