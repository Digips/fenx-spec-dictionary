"""Element extractor for OpenAPI specifications.

Traverses an OpenAPI 3.x / Swagger 2.x document and produces a flat list of
:class:`Element` objects, one per schema property, path parameter, query
parameter, or request / response body field.  Each element carries enough
metadata to populate an Excel-based configuration management workbook.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Element:
    """A single named element extracted from an OpenAPI specification."""

    name: str
    path: str
    element_type: str
    data_type: str
    format: str
    required: bool
    description: str
    enum_values: list[str]
    example: str
    parent: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "Name": self.name,
            "Path": self.path,
            "Element Type": self.element_type,
            "Data Type": self.data_type,
            "Format": self.format,
            "Required": self.required,
            "Description": self.description,
            "Enum Values": ", ".join(self.enum_values) if self.enum_values else "",
            "Example": self.example,
            "Parent": self.parent,
            "Source": self.source,
        }


class Extractor:
    """Extract :class:`Element` objects from a parsed OpenAPI document."""

    def __init__(self, spec: dict[str, Any], source_name: str = "") -> None:
        self._spec = spec
        self._source = source_name
        self._elements: list[Element] = []
        # cache resolved $refs to avoid infinite loops
        self._resolving: set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self) -> list[Element]:
        """Run the full extraction and return the list of elements."""
        self._elements = []
        self._extract_schemas()
        self._extract_paths()
        return self._elements

    # ------------------------------------------------------------------
    # Schema / component extraction
    # ------------------------------------------------------------------

    def _extract_schemas(self) -> None:
        components = self._spec.get("components", {})
        schemas = components.get("schemas", {})
        # Swagger 2.x uses "definitions"
        if not schemas:
            schemas = self._spec.get("definitions", {})
        for schema_name, schema in schemas.items():
            resolved = self._resolve_ref(schema)
            self._walk_schema(
                resolved,
                parent_path=schema_name,
                parent_name=schema_name,
                element_type="schema",
                required_fields=set(resolved.get("required", [])),
            )

    def _walk_schema(
        self,
        schema: dict[str, Any],
        parent_path: str,
        parent_name: str,
        element_type: str,
        required_fields: set[str],
    ) -> None:
        schema = self._resolve_ref(schema)
        properties = schema.get("properties", {})
        # allOf / anyOf / oneOf merging
        for combiner in ("allOf", "anyOf", "oneOf"):
            for sub in schema.get(combiner, []):
                resolved_sub = self._resolve_ref(sub)
                extra_required = set(resolved_sub.get("required", []))
                self._walk_schema(
                    resolved_sub,
                    parent_path=parent_path,
                    parent_name=parent_name,
                    element_type=element_type,
                    required_fields=required_fields | extra_required,
                )

        for prop_name, prop_schema in properties.items():
            prop_schema = self._resolve_ref(prop_schema)
            prop_path = f"{parent_path}.{prop_name}"
            data_type = prop_schema.get("type", "")
            # Determine nested type for arrays
            if data_type == "array":
                items = self._resolve_ref(prop_schema.get("items", {}))
                nested_type = items.get("type", "object")
                data_type = f"array[{nested_type}]"
            element = Element(
                name=prop_name,
                path=prop_path,
                element_type=element_type,
                data_type=data_type,
                format=prop_schema.get("format", ""),
                required=prop_name in required_fields,
                description=prop_schema.get("description", ""),
                enum_values=prop_schema.get("enum", []),
                example=str(prop_schema.get("example", "")),
                parent=parent_name,
                source=self._source,
            )
            self._elements.append(element)

            # Recurse into objects
            prop_type = prop_schema.get("type", "")
            nested_required = set(prop_schema.get("required", []))
            if prop_type == "object" or prop_schema.get("properties"):
                self._walk_schema(
                    prop_schema,
                    parent_path=prop_path,
                    parent_name=prop_name,
                    element_type=element_type,
                    required_fields=nested_required,
                )
            elif prop_type == "array":
                items = self._resolve_ref(prop_schema.get("items", {}))
                if items.get("properties") or items.get("type") == "object":
                    self._walk_schema(
                        items,
                        parent_path=prop_path,
                        parent_name=prop_name,
                        element_type=element_type,
                        required_fields=set(items.get("required", [])),
                    )

    # ------------------------------------------------------------------
    # Path / operation extraction
    # ------------------------------------------------------------------

    def _extract_paths(self) -> None:
        paths = self._spec.get("paths", {})
        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            # path-level parameters
            path_params = path_item.get("parameters", [])
            http_methods = (
                "get", "post", "put", "patch", "delete",
                "head", "options", "trace",
            )
            for method in http_methods:
                operation = path_item.get(method)
                if not isinstance(operation, dict):
                    continue
                operation_id = operation.get(
                    "operationId",
                    f"{method.upper()} {path_str}",
                )
                all_params = path_params + operation.get("parameters", [])
                self._extract_parameters(all_params, path_str, operation_id)
                self._extract_request_body(
                    operation.get("requestBody", {}),
                    path_str,
                    operation_id,
                )

    def _extract_parameters(
        self,
        parameters: list[dict[str, Any]],
        path_str: str,
        operation_id: str,
    ) -> None:
        for param in parameters:
            param = self._resolve_ref(param)
            name = param.get("name", "")
            location = param.get("in", "")
            schema = self._resolve_ref(param.get("schema", {}))
            element = Element(
                name=name,
                path=f"{path_str}#{location}.{name}",
                element_type=f"parameter.{location}",
                data_type=schema.get("type", param.get("type", "")),
                format=schema.get("format", param.get("format", "")),
                required=param.get("required", location == "path"),
                description=param.get("description", ""),
                enum_values=(
                    schema.get("enum", []) or param.get("enum", [])
                ),
                example=str(
                    param.get("example", schema.get("example", ""))
                ),
                parent=operation_id,
                source=self._source,
            )
            self._elements.append(element)

    def _extract_request_body(
        self,
        request_body: dict[str, Any],
        path_str: str,
        operation_id: str,
    ) -> None:
        if not request_body:
            return
        request_body = self._resolve_ref(request_body)
        content = request_body.get("content", {})
        for media_type, media_obj in content.items():
            if not isinstance(media_obj, dict):
                continue
            schema = self._resolve_ref(media_obj.get("schema", {}))
            if not schema:
                continue
            self._walk_schema(
                schema,
                parent_path=f"{path_str}#requestBody",
                parent_name=operation_id,
                element_type="requestBody",
                required_fields=set(schema.get("required", [])),
            )

    # ------------------------------------------------------------------
    # $ref resolution
    # ------------------------------------------------------------------

    def _resolve_ref(self, obj: Any) -> dict[str, Any]:
        if not isinstance(obj, dict):
            return obj or {}
        ref = obj.get("$ref")
        if not ref:
            return obj
        if ref in self._resolving:
            # Circular reference – return a placeholder
            return {"type": "object", "description": f"(circular ref: {ref})"}
        self._resolving.add(ref)
        try:
            resolved = self._follow_ref(ref)
        finally:
            self._resolving.discard(ref)
        # Merge any sibling keys (description, etc.) from the $ref object
        merged = copy.deepcopy(resolved)
        for key, value in obj.items():
            if key != "$ref":
                merged.setdefault(key, value)
        return merged

    def _follow_ref(self, ref: str) -> dict[str, Any]:
        """Dereference a JSON Pointer ref like '#/components/schemas/Foo'."""
        if not ref.startswith("#/"):
            # External refs are not supported; return an empty schema
            return {}
        parts = ref[2:].split("/")
        node: Any = self._spec
        for part in parts:
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or part not in node:
                return {}
            node = node[part]
        return node if isinstance(node, dict) else {}
