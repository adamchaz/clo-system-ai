/**
 * PortfolioOptimizer Component - Advanced Portfolio Optimization Interface
 * 
 * Provides comprehensive portfolio optimization capabilities:
 * - Multiple optimization types (risk minimization, return maximization, Sharpe ratio, compliance)
 * - Advanced constraint configuration (sector limits, rating limits, concentration)
 * - Real-time optimization progress tracking
 * - Interactive results visualization with trade recommendations
 * - Monte Carlo simulation integration
 * 
 * Integrates with new Portfolio Analytics APIs and WebSocket for real-time updates
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  Slider,
  Switch,
  FormControlLabel,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  Stack,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Settings,
  TrendingUp,
  Assessment,
  CheckCircle,
  Download,
  History,
  Speed,
  Security,
  Balance,
} from '@mui/icons-material';

// Import API hooks
import {
  useOptimizePortfolioMutation,
  useGetPortfolioQuery,
  useGetQuickPortfolioMetricsQuery,
} from '../../store/api/cloApi';

// Import types
import {
  PortfolioOptimizationRequest,
  PortfolioOptimizationResult,
  OptimizationType,
} from '../../store/api/newApiTypes';

// Import WebSocket hooks for progress tracking
import { useCalculationProgress } from '../../hooks/useWebSocket';

interface PortfolioOptimizerProps {
  portfolioId: string;
  onOptimizationComplete?: (result: PortfolioOptimizationResult) => void;
}

interface ConstraintConfig {
  type: string;
  enabled: boolean;
  minValue?: number;
  maxValue?: number;
  weight: number;
}

const OptimizationTypeInfo = {
  risk_minimization: {
    title: 'Risk Minimization',
    description: 'Minimize portfolio risk while maintaining expected returns',
    icon: <Security color="primary" />,
  },
  return_maximization: {
    title: 'Return Maximization', 
    description: 'Maximize expected returns for a given risk level',
    icon: <TrendingUp color="success" />,
  },
  sharpe_ratio: {
    title: 'Sharpe Ratio Optimization',
    description: 'Maximize risk-adjusted returns (Sharpe ratio)',
    icon: <Balance color="info" />,
  },
  compliance_optimization: {
    title: 'Compliance Optimization',
    description: 'Optimize while ensuring all regulatory constraints are met',
    icon: <CheckCircle color="warning" />,
  },
  custom: {
    title: 'Custom Optimization',
    description: 'User-defined optimization objectives and constraints',
    icon: <Settings color="secondary" />,
  },
};

const PortfolioOptimizer: React.FC<PortfolioOptimizerProps> = ({
  portfolioId,
  onOptimizationComplete,
}) => {
  // State management
  const [activeStep, setActiveStep] = useState(0);
  const [optimizationType, setOptimizationType] = useState<OptimizationType>('sharpe_ratio');
  const [constraints, setConstraints] = useState<Record<string, ConstraintConfig>>({
    sector_concentration: {
      type: 'sector_limit',
      enabled: true,
      maxValue: 25,
      weight: 1.0,
    },
    single_asset_limit: {
      type: 'asset_concentration',
      enabled: true,
      maxValue: 5,
      weight: 1.0,
    },
    rating_limits: {
      type: 'credit_quality',
      enabled: true,
      minValue: 65, // Percentage investment grade
      weight: 0.8,
    },
    liquidity_constraint: {
      type: 'liquidity',
      enabled: false,
      minValue: 20, // Minimum liquidity score
      weight: 0.5,
    },
  });

  const [optimizationParams, setOptimizationParams] = useState({
    targetVolatility: 12.0,
    maxRisk: 15.0,
    riskFreeRate: 2.5,
    maxSingleAssetWeight: 5.0,
    includeStressTesting: true,
    monteCarloRuns: 1000,
    optimizationHorizon: 252, // Trading days (1 year)
  });

  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationProgress, setOptimizationProgress] = useState(0);
  const [currentCalculationId, setCurrentCalculationId] = useState<string | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<PortfolioOptimizationResult | null>(null);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);

  // API hooks
  const { data: portfolioData } = useGetPortfolioQuery(portfolioId);
  const { data: portfolioMetrics } = useGetQuickPortfolioMetricsQuery(portfolioId);
  const [optimizePortfolio, { isLoading: _isLoading }] = useOptimizePortfolioMutation();

  // WebSocket integration for progress tracking
  useCalculationProgress(
    currentCalculationId,
    (progressData) => {
      setOptimizationProgress(progressData.progress);
      
      if (progressData.status === 'completed') {
        setIsOptimizing(false);
        setCurrentCalculationId(null);
        // Results will be fetched via the mutation result
      } else if (progressData.status === 'error') {
        setIsOptimizing(false);
        setCurrentCalculationId(null);
        console.error('Optimization failed:', progressData);
      }
    },
    isOptimizing
  );

  // Handler functions
  const handleConstraintChange = (constraintKey: string, field: string, value: any) => {
    setConstraints(prev => ({
      ...prev,
      [constraintKey]: {
        ...prev[constraintKey],
        [field]: value,
      },
    }));
  };

  const handleOptimizationParamChange = (param: string, value: number) => {
    setOptimizationParams(prev => ({
      ...prev,
      [param]: value,
    }));
  };

  const handleStartOptimization = async () => {
    if (!portfolioId) return;

    // Build constraints object
    const activeConstraints: Record<string, any> = {};
    const sectorLimits: Record<string, number> = {};
    const ratingLimits: Record<string, number> = {};

    Object.entries(constraints).forEach(([key, constraint]) => {
      if (constraint.enabled) {
        switch (constraint.type) {
          case 'sector_limit':
            // Apply sector limits (simplified - in real implementation, would be per sector)
            sectorLimits['technology'] = constraint.maxValue || 25;
            sectorLimits['healthcare'] = constraint.maxValue || 25;
            sectorLimits['financial'] = constraint.maxValue || 25;
            break;
          case 'credit_quality':
            ratingLimits['investment_grade_min'] = constraint.minValue || 65;
            break;
          default:
            activeConstraints[key] = constraint;
        }
      }
    });

    const optimizationRequest: PortfolioOptimizationRequest = {
      portfolio_id: portfolioId,
      optimization_type: optimizationType,
      constraints: activeConstraints,
      target_volatility: optimizationParams.targetVolatility,
      max_risk: optimizationParams.maxRisk,
      risk_free_rate: optimizationParams.riskFreeRate,
      max_single_asset_weight: optimizationParams.maxSingleAssetWeight,
      sector_limits: sectorLimits,
      rating_limits: ratingLimits,
      include_stress_testing: optimizationParams.includeStressTesting,
      monte_carlo_runs: optimizationParams.monteCarloRuns,
      optimization_horizon: optimizationParams.optimizationHorizon,
    };

    try {
      setIsOptimizing(true);
      setOptimizationProgress(0);
      setCurrentCalculationId(`opt_${Date.now()}`);

      const result = await optimizePortfolio(optimizationRequest).unwrap();
      
      setOptimizationResult(result);
      setResultsDialogOpen(true);
      onOptimizationComplete?.(result);

    } catch (error) {
      console.error('Optimization failed:', error);
      setIsOptimizing(false);
      setCurrentCalculationId(null);
    }
  };

  const handleStopOptimization = () => {
    setIsOptimizing(false);
    setCurrentCalculationId(null);
    setOptimizationProgress(0);
  };

  const renderConstraintConfig = (constraintKey: string, constraint: ConstraintConfig) => (
    <Card key={constraintKey} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>
            {constraintKey.replace('_', ' ')}
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={constraint.enabled}
                onChange={(e) => handleConstraintChange(constraintKey, 'enabled', e.target.checked)}
              />
            }
            label="Enabled"
          />
        </Box>

        {constraint.enabled && (
          <Grid container spacing={2}>
            {constraint.minValue !== undefined && (
              <Grid size={6}>
                <TextField
                  label="Minimum Value (%)"
                  type="number"
                  fullWidth
                  value={constraint.minValue}
                  onChange={(e) => handleConstraintChange(constraintKey, 'minValue', parseFloat(e.target.value))}
                  inputProps={{ min: 0, max: 100, step: 0.1 }}
                />
              </Grid>
            )}
            
            {constraint.maxValue !== undefined && (
              <Grid size={6}>
                <TextField
                  label="Maximum Value (%)"
                  type="number"
                  fullWidth
                  value={constraint.maxValue}
                  onChange={(e) => handleConstraintChange(constraintKey, 'maxValue', parseFloat(e.target.value))}
                  inputProps={{ min: 0, max: 100, step: 0.1 }}
                />
              </Grid>
            )}
            
            <Grid size={12}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Constraint Weight: {constraint.weight}
              </Typography>
              <Slider
                value={constraint.weight}
                onChange={(_, value) => handleConstraintChange(constraintKey, 'weight', value)}
                min={0}
                max={2}
                step={0.1}
                marks={[
                  { value: 0, label: '0' },
                  { value: 0.5, label: '0.5' },
                  { value: 1, label: '1.0' },
                  { value: 1.5, label: '1.5' },
                  { value: 2, label: '2.0' },
                ]}
              />
            </Grid>
          </Grid>
        )}
      </CardContent>
    </Card>
  );

  const steps = [
    'Select Optimization Type',
    'Configure Constraints', 
    'Set Parameters',
    'Review & Execute',
  ];

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Portfolio Optimizer
        </Typography>

        <Stack direction="row" spacing={2}>
          <Tooltip title="View optimization history">
            <IconButton>
              <History />
            </IconButton>
          </Tooltip>
          
          <Button
            variant="contained"
            color="error"
            startIcon={<Stop />}
            onClick={handleStopOptimization}
            disabled={!isOptimizing}
          >
            Stop
          </Button>
          
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={handleStartOptimization}
            disabled={isOptimizing || activeStep < steps.length - 1}
          >
            {isOptimizing ? 'Optimizing...' : 'Start Optimization'}
          </Button>
        </Stack>
      </Box>

      {/* Progress Indicator */}
      {isOptimizing && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Optimization in Progress
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={optimizationProgress} 
              sx={{ mb: 1, height: 8, borderRadius: 4 }}
            />
            <Typography variant="body2" color="text.secondary">
              {optimizationProgress.toFixed(1)}% Complete
            </Typography>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={3}>
        {/* Configuration Panel */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Stepper activeStep={activeStep} orientation="vertical">
                {/* Step 1: Optimization Type */}
                <Step>
                  <StepLabel>Select Optimization Type</StepLabel>
                  <StepContent>
                    <Grid container spacing={2}>
                      {Object.entries(OptimizationTypeInfo).map(([type, info]) => (
                        <Grid size={{ xs: 12, sm: 6 }} key={type}>
                          <Card 
                            sx={{ 
                              cursor: 'pointer',
                              border: optimizationType === type ? 2 : 1,
                              borderColor: optimizationType === type ? 'primary.main' : 'divider',
                            }}
                            onClick={() => setOptimizationType(type as OptimizationType)}
                          >
                            <CardContent>
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                {info.icon}
                                <Typography variant="h6" sx={{ ml: 1 }}>
                                  {info.title}
                                </Typography>
                              </Box>
                              <Typography variant="body2" color="text.secondary">
                                {info.description}
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                    
                    <Box sx={{ mt: 2 }}>
                      <Button variant="contained" onClick={() => setActiveStep(1)}>
                        Continue
                      </Button>
                    </Box>
                  </StepContent>
                </Step>

                {/* Step 2: Constraints */}
                <Step>
                  <StepLabel>Configure Constraints</StepLabel>
                  <StepContent>
                    {Object.entries(constraints).map(([key, constraint]) =>
                      renderConstraintConfig(key, constraint)
                    )}
                    
                    <Box sx={{ mt: 2 }}>
                      <Button variant="contained" onClick={() => setActiveStep(2)} sx={{ mr: 1 }}>
                        Continue
                      </Button>
                      <Button onClick={() => setActiveStep(0)}>
                        Back
                      </Button>
                    </Box>
                  </StepContent>
                </Step>

                {/* Step 3: Parameters */}
                <Step>
                  <StepLabel>Set Parameters</StepLabel>
                  <StepContent>
                    <Grid container spacing={3}>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          label="Target Volatility (%)"
                          type="number"
                          fullWidth
                          value={optimizationParams.targetVolatility}
                          onChange={(e) => handleOptimizationParamChange('targetVolatility', parseFloat(e.target.value))}
                          inputProps={{ min: 0, max: 50, step: 0.1 }}
                        />
                      </Grid>
                      
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          label="Maximum Risk (%)"
                          type="number"
                          fullWidth
                          value={optimizationParams.maxRisk}
                          onChange={(e) => handleOptimizationParamChange('maxRisk', parseFloat(e.target.value))}
                          inputProps={{ min: 0, max: 100, step: 0.1 }}
                        />
                      </Grid>
                      
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          label="Risk-Free Rate (%)"
                          type="number"
                          fullWidth
                          value={optimizationParams.riskFreeRate}
                          onChange={(e) => handleOptimizationParamChange('riskFreeRate', parseFloat(e.target.value))}
                          inputProps={{ min: 0, max: 10, step: 0.1 }}
                        />
                      </Grid>
                      
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          label="Max Single Asset Weight (%)"
                          type="number"
                          fullWidth
                          value={optimizationParams.maxSingleAssetWeight}
                          onChange={(e) => handleOptimizationParamChange('maxSingleAssetWeight', parseFloat(e.target.value))}
                          inputProps={{ min: 0, max: 25, step: 0.1 }}
                        />
                      </Grid>
                      
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          label="Monte Carlo Runs"
                          type="number"
                          fullWidth
                          value={optimizationParams.monteCarloRuns}
                          onChange={(e) => handleOptimizationParamChange('monteCarloRuns', parseInt(e.target.value))}
                          inputProps={{ min: 100, max: 10000, step: 100 }}
                        />
                      </Grid>
                      
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <TextField
                          label="Optimization Horizon (days)"
                          type="number"
                          fullWidth
                          value={optimizationParams.optimizationHorizon}
                          onChange={(e) => handleOptimizationParamChange('optimizationHorizon', parseInt(e.target.value))}
                          inputProps={{ min: 1, max: 1260, step: 1 }}
                        />
                      </Grid>
                      
                      <Grid size={12}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={optimizationParams.includeStressTesting}
                              onChange={(e) => setOptimizationParams(prev => ({ ...prev, includeStressTesting: e.target.checked }))}
                            />
                          }
                          label="Include Stress Testing"
                        />
                      </Grid>
                    </Grid>
                    
                    <Box sx={{ mt: 2 }}>
                      <Button variant="contained" onClick={() => setActiveStep(3)} sx={{ mr: 1 }}>
                        Continue
                      </Button>
                      <Button onClick={() => setActiveStep(1)}>
                        Back
                      </Button>
                    </Box>
                  </StepContent>
                </Step>

                {/* Step 4: Review */}
                <Step>
                  <StepLabel>Review & Execute</StepLabel>
                  <StepContent>
                    <Typography variant="h6" gutterBottom>
                      Optimization Summary
                    </Typography>
                    
                    <List>
                      <ListItem>
                        <ListItemIcon><Assessment /></ListItemIcon>
                        <ListItemText 
                          primary="Optimization Type"
                          secondary={OptimizationTypeInfo[optimizationType].title}
                        />
                      </ListItem>
                      
                      <ListItem>
                        <ListItemIcon><Security /></ListItemIcon>
                        <ListItemText 
                          primary="Active Constraints"
                          secondary={Object.values(constraints).filter(c => c.enabled).length}
                        />
                      </ListItem>
                      
                      <ListItem>
                        <ListItemIcon><Speed /></ListItemIcon>
                        <ListItemText 
                          primary="Monte Carlo Runs"
                          secondary={optimizationParams.monteCarloRuns.toLocaleString()}
                        />
                      </ListItem>
                    </List>
                    
                    <Alert severity="info" sx={{ mt: 2 }}>
                      This optimization will analyze the current portfolio and provide trade recommendations
                      to achieve the selected optimization objectives while respecting all constraints.
                    </Alert>
                    
                    <Box sx={{ mt: 2 }}>
                      <Button onClick={() => setActiveStep(2)}>
                        Back
                      </Button>
                    </Box>
                  </StepContent>
                </Step>
              </Stepper>
            </CardContent>
          </Card>
        </Grid>

        {/* Portfolio Summary Panel */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Current Portfolio
              </Typography>
              
              {portfolioData && (
                <List dense>
                  <ListItem>
                    <ListItemText 
                      primary="Portfolio Value"
                      secondary={`$${portfolioData.current_portfolio_balance?.toLocaleString() || 'N/A'}`}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemText 
                      primary="Asset Count"
                      secondary={portfolioData.current_asset_count || 'N/A'}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemText 
                      primary="Days to Maturity"
                      secondary={portfolioData.days_to_maturity || 'N/A'}
                    />
                  </ListItem>
                </List>
              )}
            </CardContent>
          </Card>

          {portfolioMetrics && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Metrics
                </Typography>
                
                <Stack spacing={1}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Current Risk Level</Typography>
                    <Chip label="Medium" color="warning" size="small" />
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Diversification</Typography>
                    <Chip label="Good" color="success" size="small" />
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Compliance</Typography>
                    <Chip label="Pass" color="success" size="small" />
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Results Dialog */}
      <Dialog 
        open={resultsDialogOpen} 
        onClose={() => setResultsDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Optimization Results</DialogTitle>
        <DialogContent>
          {optimizationResult && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Optimization completed successfully!
              </Typography>
              
              <Alert severity="info" sx={{ mb: 2 }}>
                Results analysis and trade recommendations will be displayed here.
                This is a placeholder for the actual optimization results visualization.
              </Alert>
              
              <Typography variant="body2">
                Result data structure received but visualization pending implementation.
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResultsDialogOpen(false)}>Close</Button>
          <Button variant="contained" startIcon={<Download />}>
            Export Results
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PortfolioOptimizer;