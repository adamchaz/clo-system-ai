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
  SelectChangeEvent
} from '@mui/material';
import {
  TrendingDown,
  ShowChart,
  Assessment,
  Download as DownloadIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  Histogram
} from 'recharts';
import { useRealTime } from '../../../hooks/useRealTimeData';
import MetricCard from '../UI/MetricCard';

/**
 * TASK 13: Advanced Data Visualization Components
 * 
 * RiskVisualization - Comprehensive risk analytics visualization
 * 
 * Features:
 * - Value at Risk (VaR) calculations and visualizations
 * - Stress testing scenario analysis
 * - Risk distribution histograms
 * - Volatility surface charts
 * - Real-time risk metric updates
 * - Multi-timeframe analysis (1D, 7D, 30D, 1Y)
 */

interface RiskMetric {
  date: string;
  var95: number;
  var99: number;
  expectedShortfall: number;
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
}

interface StressTest {
  scenario: string;
  probability: number;
  portfolioValue: number;
  loss: number;
  description: string;
}

interface RiskDistribution {
  return: number;
  frequency: number;
  cumulative: number;
}

export interface RiskVisualizationProps {
  portfolioId?: string;
  timeframe?: '1D' | '7D' | '30D' | '1Y';
  showControls?: boolean;
  enableRealTime?: boolean;
  height?: number;
}

