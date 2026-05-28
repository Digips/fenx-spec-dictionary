from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from fenx_spec_dictionary.loader import load_json


def _count_paths(spec: dict) -> int:
    paths = spec.get("paths", {})
    return len(paths) if isinstance(paths, dict) else 0


def _count_schemas(spec: dict) -> int:
    schemas = spec.get("components", {}).get("schemas", {})
    return len(schemas) if isinstance(schemas, dict) else 0


def _path_set(spec: dict) -> set[str]:
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return set()
    return {str(p) for p in paths.keys()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two Swagger/OpenAPI specs.")
    parser.add_argument("--old", required=True, help="Path to old spec JSON")
    parser.add_argument("--new", required=True, help="Path to new spec JSON")
    args = parser.parse_args()

    old_spec = load_json(Path(args.old))
    new_spec = load_json(Path(args.new))

    old_paths = _path_set(old_spec)
    new_paths = _path_set(new_spec)

    added_paths = sorted(new_paths - old_paths)
    removed_paths = sorted(old_paths - new_paths)

    print("Spec comparison summary:")
    print(f"- old paths: {_count_paths(old_spec)}")
    print(f"- new paths: {_count_paths(new_spec)}")
    print(f"- old schemas: {_count_schemas(old_spec)}")
    print(f"- new schemas: {_count_schemas(new_spec)}")
    print(f"- added paths: {len(added_paths)}")
    print(f"- removed paths: {len(removed_paths)}")

    if added_paths:
        print("Added:")
        for path in added_paths:
            print(f"  + {path}")

    if removed_paths:
        print("Removed:")
        for path in removed_paths:
            print(f"  - {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
