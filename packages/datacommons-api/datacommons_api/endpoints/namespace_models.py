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

from pydantic import BaseModel


class NamespaceResponse(BaseModel):
    name: str
    url: str
    is_readonly: bool
    is_datacommons: bool
    description: str | None = None


class NamespaceCreateRequest(BaseModel):
    name: str
    url: str
    is_readonly: bool = False
    is_datacommons: bool = False
    description: str | None = None


class NamespacePatchRequest(BaseModel):
    url: str | None = None
    is_readonly: bool | None = None
    is_datacommons: bool | None = None
    description: str | None = None
