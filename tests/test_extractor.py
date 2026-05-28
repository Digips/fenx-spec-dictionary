"""Tests for the extractor module."""

from __future__ import annotations

import pytest

from fenx_spec_dictionary.extractor import Element, Extractor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_spec(
    schemas: dict | None = None,
    paths: dict | None = None,
) -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "Test", "version": "1.0.0"},
        "components": {"schemas": schemas or {}},
        "paths": paths or {},
    }


# ---------------------------------------------------------------------------
# Schema extraction
# ---------------------------------------------------------------------------


class TestSchemaExtraction:
    def test_simple_properties(self):
        spec = _make_spec(schemas={
            "Person": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Full name"},
                    "age": {"type": "integer"},
                },
            }
        })
        elements = Extractor(spec).extract()
        paths = [e.path for e in elements]
        assert "Person.name" in paths
        assert "Person.age" in paths

    def test_required_flag(self):
        spec = _make_spec(schemas={
            "Item": {
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string"},
                    "note": {"type": "string"},
                },
            }
        })
        elements = {e.name: e for e in Extractor(spec).extract()}
        assert elements["id"].required is True
        assert elements["note"].required is False

    def test_enum_values(self):
        spec = _make_spec(schemas={
            "Status": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": ["Active", "Inactive", "Pending"],
                    }
                },
            }
        })
        elements = {e.name: e for e in Extractor(spec).extract()}
        assert elements["state"].enum_values == ["Active", "Inactive", "Pending"]

    def test_nested_object(self):
        spec = _make_spec(schemas={
            "Outer": {
                "type": "object",
                "properties": {
                    "inner": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                        },
                    }
                },
            }
        })
        elements = Extractor(spec).extract()
        paths = [e.path for e in elements]
        assert "Outer.inner" in paths
        assert "Outer.inner.value" in paths

    def test_array_property(self):
        spec = _make_spec(schemas={
            "Container": {
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
            }
        })
        elements = {e.name: e for e in Extractor(spec).extract()}
        assert elements["tags"].data_type == "array[string]"

    def test_ref_resolution(self):
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "components": {
                "schemas": {
                    "Address": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                        },
                    },
                    "Person": {
                        "type": "object",
                        "properties": {
                            "address": {"$ref": "#/components/schemas/Address"},
                        },
                    },
                }
            },
            "paths": {},
        }
        elements = Extractor(spec).extract()
        paths = [e.path for e in elements]
        # Address properties should appear both under Address and Person.address
        assert "Address.city" in paths
        assert "Person.address.city" in paths

    def test_allof_merging(self):
        spec = _make_spec(schemas={
            "Base": {
                "type": "object",
                "properties": {"id": {"type": "string"}},
            },
            "Extended": {
                "allOf": [
                    {"$ref": "#/components/schemas/Base"},
                    {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    },
                ]
            },
        })
        elements = Extractor(spec).extract()
        paths = [e.path for e in elements]
        assert "Extended.id" in paths
        assert "Extended.name" in paths


# ---------------------------------------------------------------------------
# Path / parameter extraction
# ---------------------------------------------------------------------------


class TestPathExtraction:
    def test_query_parameter(self):
        spec = _make_spec(paths={
            "/items": {
                "get": {
                    "operationId": "listItems",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            }
        })
        elements = Extractor(spec).extract()
        params = [e for e in elements if e.element_type == "parameter.query"]
        assert len(params) == 1
        assert params[0].name == "limit"
        assert params[0].required is False

    def test_path_parameter(self):
        spec = _make_spec(paths={
            "/items/{id}": {
                "get": {
                    "operationId": "getItem",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "format": "uuid"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            }
        })
        elements = Extractor(spec).extract()
        path_params = [e for e in elements if e.element_type == "parameter.path"]
        assert len(path_params) == 1
        assert path_params[0].name == "id"
        assert path_params[0].required is True
        assert path_params[0].format == "uuid"

    def test_request_body_fields(self):
        spec = _make_spec(paths={
            "/items": {
                "post": {
                    "operationId": "createItem",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "value": {"type": "number"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {"201": {"description": "Created"}},
                }
            }
        })
        elements = Extractor(spec).extract()
        body_elems = [e for e in elements if e.element_type == "requestBody"]
        names = [e.name for e in body_elems]
        assert "name" in names
        assert "value" in names

    def test_source_name(self):
        spec = _make_spec(schemas={
            "Foo": {"type": "object", "properties": {"x": {"type": "string"}}}
        })
        elements = Extractor(spec, source_name="my_spec.yaml").extract()
        assert all(e.source == "my_spec.yaml" for e in elements)


# ---------------------------------------------------------------------------
# Element.as_dict
# ---------------------------------------------------------------------------


class TestElementAsDict:
    def test_keys_present(self):
        elem = Element(
            name="foo",
            path="Foo.foo",
            element_type="schema",
            data_type="string",
            format="",
            required=True,
            description="A field",
            enum_values=["a", "b"],
            example="a",
            parent="Foo",
            source="spec.yaml",
        )
        d = elem.as_dict()
        assert d["Name"] == "foo"
        assert d["Required"] is True
        assert d["Enum Values"] == "a, b"
