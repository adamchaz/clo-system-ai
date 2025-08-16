/**
 * ReportViewer Component - Report Display and Management Interface
 * 
 * Comprehensive report viewing capabilities including:
 * - Detailed report information and metadata display
 * - Report content preview and embedded viewing
 * - Download options in multiple formats
 * - Sharing and collaboration features
 * - Report scheduling and delivery management
 * - Version history and audit trail
 * 
 * Integrates with Report Management APIs for complete report viewing experience
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  IconButton,
  Tooltip,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  Divider,
  TextField,
  Switch,
  FormControlLabel,
  LinearProgress,
  Skeleton,
} from '@mui/material';
import {
  Download,
  Share,
  Edit,
  Delete,
  Visibility,
  Schedule,
  Assessment,
  PictureAsPdf,
  TableChart,
  Description,
  Email,
  Link,
  History,
  Person,
  CalendarToday,
  Storage,
  CheckCircle,
  Error,
  Warning,
  Info,
  Close,
  Refresh,
  Print,
  Fullscreen,
  ZoomIn,
  ZoomOut,
  Save,
  Cancel,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';

// Import API hooks
import {
  useGetReportByIdQuery,
  useDownloadReportMutation,
  useDeleteReportMutation,
  useCancelReportMutation,
} from '../../store/api/cloApi';

// Import types
import {
  Report,
  ReportStatus,
  ReportFormat,
} from '../../store/api/newApiTypes';

interface ReportViewerProps {
  reportId: string;
  open: boolean;
  onClose: () => void;
  onDeleted?: () => void;
  onUpdated?: (report: Report) => void;
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

const ReportStatusConfig = {
  pending: { label: 'Pending', color: 'warning' as const, icon: <Schedule /> },
  generating: { label: 'Generating', color: 'info' as const, icon: <Assessment /> },
  completed: { label: 'Completed', color: 'success' as const, icon: <CheckCircle /> },
  failed: { label: 'Failed', color: 'error' as const, icon: <Error /> },
  cancelled: { label: 'Cancelled', color: 'default' as const, icon: <Cancel /> },
  scheduled: { label: 'Scheduled', color: 'primary' as const, icon: <Schedule /> },
};

const ReportFormatIcons = {
  pdf: <PictureAsPdf />,
  excel: <TableChart />,
  csv: <Description />,
  html: <Assessment />,
};

const ReportViewer: React.FC<ReportViewerProps> = ({
  reportId,
  open,
  onClose,
  onDeleted,
  onUpdated,
  readonly = false,
}) => {
  const [currentTab, setCurrentTab] = useState(0);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editFormData, setEditFormData] = useState({
    name: '',
    description: '',
  });
  const [shareEmail, setShareEmail] = useState('');
  const [shareMessage, setShareMessage] = useState('');

  // API hooks
  const {
    data: reportResponse,
    isLoading,
    error,
    refetch,
  } = useGetReportByIdQuery(reportId, { skip: !open });

  const [downloadReport] = useDownloadReportMutation();
  const [deleteReport, { isLoading: isDeleting }] = useDeleteReportMutation();
  const [cancelReport] = useCancelReportMutation();

  const report = reportResponse?.data;

  // Initialize edit form data when report loads
  useEffect(() => {
    if (report) {
      setEditFormData({
        name: report.report_name || '',
        description: report.report_type || '',
      });
    }
  }, [report]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleDownload = async () => {
    if (!report) return;
    
    try {
      const response = await downloadReport(report.report_id);
      
      // Create download link
      const blob = new Blob([response.data as any], { 
        type: report.output_format === 'pdf' ? 'application/pdf' : 'application/octet-stream' 
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${report.report_name}.${report.output_format}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleDelete = async () => {
    if (!report) return;

    try {
      await deleteReport(report.report_id);
      onDeleted?.();
      onClose();
    } catch (error) {
      console.error('Delete failed:', error);
    } finally {
      setDeleteConfirmOpen(false);
    }
  };

  const handleCancel = async () => {
    if (!report) return;

    try {
      await cancelReport(report.report_id);
      refetch();
    } catch (error) {
      console.error('Cancel failed:', error);
    }
  };

  const handleShare = () => {
    // Implement sharing logic
    console.log('Sharing report:', { email: shareEmail, message: shareMessage });
    setShareDialogOpen(false);
    setShareEmail('');
    setShareMessage('');
  };

  const getReportStatusChip = (status: ReportStatus) => {
    const config = ReportStatusConfig[status];
    return (
      <Chip
        icon={config.icon}
        label={config.label}
        color={config.color}
        size="small"
      />
    );
  };

  const canDownload = (report: Report) => {
    return report.status === 'completed';
  };

  const canCancel = (report: Report) => {
    return report.status === 'queued' || report.status === 'generating';
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

  if (!open) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
            {isLoading ? (
              <Skeleton variant="circular" width={40} height={40} />
            ) : report ? (
              ReportFormatIcons[report.output_format]
            ) : null}
            
            <Box sx={{ flex: 1 }}>
              {isLoading ? (
                <Skeleton variant="text" width="60%" />
              ) : (
                <Typography variant="h6" component="div" noWrap>
                  {report?.report_name || 'Report'}
                </Typography>
              )}
              
              {report && (
                <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                  {getReportStatusChip(report.status)}
                  <Chip
                    label={report.output_format.toUpperCase()}
                    size="small"
                    variant="outlined"
                  />
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
            Error loading report: {error.toString()}
          </Alert>
        )}

        {isLoading ? (
          <Box sx={{ p: 3 }}>
            <Skeleton variant="rectangular" width="100%" height={300} />
          </Box>
        ) : report ? (
          <>
            <Tabs value={currentTab} onChange={handleTabChange}>
              <Tab label="Overview" icon={<Info />} />
              <Tab label="Content" icon={<Visibility />} />
              <Tab label="Schedule" icon={<Schedule />} />
              <Tab label="History" icon={<History />} />
            </Tabs>

            {/* Overview Tab */}
            <TabPanel value={currentTab} index={0}>
              <Grid container spacing={3}>
                {/* Basic Information */}
                <Grid size={{ xs: 12, md: 8 }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Report Information
                      </Typography>
                      
                      <Stack spacing={2}>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Name
                          </Typography>
                          <Typography variant="body1">{report.report_name}</Typography>
                        </Box>
                        
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Description
                          </Typography>
                          <Typography variant="body1">
                            {report.report_type || 'No description'}
                          </Typography>
                        </Box>
                        
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Template
                          </Typography>
                          <Typography variant="body1">
                            {report.template_id ? 'Template Report' : 'Custom Report'}
                          </Typography>
                        </Box>
                        
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Status
                          </Typography>
                          {getReportStatusChip(report.status)}
                          {report.status === 'generating' && (
                            <Box sx={{ mt: 1, width: '100%' }}>
                              <LinearProgress 
                                variant="indeterminate" 
                                sx={{ height: 6, borderRadius: 3 }}
                              />
                              <Typography variant="caption" color="text.secondary">
                                Generating report...
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>

                  {/* Parameters */}
                  {report.parameters && Object.keys(report.parameters).length > 0 && (
                    <Card sx={{ mt: 2 }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Report Parameters
                        </Typography>
                        
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Parameter</TableCell>
                                <TableCell>Value</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {Object.entries(report.parameters).map(([key, value]) => (
                                <TableRow key={key}>
                                  <TableCell sx={{ fontWeight: 'medium' }}>
                                    {key}
                                  </TableCell>
                                  <TableCell>
                                    {String(value)}
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </CardContent>
                    </Card>
                  )}
                </Grid>

                {/* Metadata */}
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        File Details
                      </Typography>
                      
                      <List dense>
                        <ListItem>
                          <ListItemIcon>
                            {ReportFormatIcons[report.output_format]}
                          </ListItemIcon>
                          <ListItemText 
                            primary="Format" 
                            secondary={report.output_format.toUpperCase()}
                          />
                        </ListItem>
                        
                        <ListItem>
                          <ListItemIcon><Storage /></ListItemIcon>
                          <ListItemText 
                            primary="File Size" 
                            secondary={formatFileSize(report.file_size)}
                          />
                        </ListItem>
                        
                        <ListItem>
                          <ListItemIcon><CalendarToday /></ListItemIcon>
                          <ListItemText 
                            primary="Created" 
                            secondary={format(new Date(report.created_at), 'PPp')}
                          />
                        </ListItem>
                        
                        <ListItem>
                          <ListItemIcon><CalendarToday /></ListItemIcon>
                          <ListItemText 
                            primary="Updated" 
                            secondary={format(new Date(report.updated_at), 'PPp')}
                          />
                        </ListItem>
                        
                        {report.completed_at && (
                          <ListItem>
                            <ListItemIcon><CheckCircle /></ListItemIcon>
                            <ListItemText 
                              primary="Completed" 
                              secondary={format(new Date(report.completed_at), 'PPp')}
                            />
                          </ListItem>
                        )}
                        
                        {report.requested_by && (
                          <ListItem>
                            <ListItemIcon><Person /></ListItemIcon>
                            <ListItemText 
                              primary="Created By" 
                              secondary={report.requested_by}
                            />
                          </ListItem>
                        )}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </TabPanel>

            {/* Content Tab */}
            <TabPanel value={currentTab} index={1}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Report Preview
                  </Typography>
                  
                  {report.status === 'completed' ? (
                    <Alert severity="info">
                      Report content preview will be implemented in the next phase.
                      For now, please download the report to view its contents.
                    </Alert>
                  ) : (
                    <Alert severity="warning">
                      Report is not ready for preview. Status: {report.status}
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </TabPanel>

            {/* Schedule Tab */}
            <TabPanel value={currentTab} index={2}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Delivery Schedule
                  </Typography>
                  
                  <Alert severity="info">
                    Scheduled delivery configuration will be implemented in the next phase.
                  </Alert>
                </CardContent>
              </Card>
            </TabPanel>

            {/* History Tab */}
            <TabPanel value={currentTab} index={3}>
              <Alert severity="info">
                Report history and audit trail will be implemented in the next phase.
              </Alert>
            </TabPanel>
          </>
        ) : null}
      </DialogContent>

      <DialogActions>
        {report && canCancel(report) && (
          <Button
            startIcon={<Cancel />}
            onClick={handleCancel}
            color="warning"
          >
            Cancel Generation
          </Button>
        )}
        
        {report && canDownload(report) && (
          <>
            <Button
              startIcon={<Download />}
              onClick={handleDownload}
            >
              Download
            </Button>
            
            <Button
              startIcon={<Share />}
              onClick={() => setShareDialogOpen(true)}
            >
              Share
            </Button>
          </>
        )}
        
        {!readonly && report && (
          <Button
            startIcon={<Delete />}
            color="error"
            onClick={() => setDeleteConfirmOpen(true)}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        )}
      </DialogActions>

      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onClose={() => setShareDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Share Report</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={shareEmail}
              onChange={(e) => setShareEmail(e.target.value)}
              placeholder="Enter recipient's email"
            />
            
            <TextField
              fullWidth
              label="Message (Optional)"
              multiline
              rows={3}
              value={shareMessage}
              onChange={(e) => setShareMessage(e.target.value)}
              placeholder="Add a personal message..."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleShare}
            disabled={!shareEmail}
          >
            Send Share Link
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this report? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
};

export default ReportViewer;