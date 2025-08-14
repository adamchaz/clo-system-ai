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
  TextField,
  Paper,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  LinearProgress,
  Alert,
  IconButton,
  Stack,
  Slider,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  GetApp,
  TrendingUp,
  TrendingDown,
  Assessment,
  BarChart,
  Settings,
  Add,
  Delete,
  Edit,
} from '@mui/icons-material';
// import { format } from 'date-fns';

interface ScenarioModelingProps {
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

interface ScenarioResult {
  scenarioName: string;
  defaultRate: number;
  recoveryRate: number;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  probability: number;
  status: 'completed' | 'running' | 'failed';
}

interface MonteCarloConfig {
  iterations: number;
  timeHorizon: number;
  confidenceLevel: number;
  defaultRateRange: [number, number];
  recoveryRateRange: [number, number];
  correlationFactor: number;
}

const ScenarioModeling: React.FC<ScenarioModelingProps> = ({
  portfolioId: _portfolioId,
  onPortfolioChange: _onPortfolioChange,
}) => {
  const [currentTab, setCurrentTab] = useState(0);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedScenario, setSelectedScenario] = useState('base');

  // Monte Carlo Configuration State
  const [monteCarloConfig, setMonteCarloConfig] = useState<MonteCarloConfig>({
    iterations: 10000,
    timeHorizon: 36,
    confidenceLevel: 95,
    defaultRateRange: [0.5, 5.0],
    recoveryRateRange: [40, 70],
    correlationFactor: 0.3,
  });

  // Mock scenario results
  const scenarioResults = useMemo((): ScenarioResult[] => [
    {
      scenarioName: 'Base Case',
      defaultRate: 2.1,
      recoveryRate: 55,
      totalReturn: 12.4,
      sharpeRatio: 1.24,
      maxDrawdown: -3.8,
      probability: 60.2,
      status: 'completed',
    },
    {
      scenarioName: 'Mild Stress',
      defaultRate: 3.5,
      recoveryRate: 50,
      totalReturn: 8.7,
      sharpeRatio: 0.89,
      maxDrawdown: -8.2,
      probability: 25.8,
      status: 'completed',
    },
    {
      scenarioName: 'Severe Stress',
      defaultRate: 6.2,
      recoveryRate: 35,
      totalReturn: -2.1,
      sharpeRatio: -0.34,
      maxDrawdown: -18.7,
      probability: 12.1,
      status: 'completed',
    },
    {
      scenarioName: 'Extreme Stress',
      defaultRate: 12.0,
      recoveryRate: 25,
      totalReturn: -15.3,
      sharpeRatio: -1.87,
      maxDrawdown: -35.2,
      probability: 1.9,
      status: 'completed',
    },
  ], []);

  // Predefined stress scenarios
  const stressScenarios = [
    { id: 'base', name: 'Base Case', defaultRate: 2.0, recoveryRate: 55, spread: 150 },
    { id: 'mild', name: 'Mild Stress', defaultRate: 3.5, recoveryRate: 50, spread: 200 },
    { id: 'moderate', name: 'Moderate Stress', defaultRate: 5.0, recoveryRate: 45, spread: 300 },
    { id: 'severe', name: 'Severe Stress', defaultRate: 8.0, recoveryRate: 35, spread: 500 },
    { id: 'extreme', name: 'Extreme Stress', defaultRate: 12.0, recoveryRate: 25, spread: 800 },
  ];

  // Handlers
  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const handleRunMonteCarlo = useCallback(async () => {
    setRunning(true);
    setProgress(0);
    
    // Simulate Monte Carlo execution
    const interval = setInterval(() => {
      setProgress(prev => {
        const next = prev + Math.random() * 10;
        if (next >= 100) {
          clearInterval(interval);
          setRunning(false);
          return 100;
        }
        return next;
      });
    }, 200);

    // Clean up after completion
    setTimeout(() => {
      clearInterval(interval);
      setRunning(false);
      setProgress(100);
    }, 8000);
  }, []);

  const handleStopMonteCarlo = useCallback(() => {
    setRunning(false);
    setProgress(0);
  }, []);

  const handleConfigChange = useCallback((field: keyof MonteCarloConfig, value: any) => {
    setMonteCarloConfig(prev => ({ ...prev, [field]: value }));
  }, []);

  // Helper function for scenario status coloring (unused for now)
  // const getScenarioColor = (returnValue: number) => {
  //   if (returnValue > 10) return 'success';
  //   if (returnValue > 0) return 'warning';
  //   return 'error';
  // };

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
            Scenario Modeling
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monte Carlo simulations, stress testing, and scenario analysis for CLO portfolios.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            size="small"
            disabled={running}
          >
            Export Results
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            size="small"
          >
            New Scenario
          </Button>
        </Box>
      </Box>

