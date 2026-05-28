from __future__ import annotations

import pytest

from fenx_spec_dictionary.refs import resolve_ref


def test_resolve_ref_internal_simple() -> None:
    spec = {
        "components": {
            "schemas": {
                "DataGroupVersionDto": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                }
            }
        }
    }

    resolved = resolve_ref(spec, "#/components/schemas/DataGroupVersionDto")
    assert resolved["type"] == "object"
    assert "id" in resolved["properties"]


def test_resolve_ref_external_fails() -> None:
    spec = {"components": {"schemas": {}}}

    with pytest.raises(ValueError):
        resolve_ref(spec, "https://example.com/other.json#/components/schemas/X")
