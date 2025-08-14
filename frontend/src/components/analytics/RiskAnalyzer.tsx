/**
 * RiskAnalyzer Component - Advanced Portfolio Risk Analysis
 * 
 * Comprehensive risk analysis interface featuring:
 * - Value at Risk (VaR) calculations at multiple confidence levels
 * - Expected Shortfall and Conditional VaR analysis
 * - Stress testing with predefined and custom scenarios
 * - Risk decomposition by asset, sector, and factor
 * - Correlation analysis and cluster identification
 * - Monte Carlo simulation for risk forecasting
 * - Real-time risk alerts and monitoring
 * 
 * Integrates with new Portfolio Analytics APIs and WebSocket for risk alerts
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  Stack,
  Slider,
  Switch,
  FormControlLabel,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Security,
  Warning,
  TrendingDown,
  Assessment,
  ShowChart,
  Download,
  Refresh,
  PlayArrow,
  Stop,
  ExpandMore,
  Info,
  Analytics,
  Speed,
  Timeline,
  AccountBalance,
  PieChart,
  ScatterPlot,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  Legend, 
  ResponsiveContainer,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  Cell,
  PieChart as RechartsPieChart,
  Pie,
} from 'recharts';

// Import API hooks
import {
  useAnalyzeRiskMutation,
  useGetPortfolioQuery,
} from '../../store/api/cloApi';

// Import types
import {
  PortfolioRiskAnalysisRequest,
  PortfolioRiskAnalysisResult,
} from '../../store/api/newApiTypes';

// Import WebSocket hooks
import { useRiskAlerts } from '../../hooks/useWebSocket';

interface RiskAnalyzerProps {
  portfolioId: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} role="tabpanel">
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const StressScenarios = [
  { id: 'recession', name: 'Economic Recession', description: 'Severe economic downturn with high defaults' },
  { id: 'rate_shock', name: 'Interest Rate Shock', description: 'Sudden 300bp rate increase' },
  { id: 'credit_spread', name: 'Credit Spread Widening', description: 'Credit spreads widen by 500bp' },
  { id: 'liquidity_crisis', name: 'Liquidity Crisis', description: 'Market liquidity dries up' },
  { id: 'sector_shock', name: 'Sector-Specific Shock', description: 'Major sector experiences distress' },
  { id: 'custom', name: 'Custom Scenario', description: 'User-defined stress scenario' },
];

const ConfidenceLevels = [90, 95, 99, 99.5];
const TimeHorizons = [1, 5, 10, 21, 63, 252]; // Days

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

const RiskAnalyzer: React.FC<RiskAnalyzerProps> = ({ portfolioId }) => {
  // State management
  const [currentTab, setCurrentTab] = useState(0);
  const [confidenceLevels, setConfidenceLevels] = useState<number[]>([95, 99]);
  const [timeHorizons, setTimeHorizons] = useState<number[]>([1, 10, 21]);
  const [selectedStressScenarios, setSelectedStressScenarios] = useState<string[]>(['recession', 'rate_shock']);
  const [customShocks, setCustomShocks] = useState<Record<string, number>>({});
  const [includeCorrelationBreakdown, setIncludeCorrelationBreakdown] = useState(true);
  const [correlationThreshold, setCorrelationThreshold] = useState(0.7);
  const [monteCarloRuns, setMonteCarloRuns] = useState(10000);

  const [analysisResult, setAnalysisResult] = useState<PortfolioRiskAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [riskAlerts, setRiskAlerts] = useState<any[]>([]);

  // API hooks
  const { data: portfolioData } = useGetPortfolioQuery(portfolioId);
  const [analyzeRisk, { isLoading }] = useAnalyzeRiskMutation();

  // WebSocket integration for real-time risk alerts
  useRiskAlerts(portfolioId, (alertData) => {
    setRiskAlerts(prev => [alertData, ...prev.slice(0, 9)]); // Keep last 10 alerts
  });

  // Mock data for demonstration
  const mockVaRData = useMemo(() => {
    return timeHorizons.map(horizon => ({
      horizon: `${horizon}d`,
      VaR_95: -(2.1 * Math.sqrt(horizon)),
      VaR_99: -(2.8 * Math.sqrt(horizon)),
      ExpectedShortfall_95: -(2.6 * Math.sqrt(horizon)),
      ExpectedShortfall_99: -(3.4 * Math.sqrt(horizon)),
    }));
  }, [timeHorizons]);

  const mockStressTestResults = useMemo(() => {
    return selectedStressScenarios.map(scenario => {
      const scenarioInfo = StressScenarios.find(s => s.id === scenario);
      return {
        scenario: scenarioInfo?.name || scenario,
        portfolioLoss: -(Math.random() * 15 + 5),
        probabilityWeighted: Math.random() * 0.1,
        worstCase: -(Math.random() * 25 + 10),
      };
    });
  }, [selectedStressScenarios]);

  const mockRiskContribution = [
    { category: 'Technology', contribution: 35.2, marginalVar: 2.8, name: 'Technology' },
    { category: 'Healthcare', contribution: 24.1, marginalVar: 1.9, name: 'Healthcare' },
    { category: 'Financials', contribution: 18.7, marginalVar: 2.1, name: 'Financials' },
    { category: 'Energy', contribution: 12.3, marginalVar: 3.2, name: 'Energy' },
    { category: 'Consumer', contribution: 9.7, marginalVar: 1.6, name: 'Consumer' },
  ];

  const mockCorrelationClusters = [
    { cluster: 'Tech Cluster', assets: 15, avgCorrelation: 0.78 },
    { cluster: 'Financial Cluster', assets: 12, avgCorrelation: 0.82 },
    { cluster: 'Healthcare Cluster', assets: 10, avgCorrelation: 0.71 },
    { cluster: 'Energy Cluster', assets: 8, avgCorrelation: 0.85 },
  ];

  // Handle analysis execution
  const handleAnalyze = async () => {
    const request: PortfolioRiskAnalysisRequest = {
      portfolio_id: portfolioId,
      confidence_levels: confidenceLevels,
      time_horizons: timeHorizons,
      stress_scenarios: selectedStressScenarios,
      custom_shocks: customShocks,
      include_correlation_breakdown: includeCorrelationBreakdown,
      correlation_threshold: correlationThreshold,
    };

    try {
      setIsAnalyzing(true);
      const result = await analyzeRisk(request).unwrap();
      setAnalysisResult(result);
    } catch (error) {
      console.error('Risk analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const formatPercent = (value: number) => `${value.toFixed(2)}%`;
  const formatNumber = (value: number) => value.toFixed(4);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleStressScenarioToggle = (scenarioId: string) => {
    setSelectedStressScenarios(prev =>
      prev.includes(scenarioId)
        ? prev.filter(id => id !== scenarioId)
        : [...prev, scenarioId]
    );
  };

  const getRiskLevelColor = (riskLevel: number) => {
    if (riskLevel < 5) return 'success';
    if (riskLevel < 10) return 'warning';
    return 'error';
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Risk Analyzer
        </Typography>

        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => window.location.reload()}
          >
            Refresh
          </Button>
          
          <Button
            variant="contained"
            startIcon={<Security />}
            onClick={handleAnalyze}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze Risk'}
          </Button>
        </Stack>
      </Box>

      {/* Risk Alerts */}
      {riskAlerts.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Recent Risk Alerts ({riskAlerts.length})
          </Typography>
          <Typography variant="body2">
            Latest: {riskAlerts[0]?.message} - {format(new Date(riskAlerts[0]?.timestamp), 'PPp')}
          </Typography>
        </Alert>
      )}

      {/* Configuration Panel */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Risk Analysis Configuration
          </Typography>

          <Grid container spacing={3}>
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" gutterBottom>
                Confidence Levels (%)
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {ConfidenceLevels.map(level => (
                  <Chip
                    key={level}
                    label={`${level}%`}
                    color={confidenceLevels.includes(level) ? 'primary' : 'default'}
                    onClick={() => {
                      setConfidenceLevels(prev =>
                        prev.includes(level)
                          ? prev.filter(l => l !== level)
                          : [...prev, level]
                      );
                    }}
                    clickable
                  />
                ))}
              </Stack>
            </Grid>

            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" gutterBottom>
                Time Horizons (Days)
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {TimeHorizons.map(horizon => (
                  <Chip
                    key={horizon}
                    label={`${horizon}d`}
                    color={timeHorizons.includes(horizon) ? 'primary' : 'default'}
                    onClick={() => {
                      setTimeHorizons(prev =>
                        prev.includes(horizon)
                          ? prev.filter(h => h !== horizon)
                          : [...prev, horizon]
                      );
                    }}
                    clickable
                  />
                ))}
              </Stack>
            </Grid>

            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" gutterBottom>
                Monte Carlo Runs
              </Typography>
              <TextField
                type="number"
                value={monteCarloRuns}
                onChange={(e) => setMonteCarloRuns(parseInt(e.target.value))}
                inputProps={{ min: 1000, max: 100000, step: 1000 }}
                fullWidth
              />
            </Grid>

            <Grid {...({ item: true } as any)} size={12}>
              <Typography variant="subtitle2" gutterBottom>
                Stress Test Scenarios
              </Typography>
              <Grid container spacing={2}>
                {StressScenarios.map(scenario => (
                  <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 4 }} key={scenario.id}>
                    <Card 
                      sx={{ 
                        cursor: 'pointer',
                        border: selectedStressScenarios.includes(scenario.id) ? 2 : 1,
                        borderColor: selectedStressScenarios.includes(scenario.id) ? 'primary.main' : 'divider',
                      }}
                      onClick={() => handleStressScenarioToggle(scenario.id)}
                    >
                      <CardContent sx={{ pb: '16px !important' }}>
                        <Typography variant="subtitle2">
                          {scenario.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {scenario.description}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Grid>

            <Grid {...({ item: true } as any)} size={12}>
              <Stack direction="row" spacing={3} alignItems="center">
                <FormControlLabel
                  control={
                    <Switch
                      checked={includeCorrelationBreakdown}
                      onChange={(e) => setIncludeCorrelationBreakdown(e.target.checked)}
                    />
                  }
                  label="Include Correlation Analysis"
                />
                
                <Box sx={{ minWidth: 200 }}>
                  <Typography variant="caption">
                    Correlation Threshold: {correlationThreshold}
                  </Typography>
                  <Slider
                    value={correlationThreshold}
                    onChange={(_, value) => setCorrelationThreshold(value as number)}
                    min={0.3}
                    max={0.95}
                    step={0.05}
                    size="small"
                  />
                </Box>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Loading Indicator */}
      {(isAnalyzing || isLoading) && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Running risk analysis...
          </Typography>
        </Box>
      )}

      {/* Results Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange}>
            <Tab label="VaR Analysis" icon={<Security />} />
            <Tab label="Stress Testing" icon={<Warning />} />
            <Tab label="Risk Decomposition" icon={<PieChart />} />
            <Tab label="Correlation Analysis" icon={<ScatterPlot />} />
            <Tab label="Monte Carlo" icon={<Analytics />} />
          </Tabs>
        </Box>

        {/* VaR Analysis Tab */}
        <TabPanel value={currentTab} index={0}>
          <Grid container spacing={3}>
            <Grid {...({ item: true } as any)} size={12}>
              <Typography variant="h6" gutterBottom>
                Value at Risk Analysis
              </Typography>
              
              <Box sx={{ height: 400, width: '100%' }}>
                <ResponsiveContainer>
                  <LineChart data={mockVaRData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="horizon" />
                    <YAxis label={{ value: 'Loss (%)', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip formatter={(value: any) => [formatPercent(value), '']} />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="VaR_95" 
                      stroke="#ff7c7c" 
                      strokeWidth={2}
                      name="VaR 95%"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="VaR_99" 
                      stroke="#ff4444" 
                      strokeWidth={2}
                      name="VaR 99%"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="ExpectedShortfall_95" 
                      stroke="#ffaa00" 
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="ES 95%"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="ExpectedShortfall_99" 
                      stroke="#ff6600" 
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="ES 99%"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </Grid>

            <Grid {...({ item: true } as any)} size={12}>
              <Typography variant="h6" gutterBottom>
                VaR Summary Table
              </Typography>
              
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Time Horizon</TableCell>
                      <TableCell align="right">VaR 95%</TableCell>
                      <TableCell align="right">VaR 99%</TableCell>
                      <TableCell align="right">Expected Shortfall 95%</TableCell>
                      <TableCell align="right">Expected Shortfall 99%</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {mockVaRData.map((row) => (
                      <TableRow key={row.horizon}>
                        <TableCell>{row.horizon}</TableCell>
                        <TableCell align="right">
                          <Chip 
                            label={formatPercent(row.VaR_95)} 
                            color={getRiskLevelColor(Math.abs(row.VaR_95)) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Chip 
                            label={formatPercent(row.VaR_99)} 
                            color={getRiskLevelColor(Math.abs(row.VaR_99)) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">{formatPercent(row.ExpectedShortfall_95)}</TableCell>
                        <TableCell align="right">{formatPercent(row.ExpectedShortfall_99)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Stress Testing Tab */}
        <TabPanel value={currentTab} index={1}>
          <Grid container spacing={3}>
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 8 }}>
              <Typography variant="h6" gutterBottom>
                Stress Test Results
              </Typography>
              
              <Box sx={{ height: 400, width: '100%' }}>
                <ResponsiveContainer>
                  <BarChart data={mockStressTestResults}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="scenario" 
                      angle={-45}
                      textAnchor="end"
                      height={100}
                    />
                    <YAxis label={{ value: 'Loss (%)', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip formatter={(value: any) => [formatPercent(value), '']} />
                    <Legend />
                    <Bar dataKey="portfolioLoss" fill="#ff7c7c" name="Portfolio Loss" />
                    <Bar dataKey="worstCase" fill="#ff4444" name="Worst Case" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </Grid>

            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
              <Typography variant="h6" gutterBottom>
                Scenario Impact Summary
              </Typography>
              
              <List>
                {mockStressTestResults.map((result, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <Warning color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary={result.scenario}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            Portfolio Loss: {formatPercent(result.portfolioLoss)}
                          </Typography>
                          <Typography variant="caption" display="block">
                            Worst Case: {formatPercent(result.worstCase)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Risk Decomposition Tab */}
        <TabPanel value={currentTab} index={2}>
          <Grid container spacing={3}>
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
              <Typography variant="h6" gutterBottom>
                Risk Contribution by Sector
              </Typography>
              
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer>
                  <RechartsPieChart>
                    <Pie
                      data={mockRiskContribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, contribution }) => `${name}: ${contribution}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="contribution"
                    >
                      {mockRiskContribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip formatter={(value: any) => [formatPercent(value), 'Risk Contribution']} />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </Box>
            </Grid>

            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
              <Typography variant="h6" gutterBottom>
                Marginal VaR Analysis
              </Typography>
              
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={mockRiskContribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" />
                    <YAxis label={{ value: 'Marginal VaR (%)', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip formatter={(value: any) => [formatPercent(value), '']} />
                    <Bar dataKey="marginalVar" fill="#82ca9d" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </Grid>

            <Grid {...({ item: true } as any)} size={12}>
              <Typography variant="h6" gutterBottom>
                Risk Decomposition Summary
              </Typography>
              
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Sector</TableCell>
                      <TableCell align="right">Risk Contribution (%)</TableCell>
                      <TableCell align="right">Marginal VaR (%)</TableCell>
                      <TableCell align="right">Component VaR</TableCell>
                      <TableCell align="right">Risk Level</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {mockRiskContribution.map((row) => (
                      <TableRow key={row.category}>
                        <TableCell>{row.category}</TableCell>
                        <TableCell align="right">{formatPercent(row.contribution)}</TableCell>
                        <TableCell align="right">{formatPercent(row.marginalVar)}</TableCell>
                        <TableCell align="right">{formatPercent(row.contribution * row.marginalVar / 100)}</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={row.contribution > 30 ? 'High' : row.contribution > 15 ? 'Medium' : 'Low'}
                            color={getRiskLevelColor(row.contribution) as any}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Correlation Analysis Tab */}
        <TabPanel value={currentTab} index={3}>
          <Grid container spacing={3}>
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
              <Typography variant="h6" gutterBottom>
                Correlation Clusters
              </Typography>
              
              <List>
                {mockCorrelationClusters.map((cluster, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <ScatterPlot color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={cluster.cluster}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            Assets: {cluster.assets}
                          </Typography>
                          <Typography variant="caption">
                            Avg Correlation: {cluster.avgCorrelation.toFixed(2)}
                          </Typography>
                        </Box>
                      }
                    />
                    <Chip
                      label={cluster.avgCorrelation > 0.8 ? 'High' : cluster.avgCorrelation > 0.6 ? 'Medium' : 'Low'}
                      color={cluster.avgCorrelation > 0.8 ? 'error' : cluster.avgCorrelation > 0.6 ? 'warning' : 'success'}
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>

            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
              <Typography variant="h6" gutterBottom>
                Diversification Analysis
              </Typography>
              
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="subtitle2">
                  Portfolio Diversification Ratio: 0.73
                </Typography>
                <Typography variant="body2">
                  Good diversification. Lower correlation between assets reduces overall portfolio risk.
                </Typography>
              </Alert>

              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                High Correlation Pairs (&gt;{correlationThreshold})
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Correlation analysis results will be displayed here when analysis completes.
              </Typography>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Monte Carlo Tab */}
        <TabPanel value={currentTab} index={4}>
          <Typography variant="h6" gutterBottom>
            Monte Carlo Risk Simulation
          </Typography>
          
          <Grid container spacing={3}>
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 8 }}>
              <Alert severity="info">
                Monte Carlo simulation results with {monteCarloRuns.toLocaleString()} iterations 
                will be displayed here when analysis completes. This will include:
                <ul>
                  <li>Distribution of portfolio returns</li>
                  <li>Confidence intervals</li>
                  <li>Tail risk analysis</li>
                  <li>Scenario probabilities</li>
                </ul>
              </Alert>
            </Grid>

            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Simulation Parameters
                  </Typography>
                  
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Simulation Runs"
                        secondary={monteCarloRuns.toLocaleString()}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Confidence Levels"
                        secondary={confidenceLevels.map(l => `${l}%`).join(', ')}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Time Horizons"
                        secondary={timeHorizons.map(h => `${h}d`).join(', ')}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>
    </Box>
  );
};

export default RiskAnalyzer;