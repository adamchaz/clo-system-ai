import React, { useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Stack,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Chip,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  BarChart,
  Speed,
  AccountBalance,
  Timeline,
} from '@mui/icons-material';
import { useGetPortfoliosQuery } from '../../store/api/cloApi';

interface PerformanceOverviewProps {
  portfolioId?: string;
  timeframe?: '1M' | '3M' | '6M' | '1Y' | 'YTD';
}

interface PerformanceMetric {
  period: string;
  portfolioReturn: number;
  benchmarkReturn: number;
  outperformance: number;
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
}

const PerformanceOverview: React.FC<PerformanceOverviewProps> = ({
  portfolioId: _portfolioId,
  timeframe = 'YTD',
}) => {
  const theme = useTheme();

  const {
    isLoading: portfoliosLoading,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  // Mock performance data (in production would come from API)
  const performanceMetrics = useMemo((): PerformanceMetric[] => [
    {
      period: '1 Month',
      portfolioReturn: 2.1,
      benchmarkReturn: 1.8,
      outperformance: 0.3,
      volatility: 8.2,
      sharpeRatio: 1.24,
      maxDrawdown: -1.2,
    },
    {
      period: '3 Months', 
      portfolioReturn: 5.8,
      benchmarkReturn: 4.9,
      outperformance: 0.9,
      volatility: 9.1,
      sharpeRatio: 1.18,
      maxDrawdown: -2.8,
    },
    {
      period: '6 Months',
      portfolioReturn: 9.2,
      benchmarkReturn: 7.6,
      outperformance: 1.6,
      volatility: 10.5,
      sharpeRatio: 1.12,
      maxDrawdown: -4.1,
    },
    {
      period: '1 Year',
      portfolioReturn: 12.4,
      benchmarkReturn: 9.8,
      outperformance: 2.6,
      volatility: 11.8,
      sharpeRatio: 1.08,
      maxDrawdown: -6.7,
    },
    {
      period: 'YTD',
      portfolioReturn: 7.8,
      benchmarkReturn: 6.2,
      outperformance: 1.6,
      volatility: 9.8,
      sharpeRatio: 1.15,
      maxDrawdown: -3.4,
    },
  ], []);

  const currentMetrics = performanceMetrics.find(m => m.period === timeframe) || performanceMetrics[4];

  const sectorPerformance = [
    { sector: 'Technology', allocation: 28.5, return: 15.2, contribution: 4.3 },
    { sector: 'Healthcare', allocation: 22.1, return: 8.9, contribution: 2.0 },
    { sector: 'Financial Services', allocation: 18.7, return: 6.4, contribution: 1.2 },
    { sector: 'Consumer Discretionary', allocation: 16.2, return: 11.8, contribution: 1.9 },
    { sector: 'Industrials', allocation: 14.5, return: 7.1, contribution: 1.0 },
  ];

  const topPerformers = [
    { name: 'Portfolio Alpha Fund', return: 15.8, aum: 85.2, assets: 42 },
    { name: 'Growth Equity CLO', return: 12.9, aum: 72.1, assets: 38 },
    { name: 'Diversified Credit', return: 9.7, aum: 94.5, assets: 56 },
    { name: 'High Yield Strategy', return: 8.4, aum: 63.8, assets: 31 },
    { name: 'Conservative Income', return: 6.2, aum: 118.7, assets: 67 },
  ];

  const getPerformanceColor = (value: number, isReturn: boolean = true) => {
    if (isReturn) {
      if (value > 10) return theme.palette.success.main;
      if (value > 5) return theme.palette.info.main;
      if (value > 0) return theme.palette.warning.main;
      return theme.palette.error.main;
    } else {
      // For volatility/drawdown (lower is better)
      if (value < 5) return theme.palette.success.main;
      if (value < 10) return theme.palette.info.main;
      if (value < 15) return theme.palette.warning.main;
      return theme.palette.error.main;
    }
  };

  const getRiskLevel = (sharpeRatio: number) => {
    if (sharpeRatio > 1.5) return { level: 'Low Risk', color: 'success' as const };
    if (sharpeRatio > 1.0) return { level: 'Moderate Risk', color: 'info' as const };
    if (sharpeRatio > 0.5) return { level: 'High Risk', color: 'warning' as const };
    return { level: 'Very High Risk', color: 'error' as const };
  };

  if (portfoliosLoading) {
    return (
      <Box>
        <LinearProgress sx={{ mb: 2 }} />
        <Typography variant="body2" color="text.secondary" textAlign="center">
          Loading performance data...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Key Performance Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp color="success" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  +{currentMetrics.portfolioReturn.toFixed(1)}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Portfolio Return ({timeframe})
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Assessment color="info" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  +{currentMetrics.outperformance.toFixed(1)}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                vs Benchmark
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Speed color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {currentMetrics.sharpeRatio.toFixed(2)}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Sharpe Ratio
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <BarChart color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {Math.abs(currentMetrics.maxDrawdown).toFixed(1)}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Max Drawdown
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Chart and Risk Summary */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Trends
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
                  <Timeline sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                  <Typography variant="h6" gutterBottom>
                    Performance Chart
                  </Typography>
                  <Typography variant="body2">
                    Historical performance comparison with benchmarks and risk metrics
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
                Risk Assessment
              </Typography>
              
              <Stack spacing={3}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Risk Level
                  </Typography>
                  <Chip 
                    label={getRiskLevel(currentMetrics.sharpeRatio).level}
                    color={getRiskLevel(currentMetrics.sharpeRatio).color as "success" | "info" | "warning" | "error"}
                    size="small"
                  />
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Portfolio Volatility
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {currentMetrics.volatility.toFixed(1)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={Math.min(currentMetrics.volatility * 5, 100)}
                    sx={{ mt: 1, height: 6 }}
                  />
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Risk-Adjusted Return
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="success.main">
                    {(currentMetrics.portfolioReturn / currentMetrics.volatility).toFixed(2)}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detailed Performance Table */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Breakdown by Period
              </Typography>
              
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Period</TableCell>
                      <TableCell align="right">Portfolio</TableCell>
                      <TableCell align="right">Benchmark</TableCell>
                      <TableCell align="right">Alpha</TableCell>
                      <TableCell align="right">Volatility</TableCell>
                      <TableCell align="right">Sharpe</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {performanceMetrics.map((metric) => (
                      <TableRow key={metric.period} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight={600}>
                            {metric.period}
                          </Typography>
                        </TableCell>
                        
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            sx={{ color: getPerformanceColor(metric.portfolioReturn) }}
                          >
                            +{metric.portfolioReturn.toFixed(1)}%
                          </Typography>
                        </TableCell>
                        
                        <TableCell align="right">
                          <Typography variant="body2">
                            +{metric.benchmarkReturn.toFixed(1)}%
                          </Typography>
                        </TableCell>
                        
                        <TableCell align="right">
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                            {metric.outperformance > 0 ? (
                              <TrendingUp sx={{ fontSize: 16, mr: 0.5, color: 'success.main' }} />
                            ) : (
                              <TrendingDown sx={{ fontSize: 16, mr: 0.5, color: 'error.main' }} />
                            )}
                            <Typography
                              variant="body2"
                              fontWeight={600}
                              sx={{ color: metric.outperformance > 0 ? 'success.main' : 'error.main' }}
                            >
                              {metric.outperformance > 0 ? '+' : ''}{metric.outperformance.toFixed(1)}%
                            </Typography>
                          </Box>
                        </TableCell>
                        
                        <TableCell align="right">
                          <Typography variant="body2">
                            {metric.volatility.toFixed(1)}%
                          </Typography>
                        </TableCell>
                        
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight={600}>
                            {metric.sharpeRatio.toFixed(2)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sector Performance Contribution
              </Typography>
              
              <Stack spacing={2}>
                {sectorPerformance.map((sector, index) => (
                  <Box key={index}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {sector.sector}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {sector.allocation.toFixed(1)}%
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Return: +{sector.return.toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="success.main" fontWeight={600}>
                        Contribution: +{sector.contribution.toFixed(1)}%
                      </Typography>
                    </Box>
                    
                    <LinearProgress
                      variant="determinate"
                      value={sector.allocation}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Top Performing Portfolios */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Top Performing Portfolios (YTD)
          </Typography>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Portfolio Name</TableCell>
                  <TableCell align="right">YTD Return</TableCell>
                  <TableCell align="right">AUM</TableCell>
                  <TableCell align="right">Assets</TableCell>
                  <TableCell align="right">Performance Rank</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {topPerformers.map((portfolio, index) => (
                  <TableRow key={index} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <AccountBalance color="primary" sx={{ mr: 2, fontSize: 20 }} />
                        <Typography variant="body2" fontWeight={600}>
                          {portfolio.name}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        sx={{ color: getPerformanceColor(portfolio.return) }}
                      >
                        +{portfolio.return.toFixed(1)}%
                      </Typography>
                    </TableCell>
                    
                    <TableCell align="right">
                      <Typography variant="body2">
                        ${portfolio.aum.toFixed(1)}M
                      </Typography>
                    </TableCell>
                    
                    <TableCell align="right">
                      <Typography variant="body2">
                        {portfolio.assets}
                      </Typography>
                    </TableCell>
                    
                    <TableCell align="right">
                      <Chip
                        label={`#${index + 1}`}
                        size="small"
                        color={index === 0 ? 'success' : index < 3 ? 'info' : 'default'}
                        variant="outlined"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default PerformanceOverview;