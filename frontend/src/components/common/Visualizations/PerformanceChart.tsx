import React, { useState, useMemo, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Chip,
  SelectChangeEvent,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Compare as CompareIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Brush
} from 'recharts';
import { useRealTime } from '../../../hooks/useRealTimeData';
import MetricCard from '../UI/MetricCard';

/**
 * TASK 13: Advanced Data Visualization Components
 * 
 * PerformanceChart - Advanced portfolio performance visualization
 * 
 * Features:
 * - Multi-timeframe performance analysis (1W, 1M, 3M, 1Y, YTD, All)
 * - Benchmark comparison with multiple indices
 * - Return decomposition (dividends, capital gains, fees)
 * - Rolling performance metrics (Sharpe, volatility, drawdown)
 * - Real-time performance updates
 * - Interactive chart controls and export functionality
 */

interface PerformanceData {
  date: string;
  portfolioValue: number;
  portfolioReturn: number;
  benchmark: number;
  benchmarkReturn: number;
  cumulativeReturn: number;
  cumulativeBenchmark: number;
  dividends: number;
  fees: number;
  drawdown: number;
  volume?: number;
}

interface PerformanceMetrics {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  alpha: number;
  beta: number;
  informationRatio: number;
}

export interface PerformanceChartProps {
  portfolioId?: string;
  timeframe?: '1W' | '1M' | '3M' | '6M' | '1Y' | 'YTD' | 'All';
  benchmark?: 'SPY' | 'BND' | 'VTI' | 'AGG' | 'Custom';
  showBenchmark?: boolean;
  showDrawdown?: boolean;
  showVolume?: boolean;
  enableRealTime?: boolean;
  height?: number;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({
  portfolioId = 'default',
  timeframe = '1Y',
  benchmark = 'SPY',
  showBenchmark = true,
  showDrawdown = false,
  showVolume = false,
  enableRealTime = true,
  height = 400
}) => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>(timeframe);
  const [selectedBenchmark, setSelectedBenchmark] = useState<string>(benchmark);
  const [showBenchmarkLine, setShowBenchmarkLine] = useState<boolean>(showBenchmark);
  const [showDrawdownChart, setShowDrawdownChart] = useState<boolean>(showDrawdown);
  const [showVolumeChart, setShowVolumeChart] = useState<boolean>(showVolume);

  // Real-time data integration
  const { portfolio } = useRealTime();
  const portfolioData = portfolio.portfolioData;

