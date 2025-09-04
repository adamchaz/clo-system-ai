import React, { useState, useCallback, useMemo } from 'react';
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
  TablePagination,
  Paper,
  Button,
  IconButton,
  Chip,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Tooltip,
  Menu,
  MenuList,
  ListItemIcon,
  ListItemText,
  Avatar,
  LinearProgress,
  Collapse,
} from '@mui/material';
import {
  Search,
  Add,
  Visibility,
  Edit,
  Delete,
  MoreVert,
  FilterList,
  Refresh,
  GetApp,
  Assessment,
  TrendingUp,
  TrendingDown,
  AccountBalance,
  DateRange,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import {
  useGetPortfoliosQuery,
  Portfolio,
} from '../../store/api/cloApi';
import { AnalysisDatePicker } from '../common/UI';

interface PortfolioListProps {
  onPortfolioSelect?: (portfolio: Portfolio) => void;
  onPortfolioEdit?: (portfolio: Portfolio) => void;
  onPortfolioCreate?: () => void;
  onPortfolioView?: (portfolio: Portfolio) => void;
}

interface PortfolioFilters {
  search: string;
  status: string;
  manager: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

const PortfolioList: React.FC<PortfolioListProps> = ({
  onPortfolioSelect,
  onPortfolioEdit,
  onPortfolioCreate,
  onPortfolioView,
}) => {
  // State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [filters, setFilters] = useState<PortfolioFilters>({
    search: '',
    status: '',
    manager: '',
    sortBy: 'deal_name',
    sortOrder: 'asc',
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [menuPortfolio, setMenuPortfolio] = useState<Portfolio | null>(null);
  const [analysisDate, setAnalysisDate] = useState<string>('2016-03-23');
  const [showDatePicker, setShowDatePicker] = useState(false);

  // API hooks
  const {
    data: portfoliosData,
    isLoading,
    error,
    refetch,
  } = useGetPortfoliosQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  // Filtered and sorted data
  const filteredPortfolios = useMemo(() => {
    if (!portfoliosData?.data) return [];
    
    let filtered = [...portfoliosData.data];
    
    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(portfolio =>
        portfolio.deal_name.toLowerCase().includes(searchLower) ||
        portfolio.manager.toLowerCase().includes(searchLower) ||
        portfolio.trustee.toLowerCase().includes(searchLower)
      );
    }
    
    // Apply status filter
    if (filters.status) {
      filtered = filtered.filter(portfolio => portfolio.status === filters.status);
    }
    
    // Apply manager filter
    if (filters.manager) {
      filtered = filtered.filter(portfolio => portfolio.manager === filters.manager);
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any = a[filters.sortBy as keyof Portfolio];
      let bValue: any = b[filters.sortBy as keyof Portfolio];
      
      // Handle different data types
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (filters.sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });
    
    return filtered;
  }, [portfoliosData?.data, filters]);

  // Get unique managers for filter dropdown
  const uniqueManagers = useMemo(() => {
    if (!portfoliosData?.data) return [];
    return Array.from(new Set(portfoliosData.data.map(p => p.manager)));
  }, [portfoliosData?.data]);

  // Pagination
  const paginatedPortfolios = useMemo(() => {
    const start = page * rowsPerPage;
    return filteredPortfolios.slice(start, start + rowsPerPage);
  }, [filteredPortfolios, page, rowsPerPage]);

  // Handlers
  const handleChangePage = useCallback((event: unknown, newPage: number) => {
    setPage(newPage);
  }, []);

  const handleChangeRowsPerPage = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  }, []);

  const handleFilterChange = useCallback((field: keyof PortfolioFilters, value: any) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPage(0); // Reset to first page when filtering
  }, []);

  const handleSort = useCallback((column: string) => {
    setFilters(prev => ({
      ...prev,
      sortBy: column,
      sortOrder: prev.sortBy === column && prev.sortOrder === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const handleMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>, portfolio: Portfolio) => {
    setMenuAnchor(event.currentTarget);
    setMenuPortfolio(portfolio);
  }, []);

  const handleMenuClose = useCallback(() => {
    setMenuAnchor(null);
    setMenuPortfolio(null);
  }, []);

  const handleViewPortfolio = useCallback((portfolio: Portfolio) => {
    onPortfolioView?.(portfolio);
    handleMenuClose();
  }, [onPortfolioView, handleMenuClose]);

  const handleEditPortfolio = useCallback((portfolio: Portfolio) => {
    onPortfolioEdit?.(portfolio);
    handleMenuClose();
  }, [onPortfolioEdit, handleMenuClose]);

  const handleDeletePortfolio = useCallback((portfolio: Portfolio) => {
    setSelectedPortfolio(portfolio);
    setDeleteDialogOpen(true);
    handleMenuClose();
  }, [handleMenuClose]);

  const handleDeleteConfirm = useCallback(async () => {
    if (selectedPortfolio) {
      try {
        // In a real app, would call delete mutation
        console.log('Deleting portfolio:', selectedPortfolio.id);
        setDeleteDialogOpen(false);
        setSelectedPortfolio(null);
      } catch (error) {
        console.error('Failed to delete portfolio:', error);
      }
    }
  }, [selectedPortfolio]);

  const handleDeleteCancel = useCallback(() => {
    setDeleteDialogOpen(false);
    setSelectedPortfolio(null);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'effective':
        return 'success';
      case 'pending':
        return 'warning';
      case 'inactive':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'effective':
        return 'Active';
      case 'pending':
        return 'Pending';
      case 'inactive':
        return 'Inactive';
      default:
        return status;
    }
  };

  const calculatePerformance = (portfolio: Portfolio) => {
    // Mock performance calculation
    const performance = ((portfolio.current_portfolio_balance / portfolio.deal_size) - 1) * 100;
    return performance;
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load portfolios. Please check your connection and try again.
      </Alert>
    );
  }

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Portfolio Management
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Manage and monitor your CLO portfolios
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Tooltip title="Analysis Date">
              <IconButton 
                onClick={() => setShowDatePicker(!showDatePicker)}
                color={analysisDate !== '2016-03-23' ? 'primary' : 'default'}
              >
                <DateRange />
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh">
              <IconButton onClick={() => refetch()}>
                <Refresh />
              </IconButton>
            </Tooltip>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={onPortfolioCreate}
            >
              Create Portfolio
            </Button>
          </Box>
        </Box>

        {/* Analysis Date Picker */}
        <Collapse in={showDatePicker}>
          <Box sx={{ mb: 3, p: 3, bgcolor: 'background.default', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <DateRange sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" color="primary">
                Analysis Date Settings
              </Typography>
              <Box sx={{ ml: 'auto' }}>
                <IconButton size="small" onClick={() => setShowDatePicker(false)}>
                  <ExpandLess />
                </IconButton>
              </Box>
            </Box>
            <Box sx={{ maxWidth: 400 }}>
              <AnalysisDatePicker
                analysisDate={analysisDate}
                onDateChange={setAnalysisDate}
                helperText="Select the date for portfolio analysis and calculations"
                showQuickActions={true}
              />
            </Box>
            <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {analysisDate === '2016-03-23' 
                  ? 'Using default analysis date: March 23, 2016'
                  : `Analysis as of ${format(new Date(analysisDate), 'MMMM do, yyyy')}`
                }
              </Typography>
              {analysisDate !== '2016-03-23' && (
                <Chip 
                  label="Historical" 
                  size="small" 
                  color="info" 
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        </Collapse>

        {/* Filters */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <TextField
            size="small"
            placeholder="Search portfolios..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 300 }}
          />
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              label="Status"
            >
              <MenuItem value="">All Status</MenuItem>
              <MenuItem value="effective">Active</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="inactive">Inactive</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Manager</InputLabel>
            <Select
              value={filters.manager}
              onChange={(e) => handleFilterChange('manager', e.target.value)}
              label="Manager"
            >
              <MenuItem value="">All Managers</MenuItem>
              {uniqueManagers.map((manager) => (
                <MenuItem key={manager} value={manager}>
                  {manager}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="outlined"
            startIcon={<FilterList />}
            size="small"
          >
            More Filters
          </Button>
        </Box>

        {/* Summary Stats */}
        <Box sx={{ display: 'flex', gap: 3, mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" fontWeight={700}>
              {filteredPortfolios.length}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total Portfolios
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" fontWeight={700}>
              $
              {(filteredPortfolios.reduce((sum, p) => sum + p.current_portfolio_balance, 0) / 1000000).toFixed(1)}M
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total AUM
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" fontWeight={700}>
              {filteredPortfolios.filter(p => p.status === 'effective').length}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Active
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" fontWeight={700}>
              {filteredPortfolios.reduce((sum, p) => sum + p.current_asset_count, 0)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Total Assets
            </Typography>
          </Box>
        </Box>

        {/* Portfolio Table */}
        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell 
                  onClick={() => handleSort('deal_name')}
                  sx={{ cursor: 'pointer', fontWeight: 600 }}
                >
                  Portfolio Name
                  {filters.sortBy === 'deal_name' && (
                    filters.sortOrder === 'asc' ? ' ↑' : ' ↓'
                  )}
                </TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Manager</TableCell>
                <TableCell 
                  onClick={() => handleSort('deal_size')}
                  sx={{ cursor: 'pointer', fontWeight: 600 }}
                  align="right"
                >
                  Deal Size
                  {filters.sortBy === 'deal_size' && (
                    filters.sortOrder === 'asc' ? ' ↑' : ' ↓'
                  )}
                </TableCell>
                <TableCell 
                  onClick={() => handleSort('current_portfolio_balance')}
                  sx={{ cursor: 'pointer', fontWeight: 600 }}
                  align="right"
                >
                  Current NAV
                  {filters.sortBy === 'current_portfolio_balance' && (
                    filters.sortOrder === 'asc' ? ' ↑' : ' ↓'
                  )}
                </TableCell>
                <TableCell sx={{ fontWeight: 600 }} align="right">Performance</TableCell>
                <TableCell sx={{ fontWeight: 600 }} align="center">Assets</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Maturity</TableCell>
                <TableCell sx={{ fontWeight: 600 }} align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={9} sx={{ py: 4 }}>
                    <LinearProgress />
                    <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                      Loading portfolios...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : paginatedPortfolios.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                    <AccountBalance sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary">
                      No portfolios found
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      {filters.search || filters.status || filters.manager
                        ? 'Try adjusting your search criteria'
                        : 'Create your first portfolio to get started'
                      }
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedPortfolios.map((portfolio) => {
                  const performance = calculatePerformance(portfolio);
                  const isPositive = performance >= 0;
                  
                  return (
                    <TableRow 
                      key={portfolio.id} 
                      hover 
                      sx={{ cursor: onPortfolioSelect ? 'pointer' : 'default' }}
                      onClick={() => onPortfolioSelect?.(portfolio)}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar sx={{ mr: 2, bgcolor: 'primary.main', width: 32, height: 32 }}>
                            <AccountBalance fontSize="small" />
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight={600}>
                              {portfolio.deal_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {portfolio.currency}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2">
                          {portfolio.manager}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Trustee: {portfolio.trustee}
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight={600}>
                          ${(portfolio.deal_size / 1000000).toFixed(1)}M
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight={600}>
                          ${(portfolio.current_portfolio_balance / 1000000).toFixed(1)}M
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                          {isPositive ? (
                            <TrendingUp color="success" sx={{ mr: 0.5, fontSize: 16 }} />
                          ) : (
                            <TrendingDown color="error" sx={{ mr: 0.5, fontSize: 16 }} />
                          )}
                          <Typography
                            variant="body2"
                            color={isPositive ? 'success.main' : 'error.main'}
                            fontWeight={600}
                          >
                            {isPositive ? '+' : ''}{performance.toFixed(2)}%
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell align="center">
                        <Typography variant="body2" fontWeight={600}>
                          {portfolio.current_asset_count}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={getStatusLabel(portfolio.status)}
                          color={getStatusColor(portfolio.status)}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2">
                          {portfolio.stated_maturity 
                            ? format(parseISO(portfolio.stated_maturity), 'MMM yyyy')
                            : 'N/A'
                          }
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {portfolio.days_to_maturity || 0} days
                        </Typography>
                      </TableCell>
                      
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5 }}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleViewPortfolio(portfolio);
                              }}
                            >
                              <Visibility fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          
                          <Tooltip title="More Actions">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleMenuOpen(e, portfolio);
                              }}
                            >
                              <MoreVert fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={filteredPortfolios.length}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />

        {/* Context Menu */}
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
        >
          <MenuList>
            <MenuItem onClick={() => menuPortfolio && handleViewPortfolio(menuPortfolio)}>
              <ListItemIcon>
                <Visibility fontSize="small" />
              </ListItemIcon>
              <ListItemText>View Details</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => menuPortfolio && handleEditPortfolio(menuPortfolio)}>
              <ListItemIcon>
                <Edit fontSize="small" />
              </ListItemIcon>
              <ListItemText>Edit Portfolio</ListItemText>
            </MenuItem>
            <MenuItem>
              <ListItemIcon>
                <Assessment fontSize="small" />
              </ListItemIcon>
              <ListItemText>Risk Analysis</ListItemText>
            </MenuItem>
            <MenuItem>
              <ListItemIcon>
                <GetApp fontSize="small" />
              </ListItemIcon>
              <ListItemText>Export Data</ListItemText>
            </MenuItem>
            <MenuItem 
              onClick={() => menuPortfolio && handleDeletePortfolio(menuPortfolio)}
              sx={{ color: 'error.main' }}
            >
              <ListItemIcon>
                <Delete fontSize="small" color="error" />
              </ListItemIcon>
              <ListItemText>Delete</ListItemText>
            </MenuItem>
          </MenuList>
        </Menu>

        {/* Delete Confirmation Dialog */}
        <Dialog
          open={deleteDialogOpen}
          onClose={handleDeleteCancel}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Confirm Portfolio Deletion</DialogTitle>
          <DialogContent>
            <Typography variant="body1" gutterBottom>
              Are you sure you want to delete the following portfolio?
            </Typography>
            {selectedPortfolio && (
              <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1, mt: 2 }}>
                <Typography variant="body2" fontWeight={600}>
                  {selectedPortfolio.deal_name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Manager: {selectedPortfolio.manager}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Deal Size: ${(selectedPortfolio.deal_size / 1000000).toFixed(1)}M
                </Typography>
              </Box>
            )}
            <Alert severity="error" sx={{ mt: 2 }}>
              This action cannot be undone. All portfolio data, assets, and historical records will be permanently deleted.
            </Alert>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleDeleteCancel}>
              Cancel
            </Button>
            <Button
              onClick={handleDeleteConfirm}
              color="error"
              variant="contained"
            >
              Delete Portfolio
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default PortfolioList;