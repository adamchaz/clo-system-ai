/**
 * DocumentManager Component - Comprehensive Document Management Interface
 * 
 * Main interface for document management with:
 * - Document upload with drag & drop support
 * - Document search and filtering
 * - Document preview and download
 * - Access control and sharing
 * - Version management and history
 * 
 * Integrates with new backend Document Management APIs
 */

import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Menu,
  Divider,
  Alert,
  LinearProgress,
  Tab,
  Tabs,
  Paper,
  Stack,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  CloudUpload,
  Search,
  FilterList,
  MoreVert,
  Download,
  Share,
  Edit,
  Delete,
  Visibility,
  InsertDriveFile,
  Folder,
  Description,
  PictureAsPdf,
  TableChart,
  Assessment,
  Security,
  History,
  Add,
  Refresh,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { format } from 'date-fns';

// Import our new API hooks
import {
  useGetDocumentsQuery,
  useUploadDocumentMutation,
  useUpdateDocumentMutation,
  useDeleteDocumentMutation,
  useSearchDocumentsMutation,
  useGetDocumentStatsQuery,
  useBulkDocumentOperationMutation,
} from '../../store/api/cloApi';

// Import document types
import {
  Document,
  DocumentType,
  DocumentStatus,
  AccessLevel,
  DocumentUploadRequest,
  DocumentUpdateRequest,
  DocumentSearchRequest,
} from '../../store/api/newApiTypes';

// Import WebSocket hooks for real-time updates
import { useDocumentUpdates } from '../../hooks/useWebSocket';

