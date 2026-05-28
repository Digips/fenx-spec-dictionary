"""Tests for the dictionary module."""

from __future__ import annotations

from fenx_spec_dictionary.dictionary import Dictionary
from fenx_spec_dictionary.extractor import Element


def _make_element(
    name: str = "field",
    path: str = "Schema.field",
    element_type: str = "schema",
    source: str = "spec.yaml",
) -> Element:
    return Element(
        name=name,
        path=path,
        element_type=element_type,
        data_type="string",
        format="",
        required=False,
        description="",
        enum_values=[],
        example="",
        parent="Schema",
        source=source,
    )


class TestDictionary:
    def test_add_elements(self):
        d = Dictionary()
        d.add_elements([_make_element("a"), _make_element("b", path="Schema.b")])
        assert len(d.to_list()) == 2

    def test_deduplication_merges_sources(self):
        d = Dictionary()
        elem1 = _make_element(source="spec_v1.yaml")
        elem2 = _make_element(source="spec_v2.yaml")
        d.add_elements([elem1, elem2])
        entries = d.to_list()
        assert len(entries) == 1
        sources = entries[0]["Sources"]
        assert "spec_v1.yaml" in sources
        assert "spec_v2.yaml" in sources

    def test_filter_by_type(self):
        d = Dictionary()
        d.add_elements([
            _make_element("a", path="S.a", element_type="schema"),
            _make_element("b", path="/items#query.b", element_type="parameter.query"),
        ])
        schemas = d.schemas()
        params = d.parameters()
        assert len(schemas) == 1
        assert len(params) == 1

    def test_summary(self):
        d = Dictionary()
        d.add_elements([
            _make_element("a", path="S.a", element_type="schema"),
            _make_element("b", path="S.b", element_type="schema"),
            _make_element("c", path="/x#query.c", element_type="parameter.query"),
        ])
        summary = d.summary()
        assert summary.get("schema") == 2
        assert summary.get("parameter.query") == 1

    def test_to_list_sorted_by_path(self):
        d = Dictionary()
        d.add_elements([
            _make_element("z", path="Z.z"),
            _make_element("a", path="A.a"),
        ])
        paths = [e["Path"] for e in d.to_list()]
        assert paths == sorted(paths)
