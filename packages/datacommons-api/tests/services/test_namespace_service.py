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

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from datacommons_api.services.namespace_service import (
    DEFAULT_NAMESPACES,
    LOCAL_NAMESPACE_NAME,
    NamespaceService,
    extract_namespace_name,
)
from datacommons_db.models.namespace import NamespaceRecord


@pytest.fixture
def namespace_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    NamespaceRecord.__table__.create(bind=engine)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()


def test_ensure_default_namespaces_is_idempotent(namespace_session: Session):
    service = NamespaceService(namespace_session)

    first = service.ensure_default_namespaces()
    second = service.ensure_default_namespaces()

    assert len(first) == len(DEFAULT_NAMESPACES)
    assert len(second) == len(DEFAULT_NAMESPACES)
    assert len(service.list_namespaces()) == len(DEFAULT_NAMESPACES)


def test_create_patch_delete_namespace(namespace_session: Session):
    service = NamespaceService(namespace_session)
    service.ensure_default_namespaces()

    created = service.create_namespace(
        name="custom",
        url="https://example.org/custom/",
        description="custom namespace",
    )
    assert created.name == "custom"

    updated = service.update_namespace("custom", url="https://example.org/new/")
    assert updated.url == "https://example.org/new/"

    service.delete_namespace("custom")
    assert service.get_namespace("custom") is None


def test_delete_local_requires_cascade(namespace_session: Session):
    service = NamespaceService(namespace_session)
    service.ensure_default_namespaces()

    with pytest.raises(ValueError):
        service.delete_namespace(LOCAL_NAMESPACE_NAME, cascade=False)


def test_readonly_namespace_cannot_be_updated(namespace_session: Session):
    service = NamespaceService(namespace_session)
    service.ensure_default_namespaces()

    with pytest.raises(PermissionError):
        service.update_namespace("rdf", url="http://example.org/rdf#")


def test_extract_namespace_name_ignores_absolute_iri():
    assert extract_namespace_name("https://www.w3.org/2000/01/rdf-schema#Class") is None
    assert extract_namespace_name("http://schema.org/Thing") is None
    assert extract_namespace_name("xsd:string") == "xsd"
