"""
Document Management Schemas
Pydantic models for document-related API requests and responses
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from ..models.documents import DocumentType, DocumentStatus, AccessLevel


class DocumentUploadRequest(BaseModel):
    """Schema for document upload requests"""
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.USER_UPLOAD
    access_level: AccessLevel = AccessLevel.INTERNAL
    portfolio_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class DocumentUpdateRequest(BaseModel):
    """Schema for document update requests"""
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None
    access_level: Optional[AccessLevel] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Schema for document API responses"""
    document_id: str
    filename: str
    original_filename: str
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: DocumentType
    
    # File information
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    file_extension: Optional[str] = None
    file_hash: Optional[str] = None
    
    # Access and organization
    access_level: AccessLevel
    owner_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Status
    status: DocumentStatus
    version: str = "1.0"
    is_latest_version: bool = True
    
    # Timestamps
    uploaded_at: datetime
    updated_at: datetime
    accessed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for paginated document list responses"""
    documents: List[DocumentResponse]
    total_count: int
    skip: int
    limit: int
    has_more: bool = False
    
    def __init__(self, **data):
        super().__init__(**data)
        self.has_more = (self.skip + len(self.documents)) < self.total_count


class DocumentSearchRequest(BaseModel):
    """Schema for document search requests"""
    query: Optional[str] = None
    document_type: Optional[DocumentType] = None
    access_level: Optional[AccessLevel] = None
    portfolio_id: Optional[str] = None
    owner_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_size: Optional[int] = None  # bytes
    max_size: Optional[int] = None  # bytes
    limit: int = Field(default=50, ge=1, le=500)
    skip: int = Field(default=0, ge=0)


class DocumentShareRequest(BaseModel):
    """Schema for document sharing requests"""
    shared_with: Optional[str] = None  # User ID or group
    share_type: str = Field(default="user", pattern="^(user|group|public_link)$")
    can_view: bool = True
    can_download: bool = False
    can_edit: bool = False
    can_share: bool = False
    expires_at: Optional[datetime] = None
    password_protected: bool = False
    link_password: Optional[str] = None


class DocumentShareResponse(BaseModel):
    """Schema for document share responses"""
    share_id: str
    document_id: str
    shared_by: str
    shared_with: Optional[str] = None
    share_type: str
    
    # Permissions
    can_view: bool
    can_download: bool
    can_edit: bool
    can_share: bool
    
    # Link details (for public links)
    public_link_token: Optional[str] = None
    password_protected: bool = False
    
    # Status
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    is_active: bool = True
    
    class Config:
        from_attributes = True


class DocumentFolderBase(BaseModel):
    """Base folder model"""
    folder_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    parent_folder_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    access_level: AccessLevel = AccessLevel.INTERNAL
    tags: List[str] = Field(default_factory=list)


class DocumentFolderCreate(DocumentFolderBase):
    """Schema for creating document folders"""
    pass


class DocumentFolderUpdate(BaseModel):
    """Schema for updating document folders"""
    folder_name: Optional[str] = None
    description: Optional[str] = None
    parent_folder_id: Optional[str] = None
    access_level: Optional[AccessLevel] = None
    tags: Optional[List[str]] = None


class DocumentFolderResponse(DocumentFolderBase):
    """Schema for document folder responses"""
    folder_id: str
    folder_path: Optional[str] = None
    level: int = 0
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    document_count: int = 0
    subfolder_count: int = 0
    
    class Config:
        from_attributes = True


class DocumentFolderContentsResponse(BaseModel):
    """Schema for folder contents responses"""
    folder: DocumentFolderResponse
    documents: List[DocumentResponse]
    subfolders: List[DocumentFolderResponse]
    total_documents: int
    total_subfolders: int


class DocumentAccessLogResponse(BaseModel):
    """Schema for document access log responses"""
    access_id: str
    document_id: str
    user_id: str
    access_type: str
    access_time: datetime
    success: bool
    ip_address: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentStatsResponse(BaseModel):
    """Schema for document statistics responses"""
    total_documents: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_access_level: Dict[str, int]
    total_size: int  # bytes
    recent_uploads: List[DocumentResponse] = Field(default_factory=list)
    most_accessed: List[DocumentResponse] = Field(default_factory=list)


class BulkDocumentOperation(BaseModel):
    """Schema for bulk document operations"""
    document_ids: List[str] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., pattern="^(delete|archive|activate|move|copy)$")
    parameters: Optional[Dict[str, Any]] = None


class BulkDocumentOperationResponse(BaseModel):
    """Schema for bulk document operation responses"""
    total_requested: int
    successful: int
    failed: int
    errors: List[str] = Field(default_factory=list)
    processed_document_ids: List[str] = Field(default_factory=list)


class DocumentVersionResponse(BaseModel):
    """Schema for document version responses"""
    document_id: str
    version: str
    filename: str
    file_size: Optional[int] = None
    uploaded_at: datetime
    is_latest_version: bool
    parent_document_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentPreviewResponse(BaseModel):
    """Schema for document preview responses"""
    document_id: str
    preview_available: bool
    preview_type: str  # thumbnail, text_extract, html_preview
    preview_url: Optional[str] = None
    preview_data: Optional[str] = None  # Base64 encoded for small previews
    page_count: Optional[int] = None  # For PDF documents
    text_extract: Optional[str] = None  # Extracted text content