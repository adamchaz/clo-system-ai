import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Alert,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Checkbox,
  ListItemText,
  Tooltip,
  Avatar,
  Divider,
  useTheme,
} from '@mui/material';
import {
  Close,
  Add,
  GetApp,
  SwapHoriz,
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Assessment,
  Security,
  Timeline,
  CompareArrows,
} from '@mui/icons-material';
import { format, parseISO, differenceInDays } from 'date-fns';
import {
  useGetPortfoliosQuery,
  useGetPortfolioSummaryQuery,
  Portfolio,
} from '../../store/api/cloApi';

interface PortfolioComparisonProps {
  initialPortfolios?: Portfolio[];
  onClose?: () => void;
}

interface ComparisonMetric {
  label: string;
  key: string;
  format: (value: any) => string;
  category: 'basic' | 'financial' | 'risk' | 'performance' | 'dates';
}

const comparisonMetrics: ComparisonMetric[] = [
  // Basic Information
  { label: 'Deal Name', key: 'deal_name', format: (v) => v, category: 'basic' },
  { label: 'Manager', key: 'manager', format: (v) => v, category: 'basic' },
  { label: 'Trustee', key: 'trustee', format: (v) => v, category: 'basic' },
  { label: 'Currency', key: 'currency', format: (v) => v, category: 'basic' },
  { label: 'Status', key: 'status', format: (v) => v, category: 'basic' },
  
  // Financial Metrics
  { label: 'Deal Size', key: 'deal_size', format: (v) => `$${(v / 1000000).toFixed(1)}M`, category: 'financial' },
  { label: 'Current NAV', key: 'current_portfolio_balance', format: (v) => `$${(v / 1000000).toFixed(1)}M`, category: 'financial' },
  { label: 'Asset Count', key: 'current_asset_count', format: (v) => v.toString(), category: 'financial' },
  
  // Performance Metrics
  { label: 'NAV vs Deal Size', key: 'nav_performance', format: (v) => `${v > 0 ? '+' : ''}${v.toFixed(2)}%`, category: 'performance' },
  { label: 'Portfolio Utilization', key: 'utilization', format: (v) => `${v.toFixed(1)}%`, category: 'performance' },
  
  // Date Information
  { label: 'Effective Date', key: 'effective_date', format: (v) => format(parseISO(v), 'MMM d, yyyy'), category: 'dates' },
  { label: 'Maturity Date', key: 'stated_maturity', format: (v) => format(parseISO(v), 'MMM d, yyyy'), category: 'dates' },
  { label: 'Days to Maturity', key: 'days_to_maturity', format: (v) => `${v} days`, category: 'dates' },
  { label: 'Revolving Period End', key: 'revolving_period_end', format: (v) => v ? format(parseISO(v), 'MMM d, yyyy') : 'N/A', category: 'dates' },
  { label: 'Reinvestment Period End', key: 'reinvestment_period_end', format: (v) => v ? format(parseISO(v), 'MMM d, yyyy') : 'N/A', category: 'dates' },
];

const categories = [
  { value: 'basic', label: 'Basic Information' },
  { value: 'financial', label: 'Financial Metrics' },
  { value: 'performance', label: 'Performance' },
  { value: 'dates', label: 'Timeline' },
];

