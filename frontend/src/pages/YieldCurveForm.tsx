import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  CircularProgress,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
} from '@mui/material';
import {
  Save,
  Cancel,
  Add,
  Delete,
  Upload,
  Download,
  Calculate,
  ArrowBack,
  Warning,
} from '@mui/icons-material';
// Note: DatePicker requires @mui/x-date-pickers package installation
import { format, parseISO } from 'date-fns';

import {
  useGetYieldCurveQuery,
  useCreateYieldCurveMutation,
  useUpdateYieldCurveMutation,
  useGetAvailableCurrenciesQuery,
  useGetAvailableCurveTypesQuery,
  YieldCurveCreateRequest,
  YieldCurveUpdateRequest,
  YieldCurve,
} from '../store/api/cloApi';
import { useAuth } from '../hooks/useAuth';

interface YieldCurveFormProps {
  mode?: 'create' | 'edit' | 'view';
}

interface YieldCurveRateData {
  maturity_month: number;
  spot_rate: number;
}

const YieldCurveForm: React.FC<YieldCurveFormProps> = ({ mode = 'create' }) => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { hasRole } = useAuth();
  const isEdit = mode === 'edit';
  const isView = mode === 'view';
  const isCreate = mode === 'create';
  const curveId = id ? parseInt(id, 10) : undefined;

  // Form state
  const [formData, setFormData] = useState({
    curve_name: '',
    curve_type: 'TREASURY',
    currency: 'USD',
    analysis_date: format(new Date(), 'yyyy-MM-dd'),
    description: '',
  });
  const [rates, setRates] = useState<YieldCurveRateData[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showAddRateDialog, setShowAddRateDialog] = useState(false);
  const [newRate, setNewRate] = useState({ maturity_month: '', spot_rate: '' });

  // API hooks
  const {
    data: existingCurveResponse,
    isLoading: curveLoading,
    error: curveError,
  } = useGetYieldCurveQuery({ curveId: curveId!, includeForwards: false }, { skip: !curveId });
  
  const existingCurve = existingCurveResponse?.data;

  const { data: currencies } = useGetAvailableCurrenciesQuery();
  const { data: curveTypes } = useGetAvailableCurveTypesQuery();

  const [createCurve, { isLoading: creating, error: createError }] = useCreateYieldCurveMutation();
  const [updateCurve, { isLoading: updating, error: updateError }] = useUpdateYieldCurveMutation();

  // Permissions
  const canSave = (hasRole('admin') || hasRole('manager')) && !isView;
  const canEdit = (hasRole('admin') || hasRole('manager') || hasRole('analyst')) && !isView;

  // Initialize form with existing data
  useEffect(() => {
    if (existingCurve && (isEdit || isView)) {
      setFormData({
        curve_name: existingCurve.curve_name,
        curve_type: existingCurve.curve_type,
        currency: existingCurve.currency,
        analysis_date: existingCurve.analysis_date,
        description: existingCurve.description || '',
      });

      // Convert rates to form format
      const formRates = existingCurve.rates.map(rate => ({
        maturity_month: rate.maturity_month,
        spot_rate: rate.spot_rate,
      }));
      setRates(formRates);
    }
  }, [existingCurve, isEdit, isView]);

  // Validation
  const validateForm = useCallback(() => {
    const newErrors: Record<string, string> = {};

    if (!formData.curve_name.trim()) {
      newErrors.curve_name = 'Curve name is required';
    }

    if (!formData.curve_type) {
      newErrors.curve_type = 'Curve type is required';
    }

    if (!formData.currency) {
      newErrors.currency = 'Currency is required';
    }

    if (!formData.analysis_date) {
      newErrors.analysis_date = 'Analysis date is required';
    }

    if (rates.length === 0) {
      newErrors.rates = 'At least one rate point is required';
    }

    // Validate rates
    const rateErrors: string[] = [];
    const maturities = new Set<number>();
    
    rates.forEach((rate, index) => {
      if (!rate.maturity_month || rate.maturity_month <= 0) {
        rateErrors.push(`Rate ${index + 1}: Invalid maturity`);
      }
      
      if (!rate.spot_rate || rate.spot_rate < 0) {
        rateErrors.push(`Rate ${index + 1}: Invalid spot rate`);
      }
      
      if (maturities.has(rate.maturity_month)) {
        rateErrors.push(`Rate ${index + 1}: Duplicate maturity`);
      }
      
      maturities.add(rate.maturity_month);
    });

    if (rateErrors.length > 0) {
      newErrors.rates = rateErrors.join('; ');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, rates]);

  // Handlers
  const handleFieldChange = useCallback((field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  }, [errors]);

  const handleAddRate = useCallback(() => {
    const maturity = parseInt(newRate.maturity_month, 10);
    const rate = parseFloat(newRate.spot_rate);

    if (maturity > 0 && rate >= 0) {
      setRates(prev => [
        ...prev,
        { maturity_month: maturity, spot_rate: rate }
      ].sort((a, b) => a.maturity_month - b.maturity_month));

      setNewRate({ maturity_month: '', spot_rate: '' });
      setShowAddRateDialog(false);
    }
  }, [newRate]);

  const handleRemoveRate = useCallback((index: number) => {
    setRates(prev => prev.filter((_, i) => i !== index));
  }, []);

  const handleSave = useCallback(async () => {
    if (!validateForm()) {
      return;
    }

    try {
      const curveData = {
        ...formData,
        analysis_date: formData.analysis_date, // Already in correct format
        rates,
      };

      if (isEdit && curveId) {
        await updateCurve({ curveId: curveId, updates: curveData as YieldCurveUpdateRequest }).unwrap();
      } else {
        await createCurve(curveData as YieldCurveCreateRequest).unwrap();
      }

      navigate('/yield-curves');
    } catch (error) {
      console.error('Save error:', error);
    }
  }, [formData, rates, validateForm, isEdit, curveId, createCurve, updateCurve, navigate]);

  const handleCancel = useCallback(() => {
    navigate('/yield-curves');
  }, [navigate]);

  // Loading state
  if (curveLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (curveError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load yield curve data. Please try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
          <Button
            startIcon={<ArrowBack />}
            onClick={handleCancel}
            variant="outlined"
          >
            Back to Yield Curves
          </Button>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>
            {isView ? 'View Yield Curve' : isEdit ? 'Edit Yield Curve' : 'Create New Yield Curve'}
          </Typography>
        </Box>

        {/* Form */}
        <Grid container spacing={3}>
          {/* Basic Information */}
          <Grid size={{ xs: 12, md: 8 }}>
            <Card>
              <CardHeader title="Basic Information" />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Curve Name"
                      value={formData.curve_name}
                      onChange={(e) => handleFieldChange('curve_name', e.target.value)}
                      error={Boolean(errors.curve_name)}
                      helperText={errors.curve_name}
                      disabled={!canEdit}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, md: 3 }}>
                    <FormControl fullWidth error={Boolean(errors.curve_type)}>
                      <InputLabel>Curve Type</InputLabel>
                      <Select
                        value={formData.curve_type}
                        onChange={(e) => handleFieldChange('curve_type', e.target.value)}
                        label="Curve Type"
                        disabled={!canEdit}
                      >
                        {curveTypes?.map((type) => (
                          <MenuItem key={type} value={type}>
                            {type}
                          </MenuItem>
                        ))}
                      </Select>
                      {errors.curve_type && <Typography variant="caption" color="error">{errors.curve_type}</Typography>}
                    </FormControl>
                  </Grid>
                  <Grid size={{ xs: 12, md: 3 }}>
                    <FormControl fullWidth error={Boolean(errors.currency)}>
                      <InputLabel>Currency</InputLabel>
                      <Select
                        value={formData.currency}
                        onChange={(e) => handleFieldChange('currency', e.target.value)}
                        label="Currency"
                        disabled={!canEdit}
                      >
                        {currencies?.map((currency) => (
                          <MenuItem key={currency} value={currency}>
                            {currency}
                          </MenuItem>
                        ))}
                      </Select>
                      {errors.currency && <Typography variant="caption" color="error">{errors.currency}</Typography>}
                    </FormControl>
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <TextField
                      fullWidth
                      label="Analysis Date"
                      type="date"
                      value={formData.analysis_date}
                      onChange={(e) => handleFieldChange('analysis_date', e.target.value)}
                      error={Boolean(errors.analysis_date)}
                      helperText={errors.analysis_date}
                      disabled={!canEdit}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12 }}>
                    <TextField
                      fullWidth
                      label="Description"
                      value={formData.description}
                      onChange={(e) => handleFieldChange('description', e.target.value)}
                      multiline
                      rows={3}
                      disabled={!canEdit}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Actions */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardHeader title="Actions" />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12 }}>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<Save />}
                      onClick={handleSave}
                      disabled={!canSave || creating || updating}
                    >
                      {creating || updating ? 'Saving...' : (isEdit ? 'Update Curve' : 'Create Curve')}
                    </Button>
                  </Grid>
                  <Grid size={{ xs: 12 }}>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<Cancel />}
                      onClick={handleCancel}
                    >
                      Cancel
                    </Button>
                  </Grid>
                </Grid>

                {/* Error Display */}
                {(createError || updateError) && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    Failed to save yield curve. Please try again.
                  </Alert>
                )}

                {/* Validation Errors */}
                {Object.keys(errors).length > 0 && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    Please fix the validation errors before saving.
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Rate Data */}
          <Grid size={{ xs: 12 }}>
            <Card>
              <CardHeader
                title={`Rate Data (${rates.length} points)`}
                action={
                  canEdit && (
                    <Button
                      startIcon={<Add />}
                      onClick={() => setShowAddRateDialog(true)}
                      variant="contained"
                    >
                      Add Rate
                    </Button>
                  )
                }
              />
              <CardContent>
                {errors.rates && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {errors.rates}
                  </Alert>
                )}

                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Maturity (Months)</TableCell>
                        <TableCell>Maturity Display</TableCell>
                        <TableCell>Spot Rate (%)</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {rates.map((rate, index) => (
                        <TableRow key={index}>
                          <TableCell>{rate.maturity_month}</TableCell>
                          <TableCell>
                            <Chip
                              label={rate.maturity_month < 12 
                                ? `${rate.maturity_month}M` 
                                : `${(rate.maturity_month / 12).toFixed(1)}Y`
                              }
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>{(rate.spot_rate * 100).toFixed(4)}%</TableCell>
                          <TableCell align="right">
                            {canEdit && (
                              <Tooltip title="Remove Rate">
                                <IconButton
                                  size="small"
                                  onClick={() => handleRemoveRate(index)}
                                  color="error"
                                >
                                  <Delete fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                      {rates.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                            <Typography color="text.secondary">
                              No rate data added yet. Click "Add Rate" to get started.
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Add Rate Dialog */}
        <Dialog
          open={showAddRateDialog}
          onClose={() => setShowAddRateDialog(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Add Rate Point</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ pt: 1 }}>
              <Grid size={{ xs: 6 }}>
                <TextField
                  fullWidth
                  label="Maturity (Months)"
                  type="number"
                  value={newRate.maturity_month}
                  onChange={(e) => setNewRate(prev => ({ ...prev, maturity_month: e.target.value }))}
                  InputProps={{ inputProps: { min: 1, max: 360 } }}
                />
              </Grid>
              <Grid size={{ xs: 6 }}>
                <TextField
                  fullWidth
                  label="Spot Rate"
                  type="number"
                  value={newRate.spot_rate}
                  onChange={(e) => setNewRate(prev => ({ ...prev, spot_rate: e.target.value }))}
                  InputProps={{ inputProps: { min: 0, max: 1, step: 0.0001 } }}
                  helperText="Enter as decimal (e.g., 0.025 for 2.5%)"
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowAddRateDialog(false)}>Cancel</Button>
            <Button
              onClick={handleAddRate}
              variant="contained"
              disabled={!newRate.maturity_month || !newRate.spot_rate}
            >
              Add Rate
            </Button>
          </DialogActions>
        </Dialog>
    </Box>
  );
};

export default YieldCurveForm;