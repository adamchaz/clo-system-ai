import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Grid,
  TextField,
  Button,
  MenuItem,
  Paper,
  Alert,
  FormControl,
  InputLabel,
  Select,
  InputAdornment,
  Chip,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
} from '@mui/material';
import {
  Save,
  Cancel,
  ArrowBack,
  Lock,
  Refresh,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { Formik, Form, Field, FormikHelpers } from 'formik';
import * as Yup from 'yup';
import { parseISO } from 'date-fns';
import { useCloApi } from '../../hooks/useCloApi';
import { useAuth } from '../../hooks/useAuth';


// Types
interface Asset {
  id: string;
  cusip: string;
  issuer: string;
  asset_description?: string;
  asset_type: string;
  industry?: string;
  current_rating?: string;
  current_price?: number;
  par_amount?: number;
  current_balance?: number;
  maturity_date?: string;
  coupon_rate?: number;
  spread?: number;
  purchase_date?: string;
  purchase_price?: number;
  yield_to_maturity?: number;
  duration?: number;
  convexity?: number;
  default_probability?: number;
  recovery_rate?: number;
  lgd?: number;
  ead?: number;
  last_updated?: string;
  status: 'active' | 'inactive' | 'matured' | 'defaulted';
  performance_1d?: number;
  performance_30d?: number;
  performance_ytd?: number;
}

interface AssetEditData {
  cusip: string;
  issuer: string;
  asset_description: string;
  asset_type: string;
  industry: string;
  current_rating: string;
  current_price: number;
  par_amount: number;
  current_balance: number;
  maturity_date: Date | null;
  coupon_rate: number;
  spread: number;
  purchase_date: Date | null;
  purchase_price: number;
  yield_to_maturity: number;
  duration: number;
  convexity: number;
  default_probability: number;
  recovery_rate: number;
  lgd: number;
  ead: number;
  status: 'active' | 'inactive' | 'matured' | 'defaulted';
}

interface AssetEditFormProps {
  assetId?: string;
  onCancel?: () => void;
  onSuccess?: (asset: any) => void;
}

interface FieldPermissions {
  [key: string]: {
    editable: boolean;
    reason?: string;
  };
}

// Constants
const ASSET_TYPES = [
  { value: 'corporate_bond', label: 'Corporate Bond' },
  { value: 'bank_loan', label: 'Bank Loan' },
  { value: 'structured_product', label: 'Structured Product' },
  { value: 'equity', label: 'Equity' },
  { value: 'municipal_bond', label: 'Municipal Bond' },
  { value: 'government_bond', label: 'Government Bond' },
];

const INDUSTRIES = [
  { value: 'technology', label: 'Technology' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'financial_services', label: 'Financial Services' },
  { value: 'energy', label: 'Energy' },
  { value: 'consumer_goods', label: 'Consumer Goods' },
  { value: 'industrials', label: 'Industrials' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'utilities', label: 'Utilities' },
  { value: 'telecommunications', label: 'Telecommunications' },
  { value: 'materials', label: 'Materials' },
];

const RATING_CATEGORIES = [
  'AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-',
  'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-',
  'B+', 'B', 'B-', 'CCC+', 'CCC', 'CCC-', 'CC', 'C', 'D'
];

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'matured', label: 'Matured' },
  { value: 'defaulted', label: 'Defaulted' },
];

