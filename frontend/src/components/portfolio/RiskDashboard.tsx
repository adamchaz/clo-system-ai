import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  LinearProgress,
  useTheme,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
} from '@mui/material';
import {
  Security,
  Warning,
  TrendingUp,
  TrendingDown,
  Assessment,
  Timeline,
  BarChart,
  PieChart,
  GetApp,
  CheckCircle,
  Error,
  ShowChart,
} from '@mui/icons-material';
import {
  useGetPortfoliosQuery,
  useGetPortfolioSummaryQuery,
  useCalculateRiskMutation,
  useGetRiskHistoryQuery,
} from '../../store/api/cloApi';

interface RiskMetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
  status?: 'good' | 'warning' | 'danger';
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

const RiskMetricCard: React.FC<RiskMetricCardProps> = ({ 
  title, 
  value, 
  subtitle, 
  icon, 
  color = 'primary.main',
  status = 'good',
  trend
}) => {
  const theme = useTheme();
  
  const getStatusColor = () => {
    switch (status) {
      case 'good':
        return theme.palette.success.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'danger':
        return theme.palette.error.main;
      default:
        return color;
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'good':
        return <CheckCircle color="success" fontSize="small" />;
      case 'warning':
        return <Warning color="warning" fontSize="small" />;
      case 'danger':
        return <Error color="error" fontSize="small" />;
      default:
        return null;
    }
  };
  
  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        border: status !== 'good' ? 2 : 0,
        borderColor: getStatusColor(),
      }}
    >
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: `${getStatusColor()}15`,
              color: getStatusColor(),
              mr: 2,
            }}
          >
            {icon}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Typography
                variant="h4"
                component="div"
                sx={{
                  fontWeight: 700,
                  lineHeight: 1.2,
                  color: 'text.primary',
                }}
              >
                {value}
              </Typography>
              {getStatusIcon()}
            </Box>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 0.5 }}
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  display: 'block',
                }}
              >
                {subtitle}
              </Typography>
            )}
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {trend.isPositive ? (
                  <TrendingUp sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                ) : (
                  <TrendingDown sx={{ fontSize: 16, color: 'error.main', mr: 0.5 }} />
                )}
                <Typography
                  variant="caption"
                  sx={{
                    color: trend.isPositive ? 'success.main' : 'error.main',
                    fontWeight: 600,
                  }}
                >
                  {trend.isPositive ? '+' : ''}{trend.value}%
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
                  vs last week
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const RiskDashboard: React.FC = () => {
  const [selectedPortfolio, setSelectedPortfolio] = useState('all');
  const [currentTab, setCurrentTab] = useState(0);
  const [riskCalculationLoading, setRiskCalculationLoading] = useState(false);

  // API queries
  const {
    data: portfoliosData,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: portfolioSummary,
  } = useGetPortfolioSummaryQuery(
    selectedPortfolio !== 'all' ? selectedPortfolio : portfoliosData?.data?.[0]?.id || '',
    {
      skip: !portfoliosData?.data?.length || selectedPortfolio === 'all',
      refetchOnMountOrArgChange: true,
    }
  );

  const {} = useGetRiskHistoryQuery({
    dealId: selectedPortfolio !== 'all' ? selectedPortfolio : portfoliosData?.data?.[0]?.id || '',
    limit: 30,
  }, {
    skip: !portfoliosData?.data?.length || selectedPortfolio === 'all',
  });

  const [calculateRisk] = useCalculateRiskMutation();

  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const handlePortfolioChange = useCallback((portfolioId: string) => {
    setSelectedPortfolio(portfolioId);
  }, []);

  // const handleTimeframeChange = useCallback((timeframe: string) => {
  //   setSelectedTimeframe(timeframe);
  // }, []);

  const handleRunRiskCalculation = useCallback(async () => {
    if (selectedPortfolio === 'all' || !portfoliosData?.data?.length) return;
    
    setRiskCalculationLoading(true);
    try {
      const dealId = selectedPortfolio !== 'all' ? selectedPortfolio : portfoliosData.data[0].id;
      await calculateRisk({
        deal_id: dealId,
        risk_type: 'var',
        confidence_level: 95,
        time_horizon: 1,
      }).unwrap();
    } catch (error) {
      console.error('Risk calculation failed:', error);
    } finally {
      setRiskCalculationLoading(false);
    }
  }, [selectedPortfolio, portfoliosData, calculateRisk]);

  // Calculate aggregate risk metrics
  const aggregateMetrics = useMemo(() => {
    if (!portfoliosData?.data) return null;

    const totalPortfolios = portfoliosData.data.length;
    const activePortfolios = portfoliosData.data.filter(p => p.status === 'effective').length;
    const totalAUM = portfoliosData.data.reduce((sum, p) => sum + p.current_portfolio_balance, 0);

    return {
      totalPortfolios,
      activePortfolios,
      totalAUM,
      riskScore: 7.2, // Mock calculation
      stressTestPassed: 8,
      stressTestTotal: 10,
    };
  }, [portfoliosData]);

  const TabPanel: React.FC<{ children?: React.ReactNode; index: number; value: number }> = ({
    children,
    value,
    index,
  }) => (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );

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
            Risk Management Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor portfolio risk metrics, compliance status, and stress test results.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Portfolio</InputLabel>
            <Select
              value={selectedPortfolio}
              onChange={(e) => handlePortfolioChange(e.target.value)}
              label="Portfolio"
            >
              <MenuItem value="all">All Portfolios</MenuItem>
              {portfoliosData?.data?.map((portfolio) => (
                <MenuItem key={portfolio.id} value={portfolio.id}>
                  {portfolio.deal_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Button
            variant="contained"
            startIcon={riskCalculationLoading ? <CircularProgress size={16} /> : <Assessment />}
            onClick={handleRunRiskCalculation}
            disabled={riskCalculationLoading || selectedPortfolio === 'all'}
          >
            {riskCalculationLoading ? 'Calculating...' : 'Run Risk Analysis'}
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<GetApp />}
          >
            Export Report
          </Button>
        </Box>
      </Box>

      {/* Alert Summary */}
      {portfolioSummary?.compliance_status && !portfolioSummary.compliance_status.oc_tests_passing && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Risk Alert:</strong> OC tests are failing for {portfolioSummary.portfolio.deal_name}. 
            Immediate attention required.
          </Typography>
        </Alert>
      )}

      {/* Risk Overview Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <RiskMetricCard
            title="Overall Risk Score"
            value={aggregateMetrics?.riskScore.toFixed(1) || '0.0'}
            subtitle="Out of 10"
            icon={<Security />}
            status={aggregateMetrics && aggregateMetrics.riskScore < 5 ? 'good' : 'warning'}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <RiskMetricCard
            title="VaR (95%)"
            value="$2.3M"
            subtitle="1-day horizon"
            icon={<Timeline />}
            status="good"
            trend={{ value: -2.1, isPositive: true }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <RiskMetricCard
            title="Stress Test Results"
            value={`${aggregateMetrics?.stressTestPassed || 0}/${aggregateMetrics?.stressTestTotal || 0}`}
            subtitle="Scenarios passed"
            icon={<Assessment />}
            status={aggregateMetrics && aggregateMetrics.stressTestPassed >= 8 ? 'good' : 'warning'}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <RiskMetricCard
            title="Portfolio Correlation"
            value="0.73"
            subtitle="Average correlation"
            icon={<ShowChart />}
            status="good"
            trend={{ value: 0.8, isPositive: false }}
          />
        </Grid>
      </Grid>

      {/* Risk Analysis Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="risk analysis tabs">
          <Tab label="Portfolio Risk" />
          <Tab label="Compliance" />
          <Tab label="Concentration Risk" />
          <Tab label="Stress Testing" />
          <Tab label="Market Risk" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Portfolio Risk Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Metrics Overview
                </Typography>
                {portfolioSummary?.risk_metrics ? (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Metric</TableCell>
                          <TableCell align="right">Value</TableCell>
                          <TableCell align="right">Benchmark</TableCell>
                          <TableCell align="right">Status</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>Portfolio Value</TableCell>
                          <TableCell align="right">
                            ${(portfolioSummary.risk_metrics.portfolio_value / 1000000).toFixed(1)}M
                          </TableCell>
                          <TableCell align="right">-</TableCell>
                          <TableCell align="right">
                            <CheckCircle color="success" fontSize="small" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Weighted Average Life</TableCell>
                          <TableCell align="right">
                            {portfolioSummary.risk_metrics.weighted_average_life.toFixed(2)} years
                          </TableCell>
                          <TableCell align="right">4.5 years</TableCell>
                          <TableCell align="right">
                            {portfolioSummary.risk_metrics.weighted_average_life > 5 ? (
                              <Warning color="warning" fontSize="small" />
                            ) : (
                              <CheckCircle color="success" fontSize="small" />
                            )}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Average Rating</TableCell>
                          <TableCell align="right">
                            {portfolioSummary.risk_metrics.average_rating}
                          </TableCell>
                          <TableCell align="right">B+</TableCell>
                          <TableCell align="right">
                            <CheckCircle color="success" fontSize="small" />
                          </TableCell>
                        </TableRow>
                        {Object.entries(portfolioSummary.risk_metrics.oc_ratios).slice(0, 3).map(([test, ratio]) => (
                          <TableRow key={test}>
                            <TableCell>OC Ratio - {test}</TableCell>
                            <TableCell align="right">
                              {(ratio as number).toFixed(2)}x
                            </TableCell>
                            <TableCell align="right">
                              {test === 'Class A' ? '1.15x' : test === 'Class B' ? '1.10x' : '1.05x'}
                            </TableCell>
                            <TableCell align="right">
                              {(ratio as number) > 1.1 ? (
                                <CheckCircle color="success" fontSize="small" />
                              ) : (
                                <Warning color="warning" fontSize="small" />
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Paper
                    sx={{
                      p: 3,
                      textAlign: 'center',
                      backgroundColor: 'background.paper',
                      border: 1,
                      borderColor: 'divider',
                      borderStyle: 'dashed',
                    }}
                  >
                    <Security sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary">
                      {selectedPortfolio === 'all' 
                        ? 'Select a specific portfolio to view risk metrics'
                        : 'Loading risk metrics...'}
                    </Typography>
                  </Paper>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, lg: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Alerts
                </Typography>
                {portfolioSummary?.compliance_status ? (
                  <List>
                    {portfolioSummary.compliance_status.failed_tests.length === 0 &&
                     portfolioSummary.compliance_status.warnings.length === 0 ? (
                      <ListItem>
                        <ListItemIcon>
                          <CheckCircle color="success" />
                        </ListItemIcon>
                        <ListItemText
                          primary="All Clear"
                          secondary="No risk alerts or warnings"
                        />
                      </ListItem>
                    ) : (
                      <>
                        {portfolioSummary.compliance_status.failed_tests.map((test, index) => (
                          <ListItem key={`failed-${index}`}>
                            <ListItemIcon>
                              <Error color="error" />
                            </ListItemIcon>
                            <ListItemText
                              primary={test}
                              secondary="Failed test - requires immediate attention"
                            />
                          </ListItem>
                        ))}
                        {portfolioSummary.compliance_status.warnings.map((warning, index) => (
                          <ListItem key={`warning-${index}`}>
                            <ListItemIcon>
                              <Warning color="warning" />
                            </ListItemIcon>
                            <ListItemText
                              primary={warning}
                              secondary="Warning - monitor closely"
                            />
                          </ListItem>
                        ))}
                      </>
                    )}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {selectedPortfolio === 'all' 
                      ? 'Select a portfolio to view risk alerts'
                      : 'Loading risk alerts...'}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {/* Compliance Tab */}
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  OC/IC Test Status
                </Typography>
                {portfolioSummary?.compliance_status ? (
                  <>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Overcollateralization Tests
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {portfolioSummary.compliance_status.oc_tests_passing ? (
                          <CheckCircle color="success" />
                        ) : (
                          <Error color="error" />
                        )}
                        <Typography variant="body2" fontWeight={600}>
                          {portfolioSummary.compliance_status.oc_tests_passing ? 'Passing' : 'Failed'}
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Interest Coverage Tests
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {portfolioSummary.compliance_status.ic_tests_passing ? (
                          <CheckCircle color="success" />
                        ) : (
                          <Error color="error" />
                        )}
                        <Typography variant="body2" fontWeight={600}>
                          {portfolioSummary.compliance_status.ic_tests_passing ? 'Passing' : 'Failed'}
                        </Typography>
                      </Box>
                    </Box>

                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Concentration Tests
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {portfolioSummary.compliance_status.concentration_tests_passing ? (
                          <CheckCircle color="success" />
                        ) : (
                          <Error color="error" />
                        )}
                        <Typography variant="body2" fontWeight={600}>
                          {portfolioSummary.compliance_status.concentration_tests_passing ? 'Passing' : 'Failed'}
                        </Typography>
                      </Box>
                    </Box>
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {selectedPortfolio === 'all' 
                      ? 'Select a portfolio to view compliance status'
                      : 'Loading compliance data...'}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Compliance History
                </Typography>
                <Paper
                  sx={{
                    p: 3,
                    textAlign: 'center',
                    backgroundColor: 'background.paper',
                    border: 1,
                    borderColor: 'divider',
                    borderStyle: 'dashed',
                  }}
                >
                  <BarChart sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    Compliance trend chart coming soon
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Historical compliance performance and trends
                  </Typography>
                </Paper>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Concentration Risk Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Concentration Risk Analysis
            </Typography>
            {portfolioSummary?.risk_metrics?.concentration_metrics ? (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Concentration Type</TableCell>
                      <TableCell align="right">Current %</TableCell>
                      <TableCell align="right">Limit %</TableCell>
                      <TableCell align="right">Utilization</TableCell>
                      <TableCell align="right">Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(portfolioSummary.risk_metrics.concentration_metrics).slice(0, 10).map(([metric, value]) => {
                      const percentage = (value as number) * 100;
                      const limit = 15; // Mock limit
                      const utilization = (percentage / limit) * 100;
                      
                      return (
                        <TableRow key={metric}>
                          <TableCell>{metric.replace(/_/g, ' ').toUpperCase()}</TableCell>
                          <TableCell align="right">{percentage.toFixed(1)}%</TableCell>
                          <TableCell align="right">{limit}%</TableCell>
                          <TableCell align="right">
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <LinearProgress
                                variant="determinate"
                                value={Math.min(utilization, 100)}
                                sx={{ flexGrow: 1, height: 6 }}
                                color={utilization > 90 ? 'error' : utilization > 75 ? 'warning' : 'primary'}
                              />
                              <Typography variant="caption">
                                {utilization.toFixed(0)}%
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            {utilization > 90 ? (
                              <Error color="error" fontSize="small" />
                            ) : utilization > 75 ? (
                              <Warning color="warning" fontSize="small" />
                            ) : (
                              <CheckCircle color="success" fontSize="small" />
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Paper
                sx={{
                  p: 3,
                  textAlign: 'center',
                  backgroundColor: 'background.paper',
                  border: 1,
                  borderColor: 'divider',
                  borderStyle: 'dashed',
                }}
              >
                <PieChart sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  {selectedPortfolio === 'all' 
                    ? 'Select a portfolio to view concentration metrics'
                    : 'Loading concentration data...'}
                </Typography>
              </Paper>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Stress Testing Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Stress Testing Results
            </Typography>
            <Paper
              sx={{
                p: 3,
                textAlign: 'center',
                backgroundColor: 'background.paper',
                border: 1,
                borderColor: 'divider',
                borderStyle: 'dashed',
              }}
            >
              <Assessment sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                Stress testing module coming soon
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Monte Carlo simulations, scenario analysis, and sensitivity testing
              </Typography>
            </Paper>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={4}>
        {/* Market Risk Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Market Risk Factors
            </Typography>
            <Paper
              sx={{
                p: 3,
                textAlign: 'center',
                backgroundColor: 'background.paper',
                border: 1,
                borderColor: 'divider',
                borderStyle: 'dashed',
              }}
            >
              <Timeline sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                Market risk analysis coming soon
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Interest rate risk, credit spread risk, and correlation analysis
              </Typography>
            </Paper>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default RiskDashboard;