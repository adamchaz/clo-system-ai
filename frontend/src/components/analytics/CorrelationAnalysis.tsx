import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Tabs,
  Tab,
  Stack,
  Slider,
  IconButton,
  Alert,
  LinearProgress,
  useTheme,
} from '@mui/material';
import {
  GetApp,
  Settings,
  TrendingUp,
  TrendingDown,
  Assessment,
  PieChart,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import { format } from 'date-fns';

interface CorrelationAnalysisProps {
  portfolioId?: string;
  onPortfolioChange?: (portfolioId: string) => void;
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

interface CorrelationData {
  asset1: string;
  asset2: string;
  correlation: number;
  pValue: number;
  significance: 'high' | 'medium' | 'low';
}

interface RiskFactor {
  factor: string;
  exposure: number;
  contribution: number;
  volatility: number;
  trend: number;
}

const CorrelationAnalysis: React.FC<CorrelationAnalysisProps> = ({
  portfolioId: _portfolioId,
  onPortfolioChange: _onPortfolioChange,
}) => {
  const theme = useTheme();
  const [currentTab, setCurrentTab] = useState(0);
  const [correlationThreshold, setCorrelationThreshold] = useState(0.5);
  const [timeWindow, setTimeWindow] = useState('1Y');
  const [analysisType, setAnalysisType] = useState('pearson');
  const [sectorFilter, setSectorFilter] = useState('all');
  const [showSignificantOnly, setShowSignificantOnly] = useState(false);

  // Mock correlation data
  const correlationMatrix = useMemo(() => {
    const assets = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'JPM', 'JNJ', 'PG'];
    const matrix: { [key: string]: { [key: string]: number } } = {};
    
    assets.forEach(asset1 => {
      matrix[asset1] = {};
      assets.forEach(asset2 => {
        if (asset1 === asset2) {
          matrix[asset1][asset2] = 1.0;
        } else {
          // Generate mock correlation values
          const seed = asset1.charCodeAt(0) + asset2.charCodeAt(0);
          matrix[asset1][asset2] = Math.sin(seed / 100) * 0.8;
        }
      });
    });
    
    return { assets, matrix };
  }, []);

  const highCorrelations = useMemo((): CorrelationData[] => [
    { asset1: 'AAPL', asset2: 'MSFT', correlation: 0.84, pValue: 0.001, significance: 'high' as const },
    { asset1: 'GOOGL', asset2: 'AMZN', correlation: 0.76, pValue: 0.002, significance: 'high' as const },
    { asset1: 'JPM', asset2: 'Bank Sector', correlation: 0.92, pValue: 0.000, significance: 'high' as const },
    { asset1: 'TSLA', asset2: 'Tech Sector', correlation: 0.68, pValue: 0.008, significance: 'medium' as const },
    { asset1: 'JNJ', asset2: 'Healthcare', correlation: 0.73, pValue: 0.004, significance: 'medium' as const },
    { asset1: 'PG', asset2: 'Consumer', correlation: 0.59, pValue: 0.025, significance: 'medium' as const },
  ].filter(corr => Math.abs(corr.correlation) >= correlationThreshold), [correlationThreshold]);

  const riskFactors = useMemo((): RiskFactor[] => [
    { factor: 'Market Beta', exposure: 0.87, contribution: 32.5, volatility: 18.2, trend: -0.8 },
    { factor: 'Credit Spread', exposure: 0.64, contribution: 24.1, volatility: 12.7, trend: 1.2 },
    { factor: 'Interest Rate', exposure: 0.42, contribution: 15.8, volatility: 8.9, trend: 0.3 },
    { factor: 'Sector Tech', exposure: 0.71, contribution: 18.4, volatility: 22.1, trend: -1.5 },
    { factor: 'Currency USD', exposure: 0.23, contribution: 5.7, volatility: 6.3, trend: 0.7 },
    { factor: 'Commodity', exposure: 0.18, contribution: 3.5, volatility: 15.4, trend: -0.4 },
  ], []);

  // Handlers
  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const getCorrelationColor = (correlation: number) => {
    const abs = Math.abs(correlation);
    if (abs >= 0.8) return theme.palette.error.main;
    if (abs >= 0.6) return theme.palette.warning.main;
    if (abs >= 0.4) return theme.palette.info.main;
    return theme.palette.success.main;
  };

  const getCorrelationIntensity = (correlation: number) => {
    const abs = Math.abs(correlation);
    return abs * 0.8 + 0.2; // Scale between 0.2 and 1.0
  };

  const getSignificanceColor = (significance: string) => {
    switch (significance) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

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
            Correlation Analysis
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Asset correlation matrices, risk factor analysis, and portfolio diversification metrics.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {format(new Date(), 'MMM dd, yyyy HH:mm')}
          </Typography>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            size="small"
          >
            Export Matrix
          </Button>
          <Button
            variant="contained"
            startIcon={<Assessment />}
            size="small"
          >
            Run Analysis
          </Button>
        </Box>
      </Box>

      {/* Analysis Controls */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Time Window</InputLabel>
            <Select
              value={timeWindow}
              onChange={(e) => setTimeWindow(e.target.value)}
              label="Time Window"
            >
              <MenuItem value="1M">1 Month</MenuItem>
              <MenuItem value="3M">3 Months</MenuItem>
              <MenuItem value="6M">6 Months</MenuItem>
              <MenuItem value="1Y">1 Year</MenuItem>
              <MenuItem value="2Y">2 Years</MenuItem>
              <MenuItem value="3Y">3 Years</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Analysis Type</InputLabel>
            <Select
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
              label="Analysis Type"
            >
              <MenuItem value="pearson">Pearson</MenuItem>
              <MenuItem value="spearman">Spearman</MenuItem>
              <MenuItem value="kendall">Kendall</MenuItem>
              <MenuItem value="rolling">Rolling</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Sector Filter</InputLabel>
            <Select
              value={sectorFilter}
              onChange={(e) => setSectorFilter(e.target.value)}
              label="Sector Filter"
            >
              <MenuItem value="all">All Sectors</MenuItem>
              <MenuItem value="technology">Technology</MenuItem>
              <MenuItem value="financial">Financial</MenuItem>
              <MenuItem value="healthcare">Healthcare</MenuItem>
              <MenuItem value="consumer">Consumer</MenuItem>
              <MenuItem value="industrial">Industrial</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
          <Box>
            <Typography variant="body2" gutterBottom>
              Correlation Threshold: {correlationThreshold.toFixed(2)}
            </Typography>
            <Slider
              value={correlationThreshold}
              onChange={(_, value) => setCorrelationThreshold(value as number)}
              min={0}
              max={1}
              step={0.05}
              size="small"
            />
          </Box>
        </Grid>
      </Grid>

      {/* Analysis Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="correlation analysis tabs">
          <Tab label="Correlation Matrix" />
          <Tab label="High Correlations" />
          <Tab label="Risk Factors" />
          <Tab label="Diversification" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Correlation Matrix Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 8 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    Asset Correlation Matrix
                  </Typography>
                  <Box>
                    <IconButton
                      onClick={() => setShowSignificantOnly(!showSignificantOnly)}
                      color={showSignificantOnly ? 'primary' : 'default'}
                    >
                      {showSignificantOnly ? <Visibility /> : <VisibilityOff />}
                    </IconButton>
                    <IconButton>
                      <Settings />
                    </IconButton>
                  </Box>
                </Box>

                <TableContainer sx={{ maxHeight: 500 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell></TableCell>
                        {correlationMatrix.assets.map((asset) => (
                          <TableCell key={asset} align="center" sx={{ minWidth: 80 }}>
                            <Typography variant="caption" fontWeight={600}>
                              {asset}
                            </Typography>
                          </TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {correlationMatrix.assets.map((asset1) => (
                        <TableRow key={asset1}>
                          <TableCell sx={{ fontWeight: 600, bgcolor: 'background.default' }}>
                            {asset1}
                          </TableCell>
                          {correlationMatrix.assets.map((asset2) => {
                            const correlation = correlationMatrix.matrix[asset1][asset2];
                            const isSignificant = Math.abs(correlation) >= 0.5;
                            
                            if (showSignificantOnly && !isSignificant && asset1 !== asset2) {
                              return <TableCell key={asset2}></TableCell>;
                            }
                            
                            return (
                              <TableCell 
                                key={asset2} 
                                align="center"
                                sx={{
                                  bgcolor: asset1 === asset2 
                                    ? 'primary.main'
                                    : `${getCorrelationColor(correlation)}${Math.floor(getCorrelationIntensity(correlation) * 255).toString(16).padStart(2, '0')}`,
                                  color: asset1 === asset2 ? 'white' : 'text.primary',
                                  fontWeight: Math.abs(correlation) >= 0.7 ? 600 : 400,
                                }}
                              >
                                {correlation.toFixed(2)}
                              </TableCell>
                            );
                          })}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Legend */}
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: 16, height: 16, bgcolor: theme.palette.error.main, mr: 1 }} />
                    <Typography variant="caption">High (≥0.8)</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: 16, height: 16, bgcolor: theme.palette.warning.main, mr: 1 }} />
                    <Typography variant="caption">Medium (0.6-0.8)</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: 16, height: 16, bgcolor: theme.palette.info.main, mr: 1 }} />
                    <Typography variant="caption">Low (0.4-0.6)</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: 16, height: 16, bgcolor: theme.palette.success.main, mr: 1 }} />
                    <Typography variant="caption">Very Low (&lt;0.4)</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Matrix Statistics
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Average Correlation
                    </Typography>
                    <Typography variant="h6" fontWeight={600}>
                      0.42
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      High Correlations (≥0.7)
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color="error.main">
                      23 pairs
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Diversification Ratio
                    </Typography>
                    <Typography variant="h6" fontWeight={600} color="success.main">
                      0.68
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Portfolio VaR Contribution
                    </Typography>
                    <Typography variant="h6" fontWeight={600}>
                      15.2%
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {/* High Correlations Tab */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                High Correlation Pairs (≥{correlationThreshold.toFixed(2)})
              </Typography>
              <Chip 
                label={`${highCorrelations.length} pairs`} 
                color="primary" 
                variant="outlined" 
              />
            </Box>
            
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Asset 1</TableCell>
                    <TableCell>Asset 2</TableCell>
                    <TableCell align="right">Correlation</TableCell>
                    <TableCell align="right">P-Value</TableCell>
                    <TableCell>Significance</TableCell>
                    <TableCell>Risk Impact</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {highCorrelations.map((corr, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {corr.asset1}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {corr.asset2}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            sx={{ color: getCorrelationColor(corr.correlation) }}
                          >
                            {corr.correlation.toFixed(3)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {corr.pValue.toFixed(3)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={corr.significance}
                          size="small"
                          color={getSignificanceColor(corr.significance) as any}
                        />
                      </TableCell>
                      <TableCell>
                        {Math.abs(corr.correlation) >= 0.8 ? (
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <TrendingUp color="error" sx={{ mr: 0.5, fontSize: 16 }} />
                            <Typography variant="body2" color="error.main">
                              High Risk
                            </Typography>
                          </Box>
                        ) : (
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <TrendingDown color="warning" sx={{ mr: 0.5, fontSize: 16 }} />
                            <Typography variant="body2" color="warning.main">
                              Medium Risk
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {highCorrelations.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                No correlations found above the threshold of {correlationThreshold.toFixed(2)}. 
                Consider lowering the threshold to see more correlation pairs.
              </Alert>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Risk Factors Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Risk Factor Analysis
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Risk Factor</TableCell>
                    <TableCell align="right">Exposure</TableCell>
                    <TableCell align="right">Contribution (%)</TableCell>
                    <TableCell align="right">Volatility</TableCell>
                    <TableCell align="right">Trend</TableCell>
                    <TableCell>Impact</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {riskFactors.map((factor, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {factor.factor}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {factor.exposure.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight={600}>
                          {factor.contribution.toFixed(1)}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={factor.contribution}
                          sx={{ mt: 0.5, height: 4 }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {factor.volatility.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                          {factor.trend > 0 ? (
                            <TrendingUp color="error" sx={{ mr: 0.5, fontSize: 16 }} />
                          ) : (
                            <TrendingDown color="success" sx={{ mr: 0.5, fontSize: 16 }} />
                          )}
                          <Typography
                            variant="body2"
                            color={factor.trend > 0 ? 'error.main' : 'success.main'}
                          >
                            {factor.trend > 0 ? '+' : ''}{factor.trend.toFixed(1)}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={factor.contribution > 20 ? 'High' : factor.contribution > 10 ? 'Medium' : 'Low'}
                          size="small"
                          color={factor.contribution > 20 ? 'error' : factor.contribution > 10 ? 'warning' : 'success'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Diversification Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Diversification Metrics
                </Typography>
                <Paper
                  sx={{
                    p: 4,
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
                    <Typography variant="h6" gutterBottom>
                      Diversification Chart
                    </Typography>
                    <Typography variant="body2">
                      Portfolio concentration and diversification metrics
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
                  Portfolio Metrics
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Effective Number of Assets
                    </Typography>
                    <Typography variant="h5" fontWeight={600}>
                      42.7
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Herfindahl Index
                    </Typography>
                    <Typography variant="h5" fontWeight={600}>
                      0.23
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Concentration Ratio (Top 10)
                    </Typography>
                    <Typography variant="h5" fontWeight={600}>
                      34.2%
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Diversification Score
                    </Typography>
                    <Typography variant="h5" fontWeight={600} color="success.main">
                      B+
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

export default CorrelationAnalysis;