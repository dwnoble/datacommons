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

import re
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from datacommons_db.models.edge import EdgeRecord
from datacommons_db.models.namespace import NamespaceRecord
from datacommons_db.models.node import NodeRecord
from datacommons_db.models.observation import TimeSeriesRecord
from datacommons_db.models.observation import (
    ObservationAttributeRecord,
    ObservationRecord,
    TimeSeriesAttributeRecord,
)

LOCAL_NAMESPACE_NAME = "local"
LOCAL_NAMESPACE_URL = "http://localhost:5000/schema/local/"

DEFAULT_NAMESPACES: list[dict] = [
    {
        "name": "rdf",
        "url": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "is_readonly": True,
        "is_datacommons": False,
        "description": "RDF core namespace",
    },
    {
        "name": "rdfs",
        "url": "http://www.w3.org/2000/01/rdf-schema#",
        "is_readonly": True,
        "is_datacommons": False,
        "description": "RDF schema namespace",
    },
    {
        "name": "xsd",
        "url": "http://www.w3.org/2001/XMLSchema#",
        "is_readonly": True,
        "is_datacommons": False,
        "description": "XML schema datatypes",
    },
    {
        "name": LOCAL_NAMESPACE_NAME,
        "url": LOCAL_NAMESPACE_URL,
        "is_readonly": False,
        "is_datacommons": False,
        "description": "Local mutable namespace",
    },
    {
        "name": "dcid",
        "url": "https://datacommons.org/browser/",
        "is_readonly": True,
        "is_datacommons": True,
        "description": "Data Commons IDs",
    },
    {
        "name": "dcs",
        "url": "https://datacommons.org/browser/",
        "is_readonly": True,
        "is_datacommons": True,
        "description": "Data Commons IDs (legacy alias)",
    },
    {
        "name": "schema",
        "url": "https://schema.org/",
        "is_readonly": True,
        "is_datacommons": False,
        "description": "Schema.org namespace",
    },
    {
        "name": "system",
        "url": "http://localhost:5000/schema/system/",
        "is_readonly": True,
        "is_datacommons": False,
        "description": "Internal system namespace",
    },
]

SYSTEM_PROTECTED_NAMESPACES = {"rdf", "rdfs", "xsd"}
NAMESPACE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def is_literal_identifier(identifier: str | None) -> bool:
    return bool(identifier and identifier.startswith("l/"))


def extract_namespace_name(identifier: str | None) -> str | None:
    if not identifier or is_literal_identifier(identifier):
        return None
    if "://" in identifier:
        # Absolute IRIs are already fully-qualified and are not CURIE-style
        # namespace prefixes (e.g., avoid treating "https://..." as namespace "https").
        return None
    if ":" not in identifier:
        return None
    return identifier.split(":", 1)[0]


def ensure_qualified_identifier(identifier: str | None) -> str | None:
    if identifier is None:
        return None
    if identifier == "" or is_literal_identifier(identifier):
        return identifier
    if ":" in identifier:
        return identifier
    return f"{LOCAL_NAMESPACE_NAME}:{identifier}"


def validate_namespace_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("namespace url must be an absolute URL")
    if not (url.endswith("/") or url.endswith("#")):
        raise ValueError("namespace url must end with '/' or '#'")
    return url


class NamespaceService:
    def __init__(self, session: Session):
        self.session = session

    def ensure_default_namespaces(self) -> list[NamespaceRecord]:
        rows: list[NamespaceRecord] = []
        for entry in DEFAULT_NAMESPACES:
            existing = self.session.get(NamespaceRecord, entry["name"])
            if existing:
                rows.append(existing)
                continue
            row = NamespaceRecord(**entry)
            self.session.add(row)
            rows.append(row)
        self.session.commit()
        return rows

    def list_namespaces(self) -> list[NamespaceRecord]:
        return (
            self.session.execute(
                select(NamespaceRecord).order_by(NamespaceRecord.name.asc())
            )
            .scalars()
            .all()
        )

    def get_namespace(self, name: str) -> NamespaceRecord | None:
        return self.session.get(NamespaceRecord, name)

    def create_namespace(
        self,
        name: str,
        url: str,
        is_readonly: bool = False,
        is_datacommons: bool = False,
        description: str | None = None,
    ) -> NamespaceRecord:
        if not NAMESPACE_NAME_RE.fullmatch(name):
            raise ValueError("namespace name must match ^[a-z][a-z0-9_]*$")
        validate_namespace_url(url)
        if self.get_namespace(name):
            raise ValueError(f"namespace '{name}' already exists")

        row = NamespaceRecord(
            name=name,
            url=url,
            is_readonly=is_readonly,
            is_datacommons=is_datacommons,
            description=description,
        )
        self.session.add(row)
        self.session.commit()
        return row

    def update_namespace(
        self,
        name: str,
        url: str | None = None,
        is_readonly: bool | None = None,
        is_datacommons: bool | None = None,
        description: str | None = None,
    ) -> NamespaceRecord:
        row = self.get_namespace(name)
        if not row:
            raise LookupError(f"namespace '{name}' not found")
        if row.is_readonly:
            raise PermissionError(f"namespace '{name}' is read-only")
        if url is not None:
            row.url = validate_namespace_url(url)
        if is_readonly is not None:
            row.is_readonly = is_readonly
        if is_datacommons is not None:
            row.is_datacommons = is_datacommons
        if description is not None:
            row.description = description
        self.session.commit()
        return row

    def delete_namespace(self, name: str, cascade: bool = False) -> None:
        row = self.get_namespace(name)
        if not row:
            raise LookupError(f"namespace '{name}' not found")
        if name in SYSTEM_PROTECTED_NAMESPACES or row.is_readonly:
            raise PermissionError(f"namespace '{name}' is read-only")
        if name == LOCAL_NAMESPACE_NAME and not cascade:
            raise ValueError("deleting 'local' requires cascade=true")
        if name == LOCAL_NAMESPACE_NAME:
            self._cascade_delete_local_data()
        self.session.delete(row)
        self.session.commit()

    def namespace_name_set(self) -> set[str]:
        names = set()
        try:
            for row in self.session.execute(select(NamespaceRecord.name)).all():
                candidate = row[0]
                if isinstance(candidate, str) and candidate:
                    names.add(candidate)
        except Exception:
            names = set()
        if not names:
            names = {entry["name"] for entry in DEFAULT_NAMESPACES}
        return names

    def _cascade_delete_local_data(self) -> None:
        self.session.query(EdgeRecord).filter(
            EdgeRecord.subject_id.like(f"{LOCAL_NAMESPACE_NAME}:%")
        ).delete(synchronize_session=False)
        self.session.query(NodeRecord).filter(
            NodeRecord.namespace_name == LOCAL_NAMESPACE_NAME
        ).delete(synchronize_session=False)
        self.session.query(ObservationAttributeRecord).filter(
            ObservationAttributeRecord.id.like(f"{LOCAL_NAMESPACE_NAME}:%")
        ).delete(synchronize_session=False)
        self.session.query(ObservationRecord).filter(
            ObservationRecord.id.like(f"{LOCAL_NAMESPACE_NAME}:%")
        ).delete(synchronize_session=False)
        self.session.query(TimeSeriesAttributeRecord).filter(
            TimeSeriesAttributeRecord.id.like(f"{LOCAL_NAMESPACE_NAME}:%")
        ).delete(synchronize_session=False)
        self.session.query(TimeSeriesRecord).filter(
            TimeSeriesRecord.namespace_name == LOCAL_NAMESPACE_NAME
        ).delete(synchronize_session=False)
