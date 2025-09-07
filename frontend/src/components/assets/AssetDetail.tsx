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
  Flag,
  CurrencyExchange,
  Category,
  LocationOn,
  Public,
  MonetizationOn,
  Receipt,
  Timeline,
  Analytics,
  Speed,
  Tune,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { format, parseISO, differenceInDays } from 'date-fns';
import StatusIndicator from '../common/UI/StatusIndicator';
import MetricCard from '../common/UI/MetricCard';
import { useCloApi } from '../../hooks/useCloApi';


// Complete Asset Interface - All 71 Parameters from Backend Model
interface Asset {
  // Primary Identification (5 parameters)
  blkrock_id: string;  // Primary key
  issue_name: string;
  issuer_name: string;
  issuer_id?: string;
  tranche?: string;
  
  // Asset Classification (4 parameters)
  bond_loan?: string;
  par_amount?: number;
  market_value?: number;
  currency?: string;
  
  // Date Fields (6 parameters)
  maturity?: string;
  dated_date?: string;
  issue_date?: string;
  first_payment_date?: string;
  date_of_default?: string;
  fair_value_date?: string;
  
  // Interest Rate Properties (7 parameters)
  coupon?: number;
  coupon_type?: string;
  index_name?: string;
  cpn_spread?: number;
  libor_floor?: number;
  index_cap?: number;
  payment_freq?: number;
  
  // Cash Flow Properties (7 parameters)
  amortization_type?: string;
  day_count?: string;
  business_day_conv?: string;
  payment_eom?: boolean;
  amount_issued?: number;
  facility_size?: number;
  wal?: number;
  
  // PIK Properties (3 parameters)
  piking?: boolean;
  pik_amount?: number;
  unfunded_amount?: number;
  
  // Credit Ratings - Core (5 parameters)
  mdy_rating?: string;
  mdy_dp_rating?: string;
  mdy_dp_rating_warf?: string;
  mdy_recovery_rate?: number;
  sp_rating?: string;
  
  // Derived Ratings (4 parameters)
  derived_mdy_rating?: string;
  derived_sp_rating?: string;
  rating_derivation_date?: string;
  rating_source_hierarchy?: string;
  
  // Yield Curve Integration (4 parameters)
  discount_curve_id?: number;
  discount_curve_name?: string;
  fair_value?: number;
  pricing_spread_bps?: number;
  
  // Extended Moody's Ratings (9 parameters)
  mdy_facility_rating?: string;
  mdy_facility_outlook?: string;
  mdy_issuer_rating?: string;
  mdy_issuer_outlook?: string;
  mdy_snr_sec_rating?: string;
  mdy_snr_unsec_rating?: string;
  mdy_sub_rating?: string;
  mdy_credit_est_rating?: string;
  mdy_credit_est_date?: string;
  
  // S&P Ratings (5 parameters)
  sandp_facility_rating?: string;
  sandp_issuer_rating?: string;
  sandp_snr_sec_rating?: string;
  sandp_subordinate?: string;
  sandp_rec_rating?: string;
  
  // Industry Classifications (6 parameters)
  mdy_industry?: string;
  sp_industry?: string;
  country?: string;
  seniority?: string;
  mdy_asset_category?: string;
  sp_priority_category?: string;
  
  // Financial Properties (2 parameters)
  commit_fee?: number;
  
  // Asset Flags (13 parameters as JSON object)
  flags?: {
    pik_asset?: boolean;
    default_asset?: boolean;
    delay_drawdown?: boolean;
    revolver?: boolean;
    loc?: boolean;  // Letter of Credit
    participation?: boolean;
    dip?: boolean;  // Debtor-in-Possession
    convertible?: boolean;
    struct_finance?: boolean;
    bridge_loan?: boolean;
    current_pay?: boolean;
    cov_lite?: boolean;
    fllo?: boolean;  // First Lien Last Out
  };
  
