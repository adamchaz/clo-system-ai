/**
 * DocumentViewer Component - Document Details and Preview
 * 
 * Displays comprehensive document information including:
 * - Document metadata and properties
 * - Version history and access logs
 * - Preview capabilities (when possible)
 * - Download and sharing options
 * - Edit document metadata
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Stack,
  Divider,
  Alert,
  Skeleton,
  Tooltip,
} from '@mui/material';
import {
  Download,
  Share,
  Edit,
  Delete,
  Visibility,
  History,
  Security,
  Info,
  InsertDriveFile,
  PictureAsPdf,
  TableChart,
  Description,
  Assessment,
  Close,
  Save,
  Person,
  Schedule,
  Storage,
  Fingerprint,
} from '@mui/icons-material';
import { format } from 'date-fns';

// Import API hooks
import {
  useGetDocumentQuery,
  useUpdateDocumentMutation,
  useDeleteDocumentMutation,
  useDownloadDocumentMutation,
} from '../../store/api/cloApi';

// Import types
import {
  Document,
  DocumentType,
  DocumentStatus,
  AccessLevel,
  DocumentUpdateRequest,
} from '../../store/api/newApiTypes';

interface DocumentViewerProps {
  documentId: string;
  open: boolean;
  onClose: () => void;
  onDeleted?: () => void;
  onUpdated?: (document: Document) => void;
  readonly?: boolean;
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

const DocumentViewer: React.FC<DocumentViewerProps> = ({
  documentId,
  open,
  onClose,
  onDeleted,
  onUpdated,
  readonly = false,
}) => {
  const [currentTab, setCurrentTab] = useState(0);
  const [editMode, setEditMode] = useState(false);
  const [editFormData, setEditFormData] = useState<DocumentUpdateRequest>({});

  // API hooks
  const {
    data: documentResponse,
    isLoading,
    error,
    refetch,
  } = useGetDocumentQuery(documentId, { skip: !open });

  const [updateDocument, { isLoading: isUpdating }] = useUpdateDocumentMutation();
  const [deleteDocument, { isLoading: isDeleting }] = useDeleteDocumentMutation();
  const [downloadDocument] = useDownloadDocumentMutation();

  const doc = documentResponse?.data;

  // Initialize edit form data when document loads
  React.useEffect(() => {
    if (doc) {
      setEditFormData({
        title: doc.title || '',
        description: doc.description || '',
        document_type: doc.document_type,
        access_level: doc.access_level,
        tags: doc.tags,
      });
    }
  }, [document]);

  const getDocumentIcon = (documentType: DocumentType, mimeType?: string) => {
    if (mimeType) {
      if (mimeType.includes('pdf')) return <PictureAsPdf color="error" sx={{ fontSize: 40 }} />;
      if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return <TableChart color="success" sx={{ fontSize: 40 }} />;
      if (mimeType.includes('document') || mimeType.includes('word')) return <Description color="info" sx={{ fontSize: 40 }} />;
    }

    switch (documentType) {
      case 'report':
      case 'analysis_result':
        return <Assessment color="primary" sx={{ fontSize: 40 }} />;
      case 'legal_document':
        return <Description color="info" sx={{ fontSize: 40 }} />;
      case 'financial_statement':
        return <TableChart color="success" sx={{ fontSize: 40 }} />;
      default:
        return <InsertDriveFile sx={{ fontSize: 40 }} />;
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
    return <Chip label={config.label} color={config.color} />;
  };

  const getAccessLevelChip = (accessLevel: AccessLevel) => {
    const accessConfig = {
      public: { color: 'success' as const, label: 'Public', icon: <Visibility /> },
      internal: { color: 'info' as const, label: 'Internal', icon: <Person /> },
      confidential: { color: 'warning' as const, label: 'Confidential', icon: <Security /> },
      restricted: { color: 'error' as const, label: 'Restricted', icon: <Security /> },
    };

    const config = accessConfig[accessLevel];
    return <Chip icon={config.icon} label={config.label} color={config.color} />;
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

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleDownload = async () => {
    if (!doc) return;
    
    try {
      const response = await downloadDocument(doc.document_id);
      // Handle download response
      const link = document.createElement('a');
      link.href = URL.createObjectURL(response.data as Blob);
      link.download = doc.original_filename;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleSave = async () => {
    if (!document) return;

    try {
      const updatedDoc = await updateDocument({
        documentId: doc.document_id,
        update: editFormData,
      }).unwrap();

      setEditMode(false);
      onUpdated?.(updatedDoc.data);
      refetch();
    } catch (error) {
      console.error('Update failed:', error);
    }
  };

  const handleDelete = async () => {
    if (!document || !window.confirm('Are you sure you want to delete this document?')) return;

    try {
      await deleteDocument(doc.document_id);
      onDeleted?.();
      onClose();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const handleEditCancel = () => {
    setEditMode(false);
    if (document) {
      setEditFormData({
        title: doc.title || '',
        description: doc.description || '',
        document_type: doc.document_type,
        access_level: doc.access_level,
        tags: doc.tags,
      });
    }
  };

  if (!open) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
            {isLoading ? (
              <Skeleton variant="circular" width={40} height={40} />
            ) : document ? (
              getDocumentIcon(doc.document_type, doc.mime_type)
            ) : null}
            
            <Box sx={{ flex: 1 }}>
              {isLoading ? (
                <Skeleton variant="text" width="60%" />
              ) : (
                <Typography variant="h6" component="div" noWrap>
                  {doc?.title || 'Document'}
                </Typography>
              )}
              
              {doc && (
                <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                  {getStatusChip(doc.status)}
                  {getAccessLevelChip(doc.access_level)}
                </Stack>
              )}
            </Box>
          </Box>

          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {error && (
          <Alert severity="error" sx={{ m: 2 }}>
            Error loading document: {error.toString()}
          </Alert>
        )}

        {isLoading ? (
          <Box sx={{ p: 3 }}>
            <Skeleton variant="rectangular" width="100%" height={200} />
          </Box>
        ) : document ? (
          <>
            <Tabs value={currentTab} onChange={handleTabChange}>
              <Tab label="Details" icon={<Info />} />
              <Tab label="History" icon={<History />} />
              <Tab label="Security" icon={<Security />} />
            </Tabs>

            <TabPanel value={currentTab} index={0}>
              <Grid container spacing={3}>
                {/* Basic Information */}
                <Grid size={{ xs: 12, md: 8 }}>
                  <Card sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Basic Information
                      </Typography>
                      
                      {editMode ? (
                        <Stack spacing={2}>
                          <TextField
                            label="Title"
                            fullWidth
                            value={editFormData.title || ''}
                            onChange={(e) => setEditFormData(prev => ({ ...prev, title: e.target.value }))}
                          />
                          
                          <TextField
                            label="Description"
                            fullWidth
                            multiline
                            rows={3}
                            value={editFormData.description || ''}
                            onChange={(e) => setEditFormData(prev => ({ ...prev, description: e.target.value }))}
                          />
                          
                          <FormControl fullWidth>
                            <InputLabel>Document Type</InputLabel>
                            <Select
                              value={editFormData.document_type || ''}
                              label="Document Type"
                              onChange={(e) => setEditFormData(prev => ({ ...prev, document_type: e.target.value as DocumentType }))}
                            >
                              <MenuItem value="report">Report</MenuItem>
                              <MenuItem value="legal_document">Legal Document</MenuItem>
                              <MenuItem value="financial_statement">Financial Statement</MenuItem>
                              <MenuItem value="analysis_result">Analysis Result</MenuItem>
                              <MenuItem value="user_upload">User Upload</MenuItem>
                            </Select>
                          </FormControl>
                          
                          <FormControl fullWidth>
                            <InputLabel>Access Level</InputLabel>
                            <Select
                              value={editFormData.access_level || ''}
                              label="Access Level"
                              onChange={(e) => setEditFormData(prev => ({ ...prev, access_level: e.target.value as AccessLevel }))}
                            >
                              <MenuItem value="public">Public</MenuItem>
                              <MenuItem value="internal">Internal</MenuItem>
                              <MenuItem value="confidential">Confidential</MenuItem>
                              <MenuItem value="restricted">Restricted</MenuItem>
                            </Select>
                          </FormControl>
                        </Stack>
                      ) : (
                        <Stack spacing={2}>
                          <Box>
                            <Typography variant="body2" color="text.secondary">Title</Typography>
                            <Typography variant="body1">{doc.title || 'No title'}</Typography>
                          </Box>
                          
                          <Box>
                            <Typography variant="body2" color="text.secondary">Description</Typography>
                            <Typography variant="body1">{doc.description || 'No description'}</Typography>
                          </Box>
                          
                          <Box>
                            <Typography variant="body2" color="text.secondary">Document Type</Typography>
                            <Typography variant="body1">{doc.document_type.replace('_', ' ')}</Typography>
                          </Box>
                        </Stack>
                      )}
                    </CardContent>
                  </Card>

                  {/* Tags */}
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Tags
                      </Typography>
                      <Stack direction="row" spacing={1} flexWrap="wrap">
                        {doc.tags.length > 0 ? (
                          doc.tags.map((tag, index) => (
                            <Chip key={index} label={tag} variant="outlined" />
                          ))
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            No tags
                          </Typography>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>

                {/* Metadata */}
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        File Information
                      </Typography>
                      
                      <List dense>
                        <ListItem>
                          <ListItemIcon><InsertDriveFile /></ListItemIcon>
                          <ListItemText 
                            primary="Filename" 
                            secondary={doc.original_filename}
                          />
                        </ListItem>
                        
                        <ListItem>
                          <ListItemIcon><Storage /></ListItemIcon>
                          <ListItemText 
                            primary="File Size" 
                            secondary={formatFileSize(doc.file_size)}
                          />
                        </ListItem>
                        
                        <ListItem>
                          <ListItemIcon><Fingerprint /></ListItemIcon>
                          <ListItemText 
                            primary="Version" 
                            secondary={`v${doc.version}${doc.is_latest_version ? ' (Latest)' : ''}`}
                          />
                        </ListItem>
                        
                        <ListItem>
                          <ListItemIcon><Schedule /></ListItemIcon>
                          <ListItemText 
                            primary="Uploaded" 
                            secondary={format(new Date(doc.uploaded_at), 'PPp')}
                          />
                        </ListItem>
                        
                        <ListItem>
                          <ListItemIcon><Schedule /></ListItemIcon>
                          <ListItemText 
                            primary="Modified" 
                            secondary={format(new Date(doc.updated_at), 'PPp')}
                          />
                        </ListItem>
                        
                        {doc.accessed_at && (
                          <ListItem>
                            <ListItemIcon><Visibility /></ListItemIcon>
                            <ListItemText 
                              primary="Last Accessed" 
                              secondary={format(new Date(doc.accessed_at), 'PPp')}
                            />
                          </ListItem>
                        )}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={currentTab} index={1}>
              <Typography variant="h6" gutterBottom>
                Version History
              </Typography>
              <Alert severity="info">
                Version history feature will be implemented in the next phase.
              </Alert>
            </TabPanel>

            <TabPanel value={currentTab} index={2}>
              <Typography variant="h6" gutterBottom>
                Security & Access
              </Typography>
              <Alert severity="info">
                Security and access management features will be implemented in the next phase.
              </Alert>
            </TabPanel>
          </>
        ) : null}
      </DialogContent>

      <DialogActions>
        {editMode ? (
          <>
            <Button onClick={handleEditCancel}>Cancel</Button>
            <Button 
              variant="contained" 
              onClick={handleSave}
              disabled={isUpdating}
            >
              {isUpdating ? 'Saving...' : 'Save'}
            </Button>
          </>
        ) : (
          <>
            <Button 
              startIcon={<Download />}
              onClick={handleDownload}
              disabled={isLoading}
            >
              Download
            </Button>
            
            <Button 
              startIcon={<Share />}
              disabled
            >
              Share
            </Button>
            
            {!readonly && (
              <>
                <Button 
                  startIcon={<Edit />}
                  onClick={() => setEditMode(true)}
                  disabled={isLoading}
                >
                  Edit
                </Button>
                
                <Button 
                  startIcon={<Delete />}
                  color="error"
                  onClick={handleDelete}
                  disabled={isLoading || isDeleting}
                >
                  {isDeleting ? 'Deleting...' : 'Delete'}
                </Button>
              </>
            )}
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default DocumentViewer;