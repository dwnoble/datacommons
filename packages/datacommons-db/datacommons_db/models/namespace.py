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

import sqlalchemy as sa
from sqlalchemy.types import Boolean, String

from datacommons_db.models.base import Base

NAMESPACE_TABLE_NAME = "Namespace"


class NamespaceRecord(Base):
    __tablename__ = NAMESPACE_TABLE_NAME

    name = sa.Column(String(128), primary_key=True, autoincrement=False)
    url = sa.Column(String(2048), nullable=False)
    is_readonly = sa.Column(Boolean, nullable=False, default=False)
    is_datacommons = sa.Column(Boolean, nullable=False, default=False)
    description = sa.Column(String(1024), nullable=True)

    def __repr__(self) -> str:
        return (
            "<NamespaceRecord("
            f"name='{self.name}', url='{self.url}', readonly={self.is_readonly}, "
            f"datacommons={self.is_datacommons})>"
        )
