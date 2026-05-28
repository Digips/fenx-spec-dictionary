"""Tests for the parser module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from fenx_spec_dictionary.parser import SpecParseError, get_openapi_version, load_spec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_OPENAPI3 = {
    "openapi": "3.0.3",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {},
}

_MINIMAL_SWAGGER2 = {
    "swagger": "2.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {},
}


def _write_json(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _write_yaml(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# load_spec
# ---------------------------------------------------------------------------


class TestLoadSpec:
    def test_load_json_file(self, tmp_path):
        path = _write_json(tmp_path, _MINIMAL_OPENAPI3)
        spec = load_spec(str(path))
        assert spec["openapi"] == "3.0.3"

    def test_load_yaml_file(self, tmp_path):
        path = _write_yaml(tmp_path, _MINIMAL_OPENAPI3)
        spec = load_spec(str(path))
        assert spec["openapi"] == "3.0.3"

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(SpecParseError, match="not found"):
            load_spec(str(tmp_path / "nonexistent.yaml"))

    def test_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not: valid json", encoding="utf-8")
        with pytest.raises(SpecParseError, match="Invalid JSON"):
            load_spec(str(p))

    def test_invalid_yaml_raises(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("key: [unclosed", encoding="utf-8")
        with pytest.raises(SpecParseError, match="Invalid YAML"):
            load_spec(str(p))

    def test_non_mapping_yaml_raises(self, tmp_path):
        p = tmp_path / "list.yaml"
        p.write_text("- a\n- b\n", encoding="utf-8")
        with pytest.raises(SpecParseError, match="Expected a mapping"):
            load_spec(str(p))


# ---------------------------------------------------------------------------
# get_openapi_version
# ---------------------------------------------------------------------------


class TestGetOpenApiVersion:
    def test_openapi3(self):
        assert get_openapi_version({"openapi": "3.0.3"}) == "3.0"

    def test_swagger2(self):
        assert get_openapi_version({"swagger": "2.0"}) == "2.0"

    def test_missing(self):
        assert get_openapi_version({}) == ""
