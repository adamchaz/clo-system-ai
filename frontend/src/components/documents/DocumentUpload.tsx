/**
 * DocumentUpload Component - Standalone Document Upload Widget
 * 
 * A reusable upload component that can be embedded anywhere:
 * - Drag & drop file upload
 * - Progress tracking with real-time updates
 * - File validation and preview
 * - Batch upload support
 * - Integration with WebSocket for upload progress
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
  Collapse,
} from '@mui/material';
import {
  CloudUpload,
  InsertDriveFile,
  CheckCircle,
  Error,
  Delete,
  Close,
  ExpandMore,
  ExpandLess,
  Upload,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

// Import API hooks
import { useUploadDocumentMutation } from '../../store/api/cloApi';

// Import types
import {
  DocumentType,
  AccessLevel,
  DocumentUploadRequest,
} from '../../store/api/newApiTypes';

interface FileWithMetadata extends File {
  id: string;
  uploadProgress?: number;
  uploadStatus?: 'pending' | 'uploading' | 'completed' | 'error';
  uploadError?: string;
  metadata?: DocumentUploadRequest;
}

interface DocumentUploadProps {
  portfolioId?: string;
  onUploadComplete?: (documents: any[]) => void;
  onUploadError?: (error: string) => void;
  maxFileSize?: number; // in MB
  maxFiles?: number;
  allowedTypes?: string[];
  compact?: boolean;
  showProgress?: boolean;
  autoUpload?: boolean;
  defaultDocumentType?: DocumentType;
  defaultAccessLevel?: AccessLevel;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  portfolioId,
  onUploadComplete,
  onUploadError,
  maxFileSize = 50,
  maxFiles = 10,
  allowedTypes = [
    'application/pdf',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/csv',
    'text/plain',
  ],
  compact = false,
  showProgress = true,
  autoUpload = false,
  defaultDocumentType = 'user_upload',
  defaultAccessLevel = 'internal',
}) => {
  const [files, setFiles] = useState<FileWithMetadata[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [expandedFiles, setExpandedFiles] = useState(false);
  const [metadataDialogOpen, setMetadataDialogOpen] = useState(false);
  const [currentFileForMetadata, setCurrentFileForMetadata] = useState<FileWithMetadata | null>(null);

  const [uploadDocument] = useUploadDocumentMutation();

  const generateId = () => Math.random().toString(36).substr(2, 9);

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
        return defaultDocumentType;
    }
  };

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxFileSize * 1024 * 1024) {
      return `File size exceeds ${maxFileSize}MB limit`;
    }

    // Check file type
    if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
      return `File type ${file.type} is not allowed`;
    }

    return null;
  };

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        rejectedFiles.forEach((rejectedFile) => {
          console.error('Rejected file:', rejectedFile.file.name, rejectedFile.errors);
          onUploadError?.(`File ${rejectedFile.file.name} was rejected`);
        });
      }

      // Process accepted files
      const newFiles: FileWithMetadata[] = acceptedFiles.map((file) => {
        const validationError = validateFile(file);
        
        const fileWithMetadata: FileWithMetadata = Object.assign(file, {
          id: generateId(),
          uploadProgress: 0,
          uploadStatus: validationError ? 'error' as const : 'pending' as const,
          uploadError: validationError || undefined,
          metadata: {
            document_type: getDocumentTypeFromFile(file),
            access_level: defaultAccessLevel,
            portfolio_id: portfolioId,
            tags: [file.type],
          },
        });

        return fileWithMetadata;
      });

      // Check total file count
      const totalFiles = files.length + newFiles.length;
      if (totalFiles > maxFiles) {
        onUploadError?.(`Cannot upload more than ${maxFiles} files at once`);
        return;
      }

      setFiles(prev => [...prev, ...newFiles]);

      // Auto-upload if enabled
      if (autoUpload) {
        setTimeout(() => handleUploadAll(), 100);
      }
    },
    [files, maxFiles, maxFileSize, allowedTypes, autoUpload, portfolioId, defaultAccessLevel, defaultDocumentType, onUploadError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: allowedTypes.reduce((acc, type) => {
      acc[type] = [];
      return acc;
    }, {} as Record<string, string[]>),
    multiple: true,
    maxFiles,
    maxSize: maxFileSize * 1024 * 1024,
  });

  const handleRemoveFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const handleEditMetadata = (file: FileWithMetadata) => {
    setCurrentFileForMetadata(file);
    setMetadataDialogOpen(true);
  };

  const handleSaveMetadata = (metadata: DocumentUploadRequest) => {
    if (!currentFileForMetadata) return;

    setFiles(prev => prev.map(f => 
      f.id === currentFileForMetadata.id
        ? { ...f, metadata }
        : f
    ));

    setMetadataDialogOpen(false);
    setCurrentFileForMetadata(null);
  };

  const uploadFile = async (file: FileWithMetadata): Promise<boolean> => {
    if (!file.metadata || file.uploadStatus === 'error') return false;

    try {
      // Update file status
      setFiles(prev => prev.map(f => 
        f.id === file.id 
          ? { ...f, uploadStatus: 'uploading' as const, uploadProgress: 0 }
          : f
      ));

      // Simulate progress (real implementation would track actual upload progress)
      const progressInterval = setInterval(() => {
        setFiles(prev => prev.map(f => 
          f.id === file.id && f.uploadStatus === 'uploading'
            ? { ...f, uploadProgress: Math.min((f.uploadProgress || 0) + 10, 90) }
            : f
        ));
      }, 200);

      // Perform upload
      await uploadDocument({ file, metadata: file.metadata }).unwrap();

      // Clear progress interval
      clearInterval(progressInterval);

      // Mark as completed
      setFiles(prev => prev.map(f => 
        f.id === file.id 
          ? { ...f, uploadStatus: 'completed' as const, uploadProgress: 100 }
          : f
      ));

      return true;

    } catch (error) {
      console.error('Upload failed:', error);
      
      setFiles(prev => prev.map(f => 
        f.id === file.id 
          ? { 
              ...f, 
              uploadStatus: 'error' as const, 
              uploadError: error instanceof Error ? error.message : 'Upload failed'
            }
          : f
      ));

      return false;
    }
  };

  const handleUploadAll = async () => {
    const pendingFiles = files.filter(f => f.uploadStatus === 'pending');
    if (pendingFiles.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);

    const results = [];
    for (let i = 0; i < pendingFiles.length; i++) {
      const file = pendingFiles[i];
      const success = await uploadFile(file);
      results.push({ file, success });
      
      // Update overall progress
      setUploadProgress(((i + 1) / pendingFiles.length) * 100);
    }

    setIsUploading(false);

    // Handle completion
    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    if (successful.length > 0) {
      onUploadComplete?.(successful.map(r => r.file));
    }

    if (failed.length > 0) {
      onUploadError?.(`${failed.length} file(s) failed to upload`);
    }

    // Remove completed files after a delay
    setTimeout(() => {
      setFiles(prev => prev.filter(f => f.uploadStatus !== 'completed'));
    }, 3000);
  };

  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  return (
    <Box>
      {/* Upload Area */}
      <Card sx={{ mb: files.length > 0 ? 2 : 0 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderRadius: 2,
              p: compact ? 2 : 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'transparent',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'action.hover',
              },
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload 
              sx={{ 
                fontSize: compact ? 32 : 48, 
                color: 'text.secondary', 
                mb: compact ? 1 : 2 
              }} 
            />
            <Typography variant={compact ? 'body2' : 'h6'} gutterBottom>
              {isDragActive 
                ? 'Drop files here' 
                : 'Drag & drop files here, or click to select'
              }
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Max {maxFiles} files, {maxFileSize}MB each
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardContent sx={{ pb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6">
                Files ({files.length})
              </Typography>
              <Box>
                <Button
                  size="small"
                  onClick={() => setExpandedFiles(!expandedFiles)}
                  endIcon={expandedFiles ? <ExpandLess /> : <ExpandMore />}
                >
                  {expandedFiles ? 'Collapse' : 'Expand'}
                </Button>
                {!autoUpload && files.some(f => f.uploadStatus === 'pending') && (
                  <Button
                    variant="contained"
                    size="small"
                    startIcon={<Upload />}
                    onClick={handleUploadAll}
                    disabled={isUploading}
                    sx={{ ml: 1 }}
                  >
                    Upload All
                  </Button>
                )}
              </Box>
            </Box>

            {/* Overall Progress */}
            {showProgress && isUploading && (
              <LinearProgress 
                variant="determinate" 
                value={uploadProgress} 
                sx={{ mb: 2 }}
              />
            )}

            <Collapse in={expandedFiles}>
              <List dense>
                {files.map((file) => (
                  <ListItem key={file.id}>
                    <ListItemIcon>
                      <InsertDriveFile />
                    </ListItemIcon>

                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" noWrap>
                            {file.name}
                          </Typography>
                          <Chip 
                            label={file.uploadStatus}
                            size="small"
                            color={
                              file.uploadStatus === 'completed' ? 'success' :
                              file.uploadStatus === 'error' ? 'error' :
                              file.uploadStatus === 'uploading' ? 'warning' : 'default'
                            }
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            {formatFileSize(file.size)} • {file.metadata?.document_type.replace('_', ' ')} • {file.metadata?.access_level}
                          </Typography>
                          
                          {file.uploadStatus === 'uploading' && showProgress && (
                            <LinearProgress 
                              variant="determinate" 
                              value={file.uploadProgress || 0} 
                              sx={{ mt: 0.5, height: 4 }}
                            />
                          )}
                          
                          {file.uploadError && (
                            <Typography variant="caption" color="error">
                              {file.uploadError}
                            </Typography>
                          )}
                        </Box>
                      }
                    />

                    <ListItemSecondaryAction>
                      <Stack direction="row" spacing={0.5}>
                        {file.uploadStatus === 'pending' && (
                          <IconButton 
                            size="small"
                            onClick={() => handleEditMetadata(file)}
                          >
                            <ExpandMore />
                          </IconButton>
                        )}
                        
                        <IconButton 
                          size="small"
                          onClick={() => handleRemoveFile(file.id)}
                          disabled={file.uploadStatus === 'uploading'}
                        >
                          <Delete />
                        </IconButton>
                      </Stack>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </CardContent>
        </Card>
      )}

      {/* Metadata Edit Dialog */}
      <Dialog open={metadataDialogOpen} onClose={() => setMetadataDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Document Metadata</DialogTitle>
        <DialogContent>
          {currentFileForMetadata && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Title"
                fullWidth
                defaultValue={currentFileForMetadata.name}
              />
              
              <TextField
                label="Description"
                fullWidth
                multiline
                rows={2}
              />
              
              <FormControl fullWidth>
                <InputLabel>Document Type</InputLabel>
                <Select
                  value={currentFileForMetadata.metadata?.document_type || defaultDocumentType}
                  label="Document Type"
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
                  value={currentFileForMetadata.metadata?.access_level || defaultAccessLevel}
                  label="Access Level"
                >
                  <MenuItem value="public">Public</MenuItem>
                  <MenuItem value="internal">Internal</MenuItem>
                  <MenuItem value="confidential">Confidential</MenuItem>
                  <MenuItem value="restricted">Restricted</MenuItem>
                </Select>
              </FormControl>
              
              <TextField
                label="Tags (comma separated)"
                fullWidth
                placeholder="financial, quarterly, analysis"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMetadataDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained"
            onClick={() => {
              if (currentFileForMetadata?.metadata) {
                handleSaveMetadata(currentFileForMetadata.metadata);
              }
            }}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DocumentUpload;