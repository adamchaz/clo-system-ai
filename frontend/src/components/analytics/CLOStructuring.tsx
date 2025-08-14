import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  TextField,
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Calculate,
  TrendingUp,
  Assessment,
  AccountBalance,
  Speed,
  GetApp,
  Add,
  Edit,
  Save,
  Cancel,
  Tune,
  Timeline,
  PieChart,
} from '@mui/icons-material';

interface CLOStructuringProps {
  dealId?: string;
  onDealChange?: (dealId: string) => void;
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

interface TrancheStructure {
  id: string;
  name: string;
  rating: string;
  size: number;
  coupon: number;
  spread: number;
  subordination: number;
  maturity: string;
  callable: boolean;
}

// interface OptimizationConstraint {
//   type: 'oc_ratio' | 'ic_ratio' | 'warf' | 'diversity' | 'concentration';
//   minValue?: number;
//   maxValue?: number;
//   targetValue?: number;
//   weight: number;
// }

interface DealMetrics {
  totalSize: number;
  weightedAverageCoupon: number;
  weightedAverageSpread: number;
  diversityScore: number;
  ocRatio: number;
  icRatio: number;
  expectedYield: number;
  riskScore: number;
}

const CLOStructuring: React.FC<CLOStructuringProps> = ({
  dealId: _dealId,
  onDealChange: _onDealChange,
}) => {
  const theme = useTheme();
  const [currentTab, setCurrentTab] = useState(0);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizationProgress, setOptimizationProgress] = useState(0);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedTranche, setSelectedTranche] = useState<TrancheStructure | null>(null);

  // Default tranche structure
  const [trancheStructure, setTrancheStructure] = useState<TrancheStructure[]>([
    { id: 'A1', name: 'Class A-1', rating: 'AAA', size: 240000000, coupon: 1.2, spread: 85, subordination: 68, maturity: '2027-07-20', callable: true },
    { id: 'A2', name: 'Class A-2', rating: 'AAA', size: 150000000, coupon: 1.5, spread: 110, subordination: 52, maturity: '2027-07-20', callable: true },
    { id: 'B', name: 'Class B', rating: 'AA', size: 50000000, coupon: 1.8, spread: 140, subordination: 42, maturity: '2027-07-20', callable: false },
    { id: 'C', name: 'Class C', rating: 'A', size: 25000000, coupon: 2.2, spread: 180, subordination: 37, maturity: '2027-07-20', callable: false },
    { id: 'D', name: 'Class D', rating: 'BBB', size: 20000000, coupon: 2.8, spread: 250, subordination: 33, maturity: '2027-07-20', callable: false },
    { id: 'E', name: 'Equity', rating: 'NR', size: 15000000, coupon: 0, spread: 0, subordination: 0, maturity: '2027-07-20', callable: false },
  ]);

  // Optimization constraints (unused for now)
  // const [constraints, setConstraints] = useState<OptimizationConstraint[]>([
  //   { type: 'oc_ratio', minValue: 110, weight: 0.3 },
  //   { type: 'ic_ratio', minValue: 120, weight: 0.25 },
  //   { type: 'warf', maxValue: 2800, weight: 0.2 },
  //   { type: 'diversity', minValue: 60, weight: 0.15 },
  //   { type: 'concentration', maxValue: 2.0, weight: 0.1 },
  // ]);

  // Calculate deal metrics
  const dealMetrics = useMemo((): DealMetrics => {
    const totalSize = trancheStructure.reduce((sum, t) => sum + t.size, 0);
    const weightedAverageCoupon = trancheStructure.reduce((sum, t) => sum + (t.coupon * t.size), 0) / totalSize;
    const weightedAverageSpread = trancheStructure.reduce((sum, t) => sum + (t.spread * t.size), 0) / totalSize;
    
    return {
      totalSize,
      weightedAverageCoupon,
      weightedAverageSpread,
      diversityScore: 64.2,
      ocRatio: 112.5,
      icRatio: 125.8,
      expectedYield: 8.7,
      riskScore: 7.2,
    };
  }, [trancheStructure]);

  // Handlers
  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const handleOptimization = useCallback(async () => {
    setOptimizing(true);
    setOptimizationProgress(0);
    
    // Simulate optimization process
    const interval = setInterval(() => {
      setOptimizationProgress(prev => {
        const next = prev + Math.random() * 15;
        if (next >= 100) {
          clearInterval(interval);
          setOptimizing(false);
          return 100;
        }
        return next;
      });
    }, 300);

    // Clean up after completion
    setTimeout(() => {
      clearInterval(interval);
      setOptimizing(false);
      setOptimizationProgress(100);
    }, 6000);
  }, []);

  const handleEditTranche = useCallback((tranche: TrancheStructure) => {
    setSelectedTranche(tranche);
    setEditDialogOpen(true);
  }, []);

  const handleSaveTranche = useCallback(() => {
    if (selectedTranche) {
      setTrancheStructure(prev => prev.map(t => 
        t.id === selectedTranche.id ? selectedTranche : t
      ));
    }
    setEditDialogOpen(false);
    setSelectedTranche(null);
  }, [selectedTranche]);

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'AAA': return theme.palette.success.main;
      case 'AA': return theme.palette.info.main;
      case 'A': return theme.palette.warning.main;
      case 'BBB': return theme.palette.warning.main;
      case 'BB': return theme.palette.error.main;
      default: return theme.palette.grey[500];
    }
  };

  // Helper function for constraint validation (unused for now)
  // const getConstraintStatus = (constraint: OptimizationConstraint, actualValue: number) => {
  //   if (constraint.minValue && actualValue < constraint.minValue) return 'error';
  //   if (constraint.maxValue && actualValue > constraint.maxValue) return 'error';
  //   if (constraint.targetValue) {
  //     const diff = Math.abs(actualValue - constraint.targetValue) / constraint.targetValue;
  //     return diff < 0.05 ? 'success' : diff < 0.1 ? 'warning' : 'error';
  //   }
  //   return 'success';
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
            CLO Structuring & Optimization
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Advanced CLO deal structuring, tranche optimization, and risk constraint management.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            size="small"
          >
            Export Structure
          </Button>
          <Button
            variant="contained"
            startIcon={<Calculate />}
            onClick={handleOptimization}
            disabled={optimizing}
          >
            {optimizing ? 'Optimizing...' : 'Optimize Structure'}
          </Button>
        </Box>
      </Box>

      {/* Optimization Status */}
      {optimizing && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography>
              Running structural optimization... {optimizationProgress.toFixed(0)}% complete
            </Typography>
          </Box>
          <LinearProgress variant="determinate" value={optimizationProgress} sx={{ mt: 1 }} />
        </Alert>
      )}

      {/* Deal Metrics Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalance color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  ${(dealMetrics.totalSize / 1000000).toFixed(0)}M
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Deal Size
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Assessment color="success" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {dealMetrics.ocRatio.toFixed(1)}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                O/C Ratio
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Speed color="info" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {dealMetrics.expectedYield.toFixed(1)}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Expected Yield
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUp color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {dealMetrics.riskScore.toFixed(1)}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Risk Score
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Structuring Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="clo structuring tabs">
          <Tab label="Tranche Structure" />
          <Tab label="Optimization" />
          <Tab label="Constraints" />
          <Tab label="Analysis" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Tranche Structure Tab */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Capital Structure
              </Typography>
              <Button
                variant="outlined"
                startIcon={<Add />}
                size="small"
              >
                Add Tranche
              </Button>
            </Box>
            
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Class</TableCell>
                    <TableCell>Rating</TableCell>
                    <TableCell align="right">Size (M)</TableCell>
                    <TableCell align="right">%</TableCell>
                    <TableCell align="right">Coupon</TableCell>
                    <TableCell align="right">Spread</TableCell>
                    <TableCell align="right">Subordination</TableCell>
                    <TableCell>Callable</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trancheStructure.map((tranche) => {
                    const percentage = (tranche.size / dealMetrics.totalSize) * 100;
                    
                    return (
                      <TableRow key={tranche.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight={600}>
                            {tranche.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={tranche.rating}
                            size="small"
                            sx={{ 
                              bgcolor: `${getRatingColor(tranche.rating)}20`,
                              color: getRatingColor(tranche.rating),
                              fontWeight: 600,
                            }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight={600}>
                            ${(tranche.size / 1000000).toFixed(0)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {percentage.toFixed(1)}%
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={percentage}
                            sx={{ mt: 0.5, height: 4 }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {tranche.coupon > 0 ? `${tranche.coupon.toFixed(1)}%` : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {tranche.spread > 0 ? `+${tranche.spread}` : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2">
                            {tranche.subordination.toFixed(1)}%
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={tranche.callable ? 'Yes' : 'No'}
                            size="small"
                            color={tranche.callable ? 'success' : 'default'}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton 
                            size="small" 
                            onClick={() => handleEditTranche(tranche)}
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {/* Optimization Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Optimization Objectives
                </Typography>
                <Stack spacing={3}>
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Target Yield: 8.5%
                    </Typography>
                    <Slider
                      value={8.5}
                      min={6}
                      max={12}
                      step={0.1}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(value) => `${value}%`}
                    />
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Risk Tolerance: 7.0
                    </Typography>
                    <Slider
                      value={7.0}
                      min={5}
                      max={10}
                      step={0.1}
                      valueLabelDisplay="auto"
                    />
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Credit Quality Weight: 30%
                    </Typography>
                    <Slider
                      value={30}
                      min={0}
                      max={50}
                      step={5}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(value) => `${value}%`}
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
                  Optimization Results
                </Typography>
                <Paper
                  sx={{
                    p: 3,
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
                    <Timeline sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                    <Typography variant="h6" gutterBottom>
                      Optimization Convergence
                    </Typography>
                    <Typography variant="body2">
                      Optimization progress and convergence analysis
                    </Typography>
                  </Box>
                </Paper>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Constraints Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Regulatory & Risk Constraints
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Constraint Type</TableCell>
                    <TableCell align="right">Target/Limit</TableCell>
                    <TableCell align="right">Current Value</TableCell>
                    <TableCell align="right">Weight</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>O/C Ratio</TableCell>
                    <TableCell align="right">≥ 110%</TableCell>
                    <TableCell align="right">{dealMetrics.ocRatio.toFixed(1)}%</TableCell>
                    <TableCell align="right">30%</TableCell>
                    <TableCell>
                      <Chip label="Pass" color="success" size="small" />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small">
                        <Tune fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>I/C Ratio</TableCell>
                    <TableCell align="right">≥ 120%</TableCell>
                    <TableCell align="right">{dealMetrics.icRatio.toFixed(1)}%</TableCell>
                    <TableCell align="right">25%</TableCell>
                    <TableCell>
                      <Chip label="Pass" color="success" size="small" />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small">
                        <Tune fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>WARF</TableCell>
                    <TableCell align="right">≤ 2,800</TableCell>
                    <TableCell align="right">2,652</TableCell>
                    <TableCell align="right">20%</TableCell>
                    <TableCell>
                      <Chip label="Pass" color="success" size="small" />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small">
                        <Tune fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Diversity Score</TableCell>
                    <TableCell align="right">≥ 60</TableCell>
                    <TableCell align="right">{dealMetrics.diversityScore.toFixed(1)}</TableCell>
                    <TableCell align="right">15%</TableCell>
                    <TableCell>
                      <Chip label="Pass" color="success" size="small" />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small">
                        <Tune fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Max Single Obligor</TableCell>
                    <TableCell align="right">≤ 2.0%</TableCell>
                    <TableCell align="right">1.8%</TableCell>
                    <TableCell align="right">10%</TableCell>
                    <TableCell>
                      <Chip label="Pass" color="success" size="small" />
                    </TableCell>
                    <TableCell>
                      <IconButton size="small">
                        <Tune fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Analysis Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Capital Structure Analysis
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
                      Tranche Distribution
                    </Typography>
                    <Typography variant="body2">
                      Visual breakdown of tranche sizing and subordination
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
                  Key Metrics
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Weighted Avg. Coupon
                    </Typography>
                    <Typography variant="h6" fontWeight={600}>
                      {dealMetrics.weightedAverageCoupon.toFixed(2)}%
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Weighted Avg. Spread
                    </Typography>
                    <Typography variant="h6" fontWeight={600}>
                      +{dealMetrics.weightedAverageSpread.toFixed(0)} bps
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Total Subordination
                    </Typography>
                    <Typography variant="h6" fontWeight={600}>
                      33.0%
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Equity Enhancement
                    </Typography>
                    <Typography variant="h6" fontWeight={600}>
                      15.0%
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Edit Tranche Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit {selectedTranche?.name}</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Tranche Name"
              fullWidth
              value={selectedTranche?.name || ''}
              onChange={(e) => setSelectedTranche(prev => prev ? {...prev, name: e.target.value} : null)}
            />
            <TextField
              label="Size (USD)"
              fullWidth
              type="number"
              value={selectedTranche?.size || 0}
              onChange={(e) => setSelectedTranche(prev => prev ? {...prev, size: parseInt(e.target.value)} : null)}
            />
            <TextField
              label="Coupon (%)"
              fullWidth
              type="number"
              inputProps={{ step: 0.1 }}
              value={selectedTranche?.coupon || 0}
              onChange={(e) => setSelectedTranche(prev => prev ? {...prev, coupon: parseFloat(e.target.value)} : null)}
            />
            <TextField
              label="Spread (bps)"
              fullWidth
              type="number"
              value={selectedTranche?.spread || 0}
              onChange={(e) => setSelectedTranche(prev => prev ? {...prev, spread: parseInt(e.target.value)} : null)}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)} startIcon={<Cancel />}>
            Cancel
          </Button>
          <Button onClick={handleSaveTranche} variant="contained" startIcon={<Save />}>
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CLOStructuring;