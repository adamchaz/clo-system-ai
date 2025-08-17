import React, { useState, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Alert,
  LinearProgress,
  Breadcrumbs,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Avatar,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Edit,
  Delete,
  GetApp,
  Refresh,
  Security,
  AccountBalance,
  Warning,
  CheckCircle,
  Timeline,
  PieChart,
  BarChart,
  Home,
  BusinessCenter,
} from '@mui/icons-material';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import {
  useGetPortfolioQuery,
  useGetPortfolioSummaryQuery,
  Portfolio,
} from '../../store/api/cloApi';

interface PortfolioDetailProps {
  portfolioId: string;
  onClose?: () => void;
  onEdit?: (portfolio: Portfolio) => void;
  onDelete?: (portfolio: Portfolio) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`portfolio-tabpanel-${index}`}
      aria-labelledby={`portfolio-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const PortfolioDetail: React.FC<PortfolioDetailProps> = ({
  portfolioId,
  onClose,
  onEdit,
  onDelete,
}) => {
  const [currentTab, setCurrentTab] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // API queries
  const {
    data: portfolioData,
    isLoading: portfolioLoading,
    error: portfolioError,
    refetch: refetchPortfolio,
  } = useGetPortfolioQuery(portfolioId, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: portfolioSummary,
    isLoading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useGetPortfolioSummaryQuery(portfolioId, {
    refetchOnMountOrArgChange: true,
  });

  const portfolio = portfolioData;
  const summary = portfolioSummary;

  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const handleRefresh = useCallback(() => {
    refetchPortfolio();
    refetchSummary();
  }, [refetchPortfolio, refetchSummary]);

  const handleEdit = useCallback(() => {
    if (portfolio) {
      onEdit?.(portfolio);
    }
  }, [portfolio, onEdit]);

  const handleDeleteConfirm = useCallback(() => {
    if (portfolio) {
      onDelete?.(portfolio);
      setDeleteDialogOpen(false);
    }
  }, [portfolio, onDelete]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'effective':
        return 'success';
      case 'pending':
        return 'warning';
      case 'inactive':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'effective':
        return 'Active';
      case 'pending':
        return 'Pending';
      case 'inactive':
        return 'Inactive';
      default:
        return status;
    }
  };

  const calculatePerformance = () => {
    if (!portfolio) return 0;
    return ((portfolio.current_portfolio_balance / portfolio.deal_size) - 1) * 100;
  };

  if (portfolioError || summaryError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load portfolio data. Please check your connection and try again.
        </Alert>
      </Box>
    );
  }

  if (portfolioLoading && !portfolio) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography variant="body1" sx={{ mt: 2, textAlign: 'center' }}>
          Loading portfolio details...
        </Typography>
      </Box>
    );
  }

  if (!portfolio) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Alert severity="warning">
          Portfolio not found or you don't have access to view it.
        </Alert>
      </Box>
    );
  }

  const performance = calculatePerformance();
  const isPositivePerformance = performance >= 0;

  return (
    <Box>
      {/* Breadcrumbs */}
      <Box sx={{ mb: 3 }}>
        <Breadcrumbs aria-label="breadcrumb">
          <Link
            underline="hover"
            color="inherit"
            onClick={onClose}
            sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
          >
            <Home sx={{ mr: 0.5 }} fontSize="inherit" />
            Dashboard
          </Link>
          <Link
            underline="hover"
            color="inherit"
            onClick={onClose}
            sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
          >
            <BusinessCenter sx={{ mr: 0.5 }} fontSize="inherit" />
            Portfolios
          </Link>
          <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
            <AccountBalance sx={{ mr: 0.5 }} fontSize="inherit" />
            {portfolio.deal_name}
          </Typography>
        </Breadcrumbs>
      </Box>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
          <Avatar sx={{ bgcolor: 'primary.main', mr: 3, width: 64, height: 64 }}>
            <AccountBalance fontSize="large" />
          </Avatar>
          <Box>
            <Typography
              variant="h4"
              component="h1"
              sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}
            >
              {portfolio.deal_name}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Chip
                label={getStatusLabel(portfolio.status)}
                color={getStatusColor(portfolio.status)}
                variant="outlined"
              />
              <Typography variant="body2" color="text.secondary">
                Managed by {portfolio.manager}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Trustee: {portfolio.trustee}
              </Typography>
            </Box>
            <Typography variant="body1" color="text.secondary">
              Effective: {format(parseISO(portfolio.effective_date), 'PPP')} •
              Maturity: {format(parseISO(portfolio.stated_maturity), 'PPP')}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} disabled={portfolioLoading || summaryLoading}>
              <Refresh />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            size="small"
          >
            Export
          </Button>
          <Button
            variant="outlined"
            startIcon={<Edit />}
            onClick={handleEdit}
            size="small"
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={() => setDeleteDialogOpen(true)}
            size="small"
          >
            Delete
          </Button>
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalance color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Deal Size
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight={700}>
                ${(portfolio.deal_size / 1000000).toFixed(1)}M
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {portfolio.currency}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PieChart color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Current NAV
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight={700}>
                ${(portfolio.current_portfolio_balance / 1000000).toFixed(1)}M
              </Typography>
              <Typography variant="caption" color={isPositivePerformance ? 'success.main' : 'error.main'}>
                {isPositivePerformance ? '+' : ''}{performance.toFixed(2)}% vs deal size
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <BarChart color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Assets
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight={700}>
                {portfolio.current_asset_count}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Securities
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Timeline color="warning" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Days to Maturity
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight={700}>
                {portfolio.days_to_maturity}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatDistanceToNow(parseISO(portfolio.stated_maturity))}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="portfolio detail tabs">
          <Tab label="Overview" />
          <Tab label="Assets" />
          <Tab label="Risk Analysis" />
          <Tab label="Performance" />
          <Tab label="Compliance" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Overview Tab */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Portfolio Information
                </Typography>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Deal Name</TableCell>
                      <TableCell sx={{ border: 0 }}>{portfolio.deal_name}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Manager</TableCell>
                      <TableCell sx={{ border: 0 }}>{portfolio.manager}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Trustee</TableCell>
                      <TableCell sx={{ border: 0 }}>{portfolio.trustee}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Currency</TableCell>
                      <TableCell sx={{ border: 0 }}>{portfolio.currency}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Effective Date</TableCell>
                      <TableCell sx={{ border: 0 }}>
                        {format(parseISO(portfolio.effective_date), 'PPP')}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Stated Maturity</TableCell>
                      <TableCell sx={{ border: 0 }}>
                        {format(parseISO(portfolio.stated_maturity), 'PPP')}
                      </TableCell>
                    </TableRow>
                    {portfolio.revolving_period_end && (
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600, border: 0 }}>Revolving Period End</TableCell>
                        <TableCell sx={{ border: 0 }}>
                          {format(parseISO(portfolio.revolving_period_end), 'PPP')}
                        </TableCell>
                      </TableRow>
                    )}
                    {portfolio.reinvestment_period_end && (
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600, border: 0 }}>Reinvestment Period End</TableCell>
                        <TableCell sx={{ border: 0 }}>
                          {format(parseISO(portfolio.reinvestment_period_end), 'PPP')}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Activity
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Portfolio created"
                      secondary={`${formatDistanceToNow(parseISO(portfolio.created_at))} ago`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Last updated"
                      secondary={`${formatDistanceToNow(parseISO(portfolio.updated_at))} ago`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Current asset count"
                      secondary={`${portfolio.current_asset_count} securities`}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {/* Assets Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Asset Composition
            </Typography>
            {summary && summary.assets ? (
              <Typography variant="body2" color="text.secondary" paragraph>
                This portfolio contains {summary.assets.length} assets with a total value of ${(portfolio.current_portfolio_balance / 1000000).toFixed(1)}M.
              </Typography>
            ) : (
              <Paper
                sx={{
                  p: 4,
                  textAlign: 'center',
                  backgroundColor: 'background.paper',
                  border: 1,
                  borderColor: 'divider',
                  borderStyle: 'dashed',
                }}
              >
                <BarChart sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  Asset data will be available here
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Detailed asset breakdown, composition, and analysis coming soon
                </Typography>
              </Paper>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Risk Analysis Tab */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Metrics
                </Typography>
                {summary?.risk_metrics ? (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Metric</TableCell>
                          <TableCell align="right">Value</TableCell>
                          <TableCell align="right">Status</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>Weighted Average Life</TableCell>
                          <TableCell align="right">
                            {summary.risk_metrics.weighted_average_life.toFixed(2)} years
                          </TableCell>
                          <TableCell align="right">
                            <CheckCircle color="success" fontSize="small" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Average Rating</TableCell>
                          <TableCell align="right">
                            {summary.risk_metrics.average_rating}
                          </TableCell>
                          <TableCell align="right">
                            <CheckCircle color="success" fontSize="small" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Portfolio Value</TableCell>
                          <TableCell align="right">
                            ${(summary.risk_metrics.portfolio_value / 1000000).toFixed(1)}M
                          </TableCell>
                          <TableCell align="right">
                            <CheckCircle color="success" fontSize="small" />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Paper
                    sx={{
                      p: 4,
                      textAlign: 'center',
                      backgroundColor: 'background.paper',
                      border: 1,
                      borderColor: 'divider',
                      borderStyle: 'dashed',
                    }}
                  >
                    <Security sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary">
                      Risk analysis data loading...
                    </Typography>
                  </Paper>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Compliance Status
                </Typography>
                {summary?.compliance_status ? (
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="OC Tests"
                        secondary={summary.compliance_status.oc_tests_passing ? 'Passing' : 'Failed'}
                      />
                      {summary.compliance_status.oc_tests_passing ? (
                        <CheckCircle color="success" />
                      ) : (
                        <Warning color="error" />
                      )}
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="IC Tests"
                        secondary={summary.compliance_status.ic_tests_passing ? 'Passing' : 'Failed'}
                      />
                      {summary.compliance_status.ic_tests_passing ? (
                        <CheckCircle color="success" />
                      ) : (
                        <Warning color="error" />
                      )}
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Concentration Tests"
                        secondary={summary.compliance_status.concentration_tests_passing ? 'Passing' : 'Failed'}
                      />
                      {summary.compliance_status.concentration_tests_passing ? (
                        <CheckCircle color="success" />
                      ) : (
                        <Warning color="error" />
                      )}
                    </ListItem>
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Loading compliance data...
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Performance Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance Analysis
            </Typography>
            <Paper
              sx={{
                p: 4,
                textAlign: 'center',
                backgroundColor: 'background.paper',
                border: 1,
                borderColor: 'divider',
                borderStyle: 'dashed',
              }}
            >
              <Timeline sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                Performance charts and analysis coming soon
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Historical performance, benchmarks, and risk-adjusted returns
              </Typography>
            </Paper>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={4}>
        {/* Compliance Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Compliance Details
            </Typography>
            {summary?.compliance_status ? (
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Failed Tests
                  </Typography>
                  {summary.compliance_status.failed_tests.length > 0 ? (
                    <List>
                      {summary.compliance_status.failed_tests.map((test, index) => (
                        <ListItem key={index}>
                          <Warning color="error" sx={{ mr: 1 }} />
                          <ListItemText primary={test} />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="success.main">
                      All compliance tests are passing
                    </Typography>
                  )}
                </Grid>

                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Warnings
                  </Typography>
                  {summary.compliance_status.warnings.length > 0 ? (
                    <List>
                      {summary.compliance_status.warnings.map((warning, index) => (
                        <ListItem key={index}>
                          <Warning color="warning" sx={{ mr: 1 }} />
                          <ListItemText primary={warning} />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No warnings
                    </Typography>
                  )}
                </Grid>
              </Grid>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Loading compliance data...
              </Typography>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirm Portfolio Deletion</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to delete this portfolio?
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1, mt: 2 }}>
            <Typography variant="body2" fontWeight={600}>
              {portfolio.deal_name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Deal Size: ${(portfolio.deal_size / 1000000).toFixed(1)}M
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Assets: {portfolio.current_asset_count}
            </Typography>
          </Box>
          <Alert severity="error" sx={{ mt: 2 }}>
            This action cannot be undone. All portfolio data and historical records will be permanently deleted.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
          >
            Delete Portfolio
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PortfolioDetail;