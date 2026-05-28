from __future__ import annotations

from typing import Iterator

from .refs import dereference, resolve_ref

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def _as_text(value: object) -> str:
    return "" if value is None else str(value)


def _join_list(values: object, sep: str = "|") -> str:
    if not isinstance(values, list):
        return ""
    return sep.join(str(v) for v in values if v is not None)


def _property_path_to_payload_json_path(property_path: str) -> str:
    if not property_path:
        return "$"

    parts = [p for p in property_path.split(".") if p]
    converted: list[str] = []

    for part in parts:
        if part.endswith("[]"):
            converted.append(f"{part[:-2]}[*]")
        else:
            converted.append(part)

    return "$." + ".".join(converted)


def _iter_operations(spec: dict) -> Iterator[tuple[str, str, dict, list[dict]]]:
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_parameters = path_item.get("parameters", [])
        if not isinstance(path_parameters, list):
            path_parameters = []

        for method, operation in path_item.items():
            method_l = str(method).lower()
            if method_l not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue

            yield str(path), method_l, operation, path_parameters


def _resolve_schema(spec: dict, schema: dict, active_refs: set[str] | None = None) -> dict:
    if not isinstance(schema, dict):
        return {}

    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return schema

    active_refs = active_refs or set()
    if ref in active_refs:
        return schema

    try:
        return resolve_ref(spec, ref)
    except (KeyError, ValueError):
        return schema


def extract_endpoints(spec: dict) -> list[dict]:
    rows: list[dict] = []

    for path, method, operation, _path_parameters in _iter_operations(spec):
        rows.append(
            {
                "path": path,
                "method": method,
                "operation_id": _as_text(operation.get("operationId")),
                "summary": _as_text(operation.get("summary")),
                "description": _as_text(operation.get("description")),
                "tags": _join_list(operation.get("tags")),
                "deprecated": bool(operation.get("deprecated", False)),
            }
        )

    return rows


def extract_parameters(spec: dict) -> list[dict]:
    rows: list[dict] = []

    for path, method, operation, path_parameters in _iter_operations(spec):
        operation_id = _as_text(operation.get("operationId"))
        operation_parameters = operation.get("parameters", [])
        if not isinstance(operation_parameters, list):
            operation_parameters = []

        all_parameters = [*path_parameters, *operation_parameters]

        for param in all_parameters:
            if not isinstance(param, dict):
                continue

            resolved_param = dereference(spec, param)
            schema = resolved_param.get("schema", {})
            resolved_schema = _resolve_schema(spec, schema)

            param_type = _as_text(schema.get("type") or resolved_schema.get("type"))

            rows.append(
                {
                    "path": path,
                    "method": method,
                    "operation_id": operation_id,
                    "name": _as_text(resolved_param.get("name")),
                    "in": _as_text(resolved_param.get("in")),
                    "required": bool(resolved_param.get("required", False)),
                    "type": param_type,
                    "description": _as_text(
                        resolved_param.get("description") or schema.get("description")
                    ),
                }
            )

    return rows


def extract_responses(spec: dict) -> list[dict]:
    rows: list[dict] = []

    for path, method, operation, _path_parameters in _iter_operations(spec):
        operation_id = _as_text(operation.get("operationId"))
        responses = operation.get("responses", {})
        if not isinstance(responses, dict):
            continue

        for status_code, response in responses.items():
            if not isinstance(response, dict):
                continue

            resolved_response = dereference(spec, response)
            description = _as_text(resolved_response.get("description"))
            content = resolved_response.get("content", {})

            if not isinstance(content, dict) or not content:
                rows.append(
                    {
                        "path": path,
                        "method": method,
                        "operation_id": operation_id,
                        "status_code": _as_text(status_code),
                        "description": description,
                        "content_type": "",
                        "schema_ref": "",
                        "schema_type": "",
                    }
                )
                continue

            for content_type, content_item in content.items():
                if not isinstance(content_item, dict):
                    continue

                schema = content_item.get("schema", {})
                if not isinstance(schema, dict):
                    schema = {}

                schema_ref = _as_text(schema.get("$ref"))
                resolved_schema = _resolve_schema(spec, schema)
                schema_type = _as_text(schema.get("type") or resolved_schema.get("type"))

                rows.append(
                    {
                        "path": path,
                        "method": method,
                        "operation_id": operation_id,
                        "status_code": _as_text(status_code),
                        "description": description,
                        "content_type": _as_text(content_type),
                        "schema_ref": schema_ref,
                        "schema_type": schema_type,
                    }
                )

    return rows


def extract_schemas(spec: dict) -> list[dict]:
    rows: list[dict] = []

    schemas = spec.get("components", {}).get("schemas", {})
    if not isinstance(schemas, dict):
        return rows

    for schema_name, schema in schemas.items():
        if not isinstance(schema, dict):
            continue

        resolved_schema = _resolve_schema(spec, schema)
        properties = resolved_schema.get("properties", {})
        required = resolved_schema.get("required", [])

        rows.append(
            {
                "schema_name": _as_text(schema_name),
                "type": _as_text(resolved_schema.get("type")),
                "description": _as_text(resolved_schema.get("description")),
                "property_count": len(properties) if isinstance(properties, dict) else 0,
                "required_count": len(required) if isinstance(required, list) else 0,
            }
        )

    return rows


