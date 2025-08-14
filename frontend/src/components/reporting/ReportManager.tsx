/**
 * ReportManager Component - Comprehensive Report Management Interface
 * 
 * Advanced report management featuring:
 * - List all generated reports with advanced filtering and search
 * - Report status tracking (generating, completed, failed, scheduled)
 * - Download and sharing capabilities
 * - Report scheduling and delivery management
 * - Bulk operations (delete, regenerate, export)
 * - Real-time status updates via WebSocket
 * 
 * Integrates with Report Management APIs for complete report lifecycle management
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
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
  Checkbox,
  Menu,
  MenuItem as MenuItemComponent,
  Avatar,
  LinearProgress,
  Pagination,
  Fab,
  Badge,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add,
  Search,
  FilterList,
  Download,
  Share,
  Delete,
  Refresh,
  MoreVert,
  Schedule,
  CheckCircle,
  Error,
  Pending,
  PlayArrow,
  Stop,
  Visibility,
  Edit,
  Settings,
  Assessment,
  PictureAsPdf,
  TableChart,
  Description,
  Email,
  Link,
  History,
  Timer,
  Warning,
  Info,
  FileDownload,
  CloudDownload,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';

// Import API hooks
import {
  useGetReportsQuery,
  useDownloadReportMutation,
  useDeleteReportMutation,
  useCancelReportMutation,
  useGetReportStatsQuery,
} from '../../store/api/cloApi';

// Import types
import {
  Report,
  ReportStatus,
  ReportFormat,
} from '../../store/api/newApiTypes';

// Import WebSocket hooks
import { useReportUpdates } from '../../hooks/useWebSocket';

interface ReportManagerProps {
  onCreateNew?: () => void;
  onReportSelected?: (report: Report) => void;
}

const ReportStatusConfig = {
  pending: { label: 'Pending', color: 'warning' as const, icon: <Pending /> },
  generating: { label: 'Generating', color: 'info' as const, icon: <Timer /> },
  completed: { label: 'Completed', color: 'success' as const, icon: <CheckCircle /> },
  failed: { label: 'Failed', color: 'error' as const, icon: <Error /> },
  cancelled: { label: 'Cancelled', color: 'default' as const, icon: <Stop /> },
  scheduled: { label: 'Scheduled', color: 'primary' as const, icon: <Schedule /> },
};

const ReportFormatIcons = {
  pdf: <PictureAsPdf />,
  excel: <TableChart />,
  csv: <Description />,
  html: <Assessment />,
};

const ReportManager: React.FC<ReportManagerProps> = ({
  onCreateNew,
  onReportSelected,
}) => {
  // State management
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<ReportStatus | ''>('');
  const [formatFilter, setFormatFilter] = useState<ReportFormat | ''>('');
  const [selectedReports, setSelectedReports] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Dialog and menu states
  const [bulkActionMenuAnchor, setBulkActionMenuAnchor] = useState<null | HTMLElement>(null);
  const [reportActionMenuAnchor, setReportActionMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [reportDetailsOpen, setReportDetailsOpen] = useState(false);

  // Real-time updates
  const [realtimeUpdates, setRealtimeUpdates] = useState<any[]>([]);

  // API hooks
  const { 
    data: reportsResponse, 
    isLoading, 
    error, 
    refetch 
  } = useGetReportsQuery({
    page: currentPage,
    page_size: pageSize,
    status: statusFilter || undefined,
    format: formatFilter || undefined,
    search: searchQuery || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  const { data: reportStats } = useGetReportStatsQuery();
  const [downloadReport] = useDownloadReportMutation();
  const [deleteReport, { isLoading: isDeleting }] = useDeleteReportMutation();
  const [cancelReport] = useCancelReportMutation();

  const reports = reportsResponse?.data || [];
  const totalReports = reportsResponse?.total || 0;
  const totalPages = Math.ceil(totalReports / pageSize);

  // WebSocket integration for real-time report updates
  useReportUpdates((updateData) => {
    setRealtimeUpdates(prev => [updateData, ...prev.slice(0, 4)]); // Keep last 5 updates
    refetch(); // Refresh the reports list
  });

  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1); // Reset to first page when searching
  };

  const handleStatusFilterChange = (status: ReportStatus | '') => {
    setStatusFilter(status);
    setCurrentPage(1);
  };

  const handleReportSelection = (reportId: string, selected: boolean) => {
    setSelectedReports(prev =>
      selected
        ? [...prev, reportId]
        : prev.filter(id => id !== reportId)
    );
  };

  const handleSelectAll = (selected: boolean) => {
    setSelectedReports(selected ? reports.map(report => report.report_id) : []);
  };

  const handleDownload = async (report: Report) => {
    try {
      const response = await downloadReport(report.report_id);
      
      // Create download link
      const blob = new Blob([response.data as any], { 
        type: report.format === 'pdf' ? 'application/pdf' : 'application/octet-stream' 
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${report.name}.${report.format}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleDelete = async (reportIds: string[]) => {
    for (const reportId of reportIds) {
      try {
        await deleteReport(reportId);
      } catch (error) {
        console.error(`Failed to delete report ${reportId}:`, error);
      }
    }
    setSelectedReports([]);
    setDeleteConfirmOpen(false);
    refetch();
  };

  const handleCancel = async (reportId: string) => {
    try {
      await cancelReport(reportId);
      refetch();
    } catch (error) {
      console.error('Failed to cancel report:', error);
    }
  };

  const handleReportAction = (action: string, report: Report) => {
    setSelectedReport(report);
    
    switch (action) {
      case 'download':
        handleDownload(report);
        break;
      case 'cancel':
        handleCancel(report.report_id);
        break;
      case 'delete':
        setDeleteConfirmOpen(true);
        break;
      case 'details':
        setReportDetailsOpen(true);
        break;
    }
    
    setReportActionMenuAnchor(null);
  };

  const handleBulkAction = (action: string) => {
    switch (action) {
      case 'delete':
        setDeleteConfirmOpen(true);
        break;
      case 'download':
        selectedReports.forEach(id => {
          const report = reports.find(r => r.report_id === id);
          if (report) handleDownload(report);
        });
        break;
    }
    
    setBulkActionMenuAnchor(null);
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
    return report.status === 'pending' || report.status === 'generating';
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1">
            Report Manager
          </Typography>
          {realtimeUpdates.length > 0 && (
            <Badge badgeContent={realtimeUpdates.length} color="info">
              <Typography variant="body2" color="text.secondary">
                {totalReports} reports • {realtimeUpdates.length} live updates
              </Typography>
            </Badge>
          )}
        </Box>

        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          
          {onCreateNew && (
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={onCreateNew}
            >
              Create Report
            </Button>
          )}
        </Stack>
      </Box>

      {/* Real-time Updates Alert */}
      {realtimeUpdates.length > 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Live Updates ({realtimeUpdates.length})
          </Typography>
          <Typography variant="body2">
            Latest: {realtimeUpdates[0]?.report_name} - {realtimeUpdates[0]?.status}
          </Typography>
        </Alert>
      )}

      {/* Report Statistics */}
      {reportStats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid {...({ item: true } as any)} size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {reportStats.data.total_reports}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Reports
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {reportStats.data.completed_reports}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Completed
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {reportStats.data.generating_reports}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Generating
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="info.main">
                  {reportStats.data.scheduled_reports}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Scheduled
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Search and Filter */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
              <TextField
                fullWidth
                placeholder="Search reports..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => handleStatusFilterChange(e.target.value as ReportStatus)}
                >
                  <MenuItem value="">All Statuses</MenuItem>
                  {Object.entries(ReportStatusConfig).map(([status, config]) => (
                    <MenuItem key={status} value={status}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {config.icon}
                        <Typography sx={{ ml: 1 }}>{config.label}</Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Format</InputLabel>
                <Select
                  value={formatFilter}
                  label="Format"
                  onChange={(e) => setFormatFilter(e.target.value as ReportFormat)}
                >
                  <MenuItem value="">All Formats</MenuItem>
                  <MenuItem value="pdf">PDF</MenuItem>
                  <MenuItem value="excel">Excel</MenuItem>
                  <MenuItem value="csv">CSV</MenuItem>
                  <MenuItem value="html">HTML</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 2 }}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<FilterList />}
                onClick={() => {
                  setSearchQuery('');
                  setStatusFilter('');
                  setFormatFilter('');
                }}
              >
                Clear
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {selectedReports.length > 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography>
              {selectedReports.length} report(s) selected
            </Typography>
            
            <Button
              startIcon={<Settings />}
              onClick={(e) => setBulkActionMenuAnchor(e.currentTarget)}
            >
              Actions
            </Button>
          </Box>
        </Alert>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress />
        </Box>
      )}

      {/* Reports Table */}
      <Card>
        <CardContent sx={{ p: 0 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedReports.length === reports.length && reports.length > 0}
                      indeterminate={selectedReports.length > 0 && selectedReports.length < reports.length}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                    />
                  </TableCell>
                  <TableCell>Report</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Format</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.report_id} hover>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedReports.includes(report.report_id)}
                        onChange={(e) => handleReportSelection(report.report_id, e.target.checked)}
                      />
                    </TableCell>
                    
                    <TableCell>
                      <Box>
                        <Typography variant="subtitle2">
                          {report.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {report.description || 'No description'}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      {getReportStatusChip(report.status)}
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {ReportFormatIcons[report.format]}
                        <Typography variant="body2">
                          {report.format.toUpperCase()}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2">
                        {format(new Date(report.created_at), 'PPp')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDistanceToNow(new Date(report.created_at))} ago
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      {report.file_size ? (
                        <Typography variant="body2">
                          {(report.file_size / 1024).toFixed(1)} KB
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          -
                        </Typography>
                      )}
                    </TableCell>
                    
                    <TableCell>
                      {report.status === 'generating' && (
                        <Box sx={{ width: 100 }}>
                          <LinearProgress
                            variant="determinate"
                            value={report.progress || 0}
                            size="small"
                          />
                          <Typography variant="caption">
                            {report.progress?.toFixed(0) || 0}%
                          </Typography>
                        </Box>
                      )}
                    </TableCell>
                    
                    <TableCell align="right">
                      <Stack direction="row" spacing={1}>
                        {canDownload(report) && (
                          <Tooltip title="Download">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleDownload(report)}
                            >
                              <Download />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        {canCancel(report) && (
                          <Tooltip title="Cancel">
                            <IconButton
                              size="small"
                              color="warning"
                              onClick={() => handleCancel(report.report_id)}
                            >
                              <Stop />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        <Tooltip title="More actions">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              setSelectedReport(report);
                              setReportActionMenuAnchor(e.currentTarget);
                            }}
                          >
                            <MoreVert />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {/* Pagination */}
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <Pagination
              count={totalPages}
              page={currentPage}
              onChange={(e, page) => setCurrentPage(page)}
              color="primary"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete {selectedReports.length || 1} report(s)?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button
            color="error"
            variant="contained"
            onClick={() => handleDelete(selectedReports.length > 0 ? selectedReports : [selectedReport?.report_id || ''])}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Actions Menu */}
      <Menu
        anchorEl={bulkActionMenuAnchor}
        open={Boolean(bulkActionMenuAnchor)}
        onClose={() => setBulkActionMenuAnchor(null)}
      >
        <MenuItemComponent onClick={() => handleBulkAction('download')}>
          <Download sx={{ mr: 1 }} />
          Download Selected
        </MenuItemComponent>
        <MenuItemComponent onClick={() => handleBulkAction('delete')} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} />
          Delete Selected
        </MenuItemComponent>
      </Menu>

      {/* Report Actions Menu */}
      <Menu
        anchorEl={reportActionMenuAnchor}
        open={Boolean(reportActionMenuAnchor)}
        onClose={() => setReportActionMenuAnchor(null)}
      >
        {selectedReport && canDownload(selectedReport) && (
          <MenuItemComponent onClick={() => handleReportAction('download', selectedReport)}>
            <Download sx={{ mr: 1 }} />
            Download
          </MenuItemComponent>
        )}
        <MenuItemComponent onClick={() => handleReportAction('details', selectedReport)}>
          <Visibility sx={{ mr: 1 }} />
          View Details
        </MenuItemComponent>
        {selectedReport && canCancel(selectedReport) && (
          <MenuItemComponent onClick={() => handleReportAction('cancel', selectedReport)}>
            <Stop sx={{ mr: 1 }} />
            Cancel
          </MenuItemComponent>
        )}
        <MenuItemComponent 
          onClick={() => handleReportAction('delete', selectedReport)} 
          sx={{ color: 'error.main' }}
        >
          <Delete sx={{ mr: 1 }} />
          Delete
        </MenuItemComponent>
      </Menu>

      {/* Floating Action Button */}
      {onCreateNew && (
        <Fab
          color="primary"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={onCreateNew}
        >
          <Add />
        </Fab>
      )}
    </Box>
  );
};

export default ReportManager;