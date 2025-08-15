/**
 * DocumentList Component - Simplified Document List View
 * 
 * A reusable document list component for displaying documents in various contexts:
 * - Portfolio-specific document views
 * - Recent documents widgets
 * - Search results display
 * - Embedded document lists
 */

import React, { useState } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Chip,
  Skeleton,
  Alert,
  Menu,
  MenuItem,
  Tooltip,
  Avatar,
  Stack,
} from '@mui/material';
import {
  InsertDriveFile,
  PictureAsPdf,
  TableChart,
  Description,
  Assessment,
  Download,
  Share,
  MoreVert,
  Visibility,
  Edit,
  Delete,
  Schedule,
  Person,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';

// Import types
import {
  Document,
  DocumentType,
  DocumentStatus,
  AccessLevel,
} from '../../store/api/newApiTypes';

interface DocumentListProps {
  documents: Document[];
  loading?: boolean;
  error?: string | null;
  onDownload?: (document: Document) => void;
  onShare?: (document: Document) => void;
  onEdit?: (document: Document) => void;
  onDelete?: (document: Document) => void;
  onView?: (document: Document) => void;
  showActions?: boolean;
  showMetadata?: boolean;
  showOwner?: boolean;
  compact?: boolean;
  maxItems?: number;
  emptyMessage?: string;
  readonly?: boolean;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  loading = false,
  error = null,
  onDownload,
  onShare,
  onEdit,
  onDelete,
  onView,
  showActions = true,
  showMetadata = true,
  showOwner = false,
  compact = false,
  maxItems,
  emptyMessage = 'No documents found',
  readonly = false,
}) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  const displayDocuments = maxItems ? documents.slice(0, maxItems) : documents;

  const getDocumentIcon = (documentType: DocumentType, mimeType?: string) => {
    // Check specific MIME type first
    if (mimeType) {
      if (mimeType.includes('pdf')) return <PictureAsPdf color="error" />;
      if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return <TableChart color="success" />;
      if (mimeType.includes('document') || mimeType.includes('word')) return <Description color="info" />;
    }

    // Fallback to document type
    switch (documentType) {
      case 'report':
      case 'analysis_result':
        return <Assessment color="primary" />;
      case 'legal_document':
        return <Description color="info" />;
      case 'financial_statement':
        return <TableChart color="success" />;
      case 'portfolio_document':
        return <Assessment color="primary" />;
      default:
        return <InsertDriveFile />;
    }
  };

  const getStatusChip = (status: DocumentStatus) => {
    const statusConfig = {
      uploading: { color: 'warning' as const, label: 'Uploading' },
      processing: { color: 'warning' as const, label: 'Processing' },
      active: { color: 'success' as const, label: 'Active' },
      archived: { color: 'default' as const, label: 'Archived' },
      deleted: { color: 'error' as const, label: 'Deleted' },
      quarantined: { color: 'error' as const, label: 'Quarantined' },
    };

    const config = statusConfig[status];
    return (
      <Chip
        label={config.label}
        color={config.color}
        size="small"
        variant="outlined"
      />
    );
  };

  const getAccessLevelChip = (accessLevel: AccessLevel) => {
    const accessConfig = {
      public: { color: 'success' as const, label: 'Public' },
      internal: { color: 'info' as const, label: 'Internal' },
      confidential: { color: 'warning' as const, label: 'Confidential' },
      restricted: { color: 'error' as const, label: 'Restricted' },
    };

    const config = accessConfig[accessLevel];
    return (
      <Chip
        label={config.label}
        color={config.color}
        size="small"
        sx={{ ml: 1 }}
      />
    );
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'Unknown size';
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, document: Document) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setSelectedDocument(document);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedDocument(null);
  };

  const handleMenuAction = (action: string) => {
    if (!selectedDocument) return;

    switch (action) {
      case 'view':
        onView?.(selectedDocument);
        break;
      case 'download':
        onDownload?.(selectedDocument);
        break;
      case 'share':
        onShare?.(selectedDocument);
        break;
      case 'edit':
        onEdit?.(selectedDocument);
        break;
      case 'delete':
        onDelete?.(selectedDocument);
        break;
    }

    handleMenuClose();
  };

  // Loading state
  if (loading) {
    return (
      <List>
        {[...Array(3)].map((_, index) => (
          <ListItem key={index}>
            <ListItemIcon>
              <Skeleton variant="circular" width={24} height={24} />
            </ListItemIcon>
            <ListItemText
              primary={<Skeleton variant="text" width="60%" />}
              secondary={<Skeleton variant="text" width="40%" />}
            />
            {showActions && (
              <ListItemSecondaryAction>
                <Skeleton variant="circular" width={24} height={24} />
              </ListItemSecondaryAction>
            )}
          </ListItem>
        ))}
      </List>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  // Empty state
  if (displayDocuments.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <InsertDriveFile sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
        <Typography variant="body2" color="text.secondary">
          {emptyMessage}
        </Typography>
      </Box>
    );
  }

  return (
    <>
      <List dense={compact}>
        {displayDocuments.map((document) => (
          <ListItem
            key={document.document_id}
            component={onView ? "button" : "div"}
            onClick={() => onView?.(document)}
            sx={{
              '&:hover': { bgcolor: 'action.hover' },
              py: compact ? 0.5 : 1,
            }}
          >
            <ListItemIcon>
              {getDocumentIcon(document.document_type, document.mime_type)}
            </ListItemIcon>

            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                  <Typography 
                    variant={compact ? 'body2' : 'subtitle1'}
                    sx={{ 
                      fontWeight: 500,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxWidth: compact ? 200 : 300,
                    }}
                  >
                    {document.title || document.filename}
                  </Typography>
                  
                  {showMetadata && (
                    <>
                      {getStatusChip(document.status)}
                      {getAccessLevelChip(document.access_level)}
                    </>
                  )}
                </Box>
              }
              secondary={
                <Box>
                  {!compact && document.description && (
                    <Typography 
                      variant="body2" 
                      color="text.secondary" 
                      sx={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        mb: 0.5,
                      }}
                    >
                      {document.description}
                    </Typography>
                  )}
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                    <Typography variant="caption" color="text.secondary">
                      <Schedule sx={{ fontSize: 12, mr: 0.5 }} />
                      {formatDistanceToNow(new Date(document.uploaded_at), { addSuffix: true })}
                    </Typography>
                    
                    {showMetadata && (
                      <>
                        <Typography variant="caption" color="text.secondary">
                          {formatFileSize(document.file_size)}
                        </Typography>
                        
                        <Typography variant="caption" color="text.secondary">
                          v{document.version}
                        </Typography>
                      </>
                    )}
                    
                    {showOwner && document.owner_id && (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Person sx={{ fontSize: 12, mr: 0.5 }} />
                        <Typography variant="caption" color="text.secondary">
                          Owner ID: {document.owner_id}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </Box>
              }
            />

            {showActions && (
              <ListItemSecondaryAction>
                <Stack direction="row" spacing={0.5}>
                  {onDownload && (
                    <Tooltip title="Download">
                      <IconButton 
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDownload(document);
                        }}
                      >
                        <Download />
                      </IconButton>
                    </Tooltip>
                  )}
                  
                  {(onShare || onEdit || onDelete) && (
                    <Tooltip title="More actions">
                      <IconButton 
                        size="small"
                        onClick={(e) => handleMenuOpen(e, document)}
                      >
                        <MoreVert />
                      </IconButton>
                    </Tooltip>
                  )}
                </Stack>
              </ListItemSecondaryAction>
            )}
          </ListItem>
        ))}
      </List>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        {onView && (
          <MenuItem onClick={() => handleMenuAction('view')}>
            <Visibility fontSize="small" sx={{ mr: 1 }} />
            View
          </MenuItem>
        )}
        
        {onDownload && (
          <MenuItem onClick={() => handleMenuAction('download')}>
            <Download fontSize="small" sx={{ mr: 1 }} />
            Download
          </MenuItem>
        )}
        
        {onShare && (
          <MenuItem onClick={() => handleMenuAction('share')}>
            <Share fontSize="small" sx={{ mr: 1 }} />
            Share
          </MenuItem>
        )}
        
        {onEdit && !readonly && (
          <MenuItem onClick={() => handleMenuAction('edit')}>
            <Edit fontSize="small" sx={{ mr: 1 }} />
            Edit
          </MenuItem>
        )}
        
        {onDelete && !readonly && (
          <MenuItem onClick={() => handleMenuAction('delete')}>
            <Delete fontSize="small" sx={{ mr: 1 }} />
            Delete
          </MenuItem>
        )}
      </Menu>

      {/* Show more indicator */}
      {maxItems && documents.length > maxItems && (
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Showing {maxItems} of {documents.length} documents
          </Typography>
        </Box>
      )}
    </>
  );
};

export default DocumentList;