def extract_schema_properties(spec: dict) -> list[dict]:
    rows: list[dict] = []

    schemas = spec.get("components", {}).get("schemas", {})
    if not isinstance(schemas, dict):
        return rows

    for schema_name, schema in schemas.items():
        if not isinstance(schema, dict):
            continue

        resolved_root = _resolve_schema(spec, schema)
        root_pointer = f"#/components/schemas/{schema_name}"
        _walk_schema_properties(
            spec=spec,
            schema_name=str(schema_name),
            schema=resolved_root,
            path_prefix="",
            pointer_prefix=root_pointer,
            required_fields=set(resolved_root.get("required", []))
            if isinstance(resolved_root.get("required"), list)
            else set(),
            active_refs=set(),
            rows=rows,
        )

    return rows


def _walk_schema_properties(
    spec: dict,
    schema_name: str,
    schema: dict,
    path_prefix: str,
    pointer_prefix: str,
    required_fields: set[str],
    active_refs: set[str],
    rows: list[dict],
) -> None:
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        return

    for prop_name, prop_schema_raw in properties.items():
        if not isinstance(prop_schema_raw, dict):
            continue

        property_path = f"{path_prefix}.{prop_name}" if path_prefix else str(prop_name)
        json_pointer = f"{pointer_prefix}/properties/{prop_name}"
        prop_required = prop_name in required_fields

        _append_property_row(
            spec=spec,
            schema_name=schema_name,
            property_path=property_path,
            json_pointer=json_pointer,
            property_name=str(prop_name),
            property_schema=prop_schema_raw,
            required=prop_required,
            active_refs=active_refs,
            rows=rows,
        )

        next_schema = prop_schema_raw
        ref = prop_schema_raw.get("$ref")
        if isinstance(ref, str) and ref not in active_refs:
            try:
                next_schema = resolve_ref(spec, ref)
                active_refs = {*active_refs, ref}
            except (KeyError, ValueError):
                next_schema = prop_schema_raw

        # Recurse into object properties
        nested_required = next_schema.get("required", [])
        nested_required_set = set(nested_required) if isinstance(nested_required, list) else set()
        if isinstance(next_schema.get("properties"), dict):
            _walk_schema_properties(
                spec=spec,
                schema_name=schema_name,
                schema=next_schema,
                path_prefix=property_path,
                pointer_prefix=json_pointer,
                required_fields=nested_required_set,
                active_refs=active_refs,
                rows=rows,
            )

        # Recurse into array item object properties
        items = next_schema.get("items")
        if isinstance(items, dict):
            item_schema = items
            item_ref = items.get("$ref")
            item_active_refs = set(active_refs)
            if isinstance(item_ref, str) and item_ref not in item_active_refs:
                try:
                    item_schema = resolve_ref(spec, item_ref)
                    item_active_refs.add(item_ref)
                except (KeyError, ValueError):
                    item_schema = items

            item_required = item_schema.get("required", [])
            item_required_set = set(item_required) if isinstance(item_required, list) else set()
            if isinstance(item_schema.get("properties"), dict):
                _walk_schema_properties(
                    spec=spec,
                    schema_name=schema_name,
                    schema=item_schema,
                    path_prefix=f"{property_path}[]",
                    pointer_prefix=f"{json_pointer}/items",
                    required_fields=item_required_set,
                    active_refs=item_active_refs,
                    rows=rows,
                )


def _append_property_row(
    spec: dict,
    schema_name: str,
    property_path: str,
    json_pointer: str,
    property_name: str,
    property_schema: dict,
    required: bool,
    active_refs: set[str],
    rows: list[dict],
) -> None:
    ref = _as_text(property_schema.get("$ref"))
    resolved_property_schema = property_schema

    if ref and ref not in active_refs:
        try:
            resolved_property_schema = resolve_ref(spec, ref)
        except (KeyError, ValueError):
            resolved_property_schema = property_schema

    prop_type = _as_text(property_schema.get("type") or resolved_property_schema.get("type"))
    prop_format = _as_text(
        property_schema.get("format") or resolved_property_schema.get("format")
    )
    description = _as_text(
        property_schema.get("description") or resolved_property_schema.get("description")
    )
    enum_value = _join_list(property_schema.get("enum") or resolved_property_schema.get("enum"))

    example_raw = property_schema.get("example")
    if example_raw is None:
        example_raw = resolved_property_schema.get("example")
    example = "" if example_raw is None else str(example_raw)

    items = property_schema.get("items", {})
    item_type = ""
    item_ref = ""
    if isinstance(items, dict):
        item_ref = _as_text(items.get("$ref"))
        resolved_items = _resolve_schema(spec, items)
        item_type = _as_text(items.get("type") or resolved_items.get("type"))

    payload_json_path = _property_path_to_payload_json_path(property_path)

    rows.append(
        {
            "schema_name": schema_name,
            "property_path": property_path,
            "payload_json_path": payload_json_path,
            "json_pointer": json_pointer,
            "property_name": property_name,
            "type": prop_type,
            "format": prop_format,
            "required": required,
            "nullable": bool(property_schema.get("nullable", False)),
            "description": description,
            "enum": enum_value,
            "ref": ref,
            "item_type": item_type,
            "item_ref": item_ref,
            "example": example,
        }
    )