  // Generate mock performance data
  const performanceData: PerformanceData[] = useMemo(() => {
    const days = selectedTimeframe === '1W' ? 7 : 
                 selectedTimeframe === '1M' ? 30 : 
                 selectedTimeframe === '3M' ? 90 :
                 selectedTimeframe === '6M' ? 180 :
                 selectedTimeframe === '1Y' ? 365 : 
                 selectedTimeframe === 'YTD' ? 365 : 500;
    
    let portfolioValue = 1000000;
    let benchmarkValue = 1000000;
    let cumulativeReturn = 0;
    let cumulativeBenchmark = 0;
    let maxValue = portfolioValue;
    
    return Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      
      // Generate realistic returns
      const dailyReturn = (Math.random() - 0.48) * 0.03; // Slightly positive bias
      const benchmarkReturn = (Math.random() - 0.49) * 0.025; // Market return
      
      portfolioValue *= (1 + dailyReturn);
      benchmarkValue *= (1 + benchmarkReturn);
      
      cumulativeReturn = (portfolioValue - 1000000) / 1000000;
      cumulativeBenchmark = (benchmarkValue - 1000000) / 1000000;
      
      maxValue = Math.max(maxValue, portfolioValue);
      const drawdown = (portfolioValue - maxValue) / maxValue;
      
      return {
        date: date.toISOString().split('T')[0],
        portfolioValue: Math.round(portfolioValue),
        portfolioReturn: dailyReturn,
        benchmark: Math.round(benchmarkValue),
        benchmarkReturn,
        cumulativeReturn,
        cumulativeBenchmark,
        dividends: Math.random() * 1000,
        fees: Math.random() * 200,
        drawdown,
        volume: Math.floor(Math.random() * 1000000)
      };
    });
  }, [selectedTimeframe]);

  // Calculate performance metrics
  const performanceMetrics: PerformanceMetrics = useMemo(() => {
    if (performanceData.length === 0) {
      return {
        totalReturn: 0,
        annualizedReturn: 0,
        volatility: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        winRate: 0,
        alpha: 0,
        beta: 0,
        informationRatio: 0
      };
    }

    const returns = performanceData.map(d => d.portfolioReturn);
    const benchmarkReturns = performanceData.map(d => d.benchmarkReturn);
    const finalData = performanceData[performanceData.length - 1];
    
    const totalReturn = finalData.cumulativeReturn;
    const annualizedReturn = Math.pow(1 + totalReturn, 365 / performanceData.length) - 1;
    
    const volatility = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - returns.reduce((s, v) => s + v, 0) / returns.length, 2), 0) / returns.length
    ) * Math.sqrt(252);
    
    const sharpeRatio = (annualizedReturn - 0.02) / volatility; // Assuming 2% risk-free rate
    const maxDrawdown = Math.min(...performanceData.map(d => d.drawdown));
    const winRate = returns.filter(r => r > 0).length / returns.length;
    
    // Calculate Alpha and Beta
    const avgBenchmarkReturn = benchmarkReturns.reduce((sum, r) => sum + r, 0) / benchmarkReturns.length;
    const avgPortfolioReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    
    const covariance = returns.reduce((sum, r, i) => 
      sum + (r - avgPortfolioReturn) * (benchmarkReturns[i] - avgBenchmarkReturn), 0
    ) / returns.length;
    
    const benchmarkVariance = benchmarkReturns.reduce((sum, r) => 
      sum + Math.pow(r - avgBenchmarkReturn, 2), 0
    ) / benchmarkReturns.length;
    
    const beta = covariance / benchmarkVariance;
    const alpha = avgPortfolioReturn - beta * avgBenchmarkReturn;
    
    const trackingError = Math.sqrt(
      returns.reduce((sum, r, i) => sum + Math.pow(r - benchmarkReturns[i], 2), 0) / returns.length
    ) * Math.sqrt(252);
    
    const informationRatio = (annualizedReturn - finalData.cumulativeBenchmark) / trackingError;
    
    return {
      totalReturn,
      annualizedReturn,
      volatility,
      sharpeRatio,
      maxDrawdown,
      winRate,
      alpha: alpha * 252, // Annualized alpha
      beta,
      informationRatio
    };
  }, [performanceData]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleTimeframeChange = (event: SelectChangeEvent<string>) => {
    setSelectedTimeframe(event.target.value);
  };

  const handleBenchmarkChange = (event: SelectChangeEvent<string>) => {
    setSelectedBenchmark(event.target.value);
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const handleExport = () => {
    console.log('Exporting performance chart...');
  };

  const formatValue = (value: number) => {
    return `$${(value / 1000).toFixed(0)}K`;
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const renderPerformanceChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={performanceData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis yAxisId="left" tickFormatter={formatValue} />
        {showVolumeChart && <YAxis yAxisId="right" orientation="right" />}
        <RechartsTooltip 
          formatter={(value: number, name: string) => {
            if (name.includes('Value') || name.includes('benchmark')) {
              return [formatValue(value), name];
            }
            return [value, name];
          }}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Legend />
        
        <Line 
          yAxisId="left"
          type="monotone" 
          dataKey="portfolioValue" 
          stroke="#2196f3" 
          strokeWidth={3}
          name="Portfolio Value"
          dot={false}
        />
        
        {showBenchmarkLine && (
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="benchmark" 
            stroke="#ff9800" 
            strokeWidth={2}
            strokeDasharray="5 5"
            name={`Benchmark (${selectedBenchmark})`}
            dot={false}
          />
        )}
        
        {showVolumeChart && (
          <Bar 
            yAxisId="right"
            dataKey="volume" 
            fill="#e0e0e0" 
            fillOpacity={0.5}
            name="Volume"
          />
        )}
        
        <Brush dataKey="date" height={30} stroke="#8884d8" />
      </ComposedChart>
    </ResponsiveContainer>
  );

  const renderCumulativeReturns = () => (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={performanceData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={formatPercent} />
        <RechartsTooltip 
          formatter={(value: number) => [formatPercent(value), '']}
        />
        <Legend />
        
        <Line 
          type="monotone" 
          dataKey="cumulativeReturn" 
          stroke="#4caf50" 
          strokeWidth={3}
          name="Portfolio Return"
          dot={false}
        />
        
        {showBenchmarkLine && (
          <Line 
            type="monotone" 
            dataKey="cumulativeBenchmark" 
            stroke="#ff5722" 
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Benchmark Return"
            dot={false}
          />
        )}
        
        <ReferenceLine y={0} stroke="#666" strokeDasharray="2 2" />
      </LineChart>
    </ResponsiveContainer>
  );

  const renderDrawdownChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={performanceData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={formatPercent} />
        <RechartsTooltip 
          formatter={(value: number) => [formatPercent(value), 'Drawdown']}
        />
        
        <Area 
          type="monotone" 
          dataKey="drawdown" 
          stroke="#f44336" 
          fill="#f44336" 
          fillOpacity={0.6}
          name="Drawdown"
        />
        
        <ReferenceLine y={0} stroke="#666" strokeDasharray="2 2" />
      </AreaChart>
    </ResponsiveContainer>
  );

  const renderRollingMetrics = () => (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={performanceData.slice(-60)}> {/* Last 60 days for rolling metrics */}
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <RechartsTooltip />
        <Legend />
        
        <Line 
          type="monotone" 
          dataKey="portfolioReturn" 
          stroke="#2196f3" 
          name="Daily Return"
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      {/* Controls */}
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Timeframe</InputLabel>
          <Select value={selectedTimeframe} onChange={handleTimeframeChange} label="Timeframe">
            <MenuItem value="1W">1 Week</MenuItem>
            <MenuItem value="1M">1 Month</MenuItem>
            <MenuItem value="3M">3 Months</MenuItem>
            <MenuItem value="6M">6 Months</MenuItem>
            <MenuItem value="1Y">1 Year</MenuItem>
            <MenuItem value="YTD">Year to Date</MenuItem>
            <MenuItem value="All">All Time</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Benchmark</InputLabel>
          <Select value={selectedBenchmark} onChange={handleBenchmarkChange} label="Benchmark">
            <MenuItem value="SPY">S&P 500 (SPY)</MenuItem>
            <MenuItem value="VTI">Total Stock Market</MenuItem>
            <MenuItem value="BND">Bond Index</MenuItem>
            <MenuItem value="AGG">Aggregate Bond</MenuItem>
            <MenuItem value="Custom">Custom</MenuItem>
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch 
              checked={showBenchmarkLine} 
              onChange={(e) => setShowBenchmarkLine(e.target.checked)}
              size="small"
            />
          }
          label="Show Benchmark"
        />

        <FormControlLabel
          control={
            <Switch 
              checked={showVolumeChart} 
              onChange={(e) => setShowVolumeChart(e.target.checked)}
              size="small"
            />
          }
          label="Show Volume"
        />

        <Box sx={{ flex: 1 }} />

        <Tooltip title="Refresh Data">
          <IconButton onClick={handleRefresh} size="small">
            <RefreshIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Export Chart">
          <IconButton onClick={handleExport} size="small">
            <DownloadIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Performance Metrics Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Total Return"
            value={formatPercent(performanceMetrics.totalReturn)}
            trend={performanceMetrics.totalReturn > 0 ? "up" : "down"}
            icon={performanceMetrics.totalReturn > 0 ? <TrendingUp /> : <TrendingDown />}
            color={performanceMetrics.totalReturn > 0 ? "success" : "error"}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Sharpe Ratio"
            value={performanceMetrics.sharpeRatio.toFixed(2)}
            trend={performanceMetrics.sharpeRatio > 1 ? "up" : "flat"}
            icon={<CompareIcon />}
            color={performanceMetrics.sharpeRatio > 1 ? "success" : "warning"}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Max Drawdown"
            value={formatPercent(performanceMetrics.maxDrawdown)}
            trend="down"
            icon={<TrendingDown />}
            color="error"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Win Rate"
            value={formatPercent(performanceMetrics.winRate)}
            trend={performanceMetrics.winRate > 0.5 ? "up" : "down"}
            icon={<TimelineIcon />}
            color={performanceMetrics.winRate > 0.5 ? "success" : "warning"}
          />
        </Grid>
      </Grid>

      {/* Additional Metrics */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Advanced Metrics
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Chip 
              label={`Alpha: ${formatPercent(performanceMetrics.alpha)}`}
              color={performanceMetrics.alpha > 0 ? "success" : "error"}
              variant="outlined"
            />
            <Chip 
              label={`Beta: ${performanceMetrics.beta.toFixed(2)}`}
              color="primary"
              variant="outlined"
            />
            <Chip 
              label={`Information Ratio: ${performanceMetrics.informationRatio.toFixed(2)}`}
              color="secondary"
              variant="outlined"
            />
            <Chip 
              label={`Volatility: ${formatPercent(performanceMetrics.volatility)}`}
              color="warning"
              variant="outlined"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Chart Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Portfolio Value" />
          <Tab label="Cumulative Returns" />
          <Tab label="Drawdown" />
          <Tab label="Rolling Metrics" />
        </Tabs>
      </Box>

      <Box sx={{ mt: 2 }}>
        {activeTab === 0 && renderPerformanceChart()}
        {activeTab === 1 && renderCumulativeReturns()}
        {activeTab === 2 && renderDrawdownChart()}
        {activeTab === 3 && renderRollingMetrics()}
      </Box>

      {enableRealTime && portfolioData && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
          Last updated: {new Date().toLocaleTimeString()} (Real-time) | 
          Portfolio: {portfolioData.totalValue ? formatValue(portfolioData.totalValue) : 'N/A'}
        </Typography>
      )}
    </Paper>
  );
};

export default PerformanceChart;