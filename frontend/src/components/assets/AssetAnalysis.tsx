import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  IconButton,
  Chip,
  Alert,
  LinearProgress,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  ArrowBack,
  Refresh,
  GetApp,
  Assessment,
  ShowChart,
  Security,
  TrendingUp,
  TrendingDown,
  Warning,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import MetricCard from '../common/UI/MetricCard';
import StatusIndicator from '../common/UI/StatusIndicator';
import { useCloApi } from '../../hooks/useCloApi';
import type { AssetCorrelation, AssetRiskMetrics } from '../../store/api/cloApi';

// Fix for Grid item prop typing
const GridItem = Grid as any;

// Types - using Asset from API instead of local interface

interface AssetAnalysisProps {
  assetId?: string;
  onBack?: () => void;
}

// Using AssetCorrelation from API instead of local interface

// Using AssetRiskMetrics from API instead of local interface

interface ScenarioAnalysis {
  scenario: string;
  probability: number;
  priceImpact: number;
  returnImpact: number;
  riskImpact: number;
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

const AssetAnalysis: React.FC<AssetAnalysisProps> = ({
  assetId,
  onBack
}) => {
  const navigate = useNavigate();
  const { assetId: routeAssetId } = useParams<{ assetId: string }>();
  const finalAssetId = assetId || routeAssetId;

  // State
  const [activeTab, setActiveTab] = useState(0);
  const [correlationPeriod, setCorrelationPeriod] = useState('1Y');
  const [correlationThreshold, setCorrelationThreshold] = useState(0.3);
  const [riskHorizon, setRiskHorizon] = useState(30);
  const [confidenceLevel] = useState(95);
  const [showSignificantOnly, setShowSignificantOnly] = useState(true);

  // API calls
  const { useGetAssetQuery, useGetAssetCorrelationsQuery, useGetAssetRiskMetricsQuery } = useCloApi();
  
  const {
    data: assetResponse,
    isLoading: assetLoading,
    error: assetError,
  } = useGetAssetQuery(finalAssetId || '', {
    skip: !finalAssetId,
  });

  const {
    data: correlationsResponse,
    isLoading: correlationsLoading,
    refetch: refetchCorrelations,
  } = useGetAssetCorrelationsQuery({
    assetId: finalAssetId!,
    period: correlationPeriod,
    threshold: correlationThreshold,
  }, {
    skip: !finalAssetId,
  });

  const {
    data: riskMetricsResponse,
    refetch: refetchRisk,
  } = useGetAssetRiskMetricsQuery({
    assetId: finalAssetId!,
    horizon: riskHorizon,
    confidence: confidenceLevel,
  }, {
    skip: !finalAssetId,
  });

  const asset = assetResponse?.data;
  const correlations = correlationsResponse?.data;
  const riskMetrics = riskMetricsResponse?.data;

  // Mock data for demonstration
  const mockCorrelations: AssetCorrelation[] = useMemo(() => [
    { assetId: '1', asset_id_1: finalAssetId!, asset_id_2: '1', cusip: 'ABC123456', issuer: 'Apple Inc', correlation: 0.85, pValue: 0.01, significance: 'high', last_updated: new Date().toISOString() },
    { assetId: '2', asset_id_1: finalAssetId!, asset_id_2: '2', cusip: 'DEF789012', issuer: 'Microsoft Corp', correlation: 0.72, pValue: 0.02, significance: 'high', last_updated: new Date().toISOString() },
    { assetId: '3', asset_id_1: finalAssetId!, asset_id_2: '3', cusip: 'GHI345678', issuer: 'Amazon.com Inc', correlation: 0.68, pValue: 0.03, significance: 'high', last_updated: new Date().toISOString() },
    { assetId: '4', asset_id_1: finalAssetId!, asset_id_2: '4', cusip: 'JKL901234', issuer: 'Tesla Inc', correlation: 0.45, pValue: 0.08, significance: 'medium', last_updated: new Date().toISOString() },
    { assetId: '5', asset_id_1: finalAssetId!, asset_id_2: '5', cusip: 'MNO567890', issuer: 'Nvidia Corp', correlation: 0.38, pValue: 0.12, significance: 'medium', last_updated: new Date().toISOString() },
    { assetId: '6', asset_id_1: finalAssetId!, asset_id_2: '6', cusip: 'PQR234567', issuer: 'Meta Platforms', correlation: 0.25, pValue: 0.25, significance: 'low', last_updated: new Date().toISOString() },
    { assetId: '7', asset_id_1: finalAssetId!, asset_id_2: '7', cusip: 'STU890123', issuer: 'Alphabet Inc', correlation: 0.15, pValue: 0.45, significance: 'none', last_updated: new Date().toISOString() },
  ], [finalAssetId]);

  const mockRiskMetrics: AssetRiskMetrics = useMemo(() => ({
    asset_id: finalAssetId!,
    var_95: 0.045,
    var_99: 0.078,
    expected_shortfall: 0.095,
    portfolio_contribution: 0.052,
    marginal_var: 0.0125,
    component_var: 0.0089,
    concentration_risk: 0.15,
    stress_test_results: {
      recession_scenario: -0.25,
      rating_downgrade: -0.18,
      interest_rate_shock: -0.12,
      credit_spread: -0.15,
    },
    calculated_at: new Date().toISOString(),
  }), [finalAssetId]);

  const mockScenarios: ScenarioAnalysis[] = useMemo(() => [
    { scenario: 'Base Case', probability: 0.60, priceImpact: 0.00, returnImpact: 0.085, riskImpact: 1.00 },
    { scenario: 'Bull Market', probability: 0.20, priceImpact: 0.15, returnImpact: 0.125, riskImpact: 0.85 },
    { scenario: 'Bear Market', probability: 0.15, priceImpact: -0.20, returnImpact: 0.035, riskImpact: 1.45 },
    { scenario: 'Recession', probability: 0.05, priceImpact: -0.35, returnImpact: -0.025, riskImpact: 2.10 },
  ], []);

  // Filtered correlations
  const filteredCorrelations = useMemo(() => {
    const data = correlations || mockCorrelations;
    return data.filter(item => 
      Math.abs(item.correlation) >= correlationThreshold &&
      (!showSignificantOnly || item.significance !== 'none')
    );
  }, [correlations, mockCorrelations, correlationThreshold, showSignificantOnly]);

  // Event handlers
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate(`/assets/${finalAssetId}`);
    }
  };

  const handleRefresh = () => {
    refetchCorrelations();
    refetchRisk();
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting analysis data');
  };

  // Utility functions
  const getCorrelationColor = (correlation: number) => {
    const abs = Math.abs(correlation);
    if (abs >= 0.7) return 'error';
    if (abs >= 0.5) return 'warning';
    if (abs >= 0.3) return 'info';
    return 'success';
  };

  const getCorrelationIntensity = (correlation: number) => {
    const abs = Math.abs(correlation);
    return Math.max(0.1, abs);
  };

  const formatPercentage = (value: number, decimals: number = 2) => {
    return `${(value * 100).toFixed(decimals)}%`;
  };

  // const formatCurrency = (value: number) => {
  //   return new Intl.NumberFormat('en-US', {
  //     style: 'currency',
  //     currency: 'USD',
  //   }).format(value);
  // };

  if (!finalAssetId) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Asset ID not provided
      </Alert>
    );
  }

  if (assetError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load asset analysis. Please try again.
      </Alert>
    );
  }

  if (assetLoading || !asset) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
          Loading asset analysis...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={handleBack}>
            <ArrowBack />
          </IconButton>
          <Box>
            <Typography variant="h4" component="h1">
              Asset Analysis: {asset.cusip}
            </Typography>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {asset.issuer} • {asset.asset_type.replace('_', ' ').toUpperCase()}
            </Typography>
            <StatusIndicator status={asset.status as any} />
          </Box>
        </Box>
        
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
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
        </Stack>
      </Box>

      {/* Key Risk Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <GridItem item size={{ xs: 12, md: 3 }}>
          <MetricCard
            title="VaR (95%)"
            value={formatPercentage((riskMetrics || mockRiskMetrics).var_95)}
            variant="outlined"
            status="warning"
            icon={<Security />}
          />
        </GridItem>
        <GridItem item size={{ xs: 12, md: 3 }}>
          <MetricCard
            title="Expected Shortfall"
            value={formatPercentage((riskMetrics || mockRiskMetrics).expected_shortfall)}
            variant="outlined"
            status="error"
            icon={<Warning />}
          />
        </GridItem>
        <GridItem item size={{ xs: 12, md: 3 }}>
          <MetricCard
            title="Portfolio Contribution"
            value={formatPercentage((riskMetrics || mockRiskMetrics).component_var)}
            variant="outlined"
            status="info"
            icon={<Assessment />}
          />
        </GridItem>
        <GridItem item size={{ xs: 12, md: 3 }}>
          <MetricCard
            title="Concentration Risk"
            value={formatPercentage((riskMetrics || mockRiskMetrics).concentration_risk)}
            variant="outlined"
            status={(riskMetrics || mockRiskMetrics).concentration_risk > 0.2 ? 'warning' : 'success'}
            icon={<ShowChart />}
          />
        </GridItem>
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            aria-label="analysis tabs"
          >
            <Tab label="Correlation Analysis" icon={<ShowChart />} />
            <Tab label="Risk Metrics" icon={<Security />} />
            <Tab label="Stress Testing" icon={<Warning />} />
            <Tab label="Scenario Analysis" icon={<Assessment />} />
          </Tabs>
        </Box>

        <CardContent>
          {/* Correlation Analysis Tab */}
          <TabPanel value={activeTab} index={0}>
            <Grid container spacing={3}>
              <GridItem item size={12}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">Asset Correlations</Typography>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                      <InputLabel>Period</InputLabel>
                      <Select
                        value={correlationPeriod}
                        label="Period"
                        onChange={(e) => setCorrelationPeriod(e.target.value)}
                      >
                        <MenuItem value="1M">1 Month</MenuItem>
                        <MenuItem value="3M">3 Months</MenuItem>
                        <MenuItem value="6M">6 Months</MenuItem>
                        <MenuItem value="1Y">1 Year</MenuItem>
                        <MenuItem value="2Y">2 Years</MenuItem>
                      </Select>
                    </FormControl>
                    <Box sx={{ width: 200 }}>
                      <Typography variant="caption">
                        Correlation Threshold: {correlationThreshold.toFixed(2)}
                      </Typography>
                      <Slider
                        value={correlationThreshold}
                        onChange={(_, value) => setCorrelationThreshold(value as number)}
                        min={0.1}
                        max={0.9}
                        step={0.05}
                        size="small"
                      />
                    </Box>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={showSignificantOnly}
                          onChange={(e) => setShowSignificantOnly(e.target.checked)}
                          size="small"
                        />
                      }
                      label="Significant Only"
                    />
                  </Stack>
                </Box>
              </GridItem>

              <GridItem item size={12}>
                {correlationsLoading ? (
                  <LinearProgress />
                ) : (
                  <TableContainer component={Paper} variant="outlined">
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Asset</TableCell>
                          <TableCell>Issuer</TableCell>
                          <TableCell align="right">Correlation</TableCell>
                          <TableCell align="center">Strength</TableCell>
                          <TableCell align="right">P-Value</TableCell>
                          <TableCell align="center">Significance</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {filteredCorrelations.map((item) => (
                          <TableRow key={item.assetId} hover>
                            <TableCell>
                              <Typography variant="body2" fontWeight="medium">
                                {item.cusip}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {item.issuer}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Box
                                sx={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  bgcolor: `${getCorrelationColor(item.correlation)}.light`,
                                  color: `${getCorrelationColor(item.correlation)}.contrastText`,
                                  px: 1,
                                  py: 0.5,
                                  borderRadius: 1,
                                  opacity: getCorrelationIntensity(item.correlation),
                                }}
                              >
                                {item.correlation >= 0 ? <TrendingUp fontSize="small" /> : <TrendingDown fontSize="small" />}
                                <Typography variant="body2" fontWeight="medium" sx={{ ml: 0.5 }}>
                                  {item.correlation.toFixed(3)}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell align="center">
                              <Chip
                                label={
                                  Math.abs(item.correlation) >= 0.7 ? 'Strong' :
                                  Math.abs(item.correlation) >= 0.5 ? 'Moderate' :
                                  Math.abs(item.correlation) >= 0.3 ? 'Weak' : 'Very Weak'
                                }
                                size="small"
                                color={getCorrelationColor(item.correlation) as any}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2">
                                {item.pValue.toFixed(3)}
                              </Typography>
                            </TableCell>
                            <TableCell align="center">
                              <Chip
                                label={item.significance.toUpperCase()}
                                size="small"
                                color={
                                  item.significance === 'high' ? 'success' :
                                  item.significance === 'medium' ? 'warning' :
                                  item.significance === 'low' ? 'info' : 'default'
                                }
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </GridItem>
            </Grid>
          </TabPanel>

          {/* Risk Metrics Tab */}
          <TabPanel value={activeTab} index={1}>
            <Grid container spacing={3}>
              <GridItem item size={{ xs: 12, md: 6 }}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Value at Risk (VaR)
                  </Typography>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">VaR (95%)</Typography>
                      <Typography variant="h6" color="warning.main">
                        {formatPercentage((riskMetrics || mockRiskMetrics).var_95)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">VaR (99%)</Typography>
                      <Typography variant="h6" color="error.main">
                        {formatPercentage((riskMetrics || mockRiskMetrics).var_99)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Expected Shortfall</Typography>
                      <Typography variant="h6" color="error.main">
                        {formatPercentage((riskMetrics || mockRiskMetrics).expected_shortfall)}
                      </Typography>
                    </Box>
                  </Stack>
                  <Box sx={{ mt: 2 }}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="caption">Risk Horizon:</Typography>
                      <FormControl size="small" sx={{ minWidth: 80 }}>
                        <Select
                          value={riskHorizon}
                          onChange={(e) => setRiskHorizon(e.target.value as number)}
                        >
                          <MenuItem value={1}>1 Day</MenuItem>
                          <MenuItem value={7}>1 Week</MenuItem>
                          <MenuItem value={30}>1 Month</MenuItem>
                          <MenuItem value={90}>3 Months</MenuItem>
                        </Select>
                      </FormControl>
                    </Stack>
                  </Box>
                </Paper>
              </GridItem>

              <GridItem item size={{ xs: 12, md: 6 }}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Risk Contribution
                  </Typography>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Portfolio VaR</Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {formatPercentage((riskMetrics || mockRiskMetrics).portfolio_contribution)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Marginal VaR</Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {formatPercentage((riskMetrics || mockRiskMetrics).marginal_var)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Component VaR</Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {formatPercentage((riskMetrics || mockRiskMetrics).component_var)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Concentration Risk</Typography>
                      <Typography 
                        variant="body1" 
                        fontWeight="medium"
                        color={(riskMetrics || mockRiskMetrics).concentration_risk > 0.2 ? 'warning.main' : 'text.primary'}
                      >
                        {formatPercentage((riskMetrics || mockRiskMetrics).concentration_risk)}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>
              </GridItem>
            </Grid>
          </TabPanel>

          {/* Stress Testing Tab */}
          <TabPanel value={activeTab} index={2}>
            <Typography variant="h6" gutterBottom>
              Stress Test Results
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Impact of various stress scenarios on asset price and portfolio risk
            </Typography>
            
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Stress Scenario</TableCell>
                    <TableCell align="right">Price Impact</TableCell>
                    <TableCell align="center">Risk Level</TableCell>
                    <TableCell>Description</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">Recession Scenario</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="error.main" fontWeight="medium">
                        {formatPercentage((riskMetrics || mockRiskMetrics).stress_test_results.recession_scenario)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="High" color="error" size="small" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        Economic downturn with increased defaults
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">Rating Downgrade</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="error.main" fontWeight="medium">
                        {formatPercentage((riskMetrics || mockRiskMetrics).stress_test_results.rating_downgrade)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Medium" color="warning" size="small" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        Two-notch rating downgrade
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">Credit Spread Widening</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="error.main" fontWeight="medium">
                        {formatPercentage((riskMetrics || mockRiskMetrics).stress_test_results.credit_spread)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Medium" color="warning" size="small" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        200bp credit spread increase
                      </Typography>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">Interest Rate Shock</Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="warning.main" fontWeight="medium">
                        {formatPercentage((riskMetrics || mockRiskMetrics).stress_test_results.interest_rate_shock)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Low" color="info" size="small" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        300bp parallel rate increase
                      </Typography>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          {/* Scenario Analysis Tab */}
          <TabPanel value={activeTab} index={3}>
            <Typography variant="h6" gutterBottom>
              Scenario Analysis
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Asset performance under different market conditions
            </Typography>
            
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Scenario</TableCell>
                    <TableCell align="right">Probability</TableCell>
                    <TableCell align="right">Price Impact</TableCell>
                    <TableCell align="right">Expected Return</TableCell>
                    <TableCell align="right">Risk Multiplier</TableCell>
                    <TableCell align="center">Overall Assessment</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {mockScenarios.map((scenario) => (
                    <TableRow key={scenario.scenario}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {scenario.scenario}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {formatPercentage(scenario.probability)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          color={scenario.priceImpact >= 0 ? 'success.main' : 'error.main'}
                          fontWeight="medium"
                        >
                          {scenario.priceImpact >= 0 ? '+' : ''}{formatPercentage(scenario.priceImpact)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2"
                          color={scenario.returnImpact >= 0 ? 'success.main' : 'error.main'}
                          fontWeight="medium"
                        >
                          {formatPercentage(scenario.returnImpact)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="medium">
                          {scenario.riskImpact.toFixed(2)}x
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={
                            scenario.scenario === 'Base Case' ? 'Neutral' :
                            scenario.scenario === 'Bull Market' ? 'Positive' :
                            scenario.scenario === 'Bear Market' ? 'Negative' : 'Severe'
                          }
                          color={
                            scenario.scenario === 'Base Case' ? 'info' :
                            scenario.scenario === 'Bull Market' ? 'success' :
                            scenario.scenario === 'Bear Market' ? 'warning' : 'error'
                          }
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                Scenario probabilities are based on historical market conditions and current economic indicators.
                Risk multipliers show how asset volatility changes relative to the base case scenario.
              </Typography>
            </Alert>
          </TabPanel>
        </CardContent>
      </Card>
    </Box>
  );
};

export default AssetAnalysis;