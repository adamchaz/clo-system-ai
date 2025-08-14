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
  Alert,
  LinearProgress,
  Tabs,
  Tab,
  Stack,
  TextField,
} from '@mui/material';
import {
  Timeline,
  PlayArrow,
  GetApp,
  Assessment,
  AccountBalance,
  TrendingUp,
  TrendingDown,
  CompareArrows,
  CheckCircle,
  Warning,
  Error,
} from '@mui/icons-material';
import { format } from 'date-fns';
import {
  useGetPortfoliosQuery,
} from '../../store/api/cloApi';

interface WaterfallAnalysisProps {
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

interface WaterfallStep {
  step: number;
  description: string;
  amount: number;
  cumulativeAmount: number;
  status: 'paid' | 'partial' | 'unpaid';
  priority: number;
}

interface TrancheData {
  id: string;
  name: string;
  size: number;
  coupon: number;
  balance: number;
  payment: number;
  status: 'current' | 'delinquent' | 'default';
}

const WaterfallAnalysis: React.FC<WaterfallAnalysisProps> = ({
  portfolioId: initialPortfolioId,
  onPortfolioChange,
}) => {
  const [selectedPortfolio, setSelectedPortfolio] = useState(initialPortfolioId || '');
  const [selectedMag, setSelectedMag] = useState('MAG-17');
  const [currentTab, setCurrentTab] = useState(0);
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState<Date | null>(null);

  // API queries
  const {
    data: portfoliosData,
    isLoading: portfoliosLoading,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  // Mock waterfall data (in production, this would come from API)
  const waterfallSteps = useMemo((): WaterfallStep[] => [
    { step: 1, description: 'Senior Management Fee', amount: 125000, cumulativeAmount: 125000, status: 'paid', priority: 1 },
    { step: 2, description: 'Trustee Fee', amount: 25000, cumulativeAmount: 150000, status: 'paid', priority: 1 },
    { step: 3, description: 'Other Senior Expenses', amount: 50000, cumulativeAmount: 200000, status: 'paid', priority: 1 },
    { step: 4, description: 'Class A-1 Interest', amount: 2400000, cumulativeAmount: 2600000, status: 'paid', priority: 2 },
    { step: 5, description: 'Class A-2 Interest', amount: 1800000, cumulativeAmount: 4400000, status: 'paid', priority: 2 },
    { step: 6, description: 'Class B Interest', amount: 750000, cumulativeAmount: 5150000, status: 'paid', priority: 3 },
    { step: 7, description: 'Class C Interest', amount: 450000, cumulativeAmount: 5600000, status: 'partial', priority: 4 },
    { step: 8, description: 'Class D Interest', amount: 320000, cumulativeAmount: 5920000, status: 'unpaid', priority: 5 },
    { step: 9, description: 'Subordinated Management Fee', amount: 75000, cumulativeAmount: 5995000, status: 'unpaid', priority: 6 },
    { step: 10, description: 'Class A-1 Principal', amount: 1200000, cumulativeAmount: 7195000, status: 'unpaid', priority: 7 },
    { step: 11, description: 'Equity Distribution', amount: 0, cumulativeAmount: 7195000, status: 'unpaid', priority: 8 },
  ], []);

  const trancheData = useMemo((): TrancheData[] => [
    { id: 'A1', name: 'Class A-1', size: 240000000, coupon: 1.2, balance: 220000000, payment: 2400000, status: 'current' },
    { id: 'A2', name: 'Class A-2', size: 150000000, coupon: 1.5, balance: 140000000, payment: 1800000, status: 'current' },
    { id: 'B', name: 'Class B', size: 50000000, coupon: 1.8, balance: 45000000, payment: 750000, status: 'current' },
    { id: 'C', name: 'Class C', size: 25000000, coupon: 2.2, balance: 22000000, payment: 225000, status: 'delinquent' },
    { id: 'D', name: 'Class D', size: 20000000, coupon: 2.8, balance: 18000000, payment: 0, status: 'default' },
    { id: 'E', name: 'Equity', size: 15000000, coupon: 0, balance: 15000000, payment: 0, status: 'default' },
  ], []);

  // Handlers
  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const handlePortfolioChange = useCallback((portfolioId: string) => {
    setSelectedPortfolio(portfolioId);
    onPortfolioChange?.(portfolioId);
  }, [onPortfolioChange]);

  const handleRunWaterfall = useCallback(async () => {
    setRunning(true);
    try {
      // Simulate waterfall calculation
      await new Promise(resolve => setTimeout(resolve, 2000));
      setLastRun(new Date());
    } finally {
      setRunning(false);
    }
  }, []);

  const getStepStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'success';
      case 'partial': return 'warning';
      case 'unpaid': return 'error';
      default: return 'default';
    }
  };

  const getTrancheStatusColor = (status: string) => {
    switch (status) {
      case 'current': return 'success';
      case 'delinquent': return 'warning';
      case 'default': return 'error';
      default: return 'default';
    }
  };

