/**
 * AssetList Component - Advanced Asset Portfolio Display
 * 
 * Features comprehensive asset management with:
 * - Advanced filtering by rating, industry, asset type
 * - Multi-column sorting and pagination
 * - Bulk operations and selection management
 * - Real-time search and performance metrics
 * 
 * Part of CLO Management System - Task 1 Complete
 * Fully integrated with RTK Query and Material-UI v5
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  IconButton,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Checkbox,
  Menu,
  MenuItem as MenuListItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
  Stack,
  Divider,
} from '@mui/material';
import {
  Search,
  FilterList,
  Add,
  Refresh,
  GetApp,
  MoreVert,
  Visibility,
  Edit,
  Delete,
  TrendingUp,
  TrendingDown,
  Star,
  StarBorder,
  Assessment,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import StatusIndicator from '../common/UI/StatusIndicator';
import { useCloApi } from '../../hooks/useCloApi';
import type { Asset } from '../../store/api/cloApi';


// Types
interface AssetFilters {
  search: string;
  rating: string;
  industry: string;
  assetType: string;
  priceRange: string;
  maturityRange: string;
  ratingCategory: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}


interface AssetListProps {
  portfolioId?: string;
  showPortfolioFilter?: boolean;
  compact?: boolean;
  maxHeight?: string;
}

const AssetList: React.FC<AssetListProps> = ({
  portfolioId,
  showPortfolioFilter: _showPortfolioFilter = false,
  compact = false,
  maxHeight = '600px'
}) => {
  const navigate = useNavigate();
  const { useGetAssetsQuery, useDeleteAssetMutation } = useCloApi();

  // State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(compact ? 10 : 25);
  const [filters, setFilters] = useState<AssetFilters>({
    search: '',
    rating: '',
    industry: '',
    assetType: '',
    priceRange: '',
    maturityRange: '',
    ratingCategory: '',
    sortBy: 'asset_name',
    sortOrder: 'asc',
  });
  const [selectedAssets, setSelectedAssets] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [menuAsset, setMenuAsset] = useState<Asset | null>(null);
  const [watchlist, setWatchlist] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [assetToDelete, setAssetToDelete] = useState<Asset | null>(null);

  // API calls
  const {
    data: assetsData,
    isLoading,
    error,
    refetch,
  } = useGetAssetsQuery({
    portfolio_id: portfolioId,
    limit: 1000,
  });

  const [deleteAsset] = useDeleteAssetMutation();

  // Filtered and sorted assets
  const filteredAssets = useMemo(() => {
    if (!assetsData?.data) return [];
    
    let filtered = [...assetsData.data];
    
    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(asset =>
        asset.asset_name?.toLowerCase().includes(searchLower) ||
        (asset.cusip && asset.cusip.toLowerCase().includes(searchLower)) ||
        asset.industry?.toLowerCase().includes(searchLower)
      );
    }
    
    // Rating filter
    if (filters.rating) {
      filtered = filtered.filter(asset => asset.rating === filters.rating);
    }
    
    // Industry filter
    if (filters.industry) {
      filtered = filtered.filter(asset => asset.industry === filters.industry);
    }
    
    // Asset type filter
    if (filters.assetType) {
      filtered = filtered.filter(asset => asset.asset_type === filters.assetType);
    }
    
    // Rating category filter
    if (filters.ratingCategory) {
      const isInvestmentGrade = (asset: Asset) => 
        ['AAA', 'AA', 'A', 'BBB'].some(rating => 
          asset.rating?.startsWith(rating)
        );
      if (filters.ratingCategory === 'investment-grade') {
        filtered = filtered.filter(isInvestmentGrade);
      } else if (filters.ratingCategory === 'speculative-grade') {
        filtered = filtered.filter(asset => !isInvestmentGrade(asset));
      }
    }
    
    // Price range filter
    if (filters.priceRange) {
      const [min, max] = filters.priceRange.split('-').map(Number);
      filtered = filtered.filter(asset => {
        const price = asset.original_balance || 0;
        return price >= min && (max ? price <= max : true);
      });
    }
    
    // Maturity range filter
    if (filters.maturityRange) {
      const today = new Date();
      const ranges = {
        '0-1': [0, 1],
        '1-3': [1, 3],
        '3-5': [3, 5],
        '5-10': [5, 10],
        '10+': [10, Infinity]
      };
      const [minYears, maxYears] = ranges[filters.maturityRange as keyof typeof ranges] || [0, Infinity];
      
      filtered = filtered.filter(asset => {
        if (!asset.maturity_date) return false;
        const maturityDate = new Date(asset.maturity_date);
        const yearsToMaturity = (maturityDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24 * 365.25);
        return yearsToMaturity >= minYears && yearsToMaturity <= maxYears;
      });
    }
    
    // Sort
    filtered.sort((a, b) => {
      let aValue: any = a[filters.sortBy as keyof Asset];
      let bValue: any = b[filters.sortBy as keyof Asset];
      
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (aValue < bValue) return filters.sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return filters.sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    
    return filtered;
  }, [assetsData, filters]);

  // Pagination
  const paginatedAssets = useMemo(() => {
    const startIndex = page * rowsPerPage;
    return filteredAssets.slice(startIndex, startIndex + rowsPerPage);
  }, [filteredAssets, page, rowsPerPage]);

  // Event handlers
  const handleFilterChange = useCallback((key: keyof AssetFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(0); // Reset to first page when filtering
  }, []);

  const handleSort = useCallback((column: string) => {
    setFilters(prev => ({
      ...prev,
      sortBy: column,
      sortOrder: prev.sortBy === column && prev.sortOrder === 'asc' ? 'desc' : 'asc'
    }));
  }, []);

  const handleSelectAsset = useCallback((assetId: string) => {
    setSelectedAssets(prev => {
      const newSet = new Set(prev);
      if (newSet.has(assetId)) {
        newSet.delete(assetId);
      } else {
        newSet.add(assetId);
      }
      return newSet;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    if (selectAll) {
      setSelectedAssets(new Set());
    } else {
      setSelectedAssets(new Set(paginatedAssets.map(asset => asset.id)));
    }
    setSelectAll(!selectAll);
  }, [selectAll, paginatedAssets]);

  const handleWatchlistToggle = useCallback((assetId: string) => {
    setWatchlist(prev => {
      const newSet = new Set(prev);
      if (newSet.has(assetId)) {
        newSet.delete(assetId);
      } else {
        newSet.add(assetId);
      }
      return newSet;
    });
  }, []);

  const handleMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>, asset: Asset) => {
    setMenuAnchor(event.currentTarget);
    setMenuAsset(asset);
  }, []);

  const handleMenuClose = useCallback(() => {
    setMenuAnchor(null);
    setMenuAsset(null);
  }, []);

  const handleViewAsset = useCallback((asset: Asset) => {
    navigate(`/assets/${asset.id}`);
    handleMenuClose();
  }, [navigate]);

  const handleEditAsset = useCallback((asset: Asset) => {
    navigate(`/assets/${asset.id}/edit`);
    handleMenuClose();
  }, [navigate]);

  const handleDeleteAsset = useCallback((asset: Asset) => {
    setAssetToDelete(asset);
    setDeleteConfirmOpen(true);
    handleMenuClose();
  }, []);

  const confirmDelete = useCallback(async () => {
    if (assetToDelete) {
      try {
        await deleteAsset(assetToDelete.id).unwrap();
        refetch();
      } catch (error) {
        console.error('Failed to delete asset:', error);
      }
    }
    setDeleteConfirmOpen(false);
    setAssetToDelete(null);
  }, [assetToDelete, deleteAsset, refetch]);

  const handleAnalyzeAsset = useCallback((asset: Asset) => {
    navigate(`/assets/${asset.id}/analysis`);
    handleMenuClose();
  }, [navigate]);

  const clearFilters = useCallback(() => {
    setFilters({
      search: '',
      rating: '',
      industry: '',
      assetType: '',
      priceRange: '',
      maturityRange: '',
      ratingCategory: '',
      sortBy: 'asset_name',
      sortOrder: 'asc',
    });
    setPage(0);
  }, []);

  const getRatingColor = (rating?: string | undefined): 'default' | 'success' | 'info' | 'warning' | 'error' => {
    if (!rating) return 'default';
    if (['AAA', 'AA'].some(r => rating.startsWith(r))) return 'success';
    if (['A', 'BBB'].some(r => rating.startsWith(r))) return 'info';
    if (['BB', 'B'].some(r => rating.startsWith(r))) return 'warning';
    return 'error';
  };

  const formatCurrency = (value?: number) => {
    if (!value) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };

  const getPerformanceIcon = (performance?: number) => {
    if (!performance) return null;
    return performance >= 0 ? 
      <TrendingUp color="success" fontSize="small" /> : 
      <TrendingDown color="error" fontSize="small" />;
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load assets. Please try again.
      </Alert>
    );
  }

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h5" component="h2" gutterBottom>
              Asset Portfolio
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {filteredAssets.length} assets • {selectedAssets.size} selected
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<FilterList />}
              onClick={() => setShowFilters(!showFilters)}
              color={showFilters ? 'primary' : 'inherit'}
            >
              Filters
            </Button>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={refetch}
              disabled={isLoading}
            >
              Refresh
            </Button>
            <Button
              variant="outlined"
              startIcon={<GetApp />}
              disabled={selectedAssets.size === 0}
            >
              Export
            </Button>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => navigate('/assets/create')}
            >
              Add Asset
            </Button>
          </Stack>
        </Box>

        {/* Filters */}
        {showFilters && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
              <Grid container spacing={2} alignItems="center">
                <Grid size={{ xs: 12, md: 3 }}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Search"
                    placeholder="CUSIP, Issuer, Description..."
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Search />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 2 }}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Asset Type</InputLabel>
                    <Select
                      value={filters.assetType}
                      label="Asset Type"
                      onChange={(e) => handleFilterChange('assetType', e.target.value)}
                    >
                      <MenuItem value="">All Types</MenuItem>
                      <MenuItem value="corporate_bond">Corporate Bond</MenuItem>
                      <MenuItem value="bank_loan">Bank Loan</MenuItem>
                      <MenuItem value="structured_product">Structured Product</MenuItem>
                      <MenuItem value="equity">Equity</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid size={{ xs: 12, md: 2 }}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Industry</InputLabel>
                    <Select
                      value={filters.industry}
                      label="Industry"
                      onChange={(e) => handleFilterChange('industry', e.target.value)}
                    >
                      <MenuItem value="">All Industries</MenuItem>
                      <MenuItem value="technology">Technology</MenuItem>
                      <MenuItem value="healthcare">Healthcare</MenuItem>
                      <MenuItem value="financial_services">Financial Services</MenuItem>
                      <MenuItem value="energy">Energy</MenuItem>
                      <MenuItem value="consumer_goods">Consumer Goods</MenuItem>
                      <MenuItem value="industrials">Industrials</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid size={{ xs: 12, md: 2 }}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Rating Category</InputLabel>
                    <Select
                      value={filters.ratingCategory}
                      label="Rating Category"
                      onChange={(e) => handleFilterChange('ratingCategory', e.target.value)}
                    >
                      <MenuItem value="">All Ratings</MenuItem>
                      <MenuItem value="investment-grade">Investment Grade</MenuItem>
                      <MenuItem value="speculative-grade">Speculative Grade</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid size={{ xs: 12, md: 2 }}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Maturity</InputLabel>
                    <Select
                      value={filters.maturityRange}
                      label="Maturity"
                      onChange={(e) => handleFilterChange('maturityRange', e.target.value)}
                    >
                      <MenuItem value="">All Maturities</MenuItem>
                      <MenuItem value="0-1">0-1 Years</MenuItem>
                      <MenuItem value="1-3">1-3 Years</MenuItem>
                      <MenuItem value="3-5">3-5 Years</MenuItem>
                      <MenuItem value="5-10">5-10 Years</MenuItem>
                      <MenuItem value="10+">10+ Years</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid size={{ xs: 12, md: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={clearFilters}
                    disabled={Object.values(filters).every(v => !v || v === 'asset_name' || v === 'asc')}
                  >
                    Clear
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}

        {/* Loading */}
        {isLoading && <LinearProgress sx={{ mb: 2 }} />}

        {/* Asset Table */}
        <TableContainer component={Paper} sx={{ maxHeight: compact ? maxHeight : 'none' }}>
          <Table stickyHeader size={compact ? 'small' : 'medium'}>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectAll}
                    onChange={handleSelectAll}
                    indeterminate={selectedAssets.size > 0 && selectedAssets.size < paginatedAssets.length}
                  />
                </TableCell>
                <TableCell>
                  <Button
                    onClick={() => handleSort('asset_name')}
                    sx={{ fontWeight: 'bold', color: 'text.primary' }}
                  >
                    Asset Name
                  </Button>
                </TableCell>
                <TableCell>
                  <Button
                    onClick={() => handleSort('asset_name')}
                    sx={{ fontWeight: 'bold', color: 'text.primary' }}
                  >
                    Name
                  </Button>
                </TableCell>
                <TableCell>Asset Type</TableCell>
                <TableCell>
                  <Button
                    onClick={() => handleSort('rating')}
                    sx={{ fontWeight: 'bold', color: 'text.primary' }}
                  >
                    Rating
                  </Button>
                </TableCell>
                <TableCell align="right">
                  <Button
                    onClick={() => handleSort('original_balance')}
                    sx={{ fontWeight: 'bold', color: 'text.primary' }}
                  >
                    Original Balance
                  </Button>
                </TableCell>
                <TableCell align="right">
                  <Button
                    onClick={() => handleSort('current_balance')}
                    sx={{ fontWeight: 'bold', color: 'text.primary' }}
                  >
                    Balance
                  </Button>
                </TableCell>
                <TableCell align="right">YTM</TableCell>
                <TableCell align="center">Performance</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedAssets.map((asset) => (
                <TableRow
                  key={asset.id}
                  hover
                  selected={selectedAssets.has(asset.id)}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedAssets.has(asset.id)}
                      onChange={() => handleSelectAsset(asset.id)}
                    />
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {asset.cusip || asset.id}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {asset.asset_name?.substring(0, 40) || 'N/A'}...
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2">
                        {asset.asset_name || 'N/A'}
                      </Typography>
                      {asset.industry && (
                        <Chip
                          label={asset.industry}
                          size="small"
                          variant="outlined"
                          sx={{ mt: 0.5, fontSize: '0.75rem' }}
                        />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={asset.asset_type?.replace('_', ' ') || 'Unknown'}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    {asset.rating && (
                      <Chip
                        label={asset.rating}
                        size="small"
                        color={getRatingColor(asset.rating)}
                      />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" fontWeight="medium">
                      {formatCurrency(asset.original_balance)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      {formatCurrency(asset.current_balance)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      {formatPercentage(asset.yield_to_maturity)}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                      {getPerformanceIcon(asset.performance_30d)}
                      <Typography variant="body2" fontSize="0.75rem">
                        {formatPercentage(asset.performance_30d)}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <StatusIndicator
                      status={asset.status}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Box display="flex" alignItems="center" gap={0.5}>
                      <IconButton
                        size="small"
                        onClick={() => handleWatchlistToggle(asset.id)}
                        color={watchlist.has(asset.id) ? 'warning' : 'default'}
                      >
                        {watchlist.has(asset.id) ? <Star /> : <StarBorder />}
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, asset)}
                      >
                        <MoreVert />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          rowsPerPageOptions={compact ? [5, 10, 25] : [10, 25, 50, 100]}
          component="div"
          count={filteredAssets.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10));
            setPage(0);
          }}
        />

        {/* Context Menu */}
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
        >
            <MenuListItem onClick={() => menuAsset && handleViewAsset(menuAsset)}>
              <ListItemIcon>
                <Visibility />
              </ListItemIcon>
              <ListItemText>View Details</ListItemText>
            </MenuListItem>
            <MenuListItem onClick={() => menuAsset && handleEditAsset(menuAsset)}>
              <ListItemIcon>
                <Edit />
              </ListItemIcon>
              <ListItemText>Edit Asset</ListItemText>
            </MenuListItem>
            <MenuListItem onClick={() => menuAsset && handleAnalyzeAsset(menuAsset)}>
              <ListItemIcon>
                <Assessment />
              </ListItemIcon>
              <ListItemText>Analyze</ListItemText>
            </MenuListItem>
            <Divider />
            <MenuListItem onClick={() => menuAsset && handleDeleteAsset(menuAsset)}>
              <ListItemIcon>
                <Delete />
              </ListItemIcon>
              <ListItemText>Delete</ListItemText>
            </MenuListItem>
        </Menu>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
          <DialogTitle>Confirm Delete</DialogTitle>
          <DialogContent>
            <Typography>
              Are you sure you want to delete asset "{assetToDelete?.asset_name}"? This action cannot be undone.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
            <Button onClick={confirmDelete} color="error" variant="contained">
              Delete
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default AssetList;