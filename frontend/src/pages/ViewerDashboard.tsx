import React, { useState, useCallback } from 'react';
import {
  Box,
  Grid,
  Typography,
  Button,
  Tabs,
  Tab,
  Alert,
  useTheme,
} from '@mui/material';
import {
  Visibility,
  Assessment,
  BarChart,
  TrendingUp,
  AccountBalance,
  GetApp,
  Info,
} from '@mui/icons-material';
import { MetricCard } from '../components/common/UI';
import { 
  PortfolioSummaryView, 
  BasicReportsView, 
  PerformanceOverview 
} from '../components/viewer';
import {
  useGetPortfoliosQuery,
} from '../store/api/cloApi';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

const ViewerDashboard: React.FC = () => {
  const theme = useTheme();
  const [currentTab, setCurrentTab] = useState(0);

  // API queries - read-only access
  const {
    data: portfoliosData,
    error: portfoliosError,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  // Handlers
  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  // Calculate summary metrics (read-only view)
  const summaryMetrics = {
    totalPortfolios: portfoliosData?.data?.length || 0,
    totalAUM: portfoliosData?.data?.reduce((sum, p) => sum + p.current_portfolio_balance, 0) || 0,
    activePortfolios: portfoliosData?.data?.filter(p => p.status === 'effective').length || 0,
    totalAssets: portfoliosData?.data?.reduce((sum, p) => sum + p.current_asset_count, 0) || 0,
    avgPerformance: 7.8, // Mock data - would come from backend
    avgRating: 'A-', // Mock data
  };


  if (portfoliosError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load dashboard data. Please check your connection and try again.
      </Alert>
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
            Portfolio Overview
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Read-only access to portfolio data, reports, and performance metrics.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            size="small"
          >
            Export Reports
          </Button>
          <Button
            variant="contained"
            startIcon={<Visibility />}
            size="small"
          >
            View Details
          </Button>
        </Box>
      </Box>

      {/* Key Summary Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Total Portfolios"
            value={summaryMetrics.totalPortfolios}
            subtitle={`${summaryMetrics.activePortfolios} active`}
            icon={<AccountBalance />}
            color={theme.palette.primary.main}
            trend={{ value: 0, isPositive: true, period: 'stable' }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Total AUM"
            value={`$${(summaryMetrics.totalAUM / 1000000).toFixed(1)}M`}
            subtitle={`${summaryMetrics.totalAssets} total assets`}
            icon={<Assessment />}
            color={theme.palette.success.main}
            trend={{ value: 2.1, isPositive: true, period: 'vs last month' }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Avg Performance"
            value={`${summaryMetrics.avgPerformance}%`}
            subtitle="Year to date return"
            icon={<TrendingUp />}
            color={theme.palette.info.main}
            trend={{ value: 1.2, isPositive: true, period: 'vs benchmark' }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Avg Rating"
            value={summaryMetrics.avgRating}
            subtitle="Weighted portfolio rating"
            icon={<BarChart />}
            color={theme.palette.warning.main}
            trend={{ value: 0, isPositive: true, period: 'stable' }}
          />
        </Grid>
      </Grid>

      {/* Information Notice */}
      <Alert severity="info" sx={{ mb: 4 }} icon={<Info />}>
        <Typography variant="body2">
          <strong>Viewer Access:</strong> You have read-only access to portfolio data and reports. 
          Contact your administrator for additional permissions or to request specific reports.
        </Typography>
      </Alert>

      {/* Content Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="viewer dashboard tabs">
          <Tab label="Portfolio Summary" />
          <Tab label="Available Reports" />
          <Tab label="Performance Overview" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Portfolio Summary Tab */}
        <PortfolioSummaryView showAllPortfolios={true} />
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {/* Available Reports Tab */}
        <BasicReportsView />
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Performance Overview Tab */}
        <PerformanceOverview timeframe="YTD" />
      </TabPanel>
    </Box>
  );
};

export default ViewerDashboard;