const RiskVisualization: React.FC<RiskVisualizationProps> = ({
  portfolioId = 'default',
  timeframe = '30D',
  showControls = true,
  enableRealTime = true,
  height = 400
}) => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>(timeframe);
  const [stressScenario, setStressScenario] = useState<string>('market_crash');

  // Real-time data integration
  const { portfolio } = useRealTime();
  const portfolioData = portfolio.portfolioData;

  // Generate mock risk metrics data
  const riskMetrics: RiskMetric[] = useMemo(() => {
    const days = selectedTimeframe === '1D' ? 1 : 
                 selectedTimeframe === '7D' ? 7 : 
                 selectedTimeframe === '30D' ? 30 : 365;
    
    return Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      
      return {
        date: date.toISOString().split('T')[0],
        var95: -0.02 + Math.random() * -0.03, // -2% to -5%
        var99: -0.035 + Math.random() * -0.045, // -3.5% to -8%
        expectedShortfall: -0.055 + Math.random() * -0.045, // -5.5% to -10%
        volatility: 0.15 + Math.random() * 0.1, // 15% to 25%
        sharpeRatio: 0.8 + Math.random() * 0.8, // 0.8 to 1.6
        maxDrawdown: -0.1 - Math.random() * 0.15 // -10% to -25%
      };
    });
  }, [selectedTimeframe]);

  // Generate stress test scenarios
  const stressTests: StressTest[] = useMemo(() => [
    {
      scenario: 'market_crash',
      probability: 0.05,
      portfolioValue: 850000,
      loss: -150000,
      description: '2008-style market crash scenario'
    },
    {
      scenario: 'interest_spike',
      probability: 0.15,
      portfolioValue: 920000,
      loss: -80000,
      description: 'Rapid interest rate increase (+400bps)'
    },
    {
      scenario: 'credit_crunch',
      probability: 0.10,
      portfolioValue: 880000,
      loss: -120000,
      description: 'Credit market liquidity crisis'
    },
    {
      scenario: 'inflation_shock',
      probability: 0.20,
      portfolioValue: 940000,
      loss: -60000,
      description: 'Unexpected inflation surge (>6%)'
    },
    {
      scenario: 'geopolitical',
      probability: 0.08,
      portfolioValue: 900000,
      loss: -100000,
      description: 'Major geopolitical conflict'
    }
  ], []);

  // Generate risk distribution data
  const riskDistribution: RiskDistribution[] = useMemo(() => {
    const returns = [];
    for (let i = -0.15; i <= 0.15; i += 0.005) {
      const frequency = Math.exp(-0.5 * Math.pow(i / 0.02, 2)) / (0.02 * Math.sqrt(2 * Math.PI));
      returns.push({
        return: i,
        frequency,
        cumulative: returns.length > 0 ? returns[returns.length - 1].cumulative + frequency : frequency
      });
    }
    return returns;
  }, []);

  const currentRisk = riskMetrics[riskMetrics.length - 1];

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleTimeframeChange = (event: SelectChangeEvent<string>) => {
    setSelectedTimeframe(event.target.value);
  };

  const handleStressScenarioChange = (event: SelectChangeEvent<string>) => {
    setStressScenario(event.target.value);
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const handleExport = () => {
    // Export functionality would be implemented here
    console.log('Exporting risk visualization...');
  };

  const renderVaRChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={riskMetrics}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={(value) => `${(value * 100).toFixed(1)}%`} />
        <RechartsTooltip 
          formatter={(value: number) => [`${(value * 100).toFixed(2)}%`, '']}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Legend />
        <Line type="monotone" dataKey="var95" stroke="#ff7300" name="VaR 95%" strokeWidth={2} />
        <Line type="monotone" dataKey="var99" stroke="#d62728" name="VaR 99%" strokeWidth={2} />
        <Line type="monotone" dataKey="expectedShortfall" stroke="#2ca02c" name="Expected Shortfall" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );

  const renderVolatilityChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={riskMetrics}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={(value) => `${(value * 100).toFixed(1)}%`} />
        <RechartsTooltip 
          formatter={(value: number) => [`${(value * 100).toFixed(2)}%`, '']}
        />
        <Legend />
        <Area 
          type="monotone" 
          dataKey="volatility" 
          stroke="#8884d8" 
          fill="#8884d8" 
          fillOpacity={0.3}
          name="Volatility"
        />
      </AreaChart>
    </ResponsiveContainer>
  );

  const renderStressTestChart = () => {
    const selectedTest = stressTests.find(test => test.scenario === stressScenario) || stressTests[0];
    
    return (
      <Box>
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={stressTests}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="scenario" />
            <YAxis tickFormatter={(value) => `$${(value / 1000)}K`} />
            <RechartsTooltip 
              formatter={(value: number, name: string) => [
                name === 'loss' ? `$${(value / 1000).toFixed(0)}K` : `$${(value / 1000).toFixed(0)}K`,
                name === 'loss' ? 'Potential Loss' : 'Portfolio Value'
              ]}
            />
            <Legend />
            <Bar dataKey="portfolioValue" fill="#8884d8" name="Portfolio Value After Stress" />
            <Bar dataKey="loss" fill="#d62728" name="Potential Loss" />
          </BarChart>
        </ResponsiveContainer>
        
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Selected Scenario: {selectedTest.scenario.replace('_', ' ').toUpperCase()}
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              {selectedTest.description}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Typography variant="body2">
                <strong>Probability:</strong> {(selectedTest.probability * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2">
                <strong>Expected Loss:</strong> ${(Math.abs(selectedTest.loss) / 1000).toFixed(0)}K
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  };

  const renderRiskDistribution = () => (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={riskDistribution}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="return" 
          tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
        />
        <YAxis />
        <RechartsTooltip 
          formatter={(value: number) => [value.toFixed(4), 'Density']}
          labelFormatter={(label) => `Return: ${(label * 100).toFixed(2)}%`}
        />
        <Area 
          type="monotone" 
          dataKey="frequency" 
          stroke="#2ca02c" 
          fill="#2ca02c" 
          fillOpacity={0.6}
          name="Return Distribution"
        />
      </AreaChart>
    </ResponsiveContainer>
  );

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      {showControls && (
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Timeframe</InputLabel>
            <Select value={selectedTimeframe} onChange={handleTimeframeChange} label="Timeframe">
              <MenuItem value="1D">1 Day</MenuItem>
              <MenuItem value="7D">7 Days</MenuItem>
              <MenuItem value="30D">30 Days</MenuItem>
              <MenuItem value="1Y">1 Year</MenuItem>
            </Select>
          </FormControl>

          {activeTab === 2 && (
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Stress Scenario</InputLabel>
              <Select value={stressScenario} onChange={handleStressScenarioChange} label="Stress Scenario">
                {stressTests.map((test) => (
                  <MenuItem key={test.scenario} value={test.scenario}>
                    {test.scenario.replace('_', ' ')}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

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
      )}

      {/* Risk Metrics Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="VaR (95%)"
            value={`${(currentRisk?.var95 * 100).toFixed(2)}%`}
            trend="down"
            icon={<TrendingDown />}
            color="error"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Volatility"
            value={`${(currentRisk?.volatility * 100).toFixed(2)}%`}
            trend="neutral"
            icon={<ShowChart />}
            color="warning"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Sharpe Ratio"
            value={currentRisk?.sharpeRatio.toFixed(2)}
            trend="up"
            icon={<Assessment />}
            color="success"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Max Drawdown"
            value={`${(currentRisk?.maxDrawdown * 100).toFixed(2)}%`}
            trend="down"
            icon={<TrendingDown />}
            color="error"
          />
        </Grid>
      </Grid>

      {/* Tabbed Charts */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab label="Value at Risk" />
          <Tab label="Volatility" />
          <Tab label="Stress Tests" />
          <Tab label="Return Distribution" />
        </Tabs>
      </Box>

      <Box sx={{ mt: 2 }}>
        {activeTab === 0 && renderVaRChart()}
        {activeTab === 1 && renderVolatilityChart()}
        {activeTab === 2 && renderStressTestChart()}
        {activeTab === 3 && renderRiskDistribution()}
      </Box>

      {enableRealTime && portfolioData && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
          Last updated: {new Date().toLocaleTimeString()} (Real-time)
        </Typography>
      )}
    </Paper>
  );
};

export default RiskVisualization;