      {/* Monte Carlo Controls */}
      {running && (
        <Alert 
          severity="info" 
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" onClick={handleStopMonteCarlo}>
              Stop
            </Button>
          }
        >
          Monte Carlo simulation in progress... {progress.toFixed(0)}% complete
        </Alert>
      )}
      
      {running && <LinearProgress variant="determinate" value={progress} sx={{ mb: 3 }} />}

      {/* Quick Scenario Controls */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Stress Scenario</InputLabel>
            <Select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              label="Stress Scenario"
            >
              {stressScenarios.map((scenario) => (
                <MenuItem key={scenario.id} value={scenario.id}>
                  {scenario.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
          <Stack direction="row" spacing={1}>
            <Button
              variant={running ? "outlined" : "contained"}
              startIcon={running ? <Stop /> : <PlayArrow />}
              onClick={running ? handleStopMonteCarlo : handleRunMonteCarlo}
              disabled={false}
              color={running ? "error" : "primary"}
            >
              {running ? 'Stop Simulation' : 'Run Monte Carlo'}
            </Button>
            <IconButton>
              <Settings />
            </IconButton>
          </Stack>
        </Grid>
      </Grid>

      {/* Analysis Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="scenario modeling tabs">
          <Tab label="Scenario Results" />
          <Tab label="Monte Carlo Config" />
          <Tab label="Stress Testing" />
          <Tab label="Correlation Analysis" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Scenario Results Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Scenario Analysis Results
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Scenario</TableCell>
                        <TableCell align="right">Default Rate</TableCell>
                        <TableCell align="right">Recovery Rate</TableCell>
                        <TableCell align="right">Total Return</TableCell>
                        <TableCell align="right">Sharpe Ratio</TableCell>
                        <TableCell align="right">Max Drawdown</TableCell>
                        <TableCell align="right">Probability</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {scenarioResults.map((result, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Typography variant="body2" fontWeight={600}>
                              {result.scenarioName}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {result.defaultRate.toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {result.recoveryRate}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                              {result.totalReturn > 0 ? (
                                <TrendingUp color="success" sx={{ mr: 0.5, fontSize: 16 }} />
                              ) : (
                                <TrendingDown color="error" sx={{ mr: 0.5, fontSize: 16 }} />
                              )}
                              <Typography
                                variant="body2"
                                fontWeight={600}
                                color={result.totalReturn > 0 ? 'success.main' : 'error.main'}
                              >
                                {result.totalReturn > 0 ? '+' : ''}{result.totalReturn.toFixed(1)}%
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight={600}>
                              {result.sharpeRatio.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" color="error.main">
                              {result.maxDrawdown.toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {result.probability.toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={result.status}
                              size="small"
                              color={result.status === 'completed' ? 'success' : 'default'}
                            />
                          </TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={0.5}>
                              <IconButton size="small">
                                <Edit fontSize="small" />
                              </IconButton>
                              <IconButton size="small">
                                <Delete fontSize="small" />
                              </IconButton>
                            </Stack>
                          </TableCell>
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

      <TabPanel value={currentTab} index={1}>
        {/* Monte Carlo Config Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Simulation Parameters
                </Typography>
                <Stack spacing={3}>
                  <TextField
                    label="Number of Iterations"
                    type="number"
                    value={monteCarloConfig.iterations}
                    onChange={(e) => handleConfigChange('iterations', parseInt(e.target.value))}
                    fullWidth
                    size="small"
                  />
                  
                  <TextField
                    label="Time Horizon (months)"
                    type="number"
                    value={monteCarloConfig.timeHorizon}
                    onChange={(e) => handleConfigChange('timeHorizon', parseInt(e.target.value))}
                    fullWidth
                    size="small"
                  />
                  
                  <Box>
                    <Typography gutterBottom>
                      Confidence Level: {monteCarloConfig.confidenceLevel}%
                    </Typography>
                    <Slider
                      value={monteCarloConfig.confidenceLevel}
                      onChange={(_, value) => handleConfigChange('confidenceLevel', value)}
                      min={90}
                      max={99.9}
                      step={0.1}
                      marks={[
                        { value: 90, label: '90%' },
                        { value: 95, label: '95%' },
                        { value: 99, label: '99%' },
                      ]}
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Parameters
                </Typography>
                <Stack spacing={3}>
                  <Box>
                    <Typography gutterBottom>
                      Default Rate Range: {monteCarloConfig.defaultRateRange[0]}% - {monteCarloConfig.defaultRateRange[1]}%
                    </Typography>
                    <Slider
                      value={monteCarloConfig.defaultRateRange}
                      onChange={(_, value) => handleConfigChange('defaultRateRange', value as [number, number])}
                      min={0}
                      max={20}
                      step={0.1}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(value) => `${value}%`}
                    />
                  </Box>
                  
                  <Box>
                    <Typography gutterBottom>
                      Recovery Rate Range: {monteCarloConfig.recoveryRateRange[0]}% - {monteCarloConfig.recoveryRateRange[1]}%
                    </Typography>
                    <Slider
                      value={monteCarloConfig.recoveryRateRange}
                      onChange={(_, value) => handleConfigChange('recoveryRateRange', value as [number, number])}
                      min={0}
                      max={100}
                      step={1}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(value) => `${value}%`}
                    />
                  </Box>
                  
                  <Box>
                    <Typography gutterBottom>
                      Correlation Factor: {monteCarloConfig.correlationFactor.toFixed(2)}
                    </Typography>
                    <Slider
                      value={monteCarloConfig.correlationFactor}
                      onChange={(_, value) => handleConfigChange('correlationFactor', value)}
                      min={0}
                      max={1}
                      step={0.01}
                      valueLabelDisplay="auto"
                    />
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Stress Testing Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Stress Test Results
                </Typography>
                <Paper
                  sx={{
                    p: 4,
                    height: 350,
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
                      Stress Test Visualization
                    </Typography>
                    <Typography variant="body2">
                      Portfolio performance under various stress scenarios
                    </Typography>
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      Chart.js integration required for stress test visualization
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
                  Stress Summary
                </Typography>
                <Stack spacing={2}>
                  {stressScenarios.slice(0, 4).map((scenario) => (
                    <Box key={scenario.id}>
                      <Typography variant="body2" fontWeight={600}>
                        {scenario.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Default: {scenario.defaultRate}% | Recovery: {scenario.recoveryRate}%
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Correlation Analysis Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Asset Correlation Matrix
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
                <Assessment sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                <Typography variant="h6" gutterBottom>
                  Correlation Heatmap
                </Typography>
                <Typography variant="body2">
                  Asset correlation matrix with risk factor attribution
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  Heatmap visualization showing correlations between portfolio assets
                </Typography>
              </Box>
            </Paper>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default ScenarioModeling;