  const totalCashFlow = 7195000;
  const totalDistributed = 5600000;
  const shortfall = totalCashFlow - totalDistributed;

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
            Waterfall Analysis
          </Typography>
          <Typography variant="body1" color="text.secondary">
            CLO payment waterfall modeling and distribution analysis.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {lastRun && (
            <Typography variant="caption" color="text.secondary">
              Last run: {format(lastRun, 'MMM dd, yyyy HH:mm')}
            </Typography>
          )}
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            size="small"
            disabled={running}
          >
            Export
          </Button>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={handleRunWaterfall}
            disabled={running}
          >
            Run Waterfall
          </Button>
        </Box>
      </Box>

      {/* Controls */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Portfolio</InputLabel>
            <Select
              value={selectedPortfolio}
              onChange={(e) => handlePortfolioChange(e.target.value)}
              label="Portfolio"
              disabled={portfoliosLoading}
            >
              {portfoliosData?.data?.map((portfolio) => (
                <MenuItem key={portfolio.id} value={portfolio.id}>
                  {portfolio.deal_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Waterfall Version</InputLabel>
            <Select
              value={selectedMag}
              onChange={(e) => setSelectedMag(e.target.value)}
              label="Waterfall Version"
            >
              {Array.from({ length: 12 }, (_, i) => i + 6).map((mag) => (
                <MenuItem key={mag} value={`MAG-${mag}`}>
                  MAG-{mag} Waterfall
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
          <TextField
            fullWidth
            size="small"
            label="Payment Date"
            type="date"
            defaultValue={format(new Date(), 'yyyy-MM-dd')}
            InputLabelProps={{ shrink: true }}
          />
        </Grid>
      </Grid>

      {running && (
        <Box sx={{ mb: 3 }}>
          <Alert severity="info" icon={<Timeline />}>
            Running waterfall calculation... This may take a few moments.
          </Alert>
          <LinearProgress sx={{ mt: 1 }} />
        </Box>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <AccountBalance color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  ${(totalCashFlow / 1000000).toFixed(1)}M
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Cash Flow
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingUp color="success" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  ${(totalDistributed / 1000000).toFixed(1)}M
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Distributed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TrendingDown color="error" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  ${(shortfall / 1000000).toFixed(1)}M
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Shortfall
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Assessment color="info" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {((totalDistributed / totalCashFlow) * 100).toFixed(1)}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Coverage Ratio
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Analysis Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="waterfall analysis tabs">
          <Tab label="Waterfall Steps" />
          <Tab label="Tranche Analysis" />
          <Tab label="Scenario Comparison" />
          <Tab label="Historical Analysis" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Waterfall Steps Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Payment Waterfall - {selectedMag}
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Step</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell align="right">Amount</TableCell>
                    <TableCell align="right">Cumulative</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {waterfallSteps.map((step) => (
                    <TableRow 
                      key={step.step}
                      sx={{ 
                        '&:nth-of-type(odd)': { 
                          backgroundColor: 'background.default' 
                        }
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {step.step}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {step.description}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight={600}>
                          ${step.amount.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" color="text.secondary">
                          ${step.cumulativeAmount.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={step.priority}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={step.status}
                          size="small"
                          color={getStepStatusColor(step.status) as any}
                          icon={
                            step.status === 'paid' ? <CheckCircle /> :
                            step.status === 'partial' ? <Warning /> : <Error />
                          }
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

      <TabPanel value={currentTab} index={1}>
        {/* Tranche Analysis Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Tranche Payment Analysis
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Tranche</TableCell>
                    <TableCell align="right">Size</TableCell>
                    <TableCell align="right">Balance</TableCell>
                    <TableCell align="right">Coupon</TableCell>
                    <TableCell align="right">Payment</TableCell>
                    <TableCell align="right">Coverage</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trancheData.map((tranche) => (
                    <TableRow key={tranche.id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {tranche.name}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          ${(tranche.size / 1000000).toFixed(0)}M
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          ${(tranche.balance / 1000000).toFixed(0)}M
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {tranche.coupon.toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight={600}>
                          ${tranche.payment.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography 
                          variant="body2" 
                          color={tranche.payment > 0 ? 'success.main' : 'error.main'}
                          fontWeight={600}
                        >
                          {tranche.payment > 0 ? '100%' : '0%'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={tranche.status}
                          size="small"
                          color={getTrancheStatusColor(tranche.status) as any}
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

      <TabPanel value={currentTab} index={2}>
        {/* Scenario Comparison Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Base vs Stress Scenario
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
                    <CompareArrows sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                    <Typography variant="h6" gutterBottom>
                      Scenario Comparison Chart
                    </Typography>
                    <Typography variant="body2">
                      Waterfall performance under different stress scenarios
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
                  Scenario Summary
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" fontWeight={600} gutterBottom>
                      Base Case
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Coverage: 77.8% • Shortfall: $1.6M
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" fontWeight={600} gutterBottom>
                      Mild Stress
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Coverage: 65.2% • Shortfall: $2.5M
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" fontWeight={600} gutterBottom>
                      Severe Stress
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Coverage: 42.1% • Shortfall: $4.2M
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Historical Analysis Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Historical Waterfall Performance
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
                  Historical Analysis Chart
                </Typography>
                <Typography variant="body2">
                  Waterfall performance trends over time with payment history
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                  Chart integration required for time series visualization
                </Typography>
              </Box>
            </Paper>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default WaterfallAnalysis;