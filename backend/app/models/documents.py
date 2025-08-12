"""
Document Management Models
Database models for document storage, metadata, and access control
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, Enum as SQLEnum, LargeBinary, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from ..core.database import Base


class DocumentType(str, Enum):
    """Document type enumeration"""
    REPORT = "report"
    LEGAL_DOCUMENT = "legal_document"
    FINANCIAL_STATEMENT = "financial_statement"
    COMPLIANCE_DOCUMENT = "compliance_document"
    ASSET_DOCUMENT = "asset_document"
    PORTFOLIO_DOCUMENT = "portfolio_document"
    WATERFALL_OUTPUT = "waterfall_output"
    ANALYSIS_RESULT = "analysis_result"
    USER_UPLOAD = "user_upload"
    SYSTEM_GENERATED = "system_generated"


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    QUARANTINED = "quarantined"


class AccessLevel(str, Enum):
    """Document access level"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class Document(Base):
    """
    Document metadata and storage information
    """
    __tablename__ = 'documents'
    
    document_id = Column(String(50), primary_key=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    
    # File metadata
    file_size = Column(Integer)  # Size in bytes
    file_hash = Column(String(64))  # SHA-256 hash
    mime_type = Column(String(100))
    file_extension = Column(String(10))
    
    # Storage information
    storage_path = Column(String(500))  # Path to file in storage
    storage_provider = Column(String(50), default="local")  # local, azure_blob, s3, etc.
    
    # Document metadata
    title = Column(String(200))
    description = Column(Text)
    tags = Column(JSON)  # List of tags
    document_metadata = Column(JSON)  # Additional metadata
    
    # Access control
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.INTERNAL)
    owner_id = Column(String(100))  # User who uploaded/owns the document
    organization = Column(String(100))
    
    # Status and processing
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADING)
    processing_status = Column(Text)  # Processing details/errors
    
    # Relationships
    portfolio_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=True)
    related_entity_type = Column(String(50))  # asset, liability, report, etc.
    related_entity_id = Column(String(50))
    
    # Versioning
    version = Column(String(20), default="1.0")
    parent_document_id = Column(String(50), ForeignKey('documents.document_id'))
    is_latest_version = Column(Boolean, default=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    accessed_at = Column(DateTime)  # Last access time
    expires_at = Column(DateTime)  # Auto-cleanup date
    
    # Relationships
    portfolio = relationship("CLODeal", backref="documents")
    parent_document = relationship("Document", remote_side=[document_id], backref="versions")
    
    def __repr__(self):
        return f"<Document({self.document_id}: {self.filename})>"


class DocumentAccess(Base):
    """
    Document access log and permissions
    """
    __tablename__ = 'document_access'
    
    access_id = Column(String(50), primary_key=True)
    document_id = Column(String(50), ForeignKey('documents.document_id'), nullable=False)
    user_id = Column(String(100), nullable=False)
    
    # Access details
    access_type = Column(String(20))  # read, download, edit, delete
    access_time = Column(DateTime, default=func.now())
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Relationships
    document = relationship("Document", backref="access_logs")
    
    def __repr__(self):
        return f"<DocumentAccess({self.access_id}: {self.user_id} -> {self.document_id})>"


class DocumentShare(Base):
    """
    Document sharing and collaboration
    """
    __tablename__ = 'document_shares'
    
    share_id = Column(String(50), primary_key=True)
    document_id = Column(String(50), ForeignKey('documents.document_id'), nullable=False)
    
    # Sharing details
    shared_by = Column(String(100), nullable=False)
    shared_with = Column(String(100))  # User ID or group
    share_type = Column(String(20))  # user, group, public_link
    
    # Permissions
    can_view = Column(Boolean, default=True)
    can_download = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    
    # Link sharing
    public_link_token = Column(String(128))  # For public link sharing
    password_protected = Column(Boolean, default=False)
    link_password_hash = Column(String(128))
    
    # Timing
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)
    accessed_at = Column(DateTime)  # Last access via share
    access_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    document = relationship("Document", backref="shares")
    
    def __repr__(self):
        return f"<DocumentShare({self.share_id}: {self.document_id} shared by {self.shared_by})>"


class DocumentFolder(Base):
    """
    Document organization folders/collections
    """
    __tablename__ = 'document_folders'
    
    folder_id = Column(String(50), primary_key=True)
    folder_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Hierarchy
    parent_folder_id = Column(String(50), ForeignKey('document_folders.folder_id'))
    folder_path = Column(String(500))  # Full path for quick queries
    level = Column(Integer, default=0)  # Depth level
    
    # Organization
    portfolio_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=True)
    owner_id = Column(String(100))
    access_level = Column(SQLEnum(AccessLevel), default=AccessLevel.INTERNAL)
    
    # Metadata
    tags = Column(JSON)
    folder_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("CLODeal", backref="document_folders")
    parent_folder = relationship("DocumentFolder", remote_side=[folder_id], backref="subfolders")
    
    def __repr__(self):
        return f"<DocumentFolder({self.folder_id}: {self.folder_name})>"


class DocumentFolderItem(Base):
    """
    Many-to-many relationship between documents and folders
    """
    __tablename__ = 'document_folder_items'
    
    item_id = Column(String(50), primary_key=True)
    folder_id = Column(String(50), ForeignKey('document_folders.folder_id'), nullable=False)
    document_id = Column(String(50), ForeignKey('documents.document_id'), nullable=False)
    
    # Organization
    sort_order = Column(Integer, default=0)
    added_at = Column(DateTime, default=func.now())
    added_by = Column(String(100))
    
    # Relationships
    folder = relationship("DocumentFolder", backref="folder_items")
    document = relationship("Document", backref="folder_memberships")
    
    def __repr__(self):
        return f"<DocumentFolderItem({self.folder_id} -> {self.document_id})>"