# fenx-spec-dictionary

> **Disclaimer:** This project is independent and is not affiliated with, endorsed by, or sponsored by Fenergo. It works only with publicly available API specifications and user-provided configuration metadata.

A Python pipeline that wrangles Fen-X API specifications (OpenAPI 3.x / Swagger 2.x) into a structured dictionary of elements, exported as a multi-sheet Excel workbook in support of configuration management.

---

## Features

- Loads OpenAPI specs from **local files** (JSON or YAML) or **remote URLs**
- Extracts all schema properties, path/query/header parameters, and request-body fields
- Resolves `$ref` pointers (including `allOf` / `anyOf` / `oneOf` merging)
- Merges elements from **multiple spec files** with source-tracking
- Exports a styled, auto-filtered `.xlsx` workbook with sheets for:
  - **All Elements** – every extracted element
  - **Schemas** – data model properties
  - **Parameters** – path, query, header, and cookie parameters
  - **Request Bodies** – request-body fields
  - **Summary** – element counts per type

---

## Installation

Requires Python 3.9+.

```bash
pip install .
```

For development (includes pytest):

```bash
pip install -e ".[dev]"
```

---

## Usage

### Command-line

```bash
# Single spec file
fenx-dict my_spec.yaml

# Multiple spec files merged into one workbook
fenx-dict spec_v1.yaml spec_v2.yaml -o dictionary.xlsx

# Remote URL
fenx-dict https://example.com/openapi.json -o output.xlsx
```

Run `fenx-dict --help` for full options.

### Python API

```python
from fenx_spec_dictionary.pipeline import run

result = run(
    sources=["spec_v1.yaml", "spec_v2.yaml"],
    output_path="fenx_dictionary.xlsx",
)
print(f"Wrote {result['element_count']} elements to {result['output']}")
print(result["summary"])
```

---

## Project structure

```
src/fenx_spec_dictionary/
    __init__.py      – package version
    parser.py        – load & parse OpenAPI YAML/JSON
    extractor.py     – traverse spec, produce Element objects
    dictionary.py    – aggregate & deduplicate elements
    exporter.py      – write Excel workbook
    pipeline.py      – end-to-end orchestration
    cli.py           – Click CLI entry point

tests/               – pytest test suite
examples/            – sample Fen-X–style OpenAPI spec
```

---

## Running tests

```bash
pytest
```

---

## Excel output columns

| Column | Description |
|---|---|
| Name | Property or parameter name |
| Path | Dot-notation path within the spec |
| Element Type | `schema`, `parameter.query`, `requestBody`, etc. |
| Data Type | JSON Schema type (e.g. `string`, `array[object]`) |
| Format | JSON Schema format (e.g. `uuid`, `date`) |
| Required | `Yes` / `No` |
| Description | Description from the spec |
| Enum Values | Comma-separated allowed values |
| Example | Example value from the spec |
| Parent | Parent schema or operation |
| Source | Source spec filename or URL |
| Sources | All source specs (when merging multiple specs) |
