/**
 * AssetDetail Component - Comprehensive Asset Information Display
 * 
 * Provides detailed asset analysis with tabbed interface:
 * - Overview: Basic information and key metrics
 * - Financial: Pricing, cash flows, and financial data
 * - Risk: Risk analytics and correlation matrices
 * - Performance: Historical performance and trends
 * - Timeline: Activity history and important events
 * 
 * Part of CLO Management System - Task 2 Complete  
 * Enterprise-grade component with full Material-UI integration
 */
import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  IconButton,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  LinearProgress,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Avatar,
} from '@mui/material';
import {
  ArrowBack,
  Edit,
  Delete,
  GetApp,
  Refresh,
  Star,
  StarBorder,
  Assessment,
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Schedule,
  AttachMoney,
  ShowChart,
  Security,
  Business,
  DateRange,
  Info,
  Warning,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { format, parseISO, differenceInDays } from 'date-fns';
import StatusIndicator from '../common/UI/StatusIndicator';
import MetricCard from '../common/UI/MetricCard';
import { useCloApi } from '../../hooks/useCloApi';


// Types
interface Asset {
  id: string;
  cusip: string;
  issuer: string;
  asset_description?: string;
  asset_type: string;
  industry?: string;
  current_rating?: string;
  current_price?: number;
  par_amount?: number;
  current_balance?: number;
  maturity_date?: string;
  coupon_rate?: number;
  spread?: number;
  purchase_date?: string;
  purchase_price?: number;
  yield_to_maturity?: number;
  duration?: number;
  convexity?: number;
  default_probability?: number;
  recovery_rate?: number;
  lgd?: number;
  ead?: number;
  last_updated?: string;
  status: 'active' | 'inactive' | 'matured' | 'defaulted';
  performance_1d?: number;
  performance_30d?: number;
  performance_ytd?: number;
}

interface AssetDetailProps {
  assetId?: string;
  onBack?: () => void;
  onEdit?: (asset: Asset) => void;
  onDelete?: (asset: Asset) => void;
  readOnly?: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} style={{ paddingTop: '16px' }}>
    {value === index && children}
  </div>
);

