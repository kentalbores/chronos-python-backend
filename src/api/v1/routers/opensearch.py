"""
OpenSearch CRUD Router

Provides endpoints for direct OpenSearch operations via Swagger/docs page.
Mirrors OpenSearch's native API paths for familiarity.
"""
from fastapi import APIRouter, Path, Body
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

from src.services.opensearch import opensearch_client

router = APIRouter(prefix="/opensearch", tags=["OpenSearch"])


@router.get(
    "/_cat/indices",
    summary="List all indices",
    description="Returns a list of all indices with metadata (health, status, doc count, size)."
)
async def list_indices():
    """List all OpenSearch indices."""
    result = await opensearch_client.list_indices()
    status_code = result.pop("_status_code", 200)
    return JSONResponse(content=result, status_code=status_code)



@router.post(
    "/{index}/_search",
    summary="Search documents",
    description="""
Search documents in an index using OpenSearch Query DSL.

**Example queries:**

Match all:
```json
{
    "query": {
        "match_all": {}
    }
}
```

Match query:
```json
{
    "query": {
        "match": {
            "name": "sample"
        }
    }
}
```

Bool query with filters:
```json
{
    "query": {
        "bool": {
            "must": [
                { "match": { "name": "sample" }}
            ],
            "filter": [
                { "term": { "active": true }},
                { "range": { "count": { "gt": 5 }}}
            ]
        }
    }
}
```
"""
)
async def search_documents(
    index: str = Path(..., description="Index name to search"),
    query: Optional[Dict[str, Any]] = Body(
        default={"query": {"match_all": {}}},
        description="OpenSearch Query DSL body"
    )
):
    """Search documents using Query DSL."""
    result = await opensearch_client.search(index, query)
    status_code = result.pop("_status_code", 200)
    return JSONResponse(content=result, status_code=status_code)


@router.post(
    "/{index}/_doc",
    summary="Create document (auto-generated ID)",
    description="Index a new document with an auto-generated ID."
)
async def create_document(
    index: str = Path(..., description="Index name"),
    document: Dict[str, Any] = Body(..., description="Document body to index")
):
    """Create a new document with auto-generated ID."""
    result = await opensearch_client.create_document(index, document)
    status_code = result.pop("_status_code", 200)
    return JSONResponse(content=result, status_code=status_code)


@router.put(
    "/{index}/_doc/{doc_id}",
    summary="Create/replace document with specific ID",
    description="Index a document with a specific ID. If the document exists, it will be replaced."
)
async def create_document_with_id(
    index: str = Path(..., description="Index name"),
    doc_id: str = Path(..., description="Document ID"),
    document: Dict[str, Any] = Body(..., description="Document body to index")
):
    """Create or replace a document with a specific ID."""
    result = await opensearch_client.create_document(index, document, doc_id)
    status_code = result.pop("_status_code", 200)
    return JSONResponse(content=result, status_code=status_code)


@router.get(
    "/{index}/_doc/{doc_id}",
    summary="Get document by ID",
    description="Retrieve a specific document by its ID."
)
async def get_document(
    index: str = Path(..., description="Index name"),
    doc_id: str = Path(..., description="Document ID")
):
    """Get a document by ID."""
    result = await opensearch_client.get_document(index, doc_id)
    status_code = result.pop("_status_code", 200)
    return JSONResponse(content=result, status_code=status_code)


@router.get(
    "/{index}/_mapping",
    summary="Get index mapping",
    description="Retrieve the mapping (schema) for an index."
)
async def get_index_mapping(
    index: str = Path(..., description="Index name")
):
    """Get the mapping for an index."""
    result = await opensearch_client.get_index_mapping(index)
    status_code = result.pop("_status_code", 200)
    return JSONResponse(content=result, status_code=status_code)


@router.post(
    "/{index}/_update/{doc_id}",
    summary="Update document",
    description="""
Update a document by ID. Use either "doc" for partial updates or "script" for scripted updates.

**Partial update example:**
```json
{
    "doc": {
        "field_to_update": "new_value"
    }
}
```

**Scripted update example:**
```json
{
    "script": {
        "source": "ctx._source.counter += params.count",
        "params": {
            "count": 1
        }
    }
}
```
"""
)
async def update_document(
    index: str = Path(..., description="Index name"),
    doc_id: str = Path(..., description="Document ID"),
    update_body: Dict[str, Any] = Body(
        ...,
        description="Update body with 'doc' or 'script'"
    )
):
    """Update a document by ID."""
    result = await opensearch_client.update_document(index, doc_id, update_body)
    status_code = result.pop("_status_code", 200)
    return JSONResponse(content=result, status_code=status_code)


@router.delete(
    "/{index}/_doc/{doc_id}",
    summary="Delete document",
    description="Delete a specific document by its ID."
)
async def delete_document(
    index: str = Path(..., description="Index name"),
    doc_id: str = Path(..., description="Document ID")
):
    """Delete a document by ID."""
    result = await opensearch_client.delete_document(index, doc_id)
    status_code = result.pop("_status_code", 200)
    return JSONResponse(content=result, status_code=status_code)


@router.delete(
    "/{index}",
    summary="Delete index",
    description="⚠️ **DANGER**: Delete an entire index and all its documents. This action is irreversible!"
)
async def delete_index(
    index: str = Path(..., description="Index name to delete")
):
    """Delete an entire index."""
    result = await opensearch_client.delete_index(index)
    status_code = result.pop("_status_code", 200)
    return JSONResponse(content=result, status_code=status_code)
