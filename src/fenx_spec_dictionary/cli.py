"""Command-line interface for fenx-spec-dictionary."""

from __future__ import annotations

import sys

import click

from fenx_spec_dictionary.parser import SpecParseError
from fenx_spec_dictionary.pipeline import run


@click.command()
@click.argument("sources", nargs=-1, required=True, metavar="SPEC...")
@click.option(
    "-o",
    "--output",
    default="fenx_dictionary.xlsx",
    show_default=True,
    help="Output Excel workbook path.",
)
@click.version_option()
def main(sources: tuple[str, ...], output: str) -> None:
    """Wrangle Fen-X API specifications into an Excel dictionary.

    SPEC can be one or more local file paths or HTTP/HTTPS URLs pointing to
    OpenAPI specification files (JSON or YAML).

    Examples:

    \b
        fenx-dict my_spec.yaml
        fenx-dict spec_v1.yaml spec_v2.yaml -o dictionary.xlsx
        fenx-dict https://example.com/openapi.json -o output.xlsx
    """
    try:
        result = run(list(sources), output_path=output)
    except SpecParseError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Wrote {result['element_count']} elements to: {result['output']}")
    click.echo("\nElement type summary:")
    for element_type, count in sorted(result["summary"].items()):
        click.echo(f"  {element_type:<30} {count}")
