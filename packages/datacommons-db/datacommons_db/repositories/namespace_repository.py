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

from sqlalchemy.orm import Session

from datacommons_db.models.namespace import NamespaceRecord


class NamespaceRepository:
    """Repository helpers for namespace CRUD and bootstrap operations."""

    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[NamespaceRecord]:
        return (
            self.session.query(NamespaceRecord)
            .order_by(NamespaceRecord.name.asc())
            .all()
        )

    def get(self, name: str) -> NamespaceRecord | None:
        return self.session.get(NamespaceRecord, name)

    def create(self, namespace: NamespaceRecord) -> NamespaceRecord:
        self.session.add(namespace)
        self.session.flush()
        return namespace

    def delete(self, namespace: NamespaceRecord) -> None:
        self.session.delete(namespace)

    def commit(self) -> None:
        self.session.commit()
