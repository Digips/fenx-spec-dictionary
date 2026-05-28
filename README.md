# fenx-spec-dictionary

Reads Fenergo OpenAPI/Swagger specs and produces flat CSV dictionaries for use in data mapping, integration analysis, and documentation.

> This project is independent and is not affiliated with, endorsed by, or sponsored by Fenergo. It works only with publicly available API specifications.

## Output

The pipeline writes both merged and per-spec outputs.

Merged CSVs are written to `data/dictionary/`:

| File | Description |
|---|---|
| `endpoints.csv` | All API paths + HTTP methods |
| `parameters.csv` | Path/query/header parameters per endpoint |
| `responses.csv` | Response schemas per endpoint + status code |
| `schemas.csv` | Top-level component schemas |
| `schema_properties.csv` | All schema properties, fully expanded (nested arrays + $ref resolved) |

Per-spec CSVs are written under `data/dictionary/<source_id>/` with the same five files.

### Source provenance columns

All CSV files include these columns to identify the source spec:

- `source_id`
- `api_name`
- `api_mode`
- `api_version`
- `source_url`

### `schema_properties.csv` columns

| Column | Description |
|---|---|
| `schema_name` | Top-level schema the row belongs to |
| `property_path` | Dot-notation path with `[]` for arrays (e.g. `versions[].dataGroupFields[].name`) |
| `payload_json_path` | JSONPath from the schema root (e.g. `$.versions[*].dataGroupFields[*].name`) |
| `json_pointer` | JSON Pointer into the raw spec (e.g. `#/components/schemas/…`) |
| `property_name` | Leaf property name |
| `type` / `format` | OpenAPI type and format |
| `required` / `nullable` | Constraint flags |
| `description` | Property description from the spec |
| `enum` | Pipe-separated allowed values |
| `ref` | `$ref` if the property references another schema |
| `item_type` / `item_ref` | Type/ref of array items |
| `example` | Example value from the spec |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
pip install -e .
```

## VS Code / Pylance

This project uses a `src/` layout. Import resolution in VS Code is configured in:

- `.vscode/settings.json`
- `pyrightconfig.json`

If you still see unresolved import warnings after opening the workspace, reload the VS Code window once.

## Build

Fetch all configured specs, then build dictionary CSVs:

```bash
python scripts/fetch_spec.py
python scripts/build_dictionary.py
```

To process only selected sources, repeat `--source-id`:

```bash
python scripts/fetch_spec.py --source-id policyquery_v2 --source-id riskquery_v1
python scripts/build_dictionary.py --source-id policyquery_v2 --source-id riskquery_v1
```

Configured sources are defined in `src/fenx_spec_dictionary/spec_catalog.py`.

## Test

```bash
pytest
```

