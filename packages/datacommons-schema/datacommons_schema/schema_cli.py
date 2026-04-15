import sys
import json
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

import click
import rdflib

from datacommons_schema.converters.mcf_to_jsonld import mcf_nodes_to_jsonld
from datacommons_schema.parsers.mcf_parser import parse_mcf_string


@click.group()
def schema():
    """Data Commons Schema Parsing CLI"""


def _base_schema_context() -> dict[str, str]:
    return {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
    }


def _download_rdf_jsonld(url: str) -> dict:
    graph = rdflib.Graph()
    graph.parse(url)
    serialized = graph.serialize(
        format="json-ld",
        context=_base_schema_context(),
        auto_compact=True,
        indent=2,
    )
    if isinstance(serialized, bytes):
        serialized = serialized.decode("utf-8")
    payload = json.loads(serialized)
    if isinstance(payload, list):
        return {"@context": _base_schema_context(), "@graph": payload}
    payload.setdefault("@context", _base_schema_context())
    payload.setdefault("@graph", [])
    return payload


def _download_xsd_schema_xml() -> str:
    request = Request(
        "https://www.w3.org/2001/XMLSchema",
        headers={"Accept": "application/xml"},
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def _xsd_xml_to_jsonld(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    xsd_ns = "{http://www.w3.org/2001/XMLSchema}"
    graph = []
    for simple_type in root.findall(f".//{xsd_ns}simpleType"):
        name = simple_type.attrib.get("name")
        if not name:
            continue
        graph.append(
            {
                "@id": f"xsd:{name}",
                "@type": "rdfs:Datatype",
                "rdfs:label": {"@value": name},
            }
        )
    graph.sort(key=lambda node: node["@id"])
    return {"@context": _base_schema_context(), "@graph": graph}


def download_system_schema_docs(output_dir: Path, force: bool = False) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0

    targets = {
        "rdf.jsonld": lambda: _download_rdf_jsonld("https://www.w3.org/1999/02/22-rdf-syntax-ns"),
        "rdfs.jsonld": lambda: _download_rdf_jsonld("https://www.w3.org/2000/01/rdf-schema"),
        "xsd.jsonld": lambda: _xsd_xml_to_jsonld(_download_xsd_schema_xml()),
    }

    for filename, producer in targets.items():
        path = output_dir / filename
        if path.exists() and not force:
            continue
        payload = producer()
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        written += 1

    return written


@schema.command()
@click.argument("mcf_file", type=click.Path(exists=True))
@click.option(
    "--namespace",
    "-n",
    help='Namespace to inject into JSONLD output (e.g. "schema:https://schema.org/")',
)
@click.option(
    "--outfile", "-o", type=click.Path(), help="Output file path (defaults to stdout)"
)
@click.option(
    "--compact",
    "-c",
    is_flag=True,
    help="Output compact JSON-LD format without type information, using only literal values or object references",
)
def mcf2jsonld(mcf_file, namespace, outfile, *, compact: bool = False):
    """Convert MCF file to JSONLD format"""
    # Read MCF file
    with open(mcf_file) as f:
        mcf_content = f.read()
    # Convert nodes to JSONLD
    mcf_nodes = parse_mcf_string(mcf_content)
    jsonld = mcf_nodes_to_jsonld(mcf_nodes, compact=compact)

    # Add namespace if provided
    if namespace:
        try:
            ns_prefix, ns_url = namespace.split(":", 1)
            jsonld.context[ns_prefix] = ns_url
        except ValueError:
            click.echo(
                "Error: Invalid namespace format. Expected format: prefix:url", err=True
            )
            sys.exit(1)

    # Convert to formatted JSON string
    output = jsonld.model_dump_json(indent=2)

    # Write to file or stdout
    if outfile:
        with open(outfile, "w") as f:
            f.write(output)
    else:
        click.echo(output)


@schema.command("download-system-schemas")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("schema"),
    show_default=True,
    help="Directory where rdf.jsonld, rdfs.jsonld, and xsd.jsonld are written.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing files by re-downloading them.",
)
def download_system_schemas(output_dir: Path, force: bool):
    """Download W3C system schema docs (rdf/rdfs/xsd) as JSON-LD files."""
    try:
        written = download_system_schema_docs(output_dir=output_dir, force=force)
    except Exception as e:
        click.echo(f"Error downloading system schemas: {e}", err=True)
        raise SystemExit(1) from e

    click.echo(f"Wrote {written} system schema file(s) to {output_dir}")
