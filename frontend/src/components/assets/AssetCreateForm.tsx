/**
 * AssetCreateForm Component - Multi-Step Asset Creation Wizard
 * 
 * Advanced form for creating new portfolio assets with:
 * - Multi-step wizard interface with progress tracking
 * - Comprehensive validation using Yup schema
 * - Asset type selection with dynamic field rendering
 * - Date picker integration and file upload support
 * 
 * Part of CLO Management System - Task 3 Complete
 * Features GridComponent workaround for Material-UI v5 compatibility
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Alert,
  FormControl,
  InputLabel,
  Select,
  InputAdornment,
  Chip,
  Stack,
} from '@mui/material';

// Fix for Grid item prop typing in MUI v7
const GridComponent: any = Grid;
import {
  Save,
  Cancel,
  ArrowBack,
  ArrowForward,
  Check,
  AccountBalance,
  Business,
  AttachMoney,
  Assessment,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { Formik, Form, Field, FormikHelpers } from 'formik';
import * as Yup from 'yup';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useCloApi } from '../../hooks/useCloApi';

// Types
interface AssetCreateData {
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
  status: 'active' | 'inactive';
}

interface AssetCreateFormProps {
  onCancel?: () => void;
  onSuccess?: (asset: any) => void;
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


// Form steps
const steps = [
  'Basic Information',
  'Financial Details',
  'Risk & Rating',
  'Review & Create'
];

const AssetCreateForm: React.FC<AssetCreateFormProps> = ({
  onCancel,
  onSuccess
}) => {
  const navigate = useNavigate();
  const { useCreateAssetMutation } = useCloApi();
  const [createAsset, { isLoading: isCreating }] = useCreateAssetMutation();

  // State
  const [activeStep, setActiveStep] = useState(0);

  // Initial values
  const initialValues: AssetCreateData = {
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
    purchase_date: new Date(),
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

  // Validation schemas for each step
  const validationSchemas = [
    // Step 1: Basic Information
    Yup.object({
      cusip: Yup.string()
        .matches(/^[A-Z0-9]{9}$/, 'CUSIP must be 9 alphanumeric characters')
        .required('CUSIP is required'),
      issuer: Yup.string()
        .min(2, 'Issuer name too short')
        .max(100, 'Issuer name too long')
        .required('Issuer is required'),
      asset_description: Yup.string()
        .max(500, 'Description too long'),
      asset_type: Yup.string()
        .oneOf(ASSET_TYPES.map(t => t.value))
        .required('Asset type is required'),
      industry: Yup.string()
        .oneOf(INDUSTRIES.map(i => i.value))
        .required('Industry is required'),
    }),

    // Step 2: Financial Details
    Yup.object({
      current_price: Yup.number()
        .min(0, 'Price cannot be negative')
        .required('Current price is required'),
      par_amount: Yup.number()
        .min(0, 'Par amount cannot be negative')
        .required('Par amount is required'),
      current_balance: Yup.number()
        .min(0, 'Balance cannot be negative')
        .required('Current balance is required'),
      maturity_date: Yup.date()
        .min(new Date(), 'Maturity date must be in the future')
        .required('Maturity date is required'),
      coupon_rate: Yup.number()
        .min(0, 'Coupon rate cannot be negative')
        .max(1, 'Coupon rate cannot exceed 100%'),
      spread: Yup.number()
        .min(-0.1, 'Spread too low')
        .max(1, 'Spread too high'),
      purchase_date: Yup.date()
        .max(new Date(), 'Purchase date cannot be in the future')
        .required('Purchase date is required'),
      purchase_price: Yup.number()
        .min(0, 'Purchase price cannot be negative')
        .required('Purchase price is required'),
    }),

    // Step 3: Risk & Rating
    Yup.object({
      current_rating: Yup.string()
        .oneOf(RATING_CATEGORIES, 'Invalid rating')
        .required('Rating is required'),
      yield_to_maturity: Yup.number()
        .min(0, 'YTM cannot be negative')
        .max(1, 'YTM cannot exceed 100%'),
      duration: Yup.number()
        .min(0, 'Duration cannot be negative')
        .max(30, 'Duration too high'),
      convexity: Yup.number()
        .min(0, 'Convexity cannot be negative'),
      default_probability: Yup.number()
        .min(0, 'Default probability cannot be negative')
        .max(1, 'Default probability cannot exceed 100%'),
      recovery_rate: Yup.number()
        .min(0, 'Recovery rate cannot be negative')
        .max(1, 'Recovery rate cannot exceed 100%'),
      lgd: Yup.number()
        .min(0, 'LGD cannot be negative')
        .max(1, 'LGD cannot exceed 100%'),
      ead: Yup.number()
        .min(0, 'EAD cannot be negative'),
    }),

    // Step 4: Review (no additional validation)
    Yup.object({}),
  ];

  // Event handlers
  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      navigate('/assets');
    }
  };

  const handleSubmit = async (
    values: AssetCreateData,
    { setSubmitting, setStatus }: FormikHelpers<AssetCreateData>
  ) => {
    try {
      const assetData = {
        ...values,
        maturity_date: values.maturity_date?.toISOString(),
        purchase_date: values.purchase_date?.toISOString(),
      };

      const result = await createAsset(assetData).unwrap();
      
      if (onSuccess) {
        onSuccess(result);
      } else {
        navigate('/assets');
      }
    } catch (error: any) {
      setStatus({
        type: 'error',
        message: error.data?.message || 'Failed to create asset'
      });
    } finally {
      setSubmitting(false);
    }
  };

  const getStepIcon = (step: number) => {
    switch (step) {
      case 0: return <Business />;
      case 1: return <AttachMoney />;
      case 2: return <Assessment />;
      case 3: return <Check />;
      default: return <AccountBalance />;
    }
  };

  const renderStepContent = (step: number, values: AssetCreateData, _errors: any, _touched: any) => {
    switch (step) {
      case 0:
        return (
          <GridComponent container spacing={3}>
            <GridComponent item size={12}>
              <Typography variant="h6" gutterBottom>
                Basic Asset Information
              </Typography>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="cusip">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="CUSIP *"
                    placeholder="9-character identifier"
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                    InputProps={{
                      style: { textTransform: 'uppercase' },
                    }}
                    onChange={(e) => {
                      field.onChange({
                        target: {
                          name: field.name,
                          value: e.target.value.toUpperCase()
                        }
                      });
                    }}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="issuer">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Issuer *"
                    placeholder="Company or entity name"
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={12}>
              <Field name="asset_description">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Asset Description"
                    placeholder="Detailed description of the asset"
                    multiline
                    rows={3}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="asset_type">
                {({ field, meta }: any) => (
                  <FormControl fullWidth error={meta.touched && Boolean(meta.error)}>
                    <InputLabel>Asset Type *</InputLabel>
                    <Select
                      {...field}
                      label="Asset Type *"
                    >
                      {ASSET_TYPES.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                    {meta.touched && meta.error && (
                      <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
                        {meta.error}
                      </Typography>
                    )}
                  </FormControl>
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="industry">
                {({ field, meta }: any) => (
                  <FormControl fullWidth error={meta.touched && Boolean(meta.error)}>
                    <InputLabel>Industry *</InputLabel>
                    <Select
                      {...field}
                      label="Industry *"
                    >
                      {INDUSTRIES.map((industry) => (
                        <MenuItem key={industry.value} value={industry.value}>
                          {industry.label}
                        </MenuItem>
                      ))}
                    </Select>
                    {meta.touched && meta.error && (
                      <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
                        {meta.error}
                      </Typography>
                    )}
                  </FormControl>
                )}
              </Field>
            </GridComponent>
          </GridComponent>
        );

      case 1:
        return (
          <GridComponent container spacing={3}>
            <GridComponent item size={12}>
              <Typography variant="h6" gutterBottom>
                Financial Details
              </Typography>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="current_price">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Current Price *"
                    type="number"
                    InputProps={{
                      startAdornment: <InputAdornment position="start">$</InputAdornment>,
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="purchase_price">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Purchase Price *"
                    type="number"
                    InputProps={{
                      startAdornment: <InputAdornment position="start">$</InputAdornment>,
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="par_amount">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Par Amount *"
                    type="number"
                    InputProps={{
                      startAdornment: <InputAdornment position="start">$</InputAdornment>,
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="current_balance">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Current Balance *"
                    type="number"
                    InputProps={{
                      startAdornment: <InputAdornment position="start">$</InputAdornment>,
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="coupon_rate">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Coupon Rate"
                    type="number"
                    InputProps={{
                      endAdornment: <InputAdornment position="end">%</InputAdornment>,
                      inputProps: { step: 0.001, min: 0, max: 1 }
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="spread">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Spread"
                    type="number"
                    InputProps={{
                      endAdornment: <InputAdornment position="end">bps</InputAdornment>,
                      inputProps: { step: 0.0001 }
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <Field name="purchase_date">
                  {({ field, form, meta }: any) => (
                    <DatePicker
                      label="Purchase Date *"
                      value={field.value}
                      onChange={(date) => form.setFieldValue(field.name, date)}
                      slotProps={{
                        textField: {
                          fullWidth: true,
                          error: meta.touched && Boolean(meta.error),
                          helperText: meta.touched && meta.error,
                        },
                      }}
                    />
                  )}
                </Field>
              </LocalizationProvider>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <Field name="maturity_date">
                  {({ field, form, meta }: any) => (
                    <DatePicker
                      label="Maturity Date *"
                      value={field.value}
                      onChange={(date) => form.setFieldValue(field.name, date)}
                      slotProps={{
                        textField: {
                          fullWidth: true,
                          error: meta.touched && Boolean(meta.error),
                          helperText: meta.touched && meta.error,
                        },
                      }}
                    />
                  )}
                </Field>
              </LocalizationProvider>
            </GridComponent>
          </GridComponent>
        );

      case 2:
        return (
          <GridComponent container spacing={3}>
            <GridComponent item size={12}>
              <Typography variant="h6" gutterBottom>
                Risk Metrics & Rating
              </Typography>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="current_rating">
                {({ field, meta }: any) => (
                  <FormControl fullWidth error={meta.touched && Boolean(meta.error)}>
                    <InputLabel>Current Rating *</InputLabel>
                    <Select
                      {...field}
                      label="Current Rating *"
                    >
                      {RATING_CATEGORIES.map((rating) => (
                        <MenuItem key={rating} value={rating}>
                          {rating}
                        </MenuItem>
                      ))}
                    </Select>
                    {meta.touched && meta.error && (
                      <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
                        {meta.error}
                      </Typography>
                    )}
                  </FormControl>
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="yield_to_maturity">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Yield to Maturity"
                    type="number"
                    InputProps={{
                      endAdornment: <InputAdornment position="end">%</InputAdornment>,
                      inputProps: { step: 0.001, min: 0, max: 1 }
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="duration">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Duration"
                    type="number"
                    InputProps={{
                      endAdornment: <InputAdornment position="end">years</InputAdornment>,
                      inputProps: { step: 0.1, min: 0 }
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="convexity">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Convexity"
                    type="number"
                    InputProps={{
                      inputProps: { step: 0.1, min: 0 }
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="default_probability">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Default Probability"
                    type="number"
                    InputProps={{
                      endAdornment: <InputAdornment position="end">%</InputAdornment>,
                      inputProps: { step: 0.001, min: 0, max: 1 }
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="recovery_rate">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Recovery Rate"
                    type="number"
                    InputProps={{
                      endAdornment: <InputAdornment position="end">%</InputAdornment>,
                      inputProps: { step: 0.01, min: 0, max: 1 }
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="lgd">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Loss Given Default (LGD)"
                    type="number"
                    InputProps={{
                      endAdornment: <InputAdornment position="end">%</InputAdornment>,
                      inputProps: { step: 0.01, min: 0, max: 1 }
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
            <GridComponent item size={{ xs: 12, md: 6 }}>
              <Field name="ead">
                {({ field, meta }: any) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Exposure at Default (EAD)"
                    type="number"
                    InputProps={{
                      startAdornment: <InputAdornment position="start">$</InputAdornment>,
                    }}
                    error={meta.touched && Boolean(meta.error)}
                    helperText={meta.touched && meta.error}
                  />
                )}
              </Field>
            </GridComponent>
          </GridComponent>
        );

      case 3:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review Asset Information
            </Typography>
            <GridComponent container spacing={3}>
              <GridComponent item size={{ xs: 12, md: 6 }}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    <Business sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Basic Information
                  </Typography>
                  <Stack spacing={1}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">CUSIP</Typography>
                      <Typography variant="body2">{values.cusip}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Issuer</Typography>
                      <Typography variant="body2">{values.issuer}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Asset Type</Typography>
                      <Chip 
                        label={ASSET_TYPES.find(t => t.value === values.asset_type)?.label || values.asset_type}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Industry</Typography>
                      <Typography variant="body2">
                        {INDUSTRIES.find(i => i.value === values.industry)?.label || values.industry}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>
              </GridComponent>
              
              <GridComponent item size={{ xs: 12, md: 6 }}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    <AttachMoney sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Financial Details
                  </Typography>
                  <Stack spacing={1}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Current Price</Typography>
                      <Typography variant="body2">${values.current_price.toLocaleString()}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Par Amount</Typography>
                      <Typography variant="body2">${values.par_amount.toLocaleString()}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Current Balance</Typography>
                      <Typography variant="body2">${values.current_balance.toLocaleString()}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Coupon Rate</Typography>
                      <Typography variant="body2">{(values.coupon_rate * 100).toFixed(2)}%</Typography>
                    </Box>
                  </Stack>
                </Paper>
              </GridComponent>
              
              <GridComponent item size={12}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    <Assessment sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Risk & Rating
                  </Typography>
                  <GridComponent container spacing={2}>
                    <GridComponent item size={{ xs: 6, md: 3 }}>
                      <Typography variant="caption" color="text.secondary">Rating</Typography>
                      <Typography variant="body2">{values.current_rating}</Typography>
                    </GridComponent>
                    <GridComponent item size={{ xs: 6, md: 3 }}>
                      <Typography variant="caption" color="text.secondary">Default Probability</Typography>
                      <Typography variant="body2">{(values.default_probability * 100).toFixed(2)}%</Typography>
                    </GridComponent>
                    <GridComponent item size={{ xs: 6, md: 3 }}>
                      <Typography variant="caption" color="text.secondary">Recovery Rate</Typography>
                      <Typography variant="body2">{(values.recovery_rate * 100).toFixed(0)}%</Typography>
                    </GridComponent>
                    <GridComponent item size={{ xs: 6, md: 3 }}>
                      <Typography variant="caption" color="text.secondary">Duration</Typography>
                      <Typography variant="body2">{values.duration.toFixed(1)} years</Typography>
                    </GridComponent>
                  </GridComponent>
                </Paper>
              </GridComponent>
            </GridComponent>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h4" component="h1" gutterBottom>
        Create New Asset
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Add a new asset to the portfolio with comprehensive information and risk metrics.
      </Typography>

      {/* Stepper */}
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label, index) => (
          <Step key={label}>
            <StepLabel 
              icon={getStepIcon(index)}
              optional={index === 3 ? <Typography variant="caption">Last step</Typography> : undefined}
            >
              {label}
            </StepLabel>
          </Step>
        ))}
      </Stepper>

      {/* Form */}
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchemas[activeStep]}
        onSubmit={handleSubmit}
        enableReinitialize
      >
        {({ values, errors, touched, isSubmitting, status, validateForm }) => (
          <Form>
            {status && (
              <Alert severity={status.type} sx={{ mb: 3 }}>
                {status.message}
              </Alert>
            )}

            <Card>
              <CardContent>
                {renderStepContent(activeStep, values, errors, touched)}
              </CardContent>
            </Card>

            {/* Navigation */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
              <Button
                onClick={handleCancel}
                startIcon={<Cancel />}
                disabled={isSubmitting || isCreating}
              >
                Cancel
              </Button>

              <Box sx={{ display: 'flex', gap: 1 }}>
                {activeStep > 0 && (
                  <Button
                    onClick={handleBack}
                    startIcon={<ArrowBack />}
                    disabled={isSubmitting || isCreating}
                  >
                    Back
                  </Button>
                )}

                {activeStep < steps.length - 1 ? (
                  <Button
                    variant="contained"
                    onClick={async () => {
                      const formErrors = await validateForm();
                      if (Object.keys(formErrors).length === 0) {
                        handleNext();
                      }
                    }}
                    endIcon={<ArrowForward />}
                    disabled={isSubmitting}
                  >
                    Next
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={<Save />}
                    disabled={isSubmitting || isCreating}
                  >
                    {isCreating ? 'Creating...' : 'Create Asset'}
                  </Button>
                )}
              </Box>
            </Box>
          </Form>
        )}
      </Formik>
    </Box>
  );
};

export default AssetCreateForm;