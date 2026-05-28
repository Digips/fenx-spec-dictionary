"""Pipeline orchestration.

Ties together the parser, extractor, dictionary builder, and exporter
into a single high-level function that can be called programmatically or
driven by the CLI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fenx_spec_dictionary.dictionary import Dictionary
from fenx_spec_dictionary.exporter import export
from fenx_spec_dictionary.extractor import Extractor
from fenx_spec_dictionary.parser import load_spec


def run(
    sources: list[str],
    output_path: str | Path = "fenx_dictionary.xlsx",
) -> dict[str, Any]:
    """Execute the full pipeline.

    Parameters
    ----------
    sources:
        One or more local file paths or HTTP/HTTPS URLs pointing to OpenAPI
        specification files (JSON or YAML).
    output_path:
        Destination ``.xlsx`` file path.

    Returns
    -------
    dict
        A result summary with keys ``output``, ``element_count``, and
        ``summary``.
    """
    dictionary = Dictionary()

    for source in sources:
        spec = load_spec(source)
        source_name = Path(source).name if not source.startswith("http") else source
        extractor = Extractor(spec, source_name=source_name)
        elements = extractor.extract()
        dictionary.add_elements(elements)

    written = export(dictionary, output_path)

    return {
        "output": str(written),
        "element_count": len(dictionary.to_list()),
        "summary": dictionary.summary(),
    }
