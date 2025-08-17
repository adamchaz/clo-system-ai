import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Paper,
  Tooltip,
  Menu,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  MoreVert,
  Timeline,
  TrendingUp,
  Calculate,
  Visibility,
  GetApp,
  Refresh,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

import {
  useGetYieldCurvesQuery,
  useDeleteYieldCurveMutation,
  useGetAvailableCurrenciesQuery,
  useGetAvailableCurveTypesQuery,
  YieldCurveSummary,
} from '../store/api/cloApi';
import { useAuth } from '../hooks/useAuth';

const YieldCurves: React.FC = () => {
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [filterCurrency, setFilterCurrency] = useState('');
  const [filterCurveType, setFilterCurveType] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedCurve, setSelectedCurve] = useState<YieldCurveSummary | null>(null);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);

  // API hooks
  const {
    data: curvesData,
    isLoading: curvesLoading,
    error: curvesError,
    refetch: refetchCurves,
  } = useGetYieldCurvesQuery({
    skip: page * pageSize,
    limit: pageSize,
    currency: filterCurrency || undefined,
    curve_type: filterCurveType || undefined,
    is_active: filterActive,
    search: searchTerm || undefined,
  });

  const { data: currencies } = useGetAvailableCurrenciesQuery();
  const { data: curveTypes } = useGetAvailableCurveTypesQuery();

  const [deleteCurve, { isLoading: deleteLoading }] = useDeleteYieldCurveMutation();

  // Permissions
  const canCreate = hasRole('admin') || hasRole('manager');
  const canEdit = hasRole('admin') || hasRole('manager') || hasRole('analyst');
  const canDelete = hasRole('admin') || hasRole('manager');

  // Handlers
  const handleRefresh = useCallback(() => {
    refetchCurves();
  }, [refetchCurves]);

  const handleCreateNew = useCallback(() => {
    navigate('/yield-curves/create');
  }, [navigate]);

  const handleEdit = useCallback((curve: YieldCurveSummary) => {
    navigate(`/yield-curves/${curve.curve_id}/edit`);
  }, [navigate]);

  const handleView = useCallback((curve: YieldCurveSummary) => {
    navigate(`/yield-curves/${curve.curve_id}`);
  }, [navigate]);

  const handleVisualize = useCallback(() => {
    navigate('/yield-curves/visualization');
  }, [navigate]);

  const handleDeleteClick = useCallback((curve: YieldCurveSummary) => {
    setSelectedCurve(curve);
    setDeleteDialogOpen(true);
    setMenuAnchorEl(null);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    if (selectedCurve) {
      try {
        await deleteCurve(selectedCurve.curve_id).unwrap();
        setDeleteDialogOpen(false);
        setSelectedCurve(null);
        refetchCurves();
      } catch (error) {
        console.error('Failed to delete curve:', error);
      }
    }
  }, [selectedCurve, deleteCurve, refetchCurves]);

  const handleMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>, curve: YieldCurveSummary) => {
    setMenuAnchorEl(event.currentTarget);
    setSelectedCurve(curve);
  }, []);

  const handleMenuClose = useCallback(() => {
    setMenuAnchorEl(null);
    setSelectedCurve(null);
  }, []);

  const handleFilterReset = useCallback(() => {
    setFilterCurrency('');
    setFilterCurveType('');
    setFilterActive(undefined);
    setSearchTerm('');
    setPage(0);
  }, []);

  // Prepare chart data for curve overview
  const chartData = React.useMemo(() => {
    if (!curvesData?.curves) return [];
    
    const activeCurves = curvesData.curves
      .filter(curve => curve.is_active)
      .slice(0, 5); // Show top 5 curves
    
    return activeCurves.map(curve => ({
      name: curve.curve_name,
      currency: curve.currency,
      rates: curve.rate_count,
      maturity: curve.maturity_range,
    }));
  }, [curvesData]);

  if (curvesError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load yield curves. Please check your connection and try again.
        </Alert>
      </Box>
    );
  }

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
            Yield Curve Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage interest rate curves for asset pricing and cash flow modeling
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Timeline />}
            onClick={handleVisualize}
            sx={{ px: 3 }}
          >
            Visualize Curves
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={curvesLoading}
          >
            Refresh
          </Button>
          {canCreate && (
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={handleCreateNew}
              sx={{ px: 3 }}
            >
              Create Yield Curve
            </Button>
          )}
        </Box>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Timeline sx={{ fontSize: 40, color: 'primary.main' }} />
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    {curvesData?.total_count || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Curves
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <TrendingUp sx={{ fontSize: 40, color: 'success.main' }} />
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    {curvesData?.curves.filter(c => c.is_active).length || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Curves
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Calculate sx={{ fontSize: 40, color: 'info.main' }} />
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    {currencies?.length || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Currencies
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <GetApp sx={{ fontSize: 40, color: 'warning.main' }} />
                <Box>
                  <Typography variant="h4" fontWeight={700}>
                    {curveTypes?.length || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Curve Types
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Filter & Search
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <TextField
                fullWidth
                label="Search curves"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                size="small"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Currency</InputLabel>
                <Select
                  value={filterCurrency}
                  onChange={(e) => setFilterCurrency(e.target.value)}
                  label="Currency"
                >
                  <MenuItem value="">All</MenuItem>
                  {currencies?.map((currency) => (
                    <MenuItem key={currency} value={currency}>
                      {currency}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Type</InputLabel>
                <Select
                  value={filterCurveType}
                  onChange={(e) => setFilterCurveType(e.target.value)}
                  label="Type"
                >
                  <MenuItem value="">All</MenuItem>
                  {curveTypes?.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filterActive === undefined ? '' : filterActive.toString()}
                  onChange={(e) => {
                    const value = e.target.value;
                    setFilterActive(value === '' ? undefined : value === 'true');
                  }}
                  label="Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="true">Active</MenuItem>
                  <MenuItem value="false">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Button onClick={handleFilterReset} variant="outlined" size="small">
                Reset Filters
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Main Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Yield Curves ({curvesData?.total_count || 0})
          </Typography>
          
          {curvesLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Currency</TableCell>
                    <TableCell>Analysis Date</TableCell>
                    <TableCell>Maturity Range</TableCell>
                    <TableCell>Rate Points</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {curvesData?.curves?.map((curve) => (
                    <TableRow key={curve.curve_id} hover>
                      <TableCell>
                        <Typography variant="subtitle2" fontWeight={600}>
                          {curve.curve_name}
                        </Typography>
                        {curve.description && (
                          <Typography variant="caption" color="text.secondary">
                            {curve.description}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={curve.curve_type}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{curve.currency}</TableCell>
                      <TableCell>
                        {format(parseISO(curve.analysis_date), 'MMM dd, yyyy')}
                      </TableCell>
                      <TableCell>{curve.maturity_range}</TableCell>
                      <TableCell>{curve.rate_count}</TableCell>
                      <TableCell>
                        <Chip
                          label={curve.is_active ? 'Active' : 'Inactive'}
                          color={curve.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => handleView(curve)}
                            >
                              <Visibility fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          {canEdit && (
                            <Tooltip title="Edit">
                              <IconButton
                                size="small"
                                onClick={() => handleEdit(curve)}
                              >
                                <Edit fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                          <IconButton
                            size="small"
                            onClick={(e) => handleMenuOpen(e, curve)}
                          >
                            <MoreVert fontSize="small" />
                          </IconButton>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                  {curvesData?.curves?.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                        <Typography color="text.secondary">
                          No yield curves found. {canCreate && 'Create your first yield curve to get started.'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {curvesData && curvesData.total_count > pageSize && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Button
            disabled={!curvesData.has_prev}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <Typography sx={{ mx: 2, alignSelf: 'center' }}>
            Page {curvesData.page} of {Math.ceil(curvesData.total_count / curvesData.per_page)}
          </Typography>
          <Button
            disabled={!curvesData.has_next}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </Box>
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleView(selectedCurve!)}>
          <ListItemIcon>
            <Visibility fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        {canEdit && (
          <MenuItem onClick={() => handleEdit(selectedCurve!)}>
            <ListItemIcon>
              <Edit fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
        )}
        {canDelete && selectedCurve?.is_active && (
          <MenuItem onClick={() => handleDeleteClick(selectedCurve!)}>
            <ListItemIcon>
              <Delete fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        )}
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Yield Curve</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the yield curve "{selectedCurve?.curve_name}"? 
            This action will deactivate the curve but preserve historical data.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            disabled={deleteLoading}
          >
            {deleteLoading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default YieldCurves;