const AssetEditForm: React.FC<AssetEditFormProps> = ({
  assetId,
  onCancel,
  onSuccess
}) => {
  const navigate = useNavigate();
  const { assetId: routeAssetId } = useParams<{ assetId: string }>();
  const finalAssetId = assetId || routeAssetId;
  const { user, hasRole } = useAuth();
  
  const { useGetAssetQuery, useUpdateAssetMutation } = useCloApi();
  const [updateAsset, { isLoading: isUpdating }] = useUpdateAssetMutation();

  // State
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [pendingValues, setPendingValues] = useState<AssetEditData | null>(null);

  // API calls
  const {
    data: assetResponse,
    isLoading,
    error,
    refetch,
  } = useGetAssetQuery(finalAssetId || '', {
    skip: !finalAssetId,
  });

  const asset = assetResponse?.data as Asset;

  // Convert asset data to form data
  const initialValues: AssetEditData = useMemo(() => {
    if (!asset) {
      return {
        cusip: '',
        issuer: '',
        asset_description: '',
        asset_type: '',
        industry: '',
        current_rating: '',
        current_price: 0,
        par_amount: 0,
        current_balance: 0,
        maturity_date: null,
        coupon_rate: 0,
        spread: 0,
        purchase_date: null,
        purchase_price: 0,
        yield_to_maturity: 0,
        duration: 0,
        convexity: 0,
        default_probability: 0,
        recovery_rate: 0.4,
        lgd: 0.6,
        ead: 0,
        status: 'active',
      };
    }

    return {
      cusip: asset.cusip,
      issuer: asset.issuer,
      asset_description: asset.asset_description || '',
      asset_type: asset.asset_type,
      industry: asset.industry || '',
      current_rating: asset.current_rating || '',
      current_price: asset.current_price || 0,
      par_amount: asset.par_amount || 0,
      current_balance: asset.current_balance || 0,
      maturity_date: asset.maturity_date ? parseISO(asset.maturity_date) : null,
      coupon_rate: asset.coupon_rate || 0,
      spread: asset.spread || 0,
      purchase_date: asset.purchase_date ? parseISO(asset.purchase_date) : null,
      purchase_price: asset.purchase_price || 0,
      yield_to_maturity: asset.yield_to_maturity || 0,
      duration: asset.duration || 0,
      convexity: asset.convexity || 0,
      default_probability: asset.default_probability || 0,
      recovery_rate: asset.recovery_rate || 0.4,
      lgd: asset.lgd || 0.6,
      ead: asset.ead || 0,
      status: asset.status,
    };
  }, [asset]);

  // Field permissions based on asset status and user role
  const fieldPermissions: FieldPermissions = useMemo(() => {
    if (!asset || !user) return {};

    const permissions: FieldPermissions = {};
    const isAdmin = hasRole('system_admin');
    const isManager = hasRole('portfolio_manager');
    const isAnalyst = hasRole('financial_analyst');

    // Base permissions - administrators can edit most fields
    const baseEditableFields = isAdmin || isManager;
    
    // CUSIP is generally not editable after creation
    permissions.cusip = {
      editable: false,
      reason: 'CUSIP cannot be changed after asset creation'
    };

    // Basic information - editable for admins and managers
    permissions.issuer = {
      editable: baseEditableFields,
      reason: baseEditableFields ? undefined : 'Insufficient permissions'
    };
    permissions.asset_description = {
      editable: baseEditableFields || isAnalyst,
      reason: undefined
    };
    permissions.asset_type = {
      editable: baseEditableFields,
      reason: baseEditableFields ? undefined : 'Insufficient permissions'
    };
    permissions.industry = {
      editable: baseEditableFields,
      reason: baseEditableFields ? undefined : 'Insufficient permissions'
    };

    // Status-specific restrictions
    const statusLocked = asset.status === 'matured' || asset.status === 'defaulted';
    
    if (statusLocked) {
      // Most fields become read-only for matured/defaulted assets
      const readOnlyFields = [
        'par_amount', 'purchase_date', 'purchase_price', 
        'maturity_date', 'coupon_rate', 'status'
      ];
      
      readOnlyFields.forEach(field => {
        permissions[field] = {
          editable: false,
          reason: `Field locked - asset is ${asset.status}`
        };
      });
    } else {
      // Active/inactive assets - normal permissions
      permissions.par_amount = {
        editable: baseEditableFields,
        reason: baseEditableFields ? undefined : 'Insufficient permissions'
      };
      permissions.purchase_date = {
        editable: false,
        reason: 'Purchase date cannot be changed'
      };
      permissions.purchase_price = {
        editable: false,
        reason: 'Purchase price cannot be changed'
      };
      permissions.maturity_date = {
        editable: baseEditableFields,
        reason: baseEditableFields ? undefined : 'Insufficient permissions'
      };
      permissions.coupon_rate = {
        editable: baseEditableFields,
        reason: baseEditableFields ? undefined : 'Insufficient permissions'
      };
      permissions.status = {
        editable: baseEditableFields,
        reason: baseEditableFields ? undefined : 'Insufficient permissions'
      };
    }

    // Market data fields - editable by analysts and above
    const marketDataFields = [
      'current_price', 'current_balance', 'current_rating', 
      'spread', 'yield_to_maturity', 'duration', 'convexity'
    ];
    
    marketDataFields.forEach(field => {
      permissions[field] = {
        editable: isAdmin || isManager || isAnalyst,
        reason: (isAdmin || isManager || isAnalyst) ? undefined : 'Insufficient permissions'
      };
    });

    // Risk metrics - editable by analysts and above
    const riskFields = [
      'default_probability', 'recovery_rate', 'lgd', 'ead'
    ];
    
    riskFields.forEach(field => {
      permissions[field] = {
        editable: isAdmin || isManager || isAnalyst,
        reason: (isAdmin || isManager || isAnalyst) ? undefined : 'Insufficient permissions'
      };
    });

    return permissions;
  }, [asset, user, hasRole]);

  // Validation schema
  const validationSchema = Yup.object({
    cusip: Yup.string().required('CUSIP is required'),
    issuer: Yup.string().required('Issuer is required'),
    asset_type: Yup.string().required('Asset type is required'),
    current_price: Yup.number().min(0, 'Price cannot be negative'),
    par_amount: Yup.number().min(0, 'Par amount cannot be negative'),
    current_balance: Yup.number().min(0, 'Balance cannot be negative'),
    coupon_rate: Yup.number().min(0, 'Coupon rate cannot be negative').max(1, 'Coupon rate cannot exceed 100%'),
    yield_to_maturity: Yup.number().min(0, 'YTM cannot be negative').max(1, 'YTM cannot exceed 100%'),
    default_probability: Yup.number().min(0, 'Default probability cannot be negative').max(1, 'Default probability cannot exceed 100%'),
    recovery_rate: Yup.number().min(0, 'Recovery rate cannot be negative').max(1, 'Recovery rate cannot exceed 100%'),
    lgd: Yup.number().min(0, 'LGD cannot be negative').max(1, 'LGD cannot exceed 100%'),
  });

  // Event handlers
  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      navigate('/assets');
    }
  };

  const handleSubmit = async (
    values: AssetEditData,
    { setSubmitting, setStatus }: FormikHelpers<AssetEditData>
  ) => {
    try {
      // Detect changed fields only
      const changedFields: Partial<AssetEditData> = {};
      (Object.keys(values) as Array<keyof AssetEditData>).forEach(key => {
        if (JSON.stringify(values[key]) !== JSON.stringify(initialValues[key])) {
          (changedFields as any)[key] = values[key];
        }
      });

      if (Object.keys(changedFields).length === 0) {
        setStatus({
          type: 'info',
          message: 'No changes detected'
        });
        setSubmitting(false);
        return;
      }

      // Check if any significant changes require confirmation
      const significantFields = ['status', 'current_rating', 'default_probability'];
      const hasSignificantChanges = Object.keys(changedFields).some(field => 
        significantFields.includes(field)
      );

      if (hasSignificantChanges && !confirmDialogOpen) {
        setPendingValues(values);
        setConfirmDialogOpen(true);
        setSubmitting(false);
        return;
      }

      const updateData = {
        ...changedFields,
        maturity_date: changedFields.maturity_date?.toISOString(),
        purchase_date: changedFields.purchase_date?.toISOString(),
      };

      const result = await updateAsset({ 
        id: finalAssetId!, 
        updates: updateData 
      }).unwrap();
      
      setStatus({
        type: 'success',
        message: 'Asset updated successfully'
      });

      if (onSuccess) {
        onSuccess(result);
      } else {
        // Refresh data and stay on page
        refetch();
      }
    } catch (error: any) {
      setStatus({
        type: 'error',
        message: error.data?.message || 'Failed to update asset'
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirmSave = () => {
    if (pendingValues) {
      handleSubmit(pendingValues, {
        setSubmitting: () => {},
        setStatus: () => {},
      } as unknown as FormikHelpers<AssetEditData>);
    }
    setConfirmDialogOpen(false);
    setPendingValues(null);
  };

  // Helper function to render field with permissions
  const renderField = (
    fieldName: keyof AssetEditData,
    field: any,
    _meta: any,
    children: React.ReactNode
  ) => {
    const permission = fieldPermissions[fieldName];
    const isEditable = permission?.editable !== false;

    return (
      <Box position="relative">
        {React.cloneElement(children as React.ReactElement, {
          disabled: !isEditable || isLoading,
          InputProps: {
            ...(children as any).props.InputProps,
            endAdornment: !isEditable ? (
              <InputAdornment position="end">
                <Tooltip title={permission?.reason || 'Field is not editable'}>
                  <Lock color="disabled" fontSize="small" />
                </Tooltip>
              </InputAdornment>
            ) : (children as any).props.InputProps?.endAdornment,
          },
        } as any)}
      </Box>
    );
  };

  if (!finalAssetId) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Asset ID not provided
      </Alert>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load asset. Please try again.
      </Alert>
    );
  }

  if (isLoading || !asset) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>Loading asset details...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Edit Asset: {asset.cusip}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {asset.issuer} • {asset.asset_type.replace('_', ' ').toUpperCase()}
          </Typography>
          <Chip 
            label={asset.status.toUpperCase()} 
            color={asset.status === 'active' ? 'success' : 'default'} 
            size="small" 
            sx={{ mt: 1 }}
          />
        </Box>
        
        <Box>
          <Button
            startIcon={<Refresh />}
            onClick={refetch}
            disabled={isLoading}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Form */}
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
        enableReinitialize
      >
        {({ values: _values, errors: _errors, touched: _touched, isSubmitting, status, dirty }) => (
          <Form>
            {status && (
              <Alert severity={status.type} sx={{ mb: 3 }}>
                {status.message}
              </Alert>
            )}

            <Grid container spacing={3}>
              {/* Basic Information */}
              <Grid size={12}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Basic Information
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Field name="cusip">
                        {({ field, meta }: any) => 
                          renderField('cusip', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="CUSIP"
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Field name="issuer">
                        {({ field, meta }: any) =>
                          renderField('issuer', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Issuer"
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                    <Grid size={12}>
                      <Field name="asset_description">
                        {({ field, meta }: any) =>
                          renderField('asset_description', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Description"
                              multiline
                              rows={2}
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="asset_type">
                        {({ field, meta }: any) => (
                          <FormControl fullWidth disabled={!fieldPermissions.asset_type?.editable}>
                            <InputLabel>Asset Type</InputLabel>
                            <Select {...field} label="Asset Type">
                              {ASSET_TYPES.map((type) => (
                                <MenuItem key={type.value} value={type.value}>
                                  {type.label}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        )}
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="industry">
                        {({ field, meta }: any) => (
                          <FormControl fullWidth disabled={!fieldPermissions.industry?.editable}>
                            <InputLabel>Industry</InputLabel>
                            <Select {...field} label="Industry">
                              {INDUSTRIES.map((industry) => (
                                <MenuItem key={industry.value} value={industry.value}>
                                  {industry.label}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        )}
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="status">
                        {({ field, meta }: any) => (
                          <FormControl fullWidth disabled={!fieldPermissions.status?.editable}>
                            <InputLabel>Status</InputLabel>
                            <Select {...field} label="Status">
                              {STATUS_OPTIONS.map((status) => (
                                <MenuItem key={status.value} value={status.value}>
                                  {status.label}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        )}
                      </Field>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* Financial Details */}
              <Grid size={12}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Financial Details
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="current_price">
                        {({ field, meta }: any) =>
                          renderField('current_price', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Current Price"
                              type="number"
                              InputProps={{
                                startAdornment: <InputAdornment position="start">$</InputAdornment>,
                              }}
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="current_balance">
                        {({ field, meta }: any) =>
                          renderField('current_balance', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Current Balance"
                              type="number"
                              InputProps={{
                                startAdornment: <InputAdornment position="start">$</InputAdornment>,
                              }}
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="par_amount">
                        {({ field, meta }: any) =>
                          renderField('par_amount', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Par Amount"
                              type="number"
                              InputProps={{
                                startAdornment: <InputAdornment position="start">$</InputAdornment>,
                              }}
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="coupon_rate">
                        {({ field, meta }: any) =>
                          renderField('coupon_rate', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Coupon Rate"
                              type="number"
                              InputProps={{
                                endAdornment: <InputAdornment position="end">%</InputAdornment>,
                              }}
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="spread">
                        {({ field, meta }: any) =>
                          renderField('spread', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Spread"
                              type="number"
                              InputProps={{
                                endAdornment: <InputAdornment position="end">bps</InputAdornment>,
                              }}
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="yield_to_maturity">
                        {({ field, meta }: any) =>
                          renderField('yield_to_maturity', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Yield to Maturity"
                              type="number"
                              InputProps={{
                                endAdornment: <InputAdornment position="end">%</InputAdornment>,
                              }}
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              {/* Risk Metrics */}
              <Grid size={12}>
                <Paper variant="outlined" sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Risk Metrics
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="current_rating">
                        {({ field, meta }: any) => (
                          <FormControl fullWidth disabled={!fieldPermissions.current_rating?.editable}>
                            <InputLabel>Current Rating</InputLabel>
                            <Select {...field} label="Current Rating">
                              {RATING_CATEGORIES.map((rating) => (
                                <MenuItem key={rating} value={rating}>
                                  {rating}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        )}
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="default_probability">
                        {({ field, meta }: any) =>
                          renderField('default_probability', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Default Probability"
                              type="number"
                              InputProps={{
                                endAdornment: <InputAdornment position="end">%</InputAdornment>,
                              }}
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                    <Grid size={{ xs: 12, md: 4 }}>
                      <Field name="recovery_rate">
                        {({ field, meta }: any) =>
                          renderField('recovery_rate', field, meta,
                            <TextField
                              {...field}
                              fullWidth
                              label="Recovery Rate"
                              type="number"
                              InputProps={{
                                endAdornment: <InputAdornment position="end">%</InputAdornment>,
                              }}
                              error={meta.touched && Boolean(meta.error)}
                              helperText={meta.touched && meta.error}
                            />
                          )
                        }
                      </Field>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>
            </Grid>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
              <Button
                onClick={handleCancel}
                startIcon={<ArrowBack />}
                disabled={isSubmitting || isUpdating}
              >
                Back to Asset
              </Button>

              <Stack direction="row" spacing={1}>
                <Button
                  onClick={handleCancel}
                  startIcon={<Cancel />}
                  disabled={isSubmitting || isUpdating}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<Save />}
                  disabled={isSubmitting || isUpdating || !dirty}
                >
                  {isUpdating ? 'Saving...' : 'Save Changes'}
                </Button>
              </Stack>
            </Box>
          </Form>
        )}
      </Formik>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialogOpen} onClose={() => setConfirmDialogOpen(false)}>
        <DialogTitle>Confirm Changes</DialogTitle>
        <DialogContent>
          <Typography>
            You are about to make significant changes to this asset that may affect 
            risk calculations and portfolio metrics. Are you sure you want to proceed?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleConfirmSave} variant="contained">
            Confirm Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AssetEditForm;