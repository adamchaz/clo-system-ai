"""
Document Management Service
Business logic for document upload, storage, retrieval, and management
"""

import os
import hashlib
import uuid
import mimetypes
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, BinaryIO, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..core.database_config import get_db_session
from ..core.exceptions import CLOBusinessError, CLOValidationError
from ..models.documents import (
    Document, DocumentAccess, DocumentShare, DocumentFolder, DocumentFolderItem,
    DocumentType, DocumentStatus, AccessLevel
)
from ..schemas.documents import (
    DocumentUploadRequest, DocumentUpdateRequest, DocumentResponse,
    DocumentSearchRequest, DocumentShareRequest, DocumentShareResponse,
    DocumentFolderCreate, DocumentFolderUpdate, DocumentFolderResponse,
    DocumentStatsResponse, BulkDocumentOperation, BulkDocumentOperationResponse
)

logger = logging.getLogger(__name__)


class DocumentStorageProvider:
    """Base class for document storage providers"""
    
    def upload_file(self, file_data: BinaryIO, filename: str) -> str:
        """Upload file and return storage path"""
        raise NotImplementedError
    
    def download_file(self, storage_path: str) -> BinaryIO:
        """Download file from storage"""
        raise NotImplementedError
    
    def delete_file(self, storage_path: str) -> bool:
        """Delete file from storage"""
        raise NotImplementedError
    
    def get_file_info(self, storage_path: str) -> Dict[str, Any]:
        """Get file metadata"""
        raise NotImplementedError


class LocalFileStorageProvider(DocumentStorageProvider):
    """Local filesystem storage provider"""
    
    def __init__(self, base_path: str = "./data/documents"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, file_data: BinaryIO, filename: str) -> str:
        """Upload file to local storage"""
        # Create subdirectories based on date
        today = datetime.now()
        subdir = self.base_path / str(today.year) / f"{today.month:02d}"
        subdir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = subdir / unique_filename
        
        # Write file
        with open(file_path, "wb") as f:
            file_data.seek(0)
            f.write(file_data.read())
        
        return str(file_path.relative_to(self.base_path))
    
    def download_file(self, storage_path: str) -> BinaryIO:
        """Download file from local storage"""
        full_path = self.base_path / storage_path
        if not full_path.exists():
            raise CLOValidationError(f"File not found: {storage_path}")
        
        return open(full_path, "rb")
    
    def delete_file(self, storage_path: str) -> bool:
        """Delete file from local storage"""
        try:
            full_path = self.base_path / storage_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {storage_path}: {str(e)}")
            return False
    
    def get_file_info(self, storage_path: str) -> Dict[str, Any]:
        """Get file metadata"""
        full_path = self.base_path / storage_path
        if not full_path.exists():
            raise CLOValidationError(f"File not found: {storage_path}")
        
        stat = full_path.stat()
        return {
            "size": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime),
            "created_time": datetime.fromtimestamp(stat.st_ctime)
        }


