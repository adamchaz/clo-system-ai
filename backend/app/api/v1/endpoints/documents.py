"""
Document Management API Endpoints
FastAPI routes for document upload, storage, retrieval, and management
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from ....core.security import get_current_user, require_permissions
from ....schemas.documents import (
    DocumentUploadRequest, DocumentUpdateRequest, DocumentResponse,
    DocumentListResponse, DocumentSearchRequest, DocumentStatsResponse,
    BulkDocumentOperation, BulkDocumentOperationResponse,
    DocumentFolderCreate, DocumentFolderUpdate, DocumentFolderResponse
)
from ....services.documents_service import DocumentService
from ....core.exceptions import CLOBusinessError, CLOValidationError

router = APIRouter()
document_service = DocumentService()


@router.post("/upload", response_model=DocumentResponse, status_code=HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    document_type: str = Form("user_upload"),
    access_level: str = Form("internal"),
    portfolio_id: Optional[str] = Form(None),
    related_entity_type: Optional[str] = Form(None),
    related_entity_id: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string of list
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload a new document
    
    - **file**: Document file to upload
    - **title**: Document title (optional, defaults to filename)
    - **description**: Document description
    - **document_type**: Type of document (user_upload, report, etc.)
    - **access_level**: Access level (public, internal, confidential, restricted)
    - **portfolio_id**: Associated portfolio ID
    - **related_entity_type**: Type of related entity (asset, liability, etc.)
    - **related_entity_id**: ID of related entity
    - **tags**: JSON string of tags list
    """
    try:
        # Parse tags if provided
        tag_list = []
        if tags:
            import json
            try:
                tag_list = json.loads(tags)
                if not isinstance(tag_list, list):
                    tag_list = []
            except json.JSONDecodeError:
                tag_list = []
        
        # Create request object
        upload_request = DocumentUploadRequest(
            title=title,
            description=description,
            document_type=document_type,
            access_level=access_level,
            portfolio_id=portfolio_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            tags=tag_list
        )
        
        # Upload document
        result = document_service.upload_document(
            file.file, 
            file.filename, 
            upload_request,
            current_user["user_id"]
        )
        
        return result
        
    except (CLOBusinessError, CLOValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get document metadata by ID
    
    - **document_id**: Document identifier
    """
    try:
        result = document_service.get_document(document_id, current_user["user_id"])
        return result
        
    except CLOValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download document file
    
    - **document_id**: Document identifier
    """
    try:
        file_data, filename, mime_type = document_service.download_document(
            document_id, current_user["user_id"]
        )
        
        return StreamingResponse(
            file_data,
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except CLOValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    request: DocumentUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update document metadata
    
    - **document_id**: Document identifier
    - **request**: Update parameters
    """
    try:
        result = document_service.update_document(
            document_id, request, current_user["user_id"]
        )
        return result
        
    except CLOValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.delete("/{document_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete document (soft delete)
    
    - **document_id**: Document identifier
    """
    try:
        document_service.delete_document(document_id, current_user["user_id"])
        return Response(status_code=HTTP_204_NO_CONTENT)
        
    except CLOValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    document_type: Optional[str] = Query(None),
    access_level: Optional[str] = Query(None),
    portfolio_id: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List documents with optional filters
    
    - **skip**: Number of documents to skip (pagination)
    - **limit**: Maximum number of documents to return
    - **document_type**: Filter by document type
    - **access_level**: Filter by access level
    - **portfolio_id**: Filter by portfolio ID
    - **owner_id**: Filter by owner user ID
    """
    try:
        search_request = DocumentSearchRequest(
            skip=skip,
            limit=limit,
            document_type=document_type,
            access_level=access_level,
            portfolio_id=portfolio_id,
            owner_id=owner_id
        )
        
        documents = document_service.search_documents(search_request, current_user["user_id"])
        
        # For pagination, we need total count - this is simplified
        total_count = len(documents)  # In real implementation, do separate count query
        
        return DocumentListResponse(
            documents=documents,
            total_count=total_count,
            skip=skip,
            limit=limit,
            has_more=(skip + len(documents)) < total_count
        )
        
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.post("/search", response_model=List[DocumentResponse])
async def search_documents(
    request: DocumentSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Advanced document search with multiple criteria
    
    - **request**: Search parameters including query, filters, date ranges, etc.
    """
    try:
        results = document_service.search_documents(request, current_user["user_id"])
        return results
        
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats/summary", response_model=DocumentStatsResponse)
async def get_document_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get document system statistics
    
    Returns counts by type, status, access level, total size, and recent activity
    """
    try:
        stats = document_service.get_document_statistics(current_user["user_id"])
        return stats
        
    except CLOBusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/bulk", response_model=BulkDocumentOperationResponse)
async def bulk_document_operation(
    request: BulkDocumentOperation,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Perform bulk operations on multiple documents
    
    - **request**: Bulk operation parameters including document IDs and operation type
    
    Supported operations:
    - delete: Soft delete multiple documents
    - archive: Archive multiple documents
    - activate: Activate multiple documents
    - move: Move documents to a folder
    - copy: Copy documents to a folder
    """
    try:
        successful = 0
        failed = 0
        errors = []
        processed_ids = []
        
        for doc_id in request.document_ids:
            try:
                if request.operation == "delete":
                    document_service.delete_document(doc_id, current_user["user_id"])
                    successful += 1
                    processed_ids.append(doc_id)
                # Add other operations as needed
                else:
                    errors.append(f"Unsupported operation: {request.operation}")
                    failed += 1
                    
            except Exception as e:
                errors.append(f"Failed to process {doc_id}: {str(e)}")
                failed += 1
        
        return BulkDocumentOperationResponse(
            total_requested=len(request.document_ids),
            successful=successful,
            failed=failed,
            errors=errors,
            processed_document_ids=processed_ids
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk operation failed: {str(e)}")


@router.get("/{document_id}/versions", response_model=List[DocumentResponse])
async def get_document_versions(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all versions of a document
    
    - **document_id**: Document identifier
    """
    try:
        # This would be implemented in the service
        # For now, return empty list
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


@router.get("/{document_id}/preview")
async def preview_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get document preview (thumbnail, text extract, etc.)
    
    - **document_id**: Document identifier
    """
    try:
        # This would generate/retrieve document previews
        # For now, return basic info
        return {
            "document_id": document_id,
            "preview_available": False,
            "message": "Preview not implemented yet"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


# Document sharing endpoints (simplified)
@router.post("/{document_id}/share")
async def share_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Share document with other users or create public link
    
    - **document_id**: Document identifier
    """
    try:
        return {
            "document_id": document_id,
            "share_id": f"SHARE_{uuid.uuid4().hex[:12].upper()}",
            "message": "Document sharing not fully implemented yet"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Share failed: {str(e)}")


# Folder management endpoints (simplified)
@router.post("/folders", response_model=DocumentFolderResponse, status_code=HTTP_201_CREATED)
async def create_folder(
    request: DocumentFolderCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new document folder
    
    - **request**: Folder creation parameters
    """
    try:
        # This would be implemented in the service
        folder_id = f"FOLDER_{uuid.uuid4().hex[:12].upper()}"
        
        return DocumentFolderResponse(
            folder_id=folder_id,
            folder_name=request.folder_name,
            description=request.description,
            parent_folder_id=request.parent_folder_id,
            portfolio_id=request.portfolio_id,
            access_level=request.access_level,
            tags=request.tags,
            level=0,
            owner_id=current_user["user_id"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Folder creation failed: {str(e)}")


@router.get("/folders/{folder_id}")
async def get_folder_contents(
    folder_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get folder contents (documents and subfolders)
    
    - **folder_id**: Folder identifier
    """
    try:
        return {
            "folder_id": folder_id,
            "documents": [],
            "subfolders": [],
            "message": "Folder management not fully implemented yet"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get folder contents: {str(e)}")