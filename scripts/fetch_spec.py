from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

SPEC_URL = "https://api.fenergox.com/policyquery/swagger/1.0/swagger.json"
DEFAULT_OUTPUT = Path("data/raw/policyquery.swagger.json")


def fetch_spec(url: str = SPEC_URL, output_path: Path = DEFAULT_OUTPUT) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with urlopen(url) as response:  # nosec B310 - trusted URL input for this utility
        raw = response.read()

    spec = json.loads(raw.decode("utf-8"))

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    return output_path


if __name__ == "__main__":
    saved_path = fetch_spec()
    print(f"Saved spec to {saved_path}")