class DocumentService:
    """Service for document management operations"""
    
    def __init__(self):
        self.storage_provider = LocalFileStorageProvider()
    
    def upload_document(
        self, 
        file_data: BinaryIO, 
        filename: str,
        request: DocumentUploadRequest,
        user_id: str
    ) -> DocumentResponse:
        """Upload a new document"""
        try:
            with get_db_session() as session:
                # Generate document ID
                document_id = f"DOC_{uuid.uuid4().hex[:12].upper()}"
                
                # Calculate file hash and metadata
                file_data.seek(0)
                content = file_data.read()
                file_hash = hashlib.sha256(content).hexdigest()
                file_size = len(content)
                
                # Reset file pointer for storage
                file_data.seek(0)
                
                # Detect MIME type
                mime_type, _ = mimetypes.guess_type(filename)
                file_extension = Path(filename).suffix.lower()
                
                # Upload to storage
                storage_path = self.storage_provider.upload_file(file_data, filename)
                
                # Create database record
                document = Document(
                    document_id=document_id,
                    filename=filename,
                    original_filename=filename,
                    title=request.title or filename,
                    description=request.description,
                    document_type=request.document_type,
                    file_size=file_size,
                    file_hash=file_hash,
                    mime_type=mime_type,
                    file_extension=file_extension,
                    storage_path=storage_path,
                    storage_provider="local",
                    access_level=request.access_level,
                    owner_id=user_id,
                    portfolio_id=request.portfolio_id,
                    related_entity_type=request.related_entity_type,
                    related_entity_id=request.related_entity_id,
                    tags=request.tags,
                    metadata=request.metadata,
                    status=DocumentStatus.ACTIVE
                )
                
                session.add(document)
                session.commit()
                
                # Log access
                self._log_access(session, document_id, user_id, "upload", True)
                
                return DocumentResponse.model_validate(document)
                
        except Exception as e:
            logger.error(f"Document upload failed: {str(e)}")
            raise CLOBusinessError(f"Document upload failed: {str(e)}") from e
    
    def get_document(self, document_id: str, user_id: str) -> DocumentResponse:
        """Get document metadata"""
        try:
            with get_db_session() as session:
                document = session.query(Document).filter(
                    Document.document_id == document_id,
                    Document.status != DocumentStatus.DELETED
                ).first()
                
                if not document:
                    raise CLOValidationError(f"Document not found: {document_id}")
                
                # Update last accessed time
                document.accessed_at = datetime.utcnow()
                session.commit()
                
                # Log access
                self._log_access(session, document_id, user_id, "view", True)
                
                return DocumentResponse.model_validate(document)
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            raise CLOBusinessError(f"Failed to retrieve document: {str(e)}") from e
    
    def download_document(self, document_id: str, user_id: str) -> Tuple[BinaryIO, str, str]:
        """Download document file"""
        try:
            with get_db_session() as session:
                document = session.query(Document).filter(
                    Document.document_id == document_id,
                    Document.status == DocumentStatus.ACTIVE
                ).first()
                
                if not document:
                    raise CLOValidationError(f"Document not found: {document_id}")
                
                # Download from storage
                file_data = self.storage_provider.download_file(document.storage_path)
                
                # Update last accessed time
                document.accessed_at = datetime.utcnow()
                session.commit()
                
                # Log access
                self._log_access(session, document_id, user_id, "download", True)
                
                return file_data, document.filename, document.mime_type or "application/octet-stream"
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Failed to download document {document_id}: {str(e)}")
            raise CLOBusinessError(f"Failed to download document: {str(e)}") from e
    
    def update_document(
        self, 
        document_id: str, 
        request: DocumentUpdateRequest, 
        user_id: str
    ) -> DocumentResponse:
        """Update document metadata"""
        try:
            with get_db_session() as session:
                document = session.query(Document).filter(
                    Document.document_id == document_id,
                    Document.status != DocumentStatus.DELETED
                ).first()
                
                if not document:
                    raise CLOValidationError(f"Document not found: {document_id}")
                
                # Update fields
                if request.title is not None:
                    document.title = request.title
                if request.description is not None:
                    document.description = request.description
                if request.document_type is not None:
                    document.document_type = request.document_type
                if request.access_level is not None:
                    document.access_level = request.access_level
                if request.tags is not None:
                    document.tags = request.tags
                if request.metadata is not None:
                    document.metadata = request.metadata
                
                document.updated_at = datetime.utcnow()
                session.commit()
                
                # Log access
                self._log_access(session, document_id, user_id, "edit", True)
                
                return DocumentResponse.model_validate(document)
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            raise CLOBusinessError(f"Failed to update document: {str(e)}") from e
    
    def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete document (soft delete)"""
        try:
            with get_db_session() as session:
                document = session.query(Document).filter(
                    Document.document_id == document_id,
                    Document.status != DocumentStatus.DELETED
                ).first()
                
                if not document:
                    raise CLOValidationError(f"Document not found: {document_id}")
                
                # Soft delete
                document.status = DocumentStatus.DELETED
                document.updated_at = datetime.utcnow()
                session.commit()
                
                # Log access
                self._log_access(session, document_id, user_id, "delete", True)
                
                return True
                
        except Exception as e:
            if isinstance(e, (CLOValidationError, CLOBusinessError)):
                raise
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            raise CLOBusinessError(f"Failed to delete document: {str(e)}") from e
    
    def search_documents(
        self, 
        request: DocumentSearchRequest, 
        user_id: str
    ) -> List[DocumentResponse]:
        """Search documents with filters"""
        try:
            with get_db_session() as session:
                query = session.query(Document).filter(
                    Document.status != DocumentStatus.DELETED
                )
                
                # Apply filters
                if request.query:
                    search_term = f"%{request.query}%"
                    query = query.filter(
                        or_(
                            Document.filename.ilike(search_term),
                            Document.title.ilike(search_term),
                            Document.description.ilike(search_term)
                        )
                    )
                
                if request.document_type:
                    query = query.filter(Document.document_type == request.document_type)
                
                if request.access_level:
                    query = query.filter(Document.access_level == request.access_level)
                
                if request.portfolio_id:
                    query = query.filter(Document.portfolio_id == request.portfolio_id)
                
                if request.owner_id:
                    query = query.filter(Document.owner_id == request.owner_id)
                
                if request.tags:
                    # PostgreSQL JSON array contains operation
                    for tag in request.tags:
                        query = query.filter(Document.tags.contains([tag]))
                
                if request.date_from:
                    query = query.filter(Document.uploaded_at >= request.date_from)
                
                if request.date_to:
                    query = query.filter(Document.uploaded_at <= request.date_to)
                
                if request.min_size:
                    query = query.filter(Document.file_size >= request.min_size)
                
                if request.max_size:
                    query = query.filter(Document.file_size <= request.max_size)
                
                # Order and paginate
                query = query.order_by(desc(Document.updated_at))
                documents = query.offset(request.skip).limit(request.limit).all()
                
                return [DocumentResponse.model_validate(doc) for doc in documents]
                
        except Exception as e:
            logger.error(f"Document search failed: {str(e)}")
            raise CLOBusinessError(f"Document search failed: {str(e)}") from e
    
    def get_document_statistics(self, user_id: str) -> DocumentStatsResponse:
        """Get document statistics"""
        try:
            with get_db_session() as session:
                # Basic counts
                total_docs = session.query(Document).filter(
                    Document.status != DocumentStatus.DELETED
                ).count()
                
                # By type
                by_type = {}
                type_query = session.query(
                    Document.document_type, func.count(Document.document_id)
                ).filter(
                    Document.status != DocumentStatus.DELETED
                ).group_by(Document.document_type)
                
                for doc_type, count in type_query.all():
                    by_type[doc_type.value] = count
                
                # By status
                by_status = {}
                status_query = session.query(
                    Document.status, func.count(Document.document_id)
                ).group_by(Document.status)
                
                for status, count in status_query.all():
                    by_status[status.value] = count
                
                # By access level
                by_access_level = {}
                access_query = session.query(
                    Document.access_level, func.count(Document.document_id)
                ).filter(
                    Document.status != DocumentStatus.DELETED
                ).group_by(Document.access_level)
                
                for level, count in access_query.all():
                    by_access_level[level.value] = count
                
                # Total size
                total_size = session.query(func.sum(Document.file_size)).filter(
                    Document.status != DocumentStatus.DELETED
                ).scalar() or 0
                
                # Recent uploads
                recent = session.query(Document).filter(
                    Document.status != DocumentStatus.DELETED
                ).order_by(desc(Document.uploaded_at)).limit(5).all()
                
                # Most accessed
                most_accessed = session.query(Document).filter(
                    Document.status != DocumentStatus.DELETED,
                    Document.accessed_at.isnot(None)
                ).order_by(desc(Document.accessed_at)).limit(5).all()
                
                return DocumentStatsResponse(
                    total_documents=total_docs,
                    by_type=by_type,
                    by_status=by_status,
                    by_access_level=by_access_level,
                    total_size=int(total_size),
                    recent_uploads=[DocumentResponse.model_validate(doc) for doc in recent],
                    most_accessed=[DocumentResponse.model_validate(doc) for doc in most_accessed]
                )
                
        except Exception as e:
            logger.error(f"Failed to get document statistics: {str(e)}")
            raise CLOBusinessError(f"Failed to get document statistics: {str(e)}") from e
    
    def _log_access(
        self, 
        session: Session, 
        document_id: str, 
        user_id: str, 
        access_type: str, 
        success: bool,
        error_message: Optional[str] = None
    ):
        """Log document access"""
        try:
            access_log = DocumentAccess(
                access_id=f"ACC_{uuid.uuid4().hex[:12].upper()}",
                document_id=document_id,
                user_id=user_id,
                access_type=access_type,
                success=success,
                error_message=error_message
            )
            session.add(access_log)
            session.flush()  # Don't commit here, let caller handle transaction
            
        except Exception as e:
            logger.warning(f"Failed to log document access: {str(e)}")
            # Don't fail the main operation due to logging issues