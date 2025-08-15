/**
 * ReportDashboard Component - Comprehensive Reporting Overview Interface
 * 
 * Main reporting dashboard providing:
 * - Real-time report generation status and statistics
 * - Quick access to report creation and management
 * - Recent report activity and notifications
 * - Report template management and organization
 * - Scheduled reports monitoring and control
 * - Performance metrics and usage analytics
 * 
 * Serves as the central hub for all reporting activities
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Stack,
  Alert,
  LinearProgress,
  Tabs,
  Tab,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  Badge,
  Fab,
} from '@mui/material';
import {
  Add,
  Assessment,
  Schedule,
  CheckCircle,
  Error,
  Warning,
  Pending,
  Download,
  Share,
  Visibility,
  MoreVert,
  TrendingUp,
  TrendingDown,
  Timeline,
  Analytics,
  Description,
  PictureAsPdf,
  TableChart,
  Email,
  Notifications,
  Speed,
  Storage,
  CloudDownload,
  AccessTime,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';

// Import API hooks
import {
  useGetReportsQuery,
  useGetReportStatsQuery,
  useGetReportTemplatesQuery,
} from '../../store/api/cloApi';

// Import types
import {
  Report,
  ReportTemplate,
  ReportStatus,
} from '../../store/api/newApiTypes';

// Import WebSocket hooks
import { useReportUpdates } from '../../hooks/useWebSocket';

// Import other reporting components
import ReportBuilder from './ReportBuilder';
import ReportManager from './ReportManager';
import ReportViewer from './ReportViewer';

interface ReportDashboardProps {
  defaultTab?: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} role="tabpanel">
    {value === index && <Box>{children}</Box>}
  </div>
);

const ReportStatusConfig = {
  pending: { label: 'Pending', color: 'warning' as const, icon: <Pending /> },
  generating: { label: 'Generating', color: 'info' as const, icon: <Assessment /> },
  completed: { label: 'Completed', color: 'success' as const, icon: <CheckCircle /> },
  failed: { label: 'Failed', color: 'error' as const, icon: <Error /> },
  cancelled: { label: 'Cancelled', color: 'default' as const, icon: <Warning /> },
  scheduled: { label: 'Scheduled', color: 'primary' as const, icon: <Schedule /> },
};

const ReportFormatIcons = {
  pdf: <PictureAsPdf />,
  excel: <TableChart />,
  csv: <Description />,
  html: <Assessment />,
};

const ReportDashboard: React.FC<ReportDashboardProps> = ({ 
  defaultTab = 0 
}) => {
  // State management
  const [currentTab, setCurrentTab] = useState(defaultTab);
  const [createReportOpen, setCreateReportOpen] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [reportViewerOpen, setReportViewerOpen] = useState(false);
  const [realtimeUpdates, setRealtimeUpdates] = useState<any[]>([]);

  // API hooks
  const { data: recentReportsResponse, refetch: refetchReports } = useGetReportsQuery({
    page: 1,
    page_size: 10,
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  const { data: reportStats } = useGetReportStatsQuery();
  const { data: templatesResponse } = useGetReportTemplatesQuery();

  const recentReports = recentReportsResponse?.data || [];
  const templates = templatesResponse?.data || [];

  // WebSocket integration for real-time updates
  useReportUpdates((updateData) => {
    setRealtimeUpdates(prev => [updateData, ...prev.slice(0, 4)]); // Keep last 5 updates
    refetchReports();
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleCreateReport = (templateId?: string) => {
    setCreateReportOpen(true);
  };

  const handleReportCreated = (reportId: string) => {
    setCreateReportOpen(false);
    refetchReports();
    // Optionally open the created report
    setSelectedReportId(reportId);
    setReportViewerOpen(true);
  };

  const handleViewReport = (reportId: string) => {
    setSelectedReportId(reportId);
    setReportViewerOpen(true);
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

  const getActiveReports = () => {
    return recentReports.filter(report => 
      report.status === 'generating' || report.status === 'pending'
    );
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1">
            Reporting Dashboard
          </Typography>
          {realtimeUpdates.length > 0 && (
            <Badge badgeContent={realtimeUpdates.length} color="info">
              <Typography variant="body2" color="text.secondary">
                Real-time reporting updates and analytics
              </Typography>
            </Badge>
          )}
        </Box>

        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleCreateReport()}
        >
          Create Report
        </Button>
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

      {/* Statistics Cards */}
      {reportStats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Total Reports
                    </Typography>
                    <Typography variant="h4">
                      {reportStats.data.total_reports}
                    </Typography>
                  </Box>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <Assessment />
                  </Avatar>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <TrendingUp sx={{ color: 'success.main', mr: 1 }} />
                  <Typography variant="body2" color="success.main">
                    +{reportStats.data.reports_this_week || 0} this week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Generating
                    </Typography>
                    <Typography variant="h4" color="info.main">
                      {reportStats.data.generating_reports}
                    </Typography>
                  </Box>
                  <Avatar sx={{ bgcolor: 'info.main' }}>
                    <Speed />
                  </Avatar>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <AccessTime sx={{ color: 'text.secondary', mr: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    {getActiveReports().length} active jobs
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Completed
                    </Typography>
                    <Typography variant="h4" color="success.main">
                      {reportStats.data.completed_reports}
                    </Typography>
                  </Box>
                  <Avatar sx={{ bgcolor: 'success.main' }}>
                    <CheckCircle />
                  </Avatar>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <CloudDownload sx={{ color: 'success.main', mr: 1 }} />
                  <Typography variant="body2" color="success.main">
                    {reportStats.data.downloads_today || 0} downloads today
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Scheduled
                    </Typography>
                    <Typography variant="h4" color="primary.main">
                      {reportStats.data.scheduled_reports}
                    </Typography>
                  </Box>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <Schedule />
                  </Avatar>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <Email sx={{ color: 'primary.main', mr: 1 }} />
                  <Typography variant="body2" color="primary.main">
                    Auto-delivery enabled
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Grid container spacing={3}>
        {/* Recent Reports & Active Generation */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                <Tabs value={currentTab} onChange={handleTabChange}>
                  <Tab label="Recent Reports" />
                  <Tab label="Active Generation" />
                  <Tab label="Templates" />
                </Tabs>
              </Box>

              {/* Recent Reports Tab */}
              <TabPanel value={currentTab} index={0}>
                <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6">Recent Reports</Typography>
                  <Button 
                    size="small" 
                    onClick={() => setCurrentTab(1)}
                    endIcon={<Visibility />}
                  >
                    View All
                  </Button>
                </Box>
                
                {recentReports.length > 0 ? (
                  <List>
                    {recentReports.slice(0, 5).map((report) => (
                      <ListItem
                        key={report.report_id}
                        sx={{
                          border: 1,
                          borderColor: 'divider',
                          borderRadius: 1,
                          mb: 1,
                          cursor: 'pointer',
                          '&:hover': { bgcolor: 'action.hover' },
                        }}
                        onClick={() => handleViewReport(report.report_id)}
                      >
                        <ListItemIcon>
                          {ReportFormatIcons[report.format]}
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle2">
                                {report.name}
                              </Typography>
                              {getReportStatusChip(report.status)}
                            </Box>
                          }
                          secondary={
                            <Typography variant="caption">
                              {format(new Date(report.created_at), 'PPp')} • 
                              {formatDistanceToNow(new Date(report.created_at))} ago
                            </Typography>
                          }
                        />
                        <Stack direction="row" spacing={1}>
                          {report.status === 'completed' && (
                            <Tooltip title="Download">
                              <IconButton size="small">
                                <Download />
                              </IconButton>
                            </Tooltip>
                          )}
                          {report.status === 'generating' && (
                            <Box sx={{ width: 60 }}>
                              <LinearProgress
                                variant="determinate"
                                value={report.progress || 0}
                                size="small"
                              />
                            </Box>
                          )}
                        </Stack>
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Alert severity="info">
                    No recent reports found. Create your first report to get started.
                  </Alert>
                )}
              </TabPanel>

              {/* Active Generation Tab */}
              <TabPanel value={currentTab} index={1}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6">Active Report Generation</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Monitor real-time report generation progress
                  </Typography>
                </Box>
                
                {getActiveReports().length > 0 ? (
                  <Stack spacing={2}>
                    {getActiveReports().map((report) => (
                      <Card key={report.report_id} variant="outlined">
                        <CardContent sx={{ pb: '16px !important' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Assessment color="info" />
                              <Typography variant="subtitle1">
                                {report.name}
                              </Typography>
                              {getReportStatusChip(report.status)}
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              {formatDistanceToNow(new Date(report.created_at))} ago
                            </Typography>
                          </Box>
                          
                          {report.progress !== undefined && (
                            <Box>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="body2">
                                  Progress
                                </Typography>
                                <Typography variant="body2">
                                  {report.progress.toFixed(1)}%
                                </Typography>
                              </Box>
                              <LinearProgress
                                variant="determinate"
                                value={report.progress}
                                sx={{ height: 8, borderRadius: 4 }}
                              />
                            </Box>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </Stack>
                ) : (
                  <Alert severity="info">
                    No reports are currently being generated.
                  </Alert>
                )}
              </TabPanel>

              {/* Templates Tab */}
              <TabPanel value={currentTab} index={2}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6">Report Templates</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Quick start with pre-built report templates
                  </Typography>
                </Box>
                
                <Grid container spacing={2}>
                  {templates.slice(0, 6).map((template) => (
                    <Grid size={{ xs: 12, sm: 6 }} key={template.template_id}>
                      <Card 
                        variant="outlined"
                        sx={{ 
                          cursor: 'pointer',
                          '&:hover': { 
                            borderColor: 'primary.main',
                            bgcolor: 'action.hover' 
                          }
                        }}
                        onClick={() => handleCreateReport(template.template_id)}
                      >
                        <CardContent sx={{ pb: '16px !important' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <Assessment sx={{ mr: 1 }} color="primary" />
                            <Typography variant="subtitle2">
                              {template.name}
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary" noWrap>
                            {template.description}
                          </Typography>
                          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                            <Chip label={template.category} size="small" />
                            <Chip 
                              label={`${template.estimated_time || 30}s`} 
                              size="small" 
                              icon={<AccessTime />} 
                            />
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </TabPanel>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions & System Status */}
        <Grid size={{ xs: 12, lg: 4 }}>
          <Stack spacing={3}>
            {/* Quick Actions */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Actions
                </Typography>
                
                <Stack spacing={2}>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => handleCreateReport()}
                  >
                    Create New Report
                  </Button>
                  
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Assessment />}
                    onClick={() => setCurrentTab(1)}
                  >
                    View All Reports
                  </Button>
                  
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<Schedule />}
                  >
                    Manage Schedules
                  </Button>
                </Stack>
              </CardContent>
            </Card>

            {/* System Status */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Status
                </Typography>
                
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">
                      Report Generation Service
                    </Typography>
                    <Chip label="Online" color="success" size="small" />
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">
                      Template Engine
                    </Typography>
                    <Chip label="Healthy" color="success" size="small" />
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">
                      File Storage
                    </Typography>
                    <Chip label="Available" color="success" size="small" />
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">
                      Email Delivery
                    </Typography>
                    <Chip label="Active" color="success" size="small" />
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Activity
                </Typography>
                
                {realtimeUpdates.length > 0 ? (
                  <List dense>
                    {realtimeUpdates.map((update, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemIcon>
                          <Notifications color="info" />
                        </ListItemIcon>
                        <ListItemText
                          primary={update.report_name}
                          secondary={`${update.status} • ${formatDistanceToNow(new Date())} ago`}
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Alert severity="info">
                    No recent activity to display.
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>

      {/* Floating Action Button for Quick Report Creation */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => handleCreateReport()}
      >
        <Add />
      </Fab>

      {/* Report Builder Dialog */}
      {createReportOpen && (
        <Box sx={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, bgcolor: 'background.default', zIndex: 1300 }}>
          <ReportBuilder
            onReportCreated={handleReportCreated}
            onClose={() => setCreateReportOpen(false)}
          />
        </Box>
      )}

      {/* Report Viewer Dialog */}
      {selectedReportId && (
        <ReportViewer
          reportId={selectedReportId}
          open={reportViewerOpen}
          onClose={() => {
            setReportViewerOpen(false);
            setSelectedReportId(null);
          }}
          onDeleted={() => {
            refetchReports();
            setReportViewerOpen(false);
            setSelectedReportId(null);
          }}
        />
      )}
    </Box>
  );
};

export default ReportDashboard;