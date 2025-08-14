import React, { useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Stack,
  Grid,
  LinearProgress,
  useTheme,
} from '@mui/material';
import {
  AccountBalance,
  TrendingUp,
  TrendingDown,
  Assessment,
} from '@mui/icons-material';
import { useGetPortfoliosQuery } from '../../store/api/cloApi';

interface PortfolioSummaryViewProps {
  portfolioId?: string;
  showAllPortfolios?: boolean;
}

const PortfolioSummaryView: React.FC<PortfolioSummaryViewProps> = ({
  portfolioId,
  showAllPortfolios = true,
}) => {
  const theme = useTheme();

  const {
    data: portfoliosData,
    isLoading: portfoliosLoading,
    error: portfoliosError,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const displayPortfolios = useMemo(() => {
    if (!portfoliosData?.data) return [];
    
    if (portfolioId) {
      return portfoliosData.data.filter(p => p.id === portfolioId);
    }
    
    return showAllPortfolios ? portfoliosData.data : portfoliosData.data.slice(0, 5);
  }, [portfoliosData, portfolioId, showAllPortfolios]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'effective':
        return 'success';
      case 'pending':
        return 'warning';
      case 'inactive':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPerformanceColor = (performance: number) => {
    if (performance > 8) return theme.palette.success.main;
    if (performance > 5) return theme.palette.info.main;
    if (performance > 0) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  // Mock performance data (in production would come from API)
  const mockPerformanceData = (portfolioBalance: number) => {
    const basePerformance = (portfolioBalance / 10000000) + Math.random() * 10;
    return {
      ytdReturn: parseFloat((basePerformance - 2 + Math.random() * 4).toFixed(2)),
      monthlyReturn: parseFloat((Math.random() * 3 - 1).toFixed(2)),
      volatility: parseFloat((Math.random() * 15 + 5).toFixed(2)),
      sharpeRatio: parseFloat((Math.random() * 2 + 0.5).toFixed(2)),
    };
  };

  if (portfoliosLoading) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Portfolio Summary</Typography>
          <LinearProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Loading portfolio data...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (portfoliosError) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom color="error">
            Error Loading Portfolios
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Unable to load portfolio data. Please refresh the page or contact support.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      {/* Summary Statistics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalance color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {displayPortfolios.length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Portfolios
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
                  ${(displayPortfolios.reduce((sum, p) => sum + p.current_portfolio_balance, 0) / 1000000).toFixed(1)}M
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total AUM
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUp color="info" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  {displayPortfolios.filter(p => p.status === 'effective').length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Active Portfolios
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
                  {displayPortfolios.reduce((sum, p) => sum + p.current_asset_count, 0)}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Assets
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detailed Portfolio Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Portfolio Details
          </Typography>
          
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Portfolio Name</TableCell>
                  <TableCell align="right">Current Balance</TableCell>
                  <TableCell align="right">Assets</TableCell>
                  <TableCell align="right">YTD Return</TableCell>
                  <TableCell align="right">Monthly Return</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Days to Maturity</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {displayPortfolios.map((portfolio) => {
                  const performance = mockPerformanceData(portfolio.current_portfolio_balance);
                  
                  return (
                    <TableRow key={portfolio.id} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {portfolio.deal_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {portfolio.currency} • Size: ${(portfolio.deal_size / 1000000).toFixed(0)}M
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight={600}>
                          ${(portfolio.current_portfolio_balance / 1000000).toFixed(1)}M
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2">
                          {portfolio.current_asset_count}
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                          {performance.ytdReturn > 0 ? (
                            <TrendingUp sx={{ fontSize: 16, mr: 0.5, color: 'success.main' }} />
                          ) : (
                            <TrendingDown sx={{ fontSize: 16, mr: 0.5, color: 'error.main' }} />
                          )}
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            sx={{ color: getPerformanceColor(performance.ytdReturn) }}
                          >
                            {performance.ytdReturn > 0 ? '+' : ''}{performance.ytdReturn}%
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          sx={{ 
                            color: performance.monthlyReturn > 0 ? 'success.main' : 'error.main',
                            fontWeight: 500,
                          }}
                        >
                          {performance.monthlyReturn > 0 ? '+' : ''}{performance.monthlyReturn}%
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={portfolio.status}
                          size="small"
                          color={getStatusColor(portfolio.status) as any}
                          variant="outlined"
                        />
                      </TableCell>
                      
                      <TableCell align="right">
                        <Stack alignItems="flex-end" spacing={0.5}>
                          <Typography variant="body2" fontWeight={600}>
                            {portfolio.days_to_maturity}
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={Math.max(0, Math.min(100, (365 - portfolio.days_to_maturity) / 365 * 100))}
                            sx={{ width: 60, height: 4 }}
                          />
                        </Stack>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>

          {!showAllPortfolios && (portfoliosData?.data?.length || 0) > 5 && (
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Showing 5 of {portfoliosData?.data?.length} portfolios. 
                View the full portfolio list for complete details.
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default PortfolioSummaryView;