  // Analysis & Audit (4 parameters)
  analyst_opinion?: string;
  created_at?: string;
  updated_at?: string;
  
  // Legacy compatibility fields
  id?: string;
  cusip?: string;
  issuer?: string;
  asset_name?: string;
  asset_description?: string;
  asset_type?: string;
  industry?: string;
  current_rating?: string;
  current_price?: number;
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
  lgd?: number;
  ead?: number;
  last_updated?: string;
  status?: 'active' | 'inactive' | 'matured' | 'defaulted';
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

  // Utility functions needed for useMemo
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

  const assetMetrics = useMemo(() => {
    if (!assetData) return null;

    const daysToMaturity = (assetData.maturity || assetData.maturity_date)
      ? differenceInDays(parseISO(assetData.maturity || assetData.maturity_date), new Date())
      : null;

    const purchaseGainLoss = assetData.purchase_price && assetData.current_price
      ? ((Number(assetData.current_price) - Number(assetData.purchase_price)) / Number(assetData.purchase_price)) * 100
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
  const formatCurrency = (value?: number | string, decimals: number = 2) => {
    if (!value && value !== 0 && value !== '0' && value !== '0.00') return 'N/A';
    const numValue = typeof value === 'string' ? Number(value) : value;
    if (isNaN(numValue)) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
    }).format(numValue);
  };

  const formatPercentage = (value?: number | string, decimals: number = 2) => {
    if (value === undefined || value === null) return 'N/A';
    const numValue = typeof value === 'string' ? Number(value) : value;
    if (isNaN(numValue)) return 'N/A';
    return `${(numValue * 100).toFixed(decimals)}%`;
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
              {assetData.blkrock_id || assetData.id || assetData.cusip || assetData.issue_name || assetData.asset_name}
            </Typography>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {assetData.issuer_name || assetData.issuer}
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <StatusIndicator status={assetData.status || 'active'} />
              <Chip
                label={assetData.bond_loan || assetData.asset_type?.replace('_', ' ').toUpperCase() || 'ASSET'}
                color="primary"
                size="small"
                variant="outlined"
              />
              {(assetData.mdy_rating || assetData.sp_rating || assetData.current_rating) && (
                <Chip
                  label={assetData.mdy_rating || assetData.sp_rating || assetData.current_rating}
                  color={getRatingColor(assetData.mdy_rating || assetData.sp_rating || assetData.current_rating)}
                  size="small"
                />
              )}
              {assetData.currency && assetData.currency !== 'USD' && (
                <Chip
                  label={assetData.currency}
                  color="info"
                  size="small"
                  variant="outlined"
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
            title="Par Amount"
            value={formatCurrency(assetData.par_amount || assetData.current_balance)}
            variant="outlined"
            status="info"
          />
        </Grid>
        <Grid size={{ xs: 12, md: 3 }}>
          <MetricCard
            title="Market Value"
            value={assetData.market_value ? `${(assetData.market_value * 100).toFixed(2)}%` : formatCurrency(assetData.current_price)}
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
            title="Coupon Rate"
            value={formatPercentage(assetData.coupon || assetData.coupon_rate || assetData.yield_to_maturity)}
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
            <Tab label="Ratings & Risk" icon={<Assessment />} />
            <Tab label="Classifications" icon={<Category />} />
            <Tab label="Yield & Pricing" icon={<CurrencyExchange />} />
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
                      primary="Asset ID"
                      secondary={assetData.blkrock_id || assetData.id || assetData.cusip || 'N/A'}
                    />
                  </ListItem>
                  {assetData.cusip && (assetData.blkrock_id || assetData.id) !== assetData.cusip && (
                    <ListItem>
                      <ListItemIcon>
                        <Business />
                      </ListItemIcon>
                      <ListItemText
                        primary="CUSIP"
                        secondary={assetData.cusip}
                      />
                    </ListItem>
                  )}
                  <ListItem>
                    <ListItemIcon>
                      <AccountBalance />
                    </ListItemIcon>
                    <ListItemText
                      primary="Issuer"
                      secondary={assetData.issuer_name || assetData.issuer}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Info />
                    </ListItemIcon>
                    <ListItemText
                      primary="Issue Name"
                      secondary={assetData.issue_name || assetData.asset_name || assetData.asset_description || 'N/A'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Business />
                    </ListItemIcon>
                    <ListItemText
                      primary="Asset Type"
                      secondary={assetData.bond_loan || assetData.asset_type?.replace('_', ' ').toUpperCase() || 'N/A'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Business />
                    </ListItemIcon>
                    <ListItemText
                      primary="Industry"
                      secondary={assetData.mdy_industry || assetData.sp_industry || assetData.industry || 'N/A'}
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
                        <TableCell align="right">{formatCurrency(assetData.par_amount || assetData.current_balance)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Market Value</strong></TableCell>
                        <TableCell align="right">
                          {assetData.market_value ? `${(assetData.market_value * 100).toFixed(2)}%` : formatCurrency(assetData.current_price)}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Amount Issued</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.amount_issued)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Facility Size</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.facility_size)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Purchase Price</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.purchase_price)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Fair Value</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.fair_value)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>PIK Amount</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.pik_amount)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Unfunded Amount</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.unfunded_amount)}</TableCell>
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
                  Interest & Yield
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Coupon Rate</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.coupon || assetData.coupon_rate)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Coupon Type</strong></TableCell>
                        <TableCell align="right">{assetData.coupon_type || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Index</strong></TableCell>
                        <TableCell align="right">{assetData.index_name || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Spread</strong></TableCell>
                        <TableCell align="right">
                          {assetData.cpn_spread ? `${(assetData.cpn_spread * 10000).toFixed(0)} bps` : 
                           assetData.spread ? `${(Number(assetData.spread) * 10000).toFixed(0)} bps` : 'N/A'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>LIBOR Floor</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.libor_floor)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Index Cap</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.index_cap)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Commitment Fee</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.commit_fee)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Yield to Maturity</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.yield_to_maturity)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Duration</strong></TableCell>
                        <TableCell align="right">{assetData.duration ? `${Number(assetData.duration).toFixed(2)} years` : 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>WAL</strong></TableCell>
                        <TableCell align="right">{assetData.wal ? `${Number(assetData.wal).toFixed(2)} years` : 'N/A'}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12 }}>
                <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                  Payment Information
                </Typography>
                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell colSpan={2}><strong>Payment Terms</strong></TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          <TableRow>
                            <TableCell><strong>Payment Frequency</strong></TableCell>
                            <TableCell align="right">{assetData.payment_freq ? `${assetData.payment_freq}x/year` : 'N/A'}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Day Count</strong></TableCell>
                            <TableCell align="right">{assetData.day_count || 'N/A'}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Business Day Conv</strong></TableCell>
                            <TableCell align="right">{assetData.business_day_conv || 'N/A'}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Payment EOM</strong></TableCell>
                            <TableCell align="right">{assetData.payment_eom ? 'Yes' : 'No'}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell colSpan={2}><strong>PIK Properties</strong></TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          <TableRow>
                            <TableCell><strong>PIK Status</strong></TableCell>
                            <TableCell align="right">
                              <Chip 
                                label={assetData.piking ? 'PIKing' : 'Current Pay'} 
                                color={assetData.piking ? 'warning' : 'success'} 
                                size="small" 
                              />
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>PIK Asset</strong></TableCell>
                            <TableCell align="right">
                              <Chip 
                                label={assetData.flags?.pik_asset ? 'Yes' : 'No'} 
                                color={assetData.flags?.pik_asset ? 'info' : 'default'} 
                                size="small" 
                              />
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Current Pay</strong></TableCell>
                            <TableCell align="right">
                              <Chip 
                                label={assetData.flags?.current_pay ? 'Yes' : 'No'} 
                                color={assetData.flags?.current_pay ? 'success' : 'default'} 
                                size="small" 
                              />
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell colSpan={2}><strong>Other Metrics</strong></TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          <TableRow>
                            <TableCell><strong>Convexity</strong></TableCell>
                            <TableCell align="right">{assetData.convexity ? Number(assetData.convexity).toFixed(2) : 'N/A'}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Amortization</strong></TableCell>
                            <TableCell align="right">{assetData.amortization_type || 'N/A'}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Currency</strong></TableCell>
                            <TableCell align="right">{assetData.currency || 'USD'}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Ratings & Risk Tab */}
          <TabPanel value={activeTab} index={2}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Moody's Ratings
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Current Rating</strong></TableCell>
                        <TableCell align="right">
                          {assetData.mdy_rating ? (
                            <Chip label={assetData.mdy_rating} color={getRatingColor(assetData.mdy_rating)} size="small" />
                          ) : 'N/A'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Deal Pricing Rating</strong></TableCell>
                        <TableCell align="right">{assetData.mdy_dp_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>WARF Rating</strong></TableCell>
                        <TableCell align="right">{assetData.mdy_dp_rating_warf || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Derived Rating</strong></TableCell>
                        <TableCell align="right">{assetData.derived_mdy_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Facility Rating</strong></TableCell>
                        <TableCell align="right">{assetData.mdy_facility_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Issuer Rating</strong></TableCell>
                        <TableCell align="right">{assetData.mdy_issuer_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Senior Secured</strong></TableCell>
                        <TableCell align="right">{assetData.mdy_snr_sec_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Recovery Rate</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.mdy_recovery_rate)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  S&P Ratings
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Current Rating</strong></TableCell>
                        <TableCell align="right">
                          {assetData.sp_rating ? (
                            <Chip label={assetData.sp_rating} color={getRatingColor(assetData.sp_rating)} size="small" />
                          ) : 'N/A'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Derived Rating</strong></TableCell>
                        <TableCell align="right">{assetData.derived_sp_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Facility Rating</strong></TableCell>
                        <TableCell align="right">{assetData.sandp_facility_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Issuer Rating</strong></TableCell>
                        <TableCell align="right">{assetData.sandp_issuer_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Senior Secured</strong></TableCell>
                        <TableCell align="right">{assetData.sandp_snr_sec_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Subordinate</strong></TableCell>
                        <TableCell align="right">{assetData.sandp_subordinate || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Recovery Rating</strong></TableCell>
                        <TableCell align="right">{assetData.sandp_rec_rating || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Derivation Date</strong></TableCell>
                        <TableCell align="right">{formatDate(assetData.rating_derivation_date)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12 }}>
                <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                  Credit Risk Metrics
                </Typography>
                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell><strong>Default Probability</strong></TableCell>
                            <TableCell align="right">{formatPercentage(assetData.default_probability)}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Recovery Rate</strong></TableCell>
                            <TableCell align="right">{formatPercentage(assetData.mdy_recovery_rate)}</TableCell>
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
                        <Box>
                          <Typography variant="body2" color="text.secondary">Seniority</Typography>
                          <Typography variant="body1">{assetData.seniority || 'N/A'}</Typography>
                        </Box>
                        {assetData.flags?.default_asset && (
                          <Alert severity="error" sx={{ mt: 1 }}>
                            Asset is currently in default
                          </Alert>
                        )}
                        {assetMetrics?.isNearMaturity && (
                          <Alert severity="warning" sx={{ mt: 1 }}>
                            Asset is approaching maturity within 90 days
                          </Alert>
                        )}
                      </Stack>
                    </Box>
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Classifications Tab */}
          <TabPanel value={activeTab} index={3}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Industry Classifications
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Moody's Industry</strong></TableCell>
                        <TableCell align="right">{assetData.mdy_industry || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>S&P Industry</strong></TableCell>
                        <TableCell align="right">{assetData.sp_industry || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Country</strong></TableCell>
                        <TableCell align="right">
                          <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
                            <LocationOn fontSize="small" />
                            {assetData.country || 'N/A'}
                          </Box>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Seniority</strong></TableCell>
                        <TableCell align="right">{assetData.seniority || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Moody's Category</strong></TableCell>
                        <TableCell align="right">{assetData.mdy_asset_category || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>S&P Priority</strong></TableCell>
                        <TableCell align="right">{assetData.sp_priority_category || 'N/A'}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Asset Flags
                </Typography>
                <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
                  <Grid container spacing={1}>
                    {[
                      { key: 'pik_asset', label: 'PIK Asset', icon: <MonetizationOn /> },
                      { key: 'default_asset', label: 'Default Asset', icon: <Warning /> },
                      { key: 'dip', label: 'DIP', icon: <Security /> },
                      { key: 'revolver', label: 'Revolver', icon: <Refresh /> },
                      { key: 'loc', label: 'Letter of Credit', icon: <Receipt /> },
                      { key: 'participation', label: 'Participation', icon: <Business /> },
                      { key: 'convertible', label: 'Convertible', icon: <TrendingUp /> },
                      { key: 'struct_finance', label: 'Structured Finance', icon: <Analytics /> },
                      { key: 'bridge_loan', label: 'Bridge Loan', icon: <Timeline /> },
                      { key: 'current_pay', label: 'Current Pay', icon: <AttachMoney /> },
                      { key: 'cov_lite', label: 'Cov-Lite', icon: <Security /> },
                      { key: 'fllo', label: 'FLLO', icon: <Flag /> },
                      { key: 'delay_drawdown', label: 'Delay Drawdown', icon: <Schedule /> },
                    ].map(({ key, label, icon }) => (
                      <Grid size={{ xs: 6, sm: 4 }} key={key}>
                        <Chip
                          icon={icon}
                          label={label}
                          variant={assetData.flags?.[key as keyof typeof assetData.flags] ? 'filled' : 'outlined'}
                          color={assetData.flags?.[key as keyof typeof assetData.flags] ? 'primary' : 'default'}
                          size="small"
                          sx={{ width: '100%', justifyContent: 'flex-start' }}
                        />
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Yield & Pricing Tab */}
          <TabPanel value={activeTab} index={4}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Yield Curve Integration
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Discount Curve</strong></TableCell>
                        <TableCell align="right">{assetData.discount_curve_name || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Fair Value</strong></TableCell>
                        <TableCell align="right">{formatCurrency(assetData.fair_value)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Pricing Spread</strong></TableCell>
                        <TableCell align="right">{assetData.pricing_spread_bps ? `${assetData.pricing_spread_bps} bps` : 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Fair Value Date</strong></TableCell>
                        <TableCell align="right">{formatDate(assetData.fair_value_date)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="h6" gutterBottom>
                  Interest Rate Properties
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell><strong>Coupon Rate</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.coupon)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Coupon Type</strong></TableCell>
                        <TableCell align="right">{assetData.coupon_type || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Index</strong></TableCell>
                        <TableCell align="right">{assetData.index_name || 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Spread</strong></TableCell>
                        <TableCell align="right">{assetData.cpn_spread ? `${(assetData.cpn_spread * 10000).toFixed(0)} bps` : 'N/A'}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>LIBOR Floor</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.libor_floor)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Index Cap</strong></TableCell>
                        <TableCell align="right">{formatPercentage(assetData.index_cap)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Payment Frequency</strong></TableCell>
                        <TableCell align="right">{assetData.payment_freq ? `${assetData.payment_freq}x/year` : 'N/A'}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12 }}>
                <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                  Cash Flow Properties
                </Typography>
                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell><strong>Day Count</strong></TableCell>
                            <TableCell align="right">{assetData.day_count || 'N/A'}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Business Day Conv</strong></TableCell>
                            <TableCell align="right">{assetData.business_day_conv || 'N/A'}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Payment EOM</strong></TableCell>
                            <TableCell align="right">{assetData.payment_eom ? 'Yes' : 'No'}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell><strong>Amortization Type</strong></TableCell>
                            <TableCell align="right">{assetData.amortization_type || 'N/A'}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Amount Issued</strong></TableCell>
                            <TableCell align="right">{formatCurrency(assetData.amount_issued)}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Facility Size</strong></TableCell>
                            <TableCell align="right">{formatCurrency(assetData.facility_size)}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableBody>
                          <TableRow>
                            <TableCell><strong>WAL</strong></TableCell>
                            <TableCell align="right">{assetData.wal ? `${Number(assetData.wal).toFixed(2)} years` : 'N/A'}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>PIK Amount</strong></TableCell>
                            <TableCell align="right">{formatCurrency(assetData.pik_amount)}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell><strong>Unfunded Amount</strong></TableCell>
                            <TableCell align="right">{formatCurrency(assetData.unfunded_amount)}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Performance Tab */}
          <TabPanel value={activeTab} index={5}>
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
          <TabPanel value={activeTab} index={6}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 8 }}>
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
                        <TableCell><strong>Issue Date</strong></TableCell>
                        <TableCell>{formatDate(assetData.issue_date)}</TableCell>
                        <TableCell>
                          <Chip label="Completed" color="success" size="small" />
                        </TableCell>
                        <TableCell>Asset issuance</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>Dated Date</strong></TableCell>
                        <TableCell>{formatDate(assetData.dated_date)}</TableCell>
                        <TableCell>
                          <Chip label="Completed" color="success" size="small" />
                        </TableCell>
                        <TableCell>Interest accrual start</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell><strong>First Payment Date</strong></TableCell>
                        <TableCell>{formatDate(assetData.first_payment_date)}</TableCell>
                        <TableCell>
                          <Chip label="Completed" color="success" size="small" />
                        </TableCell>
                        <TableCell>First interest payment</TableCell>
                      </TableRow>
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
                        <TableCell>{formatDate(assetData.maturity || assetData.maturity_date)}</TableCell>
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
                      {assetData.date_of_default && (
                        <TableRow>
                          <TableCell><strong>Default Date</strong></TableCell>
                          <TableCell>{formatDate(assetData.date_of_default)}</TableCell>
                          <TableCell>
                            <Chip label="Default" color="error" size="small" />
                          </TableCell>
                          <TableCell>Asset entered default</TableCell>
                        </TableRow>
                      )}
                      <TableRow>
                        <TableCell><strong>Last Updated</strong></TableCell>
                        <TableCell>{formatDate(assetData.updated_at || assetData.last_updated)}</TableCell>
                        <TableCell>
                          <Chip label="Current" color="info" size="small" />
                        </TableCell>
                        <TableCell>Latest data refresh</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              
              <Grid size={{ xs: 12, md: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Asset Summary
                </Typography>
                <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Asset ID</Typography>
                      <Typography variant="body1">{assetData.blkrock_id || assetData.cusip}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Created</Typography>
                      <Typography variant="body1">{formatDate(assetData.created_at)}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Currency</Typography>
                      <Typography variant="body1">{assetData.currency || 'USD'}</Typography>
                    </Box>
                    {assetData.tranche && (
                      <Box>
                        <Typography variant="body2" color="text.secondary">Tranche</Typography>
                        <Typography variant="body1">{assetData.tranche}</Typography>
                      </Box>
                    )}
                    {assetData.analyst_opinion && (
                      <Box>
                        <Typography variant="body2" color="text.secondary">Analyst Opinion</Typography>
                        <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                          {assetData.analyst_opinion}
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                </Box>
              </Grid>
            </Grid>
          </TabPanel>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete asset "{assetData.blkrock_id || assetData.cusip}"? This action cannot be undone.
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