"""Dictionary builder.

Aggregates :class:`~fenx_spec_dictionary.extractor.Element` objects from one
or more OpenAPI specifications into a structured dictionary that maps element
paths to their metadata.  The builder de-duplicates elements so that the same
property defined in multiple specs is recorded once, with all source specs
noted.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fenx_spec_dictionary.extractor import Element


class Dictionary:
    """A merged dictionary of API elements built from one or more specs."""

    def __init__(self) -> None:
        # keyed by (element_type, path)
        self._store: dict[tuple[str, str], dict[str, Any]] = {}

    def add_elements(self, elements: list[Element]) -> None:
        """Add a list of extracted elements to the dictionary."""
        for element in elements:
            key = (element.element_type, element.path)
            if key not in self._store:
                self._store[key] = element.as_dict()
                self._store[key]["Sources"] = element.source
            else:
                # Merge: accumulate source references
                existing_sources = self._store[key].get("Sources", "")
                sources = {s.strip() for s in existing_sources.split(",") if s.strip()}
                sources.add(element.source)
                self._store[key]["Sources"] = ", ".join(sorted(sources))
                # Backfill any missing fields
                for attr, value in element.as_dict().items():
                    if not self._store[key].get(attr) and value:
                        self._store[key][attr] = value

    def to_list(self) -> list[dict[str, Any]]:
        """Return all elements as a list of dicts, sorted by path."""
        return sorted(self._store.values(), key=lambda e: e.get("Path", ""))

    def filter_by_type(self, element_type: str) -> list[dict[str, Any]]:
        """Return elements whose 'Element Type' starts with *element_type*."""
        return [
            entry
            for entry in self.to_list()
            if entry.get("Element Type", "").startswith(element_type)
        ]

    def schemas(self) -> list[dict[str, Any]]:
        return self.filter_by_type("schema")

    def parameters(self) -> list[dict[str, Any]]:
        return self.filter_by_type("parameter")

    def request_bodies(self) -> list[dict[str, Any]]:
        return self.filter_by_type("requestBody")

    def summary(self) -> dict[str, int]:
        """Return element counts per type."""
        counts: dict[str, int] = defaultdict(int)
        for entry in self._store.values():
            counts[entry.get("Element Type", "unknown")] += 1
        return dict(counts)
