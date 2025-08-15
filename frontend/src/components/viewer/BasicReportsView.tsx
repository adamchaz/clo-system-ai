import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Stack,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material';
import {
  Description,
  GetApp,
  Visibility,
  Schedule,
  Assessment,
  TrendingUp,
  AccountBalance,
  BarChart,
  PieChart,
  Close,
  CheckCircle,
  AccessTime,
  Error,
} from '@mui/icons-material';

interface Report {
  id: string;
  title: string;
  description: string;
  category: 'performance' | 'holdings' | 'risk' | 'compliance';
  lastGenerated: string;
  status: 'available' | 'generating' | 'error';
  size?: string;
  format: 'PDF' | 'Excel' | 'CSV';
}

interface BasicReportsViewProps {
  portfolioId?: string;
}

const BasicReportsView: React.FC<BasicReportsViewProps> = ({
  portfolioId: _portfolioId,
}) => {
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  // Mock reports data (in production would come from API)
  const availableReports: Report[] = [
    {
      id: '1',
      title: 'Monthly Performance Summary',
      description: 'Comprehensive monthly performance analysis with returns, benchmarks, and risk metrics',
      category: 'performance',
      lastGenerated: '2 days ago',
      status: 'available',
      size: '2.3 MB',
      format: 'PDF',
    },
    {
      id: '2', 
      title: 'Portfolio Holdings Report',
      description: 'Current asset holdings, allocations, and position summaries across all portfolios',
      category: 'holdings',
      lastGenerated: '1 week ago',
      status: 'available', 
      size: '1.8 MB',
      format: 'Excel',
    },
    {
      id: '3',
      title: 'Risk Analytics Overview',
      description: 'Portfolio risk metrics, VaR analysis, and compliance status summary',
      category: 'risk',
      lastGenerated: '3 days ago',
      status: 'available',
      size: '1.2 MB',
      format: 'PDF',
    },
    {
      id: '4',
      title: 'Asset Concentration Analysis',
      description: 'Asset concentration by sector, rating, and geographic distribution',
      category: 'risk',
      lastGenerated: '5 days ago',
      status: 'available',
      size: '956 KB',
      format: 'CSV',
    },
    {
      id: '5',
      title: 'Quarterly Executive Summary',
      description: 'High-level quarterly overview for executive reporting and presentations',
      category: 'performance',
      lastGenerated: '1 month ago',
      status: 'generating',
      format: 'PDF',
    },
    {
      id: '6',
      title: 'Compliance Monitoring Report',
      description: 'OC/IC trigger status, covenant compliance, and regulatory requirements tracking',
      category: 'compliance',
      lastGenerated: '1 week ago',
      status: 'error',
      format: 'PDF',
    },
  ];

  const getCategoryIcon = (category: Report['category']) => {
    switch (category) {
      case 'performance':
        return <TrendingUp color="success" />;
      case 'holdings':
        return <AccountBalance color="primary" />;
      case 'risk':
        return <Assessment color="warning" />;
      case 'compliance':
        return <CheckCircle color="info" />;
      default:
        return <Description />;
    }
  };

  const getCategoryColor = (category: Report['category']) => {
    switch (category) {
      case 'performance':
        return 'success';
      case 'holdings':
        return 'primary';
      case 'risk':
        return 'warning';
      case 'compliance':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: Report['status']) => {
    switch (status) {
      case 'available':
        return <CheckCircle color="success" />;
      case 'generating':
        return <AccessTime color="warning" />;
      case 'error':
        return <Error color="error" />;
      default:
        return <Description />;
    }
  };

  const handleReportPreview = useCallback((report: Report) => {
    setSelectedReport(report);
    setPreviewOpen(true);
  }, []);

  const handleDownloadReport = useCallback((report: Report) => {
    // In production, this would trigger actual download
    console.log(`Downloading report: ${report.title}`);
  }, []);

  const categoryGroups = availableReports.reduce((groups, report) => {
    if (!groups[report.category]) {
      groups[report.category] = [];
    }
    groups[report.category].push(report);
    return groups;
  }, {} as Record<string, Report[]>);

  return (
    <Box>
      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Description color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {availableReports.length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Reports
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircle color="success" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {availableReports.filter(r => r.status === 'available').length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Available
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Schedule color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {availableReports.filter(r => r.status === 'generating').length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                In Progress
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <GetApp color="info" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {(availableReports.reduce((sum, r) => sum + parseFloat(r.size?.split(' ')[0] || '0'), 0)).toFixed(1)}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Size (MB)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Reports by Category */}
      <Grid container spacing={3}>
        {Object.entries(categoryGroups).map(([category, reports]) => (
          <Grid size={{ xs: 12, md: 6 }} key={category}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {getCategoryIcon(category as Report['category'])}
                  <Typography variant="h6" sx={{ ml: 1, textTransform: 'capitalize' }}>
                    {category} Reports
                  </Typography>
                  <Chip 
                    label={reports.length} 
                    size="small" 
                    sx={{ ml: 'auto' }}
                    color={getCategoryColor(category as Report['category'])}
                  />
                </Box>
                
                <List dense>
                  {reports.map((report) => (
                    <ListItem key={report.id} sx={{ px: 0 }}>
                      <ListItemIcon>
                        {getStatusIcon(report.status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="body2" fontWeight={600}>
                            {report.title}
                          </Typography>
                        }
                        secondary={
                          <Box>
                            <Typography variant="caption" color="text.secondary" display="block">
                              {report.description}
                            </Typography>
                            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 0.5 }}>
                              <Chip 
                                label={report.format} 
                                size="small" 
                                variant="outlined"
                              />
                              <Typography variant="caption" color="text.secondary">
                                {report.lastGenerated}
                              </Typography>
                              {report.size && (
                                <Typography variant="caption" color="text.secondary">
                                  • {report.size}
                                </Typography>
                              )}
                            </Stack>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Stack direction="row" spacing={0.5}>
                          <IconButton 
                            size="small" 
                            onClick={() => handleReportPreview(report)}
                            disabled={report.status !== 'available'}
                          >
                            <Visibility fontSize="small" />
                          </IconButton>
                          <IconButton 
                            size="small"
                            onClick={() => handleDownloadReport(report)}
                            disabled={report.status !== 'available'}
                          >
                            <GetApp fontSize="small" />
                          </IconButton>
                        </Stack>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Report Preview Dialog */}
      <Dialog 
        open={previewOpen} 
        onClose={() => setPreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">
              {selectedReport?.title}
            </Typography>
            <IconButton onClick={() => setPreviewOpen(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {selectedReport && (
            <Box>
              <Typography variant="body1" gutterBottom>
                {selectedReport.description}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Grid container spacing={2}>
                <Grid size={6}>
                  <Typography variant="body2" color="text.secondary">
                    Category
                  </Typography>
                  <Chip 
                    label={selectedReport.category}
                    size="small"
                    color={getCategoryColor(selectedReport.category)}
                    sx={{ textTransform: 'capitalize' }}
                  />
                </Grid>
                
                <Grid size={6}>
                  <Typography variant="body2" color="text.secondary">
                    Format
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {selectedReport.format}
                  </Typography>
                </Grid>
                
                <Grid size={6}>
                  <Typography variant="body2" color="text.secondary">
                    Last Generated
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {selectedReport.lastGenerated}
                  </Typography>
                </Grid>
                
                <Grid size={6}>
                  <Typography variant="body2" color="text.secondary">
                    File Size
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {selectedReport.size || 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
              
              <Paper 
                sx={{ 
                  mt: 3,
                  p: 4,
                  textAlign: 'center',
                  backgroundColor: 'background.default',
                  border: 1,
                  borderColor: 'divider',
                  borderStyle: 'dashed',
                }}
              >
                <Box sx={{ color: 'text.secondary' }}>
                  {selectedReport.category === 'performance' && <BarChart sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />}
                  {selectedReport.category === 'holdings' && <PieChart sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />}
                  {selectedReport.category === 'risk' && <Assessment sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />}
                  {selectedReport.category === 'compliance' && <CheckCircle sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />}
                  
                  <Typography variant="h6" gutterBottom>
                    Report Preview
                  </Typography>
                  <Typography variant="body2">
                    This is a preview of the {selectedReport.title} report. 
                    The full report contains detailed analysis and data visualizations.
                  </Typography>
                </Box>
              </Paper>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setPreviewOpen(false)}>
            Close
          </Button>
          <Button 
            variant="contained"
            startIcon={<GetApp />}
            onClick={() => selectedReport && handleDownloadReport(selectedReport)}
            disabled={!selectedReport || selectedReport.status !== 'available'}
          >
            Download
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BasicReportsView;