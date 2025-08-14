import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Tabs,
  Tab,
  useTheme,
  Divider,
  Stack,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  ShowChart,
  Timeline,
  BarChart,
  PieChart,
  Assessment,
  GetApp,
  Refresh,
  CompareArrows,
  CheckCircle,
} from '@mui/icons-material';
// import { format, subDays } from 'date-fns';
import {
  useGetPortfoliosQuery,
  useGetPortfolioSummaryQuery,
  useGetPerformanceHistoryQuery,
} from '../../store/api/cloApi';

interface PerformanceTrackerProps {
  portfolioId?: string;
  onPortfolioChange?: (portfolioId: string) => void;
}

interface PerformanceMetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
  trend?: {
    value: number;
    isPositive: boolean;
    period?: string;
  };
  benchmark?: {
    value: number;
    label: string;
  };
}

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

const PerformanceMetricCard: React.FC<PerformanceMetricCardProps> = ({ 
  title, 
  value, 
  subtitle, 
  icon, 
  color = 'primary.main',
  trend,
  benchmark 
}) => {
  
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
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
                mb: 0.5,
              }}
            >
              {value}
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  mt: 0.5,
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
                  {trend.period || 'vs last period'}
                </Typography>
              </Box>
            )}
            {benchmark && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <CompareArrows sx={{ fontSize: 16, color: 'text.secondary', mr: 0.5 }} />
                <Typography variant="caption" color="text.secondary">
                  {benchmark.label}: {benchmark.value > 0 ? '+' : ''}{benchmark.value}%
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const PerformanceTracker: React.FC<PerformanceTrackerProps> = ({
  portfolioId: initialPortfolioId,
  onPortfolioChange,
}) => {
  const theme = useTheme();
  const [selectedPortfolio, setSelectedPortfolio] = useState(initialPortfolioId || 'all');
  const [selectedPeriod, setSelectedPeriod] = useState('1Y');
  const [currentTab, setCurrentTab] = useState(0);
  const [benchmarkType, setBenchmarkType] = useState('market');

  // API queries
  const {
    data: portfoliosData,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: portfolioSummary,
  } = useGetPortfolioSummaryQuery(
    selectedPortfolio !== 'all' ? selectedPortfolio : portfoliosData?.data?.[0]?.id || '',
    {
      skip: !portfoliosData?.data?.length || selectedPortfolio === 'all',
      refetchOnMountOrArgChange: true,
    }
  );

  const {} = useGetPerformanceHistoryQuery({
    dealId: selectedPortfolio !== 'all' ? selectedPortfolio : portfoliosData?.data?.[0]?.id || '',
    period: selectedPeriod,
  }, {
    skip: !portfoliosData?.data?.length || selectedPortfolio === 'all',
  });

  // Handlers
  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const handlePortfolioChange = useCallback((portfolioId: string) => {
    setSelectedPortfolio(portfolioId);
    onPortfolioChange?.(portfolioId);
  }, [onPortfolioChange]);

  const handlePeriodChange = useCallback((period: string) => {
    setSelectedPeriod(period);
  }, []);

  const handleRefresh = useCallback(() => {
    // Trigger refetch of all data
    window.location.reload();
  }, []);

  // Calculate performance metrics (mock data for demonstration)
  const performanceMetrics = useMemo(() => {
    if (!portfolioSummary) {
      return {
        totalReturn: 0,
        annualizedReturn: 0,
        volatility: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        beta: 0,
        alpha: 0,
        informationRatio: 0,
      };
    }

    // Mock calculations based on portfolio data
    const totalReturn = 8.7;
    const annualizedReturn = 12.4;
    const volatility = 14.2;
    const riskFreeRate = 3.5;
    const sharpeRatio = (annualizedReturn - riskFreeRate) / volatility;

    return {
      totalReturn,
      annualizedReturn,
      volatility,
      sharpeRatio,
      maxDrawdown: -5.8,
      beta: 0.89,
      alpha: 2.1,
      informationRatio: 0.74,
    };
  }, [portfolioSummary]);

  // Generate mock benchmark data
  const benchmarkData = useMemo(() => {
    const benchmarks = {
      market: { name: 'S&P 500', return: 10.2, volatility: 16.1 },
      clo: { name: 'CLO Index', return: 11.8, volatility: 12.7 },
      credit: { name: 'Credit Index', return: 9.4, volatility: 13.9 },
      custom: { name: 'Custom Benchmark', return: 10.8, volatility: 15.2 },
    };
    
    return benchmarks[benchmarkType as keyof typeof benchmarks] || benchmarks.market;
  }, [benchmarkType]);

  // Mock historical performance data (for future chart integration)
  // const mockPerformanceData = useMemo(() => {
  //   const periods = selectedPeriod === '1M' ? 30 : selectedPeriod === '3M' ? 90 : 
  //                  selectedPeriod === '6M' ? 180 : selectedPeriod === '1Y' ? 365 : 1095;
  //   
  //   const data = [];
  //   let cumReturn = 0;
  //   
  //   for (let i = periods; i >= 0; i--) {
  //     const date = subDays(new Date(), i);
  //     const dailyReturn = (Math.random() - 0.48) * 0.02; // Slight positive bias
  //     cumReturn += dailyReturn;
  //     
  //     data.push({
  //       date: format(date, 'yyyy-MM-dd'),
  //       portfolio: (1 + cumReturn) * 100,
  //       benchmark: (1 + cumReturn * 0.9 + Math.random() * 0.01) * 100, // Benchmark slightly different
  //     });
  //   }
  //   
  //   return data;
  // }, [selectedPeriod]);

  // Risk attribution data (mock)
  const riskAttributionData = [
    { category: 'Credit Risk', contribution: 45.2, allocation: 42.8 },
    { category: 'Interest Rate Risk', contribution: 28.7, allocation: 31.2 },
    { category: 'Sector Risk', contribution: 15.1, allocation: 16.8 },
    { category: 'Geographic Risk', contribution: 8.3, allocation: 7.4 },
    { category: 'Currency Risk', contribution: 2.7, allocation: 1.8 },
  ];

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
            Performance Analytics
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Advanced portfolio performance tracking, risk analytics, and benchmark comparison.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Portfolio</InputLabel>
            <Select
              value={selectedPortfolio}
              onChange={(e) => handlePortfolioChange(e.target.value)}
              label="Portfolio"
            >
              <MenuItem value="all">All Portfolios</MenuItem>
              {portfoliosData?.data?.map((portfolio) => (
                <MenuItem key={portfolio.id} value={portfolio.id}>
                  {portfolio.deal_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Benchmark</InputLabel>
            <Select
              value={benchmarkType}
              onChange={(e) => setBenchmarkType(e.target.value)}
              label="Benchmark"
            >
              <MenuItem value="market">S&P 500</MenuItem>
              <MenuItem value="clo">CLO Index</MenuItem>
              <MenuItem value="credit">Credit Index</MenuItem>
              <MenuItem value="custom">Custom</MenuItem>
            </Select>
          </FormControl>
          
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
          
          <Button
            variant="contained"
            startIcon={<GetApp />}
          >
            Export Report
          </Button>
        </Box>
      </Box>

      {/* Performance Period Selector */}
      <Box sx={{ display: 'flex', gap: 1, mb: 4 }}>
        {['1M', '3M', '6M', '1Y', '3Y'].map((period) => (
          <Button
            key={period}
            size="small"
            variant={selectedPeriod === period ? 'contained' : 'outlined'}
            onClick={() => handlePeriodChange(period)}
            sx={{ minWidth: 60 }}
          >
            {period}
          </Button>
        ))}
      </Box>

      {/* Key Performance Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <PerformanceMetricCard
            title="Total Return"
            value={`${performanceMetrics.totalReturn.toFixed(1)}%`}
            subtitle={`${selectedPeriod} period`}
            icon={<ShowChart />}
            color={theme.palette.success.main}
            trend={{ 
              value: 2.3, 
              isPositive: true, 
              period: 'vs last period' 
            }}
            benchmark={{ 
              value: benchmarkData.return, 
              label: benchmarkData.name 
            }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <PerformanceMetricCard
            title="Annualized Return"
            value={`${performanceMetrics.annualizedReturn.toFixed(1)}%`}
            subtitle="Risk-adjusted"
            icon={<TrendingUp />}
            color={theme.palette.primary.main}
            trend={{ 
              value: 1.8, 
              isPositive: true, 
              period: 'vs benchmark' 
            }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <PerformanceMetricCard
            title="Sharpe Ratio"
            value={performanceMetrics.sharpeRatio.toFixed(2)}
            subtitle="Risk-adjusted performance"
            icon={<Assessment />}
            color={theme.palette.info.main}
            trend={{ 
              value: 0.12, 
              isPositive: true, 
              period: 'improvement' 
            }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <PerformanceMetricCard
            title="Max Drawdown"
            value={`${performanceMetrics.maxDrawdown.toFixed(1)}%`}
            subtitle="Peak to trough"
            icon={<TrendingDown />}
            color={theme.palette.warning.main}
            trend={{ 
              value: -0.8, 
              isPositive: true, 
              period: 'vs last period' 
            }}
          />
        </Grid>
      </Grid>

      {/* Performance Analysis Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="performance analysis tabs">
          <Tab label="Performance Chart" />
          <Tab label="Risk Metrics" />
          <Tab label="Attribution" />
          <Tab label="Benchmark Analysis" />
          <Tab label="Historical Stats" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Performance Chart Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Cumulative Performance
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
                    <Timeline sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                    <Typography variant="h6" gutterBottom>
                      Performance Chart Integration
                    </Typography>
                    <Typography variant="body2">
                      Interactive line chart showing portfolio vs benchmark performance over time
                    </Typography>
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      Chart.js or Recharts integration required
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
                  Performance Summary
                </Typography>
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Best Month</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <TrendingUp color="success" sx={{ mr: 0.5, fontSize: 16 }} />
                      <Typography variant="body2" fontWeight={600} color="success.main">
                        +4.2%
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Worst Month</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <TrendingDown color="error" sx={{ mr: 0.5, fontSize: 16 }} />
                      <Typography variant="body2" fontWeight={600} color="error.main">
                        -2.1%
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Volatility</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {performanceMetrics.volatility.toFixed(1)}%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Win Rate</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      68.4%
                    </Typography>
                  </Box>
                  
                  <Divider />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">vs {benchmarkData.name}</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <TrendingUp color="success" sx={{ mr: 0.5, fontSize: 16 }} />
                      <Typography variant="body2" fontWeight={600} color="success.main">
                        +{(performanceMetrics.annualizedReturn - benchmarkData.return).toFixed(1)}%
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Beta</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {performanceMetrics.beta.toFixed(2)}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Alpha</Typography>
                    <Typography variant="body2" fontWeight={600} color="success.main">
                      {performanceMetrics.alpha.toFixed(1)}%
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {/* Risk Metrics Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Metrics Overview
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell align="right">Value</TableCell>
                        <TableCell align="right">Benchmark</TableCell>
                        <TableCell align="right">Ranking</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>Volatility</TableCell>
                        <TableCell align="right">{performanceMetrics.volatility.toFixed(1)}%</TableCell>
                        <TableCell align="right">{benchmarkData.volatility.toFixed(1)}%</TableCell>
                        <TableCell align="right">
                          <Chip label="Better" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Sharpe Ratio</TableCell>
                        <TableCell align="right">{performanceMetrics.sharpeRatio.toFixed(2)}</TableCell>
                        <TableCell align="right">0.63</TableCell>
                        <TableCell align="right">
                          <Chip label="Better" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Max Drawdown</TableCell>
                        <TableCell align="right">{performanceMetrics.maxDrawdown.toFixed(1)}%</TableCell>
                        <TableCell align="right">-7.2%</TableCell>
                        <TableCell align="right">
                          <Chip label="Better" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Beta</TableCell>
                        <TableCell align="right">{performanceMetrics.beta.toFixed(2)}</TableCell>
                        <TableCell align="right">1.00</TableCell>
                        <TableCell align="right">
                          <Chip label="Lower Risk" color="info" size="small" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Information Ratio</TableCell>
                        <TableCell align="right">{performanceMetrics.informationRatio.toFixed(2)}</TableCell>
                        <TableCell align="right">0.45</TableCell>
                        <TableCell align="right">
                          <Chip label="Better" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Assessment
                </Typography>
                <Stack spacing={3}>
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <CheckCircle color="success" sx={{ mr: 1 }} />
                      <Typography variant="body2" fontWeight={600}>
                        Risk Level: Moderate
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Portfolio risk is within acceptable parameters
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" fontWeight={600} gutterBottom>
                      VaR (95% confidence)
                    </Typography>
                    <Typography variant="h6" color="error">
                      -2.8%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Daily risk estimate
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" fontWeight={600} gutterBottom>
                      Expected Shortfall
                    </Typography>
                    <Typography variant="h6" color="error">
                      -4.1%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Tail risk (CVaR)
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" fontWeight={600} gutterBottom>
                      Correlation vs Market
                    </Typography>
                    <Typography variant="h6">
                      0.73
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Positive correlation
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Attribution Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Attribution
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
                    <PieChart sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                    <Typography variant="h6" gutterBottom>
                      Attribution Analysis Chart
                    </Typography>
                    <Typography variant="body2">
                      Sector, geographic, and asset class attribution breakdown
                    </Typography>
                  </Box>
                </Paper>
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Attribution
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Factor</TableCell>
                        <TableCell align="right">Contribution</TableCell>
                        <TableCell align="right">Allocation</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {riskAttributionData.map((row) => (
                        <TableRow key={row.category}>
                          <TableCell>{row.category}</TableCell>
                          <TableCell align="right">{row.contribution.toFixed(1)}%</TableCell>
                          <TableCell align="right">{row.allocation.toFixed(1)}%</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Benchmark Analysis Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Benchmark Comparison
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
                      Relative Performance Chart
                    </Typography>
                    <Typography variant="body2">
                      Portfolio vs benchmark performance comparison
                    </Typography>
                  </Box>
                </Paper>
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Tracking Statistics
                </Typography>
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Tracking Error</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      2.8%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Information Ratio</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {performanceMetrics.informationRatio.toFixed(2)}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Up Capture</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      94.2%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Down Capture</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      86.7%
                    </Typography>
                  </Box>
                  
                  <Divider />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Active Return</Typography>
                    <Typography variant="body2" fontWeight={600} color="success.main">
                      +{(performanceMetrics.annualizedReturn - benchmarkData.return).toFixed(1)}%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Batting Average</Typography>
                    <Typography variant="body2" fontWeight={600}>
                      58.3%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Best Relative Month</Typography>
                    <Typography variant="body2" fontWeight={600} color="success.main">
                      +2.7%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Worst Relative Month</Typography>
                    <Typography variant="body2" fontWeight={600} color="error.main">
                      -1.9%
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={4}>
        {/* Historical Stats Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Historical Performance Statistics
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Period</TableCell>
                    <TableCell align="right">Return</TableCell>
                    <TableCell align="right">Volatility</TableCell>
                    <TableCell align="right">Sharpe Ratio</TableCell>
                    <TableCell align="right">Max Drawdown</TableCell>
                    <TableCell align="right">vs Benchmark</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>1 Month</TableCell>
                    <TableCell align="right">+1.8%</TableCell>
                    <TableCell align="right">12.1%</TableCell>
                    <TableCell align="right">0.89</TableCell>
                    <TableCell align="right">-1.2%</TableCell>
                    <TableCell align="right">+0.3%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>3 Months</TableCell>
                    <TableCell align="right">+4.7%</TableCell>
                    <TableCell align="right">13.8%</TableCell>
                    <TableCell align="right">0.92</TableCell>
                    <TableCell align="right">-2.1%</TableCell>
                    <TableCell align="right">+0.8%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>6 Months</TableCell>
                    <TableCell align="right">+7.2%</TableCell>
                    <TableCell align="right">14.5%</TableCell>
                    <TableCell align="right">0.87</TableCell>
                    <TableCell align="right">-3.8%</TableCell>
                    <TableCell align="right">+1.1%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>1 Year</TableCell>
                    <TableCell align="right">+12.4%</TableCell>
                    <TableCell align="right">14.2%</TableCell>
                    <TableCell align="right">{performanceMetrics.sharpeRatio.toFixed(2)}</TableCell>
                    <TableCell align="right">{performanceMetrics.maxDrawdown.toFixed(1)}%</TableCell>
                    <TableCell align="right">+1.8%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>3 Years</TableCell>
                    <TableCell align="right">+28.9%</TableCell>
                    <TableCell align="right">15.1%</TableCell>
                    <TableCell align="right">0.71</TableCell>
                    <TableCell align="right">-8.7%</TableCell>
                    <TableCell align="right">+2.3%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default PerformanceTracker;