import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  LinearProgress,
  useTheme,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  Stack,
} from '@mui/material';
import {
  Assessment,
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Security,
  Warning,
  CheckCircle,
  Timeline,
  Refresh,
  GetApp,
  FilterList,
  PieChart,
  BarChart,
  ShowChart,
  MonetizationOn,
  Schedule,
  InfoOutlined,
  NotificationsActive,
} from '@mui/icons-material';
import { MetricCard } from '../common/UI';
import {
  useGetPortfoliosQuery,
  useGetPerformanceHistoryQuery,
} from '../../store/api/cloApi';

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

const PortfolioDashboard: React.FC = () => {
  const theme = useTheme();
  const [currentTab, setCurrentTab] = useState(0);
  const [selectedPortfolio, setSelectedPortfolio] = useState<string>('all');

  // API queries
  const {
    data: portfoliosData,
    isLoading: portfoliosLoading,
    error: portfoliosError,
    refetch: refetchPortfolios,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: performanceData,
    isLoading: performanceLoading,
  } = useGetPerformanceHistoryQuery(
    selectedPortfolio !== 'all' 
      ? { dealId: selectedPortfolio, period: '1Y', benchmark: 'market' }
      : { dealId: '', period: '1Y', benchmark: 'market' },
    {
      skip: selectedPortfolio === 'all',
      refetchOnMountOrArgChange: true,
    }
  );

  // Handlers
  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const handlePortfolioSelect = useCallback((portfolioId: string) => {
    setSelectedPortfolio(portfolioId);
  }, []);

  // Mock real-time data generation
  const generateMockMetrics = useMemo(() => {
    if (!portfoliosData?.data) return null;

    const portfolios = portfoliosData.data;
    const totalAUM = portfolios.reduce((sum, p) => sum + p.current_portfolio_balance, 0);
    const totalAssets = portfolios.reduce((sum, p) => sum + p.current_asset_count, 0);
    const activePortfolios = portfolios.filter(p => p.status === 'effective').length;
    
    // Mock performance calculations
    const avgReturn = 7.2 + (Math.random() * 2 - 1); // 6.2% to 8.2%
    const volatility = 8.5 + (Math.random() * 3 - 1.5); // 7% to 10%
    const sharpeRatio = avgReturn / volatility;
    
    return {
      totalAUM,
      totalAssets,
      activePortfolios,
      avgReturn: Number(avgReturn.toFixed(2)),
      volatility: Number(volatility.toFixed(2)),
      sharpeRatio: Number(sharpeRatio.toFixed(2)),
      totalPortfolios: portfolios.length,
    };
  }, [portfoliosData]);

  // Mock recent activity data
  const recentActivity = [
    {
      id: '1',
      type: 'trade',
      description: 'Asset purchase: Senior Secured Loan',
      amount: '$2.5M',
      portfolio: 'MAG CLO XIV-R',
      timestamp: '2 minutes ago',
      status: 'completed',
      icon: <MonetizationOn color="success" />,
    },
    {
      id: '2', 
      type: 'trigger',
      description: 'OC Trigger: Class A - Passed',
      portfolio: 'MAG CLO XV',
      timestamp: '15 minutes ago',
      status: 'info',
      icon: <CheckCircle color="success" />,
    },
    {
      id: '3',
      type: 'alert',
      description: 'Concentration Alert: Technology sector',
      portfolio: 'MAG CLO XIII-R',
      timestamp: '1 hour ago',
      status: 'warning',
      icon: <Warning color="warning" />,
    },
    {
      id: '4',
      type: 'waterfall',
      description: 'Payment Date Processing Complete',
      portfolio: 'MAG CLO XIV-R',
      timestamp: '3 hours ago',
      status: 'completed',
      icon: <Timeline color="primary" />,
    },
    {
      id: '5',
      type: 'report',
      description: 'Monthly Performance Report Generated',
      portfolio: 'All Portfolios',
      timestamp: '1 day ago', 
      status: 'completed',
      icon: <Assessment color="info" />,
    },
  ];

  // Mock top performing assets
  const topAssets = [
    { name: 'Acme Corp Term Loan', return: 12.4, allocation: 3.2, rating: 'B+' },
    { name: 'Global Industries Bond', return: 9.8, allocation: 2.8, rating: 'BB-' },
    { name: 'TechCo Senior Note', return: 8.9, allocation: 2.1, rating: 'B' },
    { name: 'Energy Partners Loan', return: 8.2, allocation: 1.9, rating: 'B+' },
    { name: 'Retail Chain Facility', return: 7.6, allocation: 1.7, rating: 'BB' },
  ];

  // Mock risk alerts
  const riskAlerts = [
    {
      level: 'high',
      title: 'Concentration Risk',
      description: 'Technology sector exposure at 32% (limit: 30%)',
      portfolio: 'MAG CLO XV',
      action: 'Reduce exposure by $5M',
    },
    {
      level: 'medium', 
      title: 'Credit Migration',
      description: '3 assets downgraded in last 30 days',
      portfolio: 'MAG CLO XIII-R',
      action: 'Review credit quality',
    },
    {
      level: 'low',
      title: 'Liquidity Notice',
      description: 'Low trading volume on 2 positions',
      portfolio: 'MAG CLO XIV-R',
      action: 'Monitor closely',
    },
  ];

  if (portfoliosLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress sx={{ mb: 2 }} />
        <Typography variant="body2" color="text.secondary" textAlign="center">
          Loading portfolio dashboard...
        </Typography>
      </Box>
    );
  }

  if (portfoliosError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load portfolio data. Please refresh and try again.
      </Alert>
    );
  }

  if (!generateMockMetrics) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No portfolio data available.
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
            Portfolio Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time portfolio metrics, performance tracking, and risk monitoring.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <IconButton onClick={refetchPortfolios} color="primary">
            <Refresh />
          </IconButton>
          <Button variant="outlined" startIcon={<FilterList />}>
            Filter
          </Button>
          <Button variant="contained" startIcon={<GetApp />}>
            Export
          </Button>
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Total AUM"
            value={`$${(generateMockMetrics.totalAUM / 1000000).toFixed(1)}M`}
            subtitle={`${generateMockMetrics.totalPortfolios} portfolios`}
            icon={<AccountBalance />}
            color={theme.palette.primary.main}
            trend={{ value: 3.2, isPositive: true, period: 'vs last month' }}
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Active Portfolios"
            value={generateMockMetrics.activePortfolios.toString()}
            subtitle={`${generateMockMetrics.totalAssets} total assets`}
            icon={<Assessment />}
            color={theme.palette.success.main}
            trend={{ value: 0, isPositive: true, period: 'stable' }}
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Avg Return"
            value={`${generateMockMetrics.avgReturn}%`}
            subtitle="Year to date"
            icon={<TrendingUp />}
            color={theme.palette.info.main}
            trend={{ value: 1.8, isPositive: true, period: 'vs benchmark' }}
          />
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Risk Score"
            value={generateMockMetrics.sharpeRatio.toString()}
            subtitle="Sharpe ratio"
            icon={<Security />}
            color={theme.palette.warning.main}
            trend={{ value: 0.1, isPositive: true, period: 'improving' }}
          />
        </Grid>
      </Grid>

      {/* Content Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="dashboard tabs">
          <Tab label="Overview" />
          <Tab label="Performance" />
          <Tab label="Risk Monitoring" />
          <Tab label="Activity Feed" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Overview Tab */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Portfolio Performance Trends
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
                    <ShowChart sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                    <Typography variant="h6" gutterBottom>
                      Performance Chart
                    </Typography>
                    <Typography variant="body2">
                      Real-time portfolio performance visualization
                    </Typography>
                  </Box>
                </Paper>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Top Performing Assets
                </Typography>
                <List dense>
                  {topAssets.map((asset, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: '0.75rem' }}>
                          {asset.rating}
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="body2" fontWeight={600}>
                            {asset.name}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="caption" color="success.main">
                              +{asset.return}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              ({asset.allocation}% allocation)
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {/* Performance Tab */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, lg: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Portfolio Performance Breakdown
                </Typography>
                <Paper
                  sx={{
                    p: 4,
                    height: 400,
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
                      Performance Analytics
                    </Typography>
                    <Typography variant="body2">
                      Portfolio returns, risk metrics, and benchmark comparisons
                    </Typography>
                  </Box>
                </Paper>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, lg: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Summary
                </Typography>
                <Stack spacing={3}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      1 Month Return
                    </Typography>
                    <Typography variant="h5" fontWeight={600} color="success.main">
                      +{(generateMockMetrics.avgReturn * 0.3).toFixed(1)}%
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      3 Month Return
                    </Typography>
                    <Typography variant="h5" fontWeight={600} color="success.main">
                      +{(generateMockMetrics.avgReturn * 0.8).toFixed(1)}%
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      YTD Return
                    </Typography>
                    <Typography variant="h5" fontWeight={600} color="success.main">
                      +{generateMockMetrics.avgReturn}%
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Volatility
                    </Typography>
                    <Typography variant="h5" fontWeight={600} color="info.main">
                      {generateMockMetrics.volatility}%
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Risk Monitoring Tab */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Alerts & Monitoring
                </Typography>
                <Stack spacing={2}>
                  {riskAlerts.map((alert, index) => (
                    <Alert
                      key={index}
                      severity={alert.level === 'high' ? 'error' : alert.level === 'medium' ? 'warning' : 'info'}
                      sx={{ borderRadius: 2 }}
                    >
                      <Box>
                        <Typography variant="body2" fontWeight={600} gutterBottom>
                          {alert.title} - {alert.portfolio}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {alert.description}
                        </Typography>
                        <Typography variant="caption" fontWeight={500}>
                          Recommended Action: {alert.action}
                        </Typography>
                      </Box>
                    </Alert>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Metrics
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Portfolio VaR (1-day, 95%)
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color="error.main">
                      -$1.2M
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={75}
                      color="error"
                      sx={{ mt: 1, height: 6, borderRadius: 3 }}
                    />
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Maximum Drawdown
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color="warning.main">
                      -3.2%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={40}
                      color="warning"
                      sx={{ mt: 1, height: 6, borderRadius: 3 }}
                    />
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Correlation Risk Score
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color="info.main">
                      0.68
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={68}
                      color="info"
                      sx={{ mt: 1, height: 6, borderRadius: 3 }}
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Activity Feed Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <List>
              {recentActivity.map((activity, index) => (
                <React.Fragment key={activity.id}>
                  <ListItem alignItems="flex-start">
                    <ListItemIcon sx={{ mt: 1 }}>
                      {activity.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontWeight={600}>
                            {activity.description}
                          </Typography>
                          {activity.amount && (
                            <Typography variant="body2" color="success.main" fontWeight={600}>
                              {activity.amount}
                            </Typography>
                          )}
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            {activity.portfolio} • {activity.timestamp}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < recentActivity.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default PortfolioDashboard;