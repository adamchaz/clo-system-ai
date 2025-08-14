import React, { useState, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  Tabs,
  Tab,
  IconButton,
  Chip,
  useTheme,
  Stack,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Analytics,
  TrendingUp,
  Assessment,
  ShowChart,
  Timeline,
  AccountBalance,
  Warning,
  CheckCircle,
  Speed,
  BarChart,
  PieChart,
  Refresh,
  GetApp,
  Calculate,
  ModelTraining,
  CompareArrows,
  TableChart,
} from '@mui/icons-material';
import { MetricCard } from '../components/common/UI';
import {
  useGetPortfoliosQuery,
  // useGetSystemHealthQuery,
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

const FinancialAnalystDashboard: React.FC = () => {
  const theme = useTheme();
  const [currentTab, setCurrentTab] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  // API queries
  const {
    data: portfoliosData,
    isLoading: portfoliosLoading,
    error: portfoliosError,
    refetch: refetchPortfolios,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  // System health monitoring (unused for now)
  // const {
  //   data: systemHealth,
  // } = useGetSystemHealthQuery(undefined, {
  //   pollingInterval: 30000,
  // });

  // Handlers
  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetchPortfolios();
      // Simulate additional data refresh
      setTimeout(() => setRefreshing(false), 1500);
    } catch (error) {
      console.error('Refresh failed:', error);
      setRefreshing(false);
    }
  }, [refetchPortfolios]);

  // Calculate analytics metrics (mock data for demonstration)
  const analyticsMetrics = {
    totalPortfolios: portfoliosData?.data?.length || 0,
    totalAUM: portfoliosData?.data?.reduce((sum, p) => sum + p.current_portfolio_balance, 0) || 0,
    avgVaR: 2.8,
    avgSharpeRatio: 1.24,
    correlationScore: 0.73,
    concentrationRisk: 'Medium',
    backTestAccuracy: 94.2,
    modelValidationScore: 'A',
  };

  const riskMetrics = [
    { label: 'Portfolio VaR (95%)', value: `${analyticsMetrics.avgVaR}%`, status: 'success' as const },
    { label: 'Concentration Risk', value: analyticsMetrics.concentrationRisk, status: 'warning' as const },
    { label: 'Model Accuracy', value: `${analyticsMetrics.backTestAccuracy}%`, status: 'success' as const },
    { label: 'Correlation Score', value: analyticsMetrics.correlationScore.toFixed(2), status: 'info' as const },
  ];

  const modelingTools = [
    {
      title: 'Waterfall Analysis',
      description: 'CLO payment waterfall modeling and optimization',
      icon: <Timeline />,
      path: '/waterfall',
      status: 'active',
      lastUpdated: '2 hours ago',
    },
    {
      title: 'Scenario Modeling',
      description: 'Monte Carlo simulations and stress testing',
      icon: <ModelTraining />,
      path: '/analytics/scenarios',
      status: 'active',
      lastUpdated: '30 minutes ago',
    },
    {
      title: 'Correlation Analysis',
      description: 'Asset correlation matrices and risk attribution',
      icon: <CompareArrows />,
      path: '/analytics/correlation',
      status: 'active',
      lastUpdated: '1 hour ago',
    },
    {
      title: 'CLO Structuring',
      description: 'Deal optimization and tranche analysis',
      icon: <Calculate />,
      path: '/analytics/structuring',
      status: 'beta',
      lastUpdated: '4 hours ago',
    },
  ];

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
            Financial Analytics Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Advanced CLO modeling, risk analytics, and quantitative analysis tools.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <IconButton 
            onClick={handleRefresh}
            disabled={refreshing}
            sx={{ 
              bgcolor: 'background.paper',
              border: 1,
              borderColor: 'divider',
            }}
          >
            <Refresh className={refreshing ? 'animate-spin' : ''} />
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            size="small"
          >
            Export Analysis
          </Button>
          <Button
            variant="contained"
            startIcon={<Analytics />}
            size="small"
          >
            New Model
          </Button>
        </Box>
      </Box>

      {refreshing && <LinearProgress sx={{ mb: 2 }} />}

      {/* Key Analytics Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Total AUM"
            value={`$${(analyticsMetrics.totalAUM / 1000000).toFixed(1)}M`}
            subtitle={`${analyticsMetrics.totalPortfolios} portfolios`}
            icon={<AccountBalance />}
            color={theme.palette.primary.main}
            trend={{ value: 2.3, isPositive: true, period: 'vs last month' }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Portfolio VaR"
            value={`${analyticsMetrics.avgVaR}%`}
            subtitle="95% confidence level"
            icon={<Assessment />}
            color={theme.palette.error.main}
            trend={{ value: -0.2, isPositive: true, period: 'improvement' }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Model Accuracy"
            value={`${analyticsMetrics.backTestAccuracy}%`}
            subtitle="Backtesting performance"
            icon={<Speed />}
            color={theme.palette.success.main}
            trend={{ value: 1.8, isPositive: true, period: 'vs benchmark' }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Avg Sharpe Ratio"
            value={analyticsMetrics.avgSharpeRatio.toFixed(2)}
            subtitle="Risk-adjusted returns"
            icon={<TrendingUp />}
            color={theme.palette.info.main}
            trend={{ value: 0.12, isPositive: true, period: 'portfolio avg' }}
          />
        </Grid>
      </Grid>

      {/* Analytics Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="financial analytics tabs">
          <Tab label="Modeling Tools" />
          <Tab label="Risk Analytics" />
          <Tab label="Portfolio Analysis" />
          <Tab label="Model Validation" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Modeling Tools Tab */}
        <Grid container spacing={3}>
          {modelingTools.map((tool, index) => (
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6, lg: 3 }} key={index}>
              <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { elevation: 4 } }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        backgroundColor: `${theme.palette.primary.main}15`,
                        color: theme.palette.primary.main,
                        mr: 2,
                      }}
                    >
                      {tool.icon}
                    </Box>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" fontWeight={600}>
                        {tool.title}
                      </Typography>
                      <Chip 
                        label={tool.status} 
                        size="small" 
                        color={tool.status === 'active' ? 'success' : 'default'}
                        sx={{ mt: 0.5 }}
                      />
                    </Box>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {tool.description}
                  </Typography>
                  
                  <Typography variant="caption" color="text.secondary">
                    Last updated: {tool.lastUpdated}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Quick Actions */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>
          <Stack direction="row" spacing={2}>
            <Button variant="outlined" startIcon={<Calculate />}>
              Run Waterfall
            </Button>
            <Button variant="outlined" startIcon={<ModelTraining />}>
              New Scenario
            </Button>
            <Button variant="outlined" startIcon={<CompareArrows />}>
              Correlation Matrix
            </Button>
            <Button variant="outlined" startIcon={<TableChart />}>
              Export Models
            </Button>
          </Stack>
        </Box>
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {/* Risk Analytics Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Metrics Overview
                </Typography>
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
                    <BarChart sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                    <Typography variant="h6" gutterBottom>
                      Risk Analytics Chart
                    </Typography>
                    <Typography variant="body2">
                      VaR analysis, stress testing, and risk attribution visualization
                    </Typography>
                  </Box>
                </Paper>
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Summary
                </Typography>
                <Stack spacing={3}>
                  {riskMetrics.map((metric, index) => (
                    <Box key={index}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        {metric.status === 'success' && <CheckCircle color="success" sx={{ mr: 1, fontSize: 20 }} />}
                        {metric.status === 'warning' && <Warning color="warning" sx={{ mr: 1, fontSize: 20 }} />}
                        {metric.status === 'info' && <Analytics color="info" sx={{ mr: 1, fontSize: 20 }} />}
                        <Typography variant="body2" fontWeight={600}>
                          {metric.label}
                        </Typography>
                      </Box>
                      <Typography variant="h6" sx={{ ml: 3 }}>
                        {metric.value}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Portfolio Analysis Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Portfolio Distribution
                </Typography>
                <Paper
                  sx={{
                    p: 3,
                    height: 250,
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
                    <PieChart sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                    <Typography variant="body1" gutterBottom>
                      Portfolio Analysis Chart
                    </Typography>
                    <Typography variant="body2">
                      Sector allocation and performance attribution
                    </Typography>
                  </Box>
                </Paper>
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Analytics
                </Typography>
                <Paper
                  sx={{
                    p: 3,
                    height: 250,
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
                    <ShowChart sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                    <Typography variant="body1" gutterBottom>
                      Performance Trends
                    </Typography>
                    <Typography variant="body2">
                      Historical performance and attribution analysis
                    </Typography>
                  </Box>
                </Paper>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Portfolio Summary */}
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Portfolio Summary
            </Typography>
            {portfoliosLoading ? (
              <LinearProgress />
            ) : (
              <Grid container spacing={3}>
                <Grid {...({ item: true } as any)} size={{ xs: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Total Portfolios
                  </Typography>
                  <Typography variant="h5" fontWeight={600}>
                    {analyticsMetrics.totalPortfolios}
                  </Typography>
                </Grid>
                <Grid {...({ item: true } as any)} size={{ xs: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Active Portfolios
                  </Typography>
                  <Typography variant="h5" fontWeight={600}>
                    {portfoliosData?.data?.filter(p => p.status === 'effective').length || 0}
                  </Typography>
                </Grid>
                <Grid {...({ item: true } as any)} size={{ xs: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Total Assets
                  </Typography>
                  <Typography variant="h5" fontWeight={600}>
                    {portfoliosData?.data?.reduce((sum, p) => sum + p.current_asset_count, 0) || 0}
                  </Typography>
                </Grid>
                <Grid {...({ item: true } as any)} size={{ xs: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Avg. Deal Size
                  </Typography>
                  <Typography variant="h5" fontWeight={600}>
                    $
                    {portfoliosData?.data?.length 
                      ? ((portfoliosData.data.reduce((sum, p) => sum + p.deal_size, 0) / portfoliosData.data.length) / 1000000).toFixed(1)
                      : '0'
                    }M
                  </Typography>
                </Grid>
              </Grid>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Model Validation Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Performance
                </Typography>
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">Backtesting Accuracy</Typography>
                    <Typography variant="body2" fontWeight={600} color="success.main">
                      {analyticsMetrics.backTestAccuracy}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">Validation Score</Typography>
                    <Chip label={analyticsMetrics.modelValidationScore} color="success" size="small" />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2">Last Validation</Typography>
                    <Typography variant="body2" color="text.secondary">
                      2 days ago
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Validation Status
                </Typography>
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CheckCircle color="success" sx={{ mr: 1 }} />
                    <Typography variant="body2">
                      VaR Models: Validated
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CheckCircle color="success" sx={{ mr: 1 }} />
                    <Typography variant="body2">
                      Waterfall Models: Current
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Warning color="warning" sx={{ mr: 1 }} />
                    <Typography variant="body2">
                      Scenario Models: Review Required
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
};

export default FinancialAnalystDashboard;