const PortfolioComparison: React.FC<PortfolioComparisonProps> = ({
  initialPortfolios = [],
  onClose,
}) => {
  const theme = useTheme();
  const [selectedPortfolioIds, setSelectedPortfolioIds] = useState<string[]>(
    initialPortfolios.map(p => p.id)
  );
  const [visibleCategories, setVisibleCategories] = useState<string[]>(['basic', 'financial', 'performance']);
  const [highlightDifferences, setHighlightDifferences] = useState(true);

  // API queries
  const {
    data: portfoliosData,
    isLoading: portfoliosLoading,
    error: portfoliosError,
  } = useGetPortfoliosQuery();

  const portfolios = portfoliosData?.data || [];
  const selectedPortfolios = portfolios.filter(p => selectedPortfolioIds.includes(p.id));

  // Calculate derived metrics for comparison
  const portfoliosWithMetrics = useMemo(() => {
    return selectedPortfolios.map(portfolio => ({
      ...portfolio,
      nav_performance: ((portfolio.current_portfolio_balance / portfolio.deal_size) - 1) * 100,
      utilization: (portfolio.current_portfolio_balance / portfolio.deal_size) * 100,
    }));
  }, [selectedPortfolios]);

  // Filter metrics by visible categories
  const visibleMetrics = comparisonMetrics.filter(metric => 
    visibleCategories.includes(metric.category)
  );

  // Handle portfolio selection
  const handlePortfolioSelection = useCallback((portfolioIds: string[]) => {
    setSelectedPortfolioIds(portfolioIds);
  }, []);

  const handleAddPortfolio = useCallback((portfolioId: string) => {
    if (!selectedPortfolioIds.includes(portfolioId)) {
      setSelectedPortfolioIds(prev => [...prev, portfolioId]);
    }
  }, [selectedPortfolioIds]);

  const handleRemovePortfolio = useCallback((portfolioId: string) => {
    setSelectedPortfolioIds(prev => prev.filter(id => id !== portfolioId));
  }, []);

  // Check if values are different across portfolios for highlighting
  const areValuesDifferent = (key: string): boolean => {
    if (!highlightDifferences || portfoliosWithMetrics.length < 2) return false;
    
    const values = portfoliosWithMetrics.map(p => {
      // Handle nested properties and calculated fields
      if (key === 'nav_performance' || key === 'utilization') {
        return (p as any)[key];
      }
      return (p as any)[key];
    });
    
    // Check if all values are the same
    const firstValue = JSON.stringify(values[0]);
    return values.some(v => JSON.stringify(v) !== firstValue);
  };

  // Get best/worst values for performance highlighting
  const getPerformanceIndicator = (key: string, value: any) => {
    if (!highlightDifferences || portfoliosWithMetrics.length < 2) return null;
    
    const numericKeys = ['deal_size', 'current_portfolio_balance', 'current_asset_count', 'nav_performance', 'utilization'];
    if (!numericKeys.includes(key)) return null;
    
    const values = portfoliosWithMetrics.map(p => (p as any)[key]).filter(v => v != null);
    if (values.length < 2) return null;
    
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);
    
    // For some metrics, higher is better, for others lower is better
    const higherIsBetter = ['current_portfolio_balance', 'current_asset_count', 'nav_performance', 'utilization'];
    
    if (value === maxValue && higherIsBetter.includes(key)) return 'best';
    if (value === minValue && !higherIsBetter.includes(key)) return 'best';
    if (value === minValue && higherIsBetter.includes(key)) return 'worst';
    if (value === maxValue && !higherIsBetter.includes(key)) return 'worst';
    
    return null;
  };

  const getCellStyle = (indicator: string | null, isDifferent: boolean) => {
    if (!indicator && !isDifferent) return {};
    
    const baseStyle = isDifferent ? { 
      borderLeft: `3px solid ${theme.palette.primary.main}`,
      backgroundColor: theme.palette.action.hover,
    } : {};
    
    if (indicator === 'best') {
      return {
        ...baseStyle,
        backgroundColor: theme.palette.success.light + '20',
        borderLeft: `3px solid ${theme.palette.success.main}`,
      };
    }
    
    if (indicator === 'worst') {
      return {
        ...baseStyle,
        backgroundColor: theme.palette.error.light + '20',
        borderLeft: `3px solid ${theme.palette.error.main}`,
      };
    }
    
    return baseStyle;
  };

  if (portfoliosError) {
    return (
      <Alert severity="error">
        Failed to load portfolio data for comparison.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            <CompareArrows sx={{ mr: 1, verticalAlign: 'middle' }} />
            Portfolio Comparison
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Compare key metrics across multiple portfolios side by side
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            disabled={selectedPortfolioIds.length === 0}
          >
            Export
          </Button>
          {onClose && (
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Portfolio Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Select Portfolios to Compare
          </Typography>
          
          <Grid container spacing={3} alignItems="center">
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Portfolios</InputLabel>
                <Select
                  multiple
                  value={selectedPortfolioIds}
                  onChange={(e) => handlePortfolioSelection(e.target.value as string[])}
                  input={<OutlinedInput label="Portfolios" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => {
                        const portfolio = portfolios.find(p => p.id === value);
                        return (
                          <Chip
                            key={value}
                            label={portfolio?.deal_name || value}
                            size="small"
                            onDelete={() => handleRemovePortfolio(value)}
                            deleteIcon={<Close />}
                          />
                        );
                      })}
                    </Box>
                  )}
                  disabled={portfoliosLoading}
                >
                  {portfolios.map((portfolio) => (
                    <MenuItem key={portfolio.id} value={portfolio.id}>
                      <Checkbox checked={selectedPortfolioIds.indexOf(portfolio.id) > -1} />
                      <ListItemText 
                        primary={portfolio.deal_name}
                        secondary={`${portfolio.manager} • $${(portfolio.deal_size / 1000000).toFixed(1)}M`}
                      />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, md: 4 }}>
              <FormControl fullWidth>
                <InputLabel>Visible Categories</InputLabel>
                <Select
                  multiple
                  value={visibleCategories}
                  onChange={(e) => setVisibleCategories(e.target.value as string[])}
                  input={<OutlinedInput label="Visible Categories" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => {
                        const category = categories.find(c => c.value === value);
                        return (
                          <Chip
                            key={value}
                            label={category?.label || value}
                            size="small"
                            variant="outlined"
                          />
                        );
                      })}
                    </Box>
                  )}
                >
                  {categories.map((category) => (
                    <MenuItem key={category.value} value={category.value}>
                      <Checkbox checked={visibleCategories.indexOf(category.value) > -1} />
                      <ListItemText primary={category.label} />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, md: 2 }}>
              <Button
                variant="outlined"
                startIcon={<SwapHoriz />}
                onClick={() => setHighlightDifferences(!highlightDifferences)}
                color={highlightDifferences ? 'primary' : 'inherit'}
              >
                Highlight Differences
              </Button>
            </Grid>
          </Grid>

          {selectedPortfolioIds.length === 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Select at least one portfolio to begin comparison.
            </Alert>
          )}
          
          {selectedPortfolioIds.length > 5 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              Comparing more than 5 portfolios may affect readability. Consider reducing the selection.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Comparison Table */}
      {selectedPortfolioIds.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Portfolio Comparison Matrix
            </Typography>
            
            {portfoliosLoading ? (
              <Box sx={{ py: 4 }}>
                <LinearProgress />
                <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
                  Loading portfolio data...
                </Typography>
              </Box>
            ) : (
              <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 600 }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700, minWidth: 200, bgcolor: 'background.paper' }}>
                        Metric
                      </TableCell>
                      {portfoliosWithMetrics.map((portfolio) => (
                        <TableCell 
                          key={portfolio.id}
                          sx={{ 
                            fontWeight: 700, 
                            minWidth: 150,
                            bgcolor: 'background.paper',
                            textAlign: 'center',
                          }}
                        >
                          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <Avatar sx={{ mb: 1, bgcolor: 'primary.main', width: 32, height: 32 }}>
                              <AccountBalance fontSize="small" />
                            </Avatar>
                            <Typography variant="body2" fontWeight={600}>
                              {portfolio.deal_name}
                            </Typography>
                            <Chip
                              label={portfolio.status === 'effective' ? 'Active' : portfolio.status}
                              color={portfolio.status === 'effective' ? 'success' : 'default'}
                              size="small"
                              sx={{ mt: 0.5 }}
                            />
                          </Box>
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {categories.map((category) => (
                      visibleCategories.includes(category.value) && (
                        <React.Fragment key={category.value}>
                          {/* Category Header */}
                          <TableRow>
                            <TableCell 
                              colSpan={portfoliosWithMetrics.length + 1}
                              sx={{ 
                                bgcolor: 'action.hover',
                                fontWeight: 700,
                                color: 'primary.main',
                                borderTop: 1,
                                borderColor: 'divider',
                              }}
                            >
                              {category.label}
                            </TableCell>
                          </TableRow>
                          
                          {/* Category Metrics */}
                          {visibleMetrics
                            .filter(metric => metric.category === category.value)
                            .map((metric) => {
                              const isDifferent = areValuesDifferent(metric.key);
                              
                              return (
                                <TableRow key={metric.key} hover>
                                  <TableCell sx={{ fontWeight: 600 }}>
                                    {metric.label}
                                  </TableCell>
                                  {portfoliosWithMetrics.map((portfolio) => {
                                    const value = (portfolio as any)[metric.key];
                                    const indicator = getPerformanceIndicator(metric.key, value);
                                    
                                    return (
                                      <TableCell 
                                        key={portfolio.id}
                                        sx={{
                                          textAlign: 'center',
                                          ...getCellStyle(indicator, isDifferent),
                                        }}
                                      >
                                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                          <Typography variant="body2">
                                            {value != null ? metric.format(value) : 'N/A'}
                                          </Typography>
                                          {indicator === 'best' && (
                                            <Tooltip title="Best value">
                                              <TrendingUp color="success" sx={{ ml: 0.5, fontSize: 16 }} />
                                            </Tooltip>
                                          )}
                                          {indicator === 'worst' && (
                                            <Tooltip title="Needs attention">
                                              <TrendingDown color="error" sx={{ ml: 0.5, fontSize: 16 }} />
                                            </Tooltip>
                                          )}
                                        </Box>
                                      </TableCell>
                                    );
                                  })}
                                </TableRow>
                              );
                            })}
                        </React.Fragment>
                      )
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
            
            {/* Legend */}
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Legend:
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ 
                      width: 16, 
                      height: 16, 
                      bgcolor: theme.palette.success.light + '20',
                      border: `2px solid ${theme.palette.success.main}`,
                      mr: 1,
                    }} />
                    <Typography variant="caption">Best performing value</Typography>
                  </Box>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ 
                      width: 16, 
                      height: 16, 
                      bgcolor: theme.palette.error.light + '20',
                      border: `2px solid ${theme.palette.error.main}`,
                      mr: 1,
                    }} />
                    <Typography variant="caption">Needs attention</Typography>
                  </Box>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ 
                      width: 16, 
                      height: 16, 
                      bgcolor: theme.palette.action.hover,
                      border: `2px solid ${theme.palette.primary.main}`,
                      mr: 1,
                    }} />
                    <Typography variant="caption">Different values</Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default PortfolioComparison;