interface DocumentManagerProps {
  portfolioId?: string;
  readonly?: boolean;
  maxUploadSize?: number; // in MB
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} role="tabpanel">
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const DocumentManager: React.FC<DocumentManagerProps> = ({
  portfolioId,
  readonly = false,
  maxUploadSize = 50, // 50MB default
}) => {
  // State management
  const [currentTab, setCurrentTab] = useState(0);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [documentTypeFilter, setDocumentTypeFilter] = useState<DocumentType | ''>('');
  const [accessLevelFilter, setAccessLevelFilter] = useState<AccessLevel | ''>('');
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [menuAnchorEl, setMenuAnchorEl] = useState<HTMLElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // API hooks
  const {
    data: documentsResponse,
    isLoading,
    error,
    refetch,
  } = useGetDocumentsQuery({
    portfolio_id: portfolioId,
    limit: 100,
  });

  const { data: documentStats } = useGetDocumentStatsQuery();
  const [uploadDocument, { isLoading: isUploading }] = useUploadDocumentMutation();
  const [updateDocument] = useUpdateDocumentMutation();
  const [deleteDocument] = useDeleteDocumentMutation();
  const [searchDocuments, { isLoading: isSearching }] = useSearchDocumentsMutation();
  const [bulkDocumentOperation] = useBulkDocumentOperationMutation();

  const documents = documentsResponse?.data || [];

  // WebSocket integration for real-time updates
  useDocumentUpdates((updateData) => {
    console.log('Document update received:', updateData);
    // Refresh document list on updates
    refetch();
  });

  // File upload with drag & drop
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      if (file.size > maxUploadSize * 1024 * 1024) {
        alert(`File ${file.name} is too large. Maximum size is ${maxUploadSize}MB.`);
        continue;
      }

      const metadata: DocumentUploadRequest = {
        document_type: getDocumentTypeFromFile(file),
        access_level: 'internal',
        portfolio_id: portfolioId,
        tags: [file.type],
      };

      try {
        await uploadDocument({ file, metadata }).unwrap();
        console.log(`Uploaded: ${file.name}`);
      } catch (error) {
        console.error(`Failed to upload ${file.name}:`, error);
      }
    }
  }, [uploadDocument, portfolioId, maxUploadSize]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
    },
    multiple: true,
    disabled: readonly,
  });

  // Helper functions
  const getDocumentTypeFromFile = (file: File): DocumentType => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return 'report';
      case 'xls':
      case 'xlsx':
      case 'csv':
        return 'analysis_result';
      case 'doc':
      case 'docx':
        return 'legal_document';
      default:
        return 'user_upload';
    }
  };

  const getDocumentIcon = (document: Document) => {
    switch (document.document_type) {
      case 'report':
        return <Assessment />;
      case 'legal_document':
        return <Description />;
      case 'financial_statement':
        return <TableChart />;
      case 'analysis_result':
        return <TableChart />;
      default:
        return <InsertDriveFile />;
    }
  };

  const getStatusColor = (status: DocumentStatus) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'processing':
        return 'warning';
      case 'quarantined':
        return 'error';
      default:
        return 'default';
    }
  };

  const getAccessLevelColor = (accessLevel: AccessLevel) => {
    switch (accessLevel) {
      case 'public':
        return 'success';
      case 'internal':
        return 'info';
      case 'confidential':
        return 'warning';
      case 'restricted':
        return 'error';
      default:
        return 'default';
    }
  };

  // Event handlers
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleDocumentSelect = (documentId: string) => {
    setSelectedDocuments(prev => 
      prev.includes(documentId) 
        ? prev.filter(id => id !== documentId)
        : [...prev, documentId]
    );
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    const searchParams: DocumentSearchRequest = {
      query: searchQuery,
      document_type: documentTypeFilter || undefined,
      access_level: accessLevelFilter || undefined,
      portfolio_id: portfolioId,
      limit: 50,
      skip: 0,
    };

    try {
      await searchDocuments(searchParams);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleDownload = (document: Document) => {
    // Implement download functionality
    const link = document.createElement('a');
    link.href = `/api/v1/documents/${document.document_id}/download`;
    link.download = document.original_filename;
    link.click();
  };

  const handleDelete = async (documentId: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await deleteDocument(documentId);
      } catch (error) {
        console.error('Delete failed:', error);
      }
    }
  };

  const handleBulkOperation = async (operation: string) => {
    if (selectedDocuments.length === 0) return;

    try {
      await bulkDocumentOperation({
        item_ids: selectedDocuments,
        operation,
        reason: `Bulk ${operation} operation`,
      });
      setSelectedDocuments([]);
    } catch (error) {
      console.error('Bulk operation failed:', error);
    }
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesType = !documentTypeFilter || doc.document_type === documentTypeFilter;
    const matchesAccess = !accessLevelFilter || doc.access_level === accessLevelFilter;
    const matchesSearch = !searchQuery || 
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description?.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesType && matchesAccess && matchesSearch;
  });

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Document Management
          {documentStats && (
            <Badge badgeContent={documentStats.data?.total_documents} color="primary" sx={{ ml: 2 }}>
              <Folder />
            </Badge>
          )}
        </Typography>

        <Stack direction="row" spacing={2}>
          <Tooltip title="Refresh">
            <IconButton onClick={() => refetch()}>
              <Refresh />
            </IconButton>
          </Tooltip>
          
          {!readonly && (
            <>
              <Button
                variant="contained"
                startIcon={<CloudUpload />}
                onClick={() => setUploadDialogOpen(true)}
              >
                Upload Documents
              </Button>
              
              {selectedDocuments.length > 0 && (
                <Button
                  variant="outlined"
                  color="error"
                  onClick={() => handleBulkOperation('delete')}
                >
                  Delete Selected ({selectedDocuments.length})
                </Button>
              )}
            </>
          )}
        </Stack>
      </Box>

      {/* Statistics Cards */}
      {documentStats?.data && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Documents
                </Typography>
                <Typography variant="h4">
                  {documentStats.data.total_documents.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Size
                </Typography>
                <Typography variant="h4">
                  {(documentStats.data.total_size / (1024 * 1024)).toFixed(1)} MB
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Document Types
                </Typography>
                <Typography variant="h4">
                  {Object.keys(documentStats.data.by_type || {}).length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Recent Uploads
                </Typography>
                <Typography variant="h4">
                  {documentStats.data.recent_uploads?.length || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters and Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
              <TextField
                fullWidth
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Document Type</InputLabel>
                <Select
                  value={documentTypeFilter}
                  label="Document Type"
                  onChange={(e) => setDocumentTypeFilter(e.target.value as DocumentType)}
                >
                  <MenuItem value="">All Types</MenuItem>
                  <MenuItem value="report">Reports</MenuItem>
                  <MenuItem value="legal_document">Legal Documents</MenuItem>
                  <MenuItem value="financial_statement">Financial Statements</MenuItem>
                  <MenuItem value="analysis_result">Analysis Results</MenuItem>
                  <MenuItem value="user_upload">User Uploads</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Access Level</InputLabel>
                <Select
                  value={accessLevelFilter}
                  label="Access Level"
                  onChange={(e) => setAccessLevelFilter(e.target.value as AccessLevel)}
                >
                  <MenuItem value="">All Levels</MenuItem>
                  <MenuItem value="public">Public</MenuItem>
                  <MenuItem value="internal">Internal</MenuItem>
                  <MenuItem value="confidential">Confidential</MenuItem>
                  <MenuItem value="restricted">Restricted</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 2 }}>
              <Button
                fullWidth
                variant="contained"
                startIcon={<Search />}
                onClick={handleSearch}
                disabled={isSearching}
              >
                Search
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Loading indicator */}
      {(isLoading || isUploading) && <LinearProgress sx={{ mb: 2 }} />}

      {/* Error display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Error loading documents: {error.toString()}
        </Alert>
      )}

      {/* Document List */}
      <Card>
        <List>
          {filteredDocuments.map((document) => (
            <React.Fragment key={document.document_id}>
              <ListItem
                sx={{ 
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'action.hover' },
                  bgcolor: selectedDocuments.includes(document.document_id) ? 'action.selected' : 'transparent',
                }}
                onClick={() => handleDocumentSelect(document.document_id)}
              >
                <ListItemIcon>
                  {getDocumentIcon(document)}
                </ListItemIcon>
                
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">
                        {document.title || document.filename}
                      </Typography>
                      <Chip 
                        label={document.status} 
                        size="small" 
                        color={getStatusColor(document.status) as any}
                      />
                      <Chip 
                        label={document.access_level} 
                        size="small" 
                        color={getAccessLevelColor(document.access_level) as any}
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {document.description || 'No description'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Uploaded: {format(new Date(document.uploaded_at), 'PPp')} • 
                        Size: {document.file_size ? `${(document.file_size / 1024).toFixed(1)} KB` : 'Unknown'} • 
                        Type: {document.document_type.replace('_', ' ')}
                      </Typography>
                    </Box>
                  }
                />
                
                <ListItemSecondaryAction>
                  <Stack direction="row" spacing={1}>
                    <Tooltip title="Download">
                      <IconButton 
                        size="small" 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownload(document);
                        }}
                      >
                        <Download />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title="Share">
                      <IconButton 
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedDocument(document);
                          setShareDialogOpen(true);
                        }}
                      >
                        <Share />
                      </IconButton>
                    </Tooltip>
                    
                    {!readonly && (
                      <Tooltip title="Delete">
                        <IconButton 
                          size="small"
                          color="error"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(document.document_id);
                          }}
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Stack>
                </ListItemSecondaryAction>
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      </Card>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Upload Documents</DialogTitle>
        <DialogContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'transparent',
              mb: 2,
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop files here' : 'Drag & drop files here, or click to select'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Supported formats: PDF, Excel, Word, CSV, Text (Max: {maxUploadSize}MB each)
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onClose={() => setShareDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Share Document</DialogTitle>
        <DialogContent>
          {selectedDocument && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                {selectedDocument.title || selectedDocument.filename}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Configure sharing permissions and access for this document.
              </Typography>
              {/* Add sharing controls here */}
              <Alert severity="info">
                Document sharing features will be implemented in the next phase.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialogOpen(false)}>Close</Button>
          <Button variant="contained" disabled>Share</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentManager;