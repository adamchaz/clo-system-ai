import React, { useState, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Alert,
  LinearProgress,
  useTheme,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Security,
  Add,
  Refresh,
  Visibility,
  Timeline,
  PieChart,
  ShowChart,
  BarChart,
} from '@mui/icons-material';
import {
  useGetPortfoliosQuery,
  useGetPortfolioSummaryQuery,
  useGetSystemHealthQuery,
  useGetAssetStatsQuery,
} from '../store/api/cloApi';
import { useAuth } from '../hooks/useAuth';

interface PortfolioMetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  onClick?: () => void;
}

const PortfolioMetricCard: React.FC<PortfolioMetricCardProps> = ({ 
  title, 
  value, 
  subtitle, 
  icon, 
  color = 'primary.main',
  trend,
  onClick 
}) => {
  const theme = useTheme();
  
  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s ease-in-out',
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[8],
        } : {},
      }}
      onClick={onClick}
    >
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: `${color}15`,
              color,
              mr: 2,
            }}
          >
            {icon}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography
              variant="h4"
              component="div"
              sx={{
                fontWeight: 700,
                lineHeight: 1.2,
                color: 'text.primary',
              }}
            >
              {value}
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  mt: 1,
                  display: 'block',
                }}
              >
                {subtitle}
              </Typography>
            )}
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {trend.isPositive ? (
                  <TrendingUp sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                ) : (
                  <TrendingDown sx={{ fontSize: 16, color: 'error.main', mr: 0.5 }} />
                )}
                <Typography
                  variant="caption"
                  sx={{
                    color: trend.isPositive ? 'success.main' : 'error.main',
                    fontWeight: 600,
                  }}
                >
                  {trend.isPositive ? '+' : ''}{trend.value}%
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
                  vs last month
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const PortfolioManagerDashboard: React.FC = () => {
  const { user } = useAuth();
  const theme = useTheme();
  const [selectedPeriod, setSelectedPeriod] = useState('1M');

  // API queries
  const {
    data: portfoliosData,
    isLoading: portfoliosLoading,
    error: portfoliosError,
    refetch: refetchPortfolios,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const {} = useGetSystemHealthQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: assetStats,
  } = useGetAssetStatsQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  // Get first portfolio for summary (in real app, would be user's primary portfolio)
  const primaryPortfolioId = portfoliosData?.data?.[0]?.id;
  const {
    data: portfolioSummary,
  } = useGetPortfolioSummaryQuery(primaryPortfolioId || '', {
    skip: !primaryPortfolioId,
    refetchOnMountOrArgChange: true,
  });

  const handleRefresh = useCallback(() => {
    refetchPortfolios();
  }, [refetchPortfolios]);

  const handleViewPortfolios = useCallback(() => {
    // Navigate to portfolios page
    window.location.href = '/portfolios';
  }, []);

  const handleViewAssets = useCallback(() => {
    // Navigate to assets page
    window.location.href = '/assets';
  }, []);

  const handleViewAnalytics = useCallback(() => {
    // Navigate to analytics page
    window.location.href = '/analytics';
  }, []);

  // Calculate portfolio metrics
  const totalAUM = portfoliosData?.data?.reduce((sum, portfolio) => 
    sum + portfolio.current_portfolio_balance, 0) || 0;
  
  const activePortfolios = portfoliosData?.data?.filter(p => p.status === 'effective').length || 0;
  
  const avgPerformance = portfolioSummary?.risk_metrics ? 1.8 : 0; // Mock calculation

  if (portfoliosError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load portfolio data. Please check your connection and try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography
            variant="h4"
            component="h1"
            sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}
          >
            Portfolio Management
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            Monitor and manage your CLO portfolios, track performance, and analyze risk.
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              {user?.firstName?.[0]}{user?.lastName?.[0]}
            </Avatar>
            <Box>
              <Typography variant="body2" fontWeight={600}>
                {user?.firstName} {user?.lastName}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Portfolio Manager
              </Typography>
            </Box>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={portfoliosLoading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            sx={{ px: 3 }}
          >
            New Portfolio
          </Button>
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <PortfolioMetricCard
            title="Total AUM"
            value={`$${(totalAUM / 1000000).toFixed(1)}M`}
            subtitle="Assets under management"
            icon={<AccountBalance />}
            color={theme.palette.primary.main}
            trend={{ value: 2.3, isPositive: true }}
            onClick={handleViewPortfolios}
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <PortfolioMetricCard
            title="Active Portfolios"
            value={activePortfolios}
            subtitle="Currently managed"
            icon={<PieChart />}
            color={theme.palette.success.main}
            trend={{ value: 0, isPositive: true }}
            onClick={handleViewPortfolios}
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <PortfolioMetricCard
            title="Avg Performance"
            value={`+${avgPerformance.toFixed(1)}%`}
            subtitle="Monthly return"
            icon={<ShowChart />}
            color={theme.palette.info.main}
            trend={{ value: 1.2, isPositive: true }}
            onClick={handleViewAnalytics}
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <PortfolioMetricCard
            title="Total Assets"
            value={assetStats?.total_assets || 0}
            subtitle="Underlying securities"
            icon={<BarChart />}
            color={theme.palette.warning.main}
            onClick={handleViewAssets}
          />
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Portfolio Performance Chart Placeholder */}
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" fontWeight={600}>
                  Portfolio Performance
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {['1W', '1M', '3M', '1Y'].map((period) => (
                    <Button
                      key={period}
                      size="small"
                      variant={selectedPeriod === period ? 'contained' : 'outlined'}
                      onClick={() => setSelectedPeriod(period)}
                    >
                      {period}
                    </Button>
                  ))}
                </Box>
              </Box>
              
              <Paper
                sx={{
                  p: 4,
                  height: 300,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: 'background.paper',
                  border: 1,
                  borderColor: 'divider',
                  borderStyle: 'dashed',
                }}
              >
                <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
                  <Timeline sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                  <Typography variant="h6" gutterBottom>
                    Performance Chart Coming Soon
                  </Typography>
                  <Typography variant="body2">
                    Interactive portfolio performance visualization with risk metrics
                  </Typography>
                </Box>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Portfolio Quick View */}
        <Grid size={{ xs: 12, lg: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Active Portfolios
              </Typography>
              
              {portfoliosLoading ? (
                <Box sx={{ py: 2 }}>
                  <LinearProgress />
                  <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                    Loading portfolios...
                  </Typography>
                </Box>
              ) : portfoliosData?.data?.length === 0 ? (
                <Box sx={{ py: 4, textAlign: 'center' }}>
                  <AccountBalance sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    No portfolios found
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Create your first portfolio to get started
                  </Typography>
                </Box>
              ) : (
                <List dense>
                  {portfoliosData?.data?.slice(0, 5).map((portfolio) => (
                    <ListItem key={portfolio.id} divider>
                      <ListItemText
                        primary={
                          <Typography variant="body2" fontWeight={600}>
                            {portfolio.deal_name}
                          </Typography>
                        }
                        secondary={
                          <Box>
                            <Typography variant="caption" display="block">
                              ${((portfolio.current_portfolio_balance || 0) / 1000000).toFixed(1)}M
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                              <Chip
                                label={portfolio.status}
                                color={portfolio.status === 'effective' ? 'success' : 'default'}
                                size="small"
                                variant="outlined"
                              />
                              <Typography variant="caption" sx={{ ml: 1 }}>
                                {portfolio.current_asset_count} assets
                              </Typography>
                            </Box>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Tooltip title="View Portfolio">
                          <IconButton size="small">
                            <Visibility fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
              
              <Box sx={{ textAlign: 'center', mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                <Button size="small" onClick={handleViewPortfolios}>
                  View All Portfolios
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Risk Dashboard Summary */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Risk Overview
              </Typography>
              
              {portfolioSummary ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell align="right">Value</TableCell>
                        <TableCell align="right">Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>OC Tests</TableCell>
                        <TableCell align="right">
                          {Object.keys(portfolioSummary.risk_metrics.oc_ratios).length}
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={portfolioSummary.compliance_status.oc_tests_passing ? 'Passing' : 'Failed'}
                            color={portfolioSummary.compliance_status.oc_tests_passing ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>IC Tests</TableCell>
                        <TableCell align="right">
                          {Object.keys(portfolioSummary.risk_metrics.ic_ratios).length}
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={portfolioSummary.compliance_status.ic_tests_passing ? 'Passing' : 'Failed'}
                            color={portfolioSummary.compliance_status.ic_tests_passing ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Concentration</TableCell>
                        <TableCell align="right">
                          {Object.keys(portfolioSummary.risk_metrics.concentration_metrics).length}
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label={portfolioSummary.compliance_status.concentration_tests_passing ? 'Passing' : 'Failed'}
                            color={portfolioSummary.compliance_status.concentration_tests_passing ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>WAL</TableCell>
                        <TableCell align="right">
                          {portfolioSummary.risk_metrics.weighted_average_life?.toFixed(2) ?? 'N/A'} years
                        </TableCell>
                        <TableCell align="right">
                          <Chip
                            label="Normal"
                            color="success"
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Paper
                  sx={{
                    p: 3,
                    textAlign: 'center',
                    backgroundColor: 'background.paper',
                    border: 1,
                    borderColor: 'divider',
                    borderStyle: 'dashed',
                  }}
                >
                  <Security sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="body2" color="text.secondary">
                    Select a portfolio to view risk metrics
                  </Typography>
                </Paper>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Market Overview */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Market Overview
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">Credit Spreads</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TrendingDown sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                    <Typography variant="body2" fontWeight={600}>
                      425 bps
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">Default Rate</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TrendingUp sx={{ fontSize: 16, color: 'warning.main', mr: 0.5 }} />
                    <Typography variant="body2" fontWeight={600}>
                      2.1%
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">Recovery Rate</Typography>
                  <Typography variant="body2" fontWeight={600}>
                    67%
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">CLO Issuance YTD</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TrendingUp sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                    <Typography variant="body2" fontWeight={600}>
                      $89.2B
                    </Typography>
                  </Box>
                </Box>

                {portfolioSummary?.compliance_status.warnings.length && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    <Typography variant="caption">
                      {portfolioSummary.compliance_status.warnings.length} portfolio warning(s) require attention
                    </Typography>
                  </Alert>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PortfolioManagerDashboard;