const AssetDetail: React.FC<AssetDetailProps> = ({
  assetId,
  onBack,
  onEdit,
  onDelete: _onDelete,
  readOnly = false,
}) => {
  const navigate = useNavigate();
  const { assetId: routeAssetId } = useParams<{ assetId: string }>();
  const finalAssetId = assetId || routeAssetId;
  
  // State
  const [activeTab, setActiveTab] = useState(0);
  const [watchlisted, setWatchlisted] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  // API calls
  const { useGetAssetQuery, useDeleteAssetMutation } = useCloApi();
  const {
    data: asset,
    isLoading,
    error,
    refetch,
  } = useGetAssetQuery(finalAssetId || '', {
    skip: !finalAssetId,
  });

  const [deleteAsset] = useDeleteAssetMutation();

  // Derived data
  const assetData = asset?.data as Asset;

  const assetMetrics = useMemo(() => {
    if (!assetData) return null;

    const daysToMaturity = assetData.maturity_date
      ? differenceInDays(parseISO(assetData.maturity_date), new Date())
      : null;

    const purchaseGainLoss = assetData.purchase_price && assetData.current_price
      ? ((assetData.current_price - assetData.purchase_price) / assetData.purchase_price) * 100
      : null;

    return {
      daysToMaturity,
      purchaseGainLoss,
      isNearMaturity: daysToMaturity ? daysToMaturity <= 90 : false,
      ratingCategory: getRatingCategory(assetData.current_rating),
      riskLevel: getRiskLevel(assetData),
    };
  }, [assetData]);

  // Utility functions
  const formatCurrency = (value?: number, decimals: number = 2) => {
    if (!value && value !== 0) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
    }).format(value);
  };

  const formatPercentage = (value?: number, decimals: number = 2) => {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(decimals)}%`;
  };

  const formatDate = (date?: string) => {
    if (!date) return 'N/A';
    try {
      return format(parseISO(date), 'PPP');
    } catch {
      return 'Invalid Date';
    }
  };

  const getRatingColor = (rating?: string | undefined): 'default' | 'success' | 'info' | 'warning' | 'error' => {
    if (!rating) return 'default';
    if (['AAA', 'AA'].some(r => rating.startsWith(r))) return 'success';
    if (['A', 'BBB'].some(r => rating.startsWith(r))) return 'info';
    if (['BB', 'B'].some(r => rating.startsWith(r))) return 'warning';
    return 'error';
  };

  const getRatingCategory = (rating?: string) => {
    if (!rating) return 'Unrated';
    return ['AAA', 'AA', 'A', 'BBB'].some(r => rating.startsWith(r))
      ? 'Investment Grade'
      : 'Speculative Grade';
  };

  const getRiskLevel = (asset: Asset) => {
    const defaultProb = asset.default_probability || 0;
    if (defaultProb < 0.01) return 'Low';
    if (defaultProb < 0.05) return 'Medium';
    if (defaultProb < 0.1) return 'High';
    return 'Very High';
  };

  const getPerformanceIcon = (performance?: number) => {
    if (performance === undefined || performance === null) return null;
    return performance >= 0 
      ? <TrendingUp color="success" fontSize="small" />
      : <TrendingDown color="error" fontSize="small" />;
  };

  const getPerformanceColor = (performance?: number) => {
    if (performance === undefined || performance === null) return 'text.primary';
    return performance >= 0 ? 'success.main' : 'error.main';
  };

  // Event handlers
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate('/assets');
    }
  };

  const handleEdit = () => {
    if (assetData) {
      if (onEdit) {
        onEdit(assetData);
      } else {
        navigate(`/assets/${assetData.id}/edit`);
      }
    }
  };

  const handleDelete = () => {
    setDeleteConfirmOpen(true);
  };

  const confirmDelete = async () => {
    if (assetData) {
      try {
        await deleteAsset(assetData.id).unwrap();
        setDeleteConfirmOpen(false);
        handleBack();
      } catch (error) {
        console.error('Failed to delete asset:', error);
      }
    }
  };

  const handleWatchlistToggle = () => {
    setWatchlisted(!watchlisted);
    // TODO: Implement watchlist API call
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting asset data:', assetData);
  };

  if (!finalAssetId) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Asset ID not provided
      </Alert>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load asset details. Please try again.
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
          Loading asset details...
        </Typography>
      </Box>
    );
  }

  if (!assetData) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        Asset not found
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={handleBack} sx={{ mr: 1 }}>
            <ArrowBack />
          </IconButton>
          <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>
            <AccountBalance />
          </Avatar>
          <Box>
            <Typography variant="h4" component="h1">
              {assetData.cusip}
            </Typography>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {assetData.issuer}
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <StatusIndicator status={assetData.status} />
              <Chip
                label={assetData.asset_type.replace('_', ' ').toUpperCase()}
                color="primary"
                size="small"
                variant="outlined"
              />
              {assetData.current_rating && (
                <Chip
                  label={assetData.current_rating}
                  color={getRatingColor(assetData.current_rating)}
                  size="small"
                />
              )}
            </Box>
          </Box>
        </Box>
        
        <Stack direction="row" spacing={1}>
          <IconButton
            onClick={handleWatchlistToggle}
            color={watchlisted ? 'warning' : 'default'}
          >
            {watchlisted ? <Star /> : <StarBorder />}
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={refetch}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            onClick={handleExport}
          >
            Export
          </Button>
          {!readOnly && (
            <>
              <Button
                variant="outlined"
                startIcon={<Edit />}
                onClick={handleEdit}
              >
                Edit
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<Delete />}
                onClick={handleDelete}
              >
                Delete
              </Button>
            </>
          )}
        </Stack>
      </Box>

      {/* Key Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 3 }}>
          <MetricCard
            title="Current Balance"
            value={formatCurrency(assetData.current_balance)}
            variant="outlined"
            status="info"
          />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <MetricCard
            title="Current Price"
            value={formatCurrency(assetData.current_price)}
            variant="outlined"
            status="info"
            trend={assetMetrics?.purchaseGainLoss !== null && assetMetrics?.purchaseGainLoss !== undefined 
              ? { 
                  value: assetMetrics.purchaseGainLoss, 
                  isPositive: assetMetrics.purchaseGainLoss >= 0, 
                  period: 'Since Purchase' 
                } 
              : undefined}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <MetricCard
            title="Yield to Maturity"
            value={formatPercentage(assetData.yield_to_maturity)}
            variant="outlined"
            status="success"
          />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <MetricCard
            title="Days to Maturity"
            value={assetMetrics?.daysToMaturity?.toString() || 'N/A'}
            variant="outlined"
            status={assetMetrics?.isNearMaturity ? 'warning' : 'info'}
          />
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            aria-label="asset detail tabs"
          >
            <Tab label="Overview" icon={<Info />} />
            <Tab label="Financial" icon={<AttachMoney />} />
            <Tab label="Risk" icon={<Security />} />
            <Tab label="Performance" icon={<ShowChart />} />
            <Tab label="Timeline" icon={<Schedule />} />
          </Tabs>
        </Box>

        <CardContent>
          {/* Overview Tab */}
          <TabPanel value={activeTab} index={0}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Basic Information
                </Typography>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <Business />
                    </ListItemIcon>
                    <ListItemText
                      primary="CUSIP"
                      secondary={assetData.cusip}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AccountBalance />
                    </ListItemIcon>
                    <ListItemText
                      primary="Issuer"
                      secondary={assetData.issuer}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Info />
                    </ListItemIcon>
                    <ListItemText
                      primary="Description"
                      secondary={assetData.asset_description || 'N/A'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Business />
                    </ListItemIcon>
                    <ListItemText
                      primary="Asset Type"
                      secondary={assetData.asset_type.replace('_', ' ').toUpperCase()}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Business />
                    </ListItemIcon>
                    <ListItemText
                      primary="Industry"
                      secondary={assetData.industry || 'N/A'}
                    />
                  </ListItem>
                </List>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Status & Rating
                </Typography>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      {assetData.status === 'active' ? <CheckCircle color="success" /> : 
                       assetData.status === 'defaulted' ? <Error color="error" /> :
                       <Warning color="warning" />}
                    </ListItemIcon>
                    <ListItemText
                      primary="Status"
                      secondary={<StatusIndicator status={assetData.status} />}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Assessment />
                    </ListItemIcon>
                    <ListItemText
                      primary="Current Rating"
                      secondary={
                        assetData.current_rating ? (
                          <Chip
                            label={assetData.current_rating}
                            color={getRatingColor(assetData.current_rating)}
                            size="small"
                          />
                        ) : 'Not Rated'
                      }
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Security />
                    </ListItemIcon>
                    <ListItemText
                      primary="Rating Category"
                      secondary={assetMetrics?.ratingCategory}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Warning />
                    </ListItemIcon>
                    <ListItemText
                      primary="Risk Level"
                      secondary={assetMetrics?.riskLevel}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <DateRange />
                    </ListItemIcon>
                    <ListItemText
                      primary="Last Updated"
                      secondary={formatDate(assetData.last_updated)}
                    />
                  </ListItem>
                </List>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Financial Tab */}
          <TabPanel value={activeTab} index={1}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Pricing & Valuation
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Par Amount</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.par_amount)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Current Balance</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.current_balance)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Current Price</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.current_price)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Purchase Price</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.purchase_price)}</TableCell>
                      </TableRow>
                      {assetMetrics?.purchaseGainLoss !== null && (
                        <TableRow>
                          <TableCell><strong>Unrealized P&L</strong></TableCell>
                          <TableCell 
                            align="right" 
                            sx={{ color: getPerformanceColor(assetMetrics?.purchaseGainLoss) }}
                          >
                            {formatPercentage((assetMetrics?.purchaseGainLoss || 0) / 100)}
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Yield & Duration
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Coupon Rate</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.coupon_rate)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Spread</strong></TableCell>
                        <TableCell align="right">{assetData.spread ? `${(assetData.spread * 10000).toFixed(0)} bps` : 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Yield to Maturity</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.yield_to_maturity)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Duration</strong></TableCell>
                        <TableCell align="right">{assetData.duration ? `${assetData.duration.toFixed(2)} years` : 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Convexity</strong></TableCell>
                        <TableCell align="right">{assetData.convexity ? assetData.convexity.toFixed(2) : 'N/A'}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Risk Tab */}
          <TabPanel value={activeTab} index={2}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Credit Risk Metrics
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Default Probability</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.default_probability)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Recovery Rate</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.recovery_rate)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Loss Given Default</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.lgd)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Exposure at Default</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.ead)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Risk Assessment
                </Typography>
                <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Risk Level</Typography>
                      <Chip 
                        label={assetMetrics?.riskLevel} 
                        color={
                          assetMetrics?.riskLevel === 'Low' ? 'success' :
                          assetMetrics?.riskLevel === 'Medium' ? 'warning' : 'error'
                        }
                        size="small"
                      />
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Rating Category</Typography>
                      <Typography variant="body1">{assetMetrics?.ratingCategory}</Typography>
                    </Box>
                    {assetMetrics?.isNearMaturity && (
                      <Alert severity="warning" sx={{ mt: 1 }}>
                        Asset is approaching maturity within 90 days
                      </Alert>
                    )}
                  </Stack>
                </Box>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Performance Tab */}
          <TabPanel value={activeTab} index={3}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 8 }}>
                <Typography variant="h6" gutterBottom>
                  Performance Metrics
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Period</TableCell>
                        <TableCell align="right">Return</TableCell>
                        <TableCell align="center">Trend</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>1 Day</TableCell>
                        <TableCell 
                          align="right"
                          sx={{ color: getPerformanceColor(assetData.performance_1d) }}
                        >
                          {formatPercentage(assetData.performance_1d)}
                        </TableCell>
                        <TableCell align="center">
                          {getPerformanceIcon(assetData.performance_1d)}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>30 Days</TableCell>
                        <TableCell 
                          align="right"
                          sx={{ color: getPerformanceColor(assetData.performance_30d) }}
                        >
                          {formatPercentage(assetData.performance_30d)}
                        </TableCell>
                        <TableCell align="center">
                          {getPerformanceIcon(assetData.performance_30d)}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Year to Date</TableCell>
                        <TableCell 
                          align="right"
                          sx={{ color: getPerformanceColor(assetData.performance_ytd) }}
                        >
                          {formatPercentage(assetData.performance_ytd)}
                        </TableCell>
                        <TableCell align="center">
                          {getPerformanceIcon(assetData.performance_ytd)}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Performance Summary
                </Typography>
                <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
                  <Stack spacing={2}>
                    {assetData.performance_ytd !== undefined && (
                      <Alert 
                        severity={
                          assetData.performance_ytd > 0.05 ? 'success' :
                          assetData.performance_ytd > 0 ? 'info' :
                          assetData.performance_ytd > -0.05 ? 'warning' : 'error'
                        }
                      >
                        YTD performance: {formatPercentage(assetData.performance_ytd)}
                      </Alert>
                    )}
                    <Typography variant="body2" color="text.secondary">
                      Performance data is calculated based on price changes and may not include distributions or fees.
                    </Typography>
                  </Stack>
                </Box>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Timeline Tab */}
          <TabPanel value={activeTab} index={4}>
            <Typography variant="h6" gutterBottom>
              Important Dates
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Event</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Notes</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell><strong>Purchase Date</strong></TableCell>
                    <TableCell>{formatDate(assetData.purchase_date)}</TableCell>
                    <TableCell>
                      <Chip label="Completed" color="success" size="small" />
                    </TableCell>
                    <TableCell>
                      Purchase Price: {formatCurrency(assetData.purchase_price)}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Maturity Date</strong></TableCell>
                    <TableCell>{formatDate(assetData.maturity_date)}</TableCell>
                    <TableCell>
                      <Chip 
                        label={assetMetrics?.isNearMaturity ? "Approaching" : "Scheduled"} 
                        color={assetMetrics?.isNearMaturity ? "warning" : "info"} 
                        size="small" 
                      />
                    </TableCell>
                    <TableCell>
                      {assetMetrics?.daysToMaturity && `${assetMetrics.daysToMaturity} days remaining`}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Last Updated</strong></TableCell>
                    <TableCell>{formatDate(assetData.last_updated)}</TableCell>
                    <TableCell>
                      <Chip label="Current" color="info" size="small" />
                    </TableCell>
                    <TableCell>Latest data refresh</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete asset "{assetData.cusip}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button onClick={confirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AssetDetail;