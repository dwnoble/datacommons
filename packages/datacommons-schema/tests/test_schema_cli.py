# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from datacommons_schema.schema_cli import (
    download_system_schema_docs,
    schema,
    _xsd_xml_to_jsonld,
)


def test_xsd_xml_to_jsonld_extracts_simple_types():
    xml = """<?xml version='1.0'?>
    <xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>
      <xs:simpleType name='string'/>
      <xs:simpleType name='boolean'/>
    </xs:schema>
    """
    payload = _xsd_xml_to_jsonld(xml)
    ids = [n["@id"] for n in payload["@graph"]]
    assert ids == ["xsd:boolean", "xsd:string"]


def test_download_system_schema_docs_writes_files(tmp_path: Path):
    with (
        patch(
            "datacommons_schema.schema_cli._download_rdf_jsonld",
            side_effect=[
                {"@context": {}, "@graph": [{"@id": "rdf:Property"}]},
                {"@context": {}, "@graph": [{"@id": "rdfs:Class"}]},
            ],
        ),
        patch(
            "datacommons_schema.schema_cli._download_xsd_schema_xml",
            return_value="<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'><xs:simpleType name='string'/></xs:schema>",
        ),
    ):
        written = download_system_schema_docs(output_dir=tmp_path, force=True)

    assert written == 3
    for filename in ("rdf.jsonld", "rdfs.jsonld", "xsd.jsonld"):
        assert (tmp_path / filename).exists()
        parsed = json.loads((tmp_path / filename).read_text(encoding="utf-8"))
        assert "@graph" in parsed


def test_download_system_schemas_command(tmp_path: Path):
    runner = CliRunner()
    with (
        patch(
            "datacommons_schema.schema_cli.download_system_schema_docs",
            return_value=3,
        ) as mock_download,
    ):
        result = runner.invoke(
            schema,
            [
                "download-system-schemas",
                "--output-dir",
                str(tmp_path),
                "--force",
            ],
        )

    assert result.exit_code == 0
    assert "Wrote 3 system schema file(s)" in result.output
    mock_download.assert_called_once_with(output_dir=tmp_path, force=True)
