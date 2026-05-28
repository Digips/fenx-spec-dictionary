from __future__ import annotations

from fenx_spec_dictionary.extractor import extract_endpoints, extract_schema_properties


def test_extract_simple_endpoint() -> None:
    spec = {
        "paths": {
            "/items": {
                "get": {
                    "operationId": "getItems",
                    "summary": "Get items",
                    "description": "Returns items",
                    "tags": ["Items"],
                    "deprecated": False,
                }
            }
        }
    }

    rows = extract_endpoints(spec)
    assert len(rows) == 1
    assert rows[0]["path"] == "/items"
    assert rows[0]["method"] == "get"
    assert rows[0]["operation_id"] == "getItems"


def test_extract_simple_schema_property() -> None:
    spec = {
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string", "description": "User name"},
                    },
                }
            }
        }
    }

    rows = extract_schema_properties(spec)
    assert len(rows) == 1
    row = rows[0]
    assert row["schema_name"] == "User"
    assert row["property_path"] == "name"
    assert row["payload_json_path"] == "$.name"
    assert row["json_pointer"] == "#/components/schemas/User/properties/name"
    assert row["property_name"] == "name"
    assert row["type"] == "string"
    assert row["required"] is True


def test_extract_array_property_with_item_ref() -> None:
    spec = {
        "components": {
            "schemas": {
                "Order": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/OrderItem"},
                        }
                    },
                },
                "OrderItem": {
                    "type": "object",
                    "properties": {
                        "sku": {"type": "string"},
                    },
                },
            }
        }
    }

    rows = extract_schema_properties(spec)

    items_row = next(r for r in rows if r["property_path"] == "items")
    nested_row = next(r for r in rows if r["property_path"] == "items[].sku")

    assert items_row["type"] == "array"
    assert items_row["payload_json_path"] == "$.items"
    assert items_row["json_pointer"] == "#/components/schemas/Order/properties/items"
    assert items_row["item_ref"] == "#/components/schemas/OrderItem"
    assert nested_row["payload_json_path"] == "$.items[*].sku"
    assert (
        nested_row["json_pointer"]
        == "#/components/schemas/Order/properties/items/items/properties/sku"
    )
    assert nested_row["type"] == "string"
