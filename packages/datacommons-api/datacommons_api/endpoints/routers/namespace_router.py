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

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from datacommons_api.endpoints.dependencies import with_namespace_service
from datacommons_api.endpoints.namespace_models import (
    NamespaceCreateRequest,
    NamespacePatchRequest,
    NamespaceResponse,
)
from datacommons_api.services.namespace_service import NamespaceService

router = APIRouter()


def _as_response(row) -> NamespaceResponse:
    return NamespaceResponse(
        name=row.name,
        url=row.url,
        is_readonly=row.is_readonly,
        is_datacommons=row.is_datacommons,
        description=row.description,
    )


@router.get("/namespaces", response_model=list[NamespaceResponse])
def list_namespaces(
    namespace_service: Annotated[NamespaceService, Depends(with_namespace_service)],
) -> list[NamespaceResponse]:
    return [_as_response(row) for row in namespace_service.list_namespaces()]


@router.get("/namespaces/{name}", response_model=NamespaceResponse)
def get_namespace(
    name: str,
    namespace_service: Annotated[NamespaceService, Depends(with_namespace_service)],
) -> NamespaceResponse:
    row = namespace_service.get_namespace(name)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"namespace '{name}' not found",
        )
    return _as_response(row)


@router.post("/namespaces", response_model=NamespaceResponse, status_code=201)
def create_namespace(
    request: NamespaceCreateRequest,
    namespace_service: Annotated[NamespaceService, Depends(with_namespace_service)],
) -> NamespaceResponse:
    try:
        row = namespace_service.create_namespace(
            name=request.name,
            url=request.url,
            is_readonly=request.is_readonly,
            is_datacommons=request.is_datacommons,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _as_response(row)


@router.patch("/namespaces/{name}", response_model=NamespaceResponse)
def patch_namespace(
    name: str,
    request: NamespacePatchRequest,
    namespace_service: Annotated[NamespaceService, Depends(with_namespace_service)],
) -> NamespaceResponse:
    try:
        row = namespace_service.update_namespace(
            name=name,
            url=request.url,
            is_readonly=request.is_readonly,
            is_datacommons=request.is_datacommons,
            description=request.description,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _as_response(row)


@router.delete("/namespaces/{name}", status_code=204)
def delete_namespace(
    name: str,
    cascade: Annotated[bool, Query()] = False,
    namespace_service: Annotated[NamespaceService, Depends(with_namespace_service)] = None,
) -> None:
    try:
        namespace_service.delete_namespace(name, cascade=cascade)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
