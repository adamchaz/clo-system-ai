import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Divider,
  Switch,
  FormControlLabel,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack,
  Timeline,
  Compare,
  Download,
  Refresh,
  Settings,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';

import {
  useGetYieldCurvesQuery,
  useGetAvailableCurrenciesQuery,
  useGetAvailableCurveTypesQuery,
} from '../store/api/cloApi';
import { useAuth } from '../hooks/useAuth';
import YieldCurveChart from '../components/charts/YieldCurveChart';

const YieldCurveVisualization: React.FC = () => {
  const navigate = useNavigate();
  const { hasRole } = useAuth();

  // Filter state
  const [selectedCurrency, setSelectedCurrency] = useState('');
  const [selectedCurveType, setSelectedCurveType] = useState('');
  const [selectedCurveIds, setSelectedCurveIds] = useState<number[]>([]);
  const [showActiveOnly, setShowActiveOnly] = useState(true);
  const [comparisonMode, setComparisonMode] = useState(false);

  // API hooks
  const {
    data: curvesData,
    isLoading: curvesLoading,
    error: curvesError,
    refetch: refetchCurves,
  } = useGetYieldCurvesQuery({
    limit: 100,
    currency: selectedCurrency || undefined,
    curve_type: selectedCurveType || undefined,
    is_active: showActiveOnly,
  });

  const { data: currencies } = useGetAvailableCurrenciesQuery();
  const { data: curveTypes } = useGetAvailableCurveTypesQuery();

  // Get full curve details for visualization
  const selectedCurvesForChart = React.useMemo(() => {
    if (!curvesData?.curves) return [];
    return curvesData.curves.filter(curve => 
      selectedCurveIds.length === 0 || selectedCurveIds.includes(curve.curve_id)
    ).slice(0, 5); // Limit to 5 curves for readability
  }, [curvesData, selectedCurveIds]);

  // Permissions
  const canViewAll = hasRole('admin') || hasRole('manager') || hasRole('analyst');

  // Handlers
  const handleBack = useCallback(() => {
    navigate('/yield-curves');
  }, [navigate]);

  const handleRefresh = useCallback(() => {
    refetchCurves();
  }, [refetchCurves]);

  const handleCurveSelection = useCallback((curveId: number, selected: boolean) => {
    setSelectedCurveIds(prev => 
      selected 
        ? [...prev, curveId].slice(0, 5) // Limit to 5 curves
        : prev.filter(id => id !== curveId)
    );
  }, []);

  const handleSelectAll = useCallback(() => {
    const allIds = curvesData?.curves.slice(0, 5).map(c => c.curve_id) || [];
    setSelectedCurveIds(allIds);
  }, [curvesData]);

  const handleClearSelection = useCallback(() => {
    setSelectedCurveIds([]);
  }, []);

  const handleFilterReset = useCallback(() => {
    setSelectedCurrency('');
    setSelectedCurveType('');
    setSelectedCurveIds([]);
  }, []);

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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            startIcon={<ArrowBack />}
            onClick={handleBack}
            variant="outlined"
          >
            Back to Yield Curves
          </Button>
          <Box>
            <Typography
              variant="h4"
              component="h1"
              sx={{ fontWeight: 700, color: 'text.primary', display: 'flex', alignItems: 'center', gap: 1 }}
            >
              <Timeline />
              Yield Curve Visualization
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Interactive analysis and comparison of interest rate curves
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={curvesLoading}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            disabled
          >
            Export
          </Button>
        </Box>
      </Box>

      {/* Filters & Selection */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          title="Curve Selection & Filters"
          action={
            <FormControlLabel
              control={
                <Switch
                  checked={comparisonMode}
                  onChange={(e) => setComparisonMode(e.target.checked)}
                />
              }
              label="Comparison Mode"
            />
          }
        />
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            {/* Filters */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Currency</InputLabel>
                <Select
                  value={selectedCurrency}
                  onChange={(e) => setSelectedCurrency(e.target.value)}
                  label="Currency"
                >
                  <MenuItem value="">All Currencies</MenuItem>
                  {currencies?.map((currency) => (
                    <MenuItem key={currency} value={currency}>
                      {currency}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Curve Type</InputLabel>
                <Select
                  value={selectedCurveType}
                  onChange={(e) => setSelectedCurveType(e.target.value)}
                  label="Curve Type"
                >
                  <MenuItem value="">All Types</MenuItem>
                  {curveTypes?.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={showActiveOnly}
                    onChange={(e) => setShowActiveOnly(e.target.checked)}
                  />
                }
                label="Active Only"
              />
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <Button onClick={handleSelectAll} variant="outlined" size="small">
                Select All
              </Button>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 2 }}>
              <Button onClick={handleClearSelection} variant="outlined" size="small">
                Clear
              </Button>
            </Grid>

            <Grid size={{ xs: 12 }}>
              <Button onClick={handleFilterReset} variant="outlined" size="small">
                Reset Filters
              </Button>
            </Grid>
          </Grid>

          <Divider sx={{ my: 2 }} />

          {/* Available Curves */}
          <Typography variant="subtitle2" gutterBottom>
            Available Curves ({curvesData?.total_count || 0}):
          </Typography>
          
          {curvesLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress size={24} />
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {curvesData?.curves.map((curve) => (
                <Chip
                  key={curve.curve_id}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <span>{curve.curve_name}</span>
                      <Chip
                        label={curve.currency}
                        size="small"
                        color="secondary"
                        sx={{ height: 16, fontSize: '0.7em' }}
                      />
                    </Box>
                  }
                  onClick={() => handleCurveSelection(
                    curve.curve_id,
                    !selectedCurveIds.includes(curve.curve_id)
                  )}
                  color={selectedCurveIds.includes(curve.curve_id) ? 'primary' : 'default'}
                  variant={selectedCurveIds.includes(curve.curve_id) ? 'filled' : 'outlined'}
                  disabled={
                    !selectedCurveIds.includes(curve.curve_id) && 
                    selectedCurveIds.length >= 5
                  }
                />
              ))}
              {curvesData?.curves.length === 0 && (
                <Typography color="text.secondary">
                  No curves match the current filters.
                </Typography>
              )}
            </Box>
          )}

          {selectedCurveIds.length > 5 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              Only the first 5 selected curves will be displayed for better readability.
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Visualization Placeholder */}
      {selectedCurvesForChart.length > 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Timeline sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h6" color="text.primary" gutterBottom>
            Yield Curve Visualization
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {selectedCurvesForChart.length} curve{selectedCurvesForChart.length > 1 ? 's' : ''} selected for visualization
          </Typography>
          {selectedCurvesForChart.map((curve) => (
            <Typography key={curve.curve_id} variant="body2" sx={{ mb: 1 }}>
              • {curve.curve_name} ({curve.currency}) - {curve.rate_count} rate points
            </Typography>
          ))}
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            Full visualization will be implemented with detailed rate data fetching.
          </Typography>
        </Paper>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Timeline sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Curves Selected
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Select one or more yield curves from the list above to begin visualization.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default YieldCurveVisualization;