"""OpenAPI specification parser.

Loads an OpenAPI 3.x (or Swagger 2.x) specification from a local file path
or a remote URL and returns the parsed document as a plain Python dict.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml


class SpecParseError(Exception):
    """Raised when a specification cannot be loaded or parsed."""


def load_spec(source: str) -> dict[str, Any]:
    """Load and parse an OpenAPI specification.

    Parameters
    ----------
    source:
        A file-system path (absolute or relative) **or** an HTTP/HTTPS URL
        pointing to a JSON or YAML OpenAPI specification file.

    Returns
    -------
    dict
        The parsed specification document.

    Raises
    ------
    SpecParseError
        If the source cannot be read or the content cannot be parsed.
    """
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        return _load_from_url(source)
    return _load_from_file(Path(source))


def _load_from_url(url: str) -> dict[str, Any]:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        content = response.text
    except requests.RequestException as exc:
        raise SpecParseError(f"Failed to download spec from '{url}': {exc}") from exc
    return _parse_content(content, url)


def _load_from_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SpecParseError(f"Spec file not found: '{path}'")
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecParseError(f"Cannot read spec file '{path}': {exc}") from exc
    return _parse_content(content, str(path))


def _parse_content(content: str, source_hint: str) -> dict[str, Any]:
    """Try JSON first, fall back to YAML."""
    stripped = content.lstrip()
    if stripped.startswith("{"):
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise SpecParseError(
                f"Invalid JSON in '{source_hint}': {exc}"
            ) from exc
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise SpecParseError(
            f"Invalid YAML in '{source_hint}': {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise SpecParseError(
            f"Expected a mapping at the top level of '{source_hint}'"
        )
    return data


def get_openapi_version(spec: dict[str, Any]) -> str:
    """Return a normalised OpenAPI version string, e.g. '3.0', '2.0'."""
    version = spec.get("openapi") or spec.get("swagger") or ""
    match = re.match(r"(\d+\.\d+)", str(version))
    return match.group(1) if match else ""
