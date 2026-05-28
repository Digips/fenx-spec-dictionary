# fenx-spec-dictionary

Reads a Fenergo OpenAPI/Swagger spec and produces flat CSV dictionaries for use in data mapping, integration analysis, and documentation.

> This project is independent and is not affiliated with, endorsed by, or sponsored by Fenergo. It works only with publicly available API specifications.

## Output

All CSVs are written to `data/dictionary/`:

| File | Description |
|---|---|
| `endpoints.csv` | All API paths + HTTP methods |
| `parameters.csv` | Path/query/header parameters per endpoint |
| `responses.csv` | Response schemas per endpoint + status code |
| `schemas.csv` | Top-level component schemas |
| `schema_properties.csv` | All schema properties, fully expanded (nested arrays + $ref resolved) |

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
```

## Build

Place the source spec at `data/raw/policyquery.swagger.json` then run:

```bash
python scripts/build_dictionary.py
```

## Test

```bash
pytest
```

