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

from pathlib import Path
from unittest.mock import MagicMock, patch

from datacommons_api.api_cli import _seed_core_schema_docs


def _write_schema_doc(path: Path, payload: str) -> None:
    path.write_text(payload, encoding="utf-8")


def test_seed_core_schema_docs_imports_non_empty_graphs(tmp_path: Path):
    _write_schema_doc(
        tmp_path / "rdf.jsonld",
        '{"@context":{"rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#"},"@graph":[{"@id":"rdf:Thing"}]}',
    )
    _write_schema_doc(
        tmp_path / "rdfs.jsonld",
        '{"@context":{"rdfs":"http://www.w3.org/2000/01/rdf-schema#"},"@graph":[{"@id":"rdfs:Class"}]}',
    )
    _write_schema_doc(
        tmp_path / "xsd.jsonld",
        '{"@context":{"xsd":"http://www.w3.org/2001/XMLSchema#"},"@graph":[]}',
    )

    db = MagicMock()
    mock_graph_service = MagicMock()
    with patch("datacommons_api.api_cli.GraphService", return_value=mock_graph_service):
        imported = _seed_core_schema_docs(db, schema_dir=tmp_path)

    assert imported == 2
    assert mock_graph_service.insert_graph_nodes.call_count == 2


def test_seed_core_schema_docs_skips_missing_files(tmp_path: Path):
    _write_schema_doc(
        tmp_path / "rdf.jsonld",
        '{"@context":{"rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#"},"@graph":[]}',
    )

    db = MagicMock()
    mock_graph_service = MagicMock()
    with patch("datacommons_api.api_cli.GraphService", return_value=mock_graph_service):
        imported = _seed_core_schema_docs(db, schema_dir=tmp_path)

    assert imported == 0
    mock_graph_service.insert_graph_nodes.assert_not_called()
