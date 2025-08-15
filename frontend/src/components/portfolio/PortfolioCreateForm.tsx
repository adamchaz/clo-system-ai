import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Divider,
  InputAdornment,
  Switch,
  FormControlLabel,
  Stepper,
  Step,
  StepLabel,
  Paper,
} from '@mui/material';
import {
  Save,
  Cancel,
  AccountBalance,
  Business,
  CalendarToday,
  AttachMoney,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { addDays, addYears } from 'date-fns';

interface PortfolioCreateFormProps {
  onSubmit: (portfolio: PortfolioFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

interface PortfolioFormData {
  dealName: string;
  manager: string;
  trustee: string;
  currency: string;
  dealSize: number;
  effectiveDate: Date;
  statedMaturity: Date;
  revolvingPeriodEnd?: Date;
  reinvestmentPeriodEnd?: Date;
  hasRevolvingPeriod: boolean;
  hasReinvestmentPeriod: boolean;
  description: string;
  ratingAgency: string;
  jurisdiction: string;
  govLaw: string;
  collateralType: string;
  minimumDenomination: number;
  paymentFrequency: string;
}

const steps = [
  'Basic Information',
  'Financial Details', 
  'Dates & Periods',
  'Additional Details'
];

const PortfolioCreateForm: React.FC<PortfolioCreateFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState<PortfolioFormData>({
    dealName: '',
    manager: '',
    trustee: '',
    currency: 'USD',
    dealSize: 0,
    effectiveDate: new Date(),
    statedMaturity: addYears(new Date(), 7), // Default 7 year term
    revolvingPeriodEnd: undefined,
    reinvestmentPeriodEnd: undefined,
    hasRevolvingPeriod: false,
    hasReinvestmentPeriod: false,
    description: '',
    ratingAgency: 'Moody\'s',
    jurisdiction: 'United States',
    govLaw: 'New York',
    collateralType: 'Broadly Syndicated Loans',
    minimumDenomination: 100000,
    paymentFrequency: 'Quarterly',
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Handle field changes
  const handleFieldChange = useCallback((field: keyof PortfolioFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  }, [errors]);

  // Validation
  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};
    
    switch (step) {
      case 0: // Basic Information
        if (!formData.dealName) newErrors.dealName = 'Deal name is required';
        if (!formData.manager) newErrors.manager = 'Manager is required';
        if (!formData.trustee) newErrors.trustee = 'Trustee is required';
        break;
        
      case 1: // Financial Details
        if (formData.dealSize <= 0) newErrors.dealSize = 'Deal size must be greater than 0';
        if (formData.minimumDenomination <= 0) newErrors.minimumDenomination = 'Minimum denomination must be greater than 0';
        break;
        
      case 2: // Dates & Periods
        if (formData.statedMaturity <= formData.effectiveDate) {
          newErrors.statedMaturity = 'Maturity date must be after effective date';
        }
        if (formData.hasRevolvingPeriod && formData.revolvingPeriodEnd) {
          if (formData.revolvingPeriodEnd <= formData.effectiveDate) {
            newErrors.revolvingPeriodEnd = 'Revolving period end must be after effective date';
          }
          if (formData.revolvingPeriodEnd >= formData.statedMaturity) {
            newErrors.revolvingPeriodEnd = 'Revolving period end must be before maturity date';
          }
        }
        if (formData.hasReinvestmentPeriod && formData.reinvestmentPeriodEnd) {
          if (formData.reinvestmentPeriodEnd <= formData.effectiveDate) {
            newErrors.reinvestmentPeriodEnd = 'Reinvestment period end must be after effective date';
          }
          if (formData.reinvestmentPeriodEnd >= formData.statedMaturity) {
            newErrors.reinvestmentPeriodEnd = 'Reinvestment period end must be before maturity date';
          }
        }
        break;
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Step navigation
  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  // Form submission
  const handleSubmit = () => {
    if (validateStep(activeStep)) {
      // Set default periods if enabled but not set
      const finalData = { ...formData };
      if (finalData.hasRevolvingPeriod && !finalData.revolvingPeriodEnd) {
        finalData.revolvingPeriodEnd = addYears(finalData.effectiveDate, 2);
      }
      if (finalData.hasReinvestmentPeriod && !finalData.reinvestmentPeriodEnd) {
        finalData.reinvestmentPeriodEnd = addYears(finalData.effectiveDate, 3);
      }
      
      onSubmit(finalData);
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0: // Basic Information
        return (
          <Grid container spacing={3}>
            <Grid size={12}>
              <Typography variant="h6" gutterBottom color="primary">
                <AccountBalance sx={{ mr: 1, verticalAlign: 'middle' }} />
                Portfolio Identity
              </Typography>
            </Grid>
            
            <Grid size={12}>
              <TextField
                fullWidth
                label="Deal Name"
                value={formData.dealName}
                onChange={(e) => handleFieldChange('dealName', e.target.value)}
                error={!!errors.dealName}
                helperText={errors.dealName || 'Enter the official name of the CLO deal'}
                placeholder="e.g., MAG CLO XVI-R"
              />
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Manager"
                value={formData.manager}
                onChange={(e) => handleFieldChange('manager', e.target.value)}
                error={!!errors.manager}
                helperText={errors.manager || 'Investment manager'}
                placeholder="e.g., Magnetar Capital"
              />
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Trustee"
                value={formData.trustee}
                onChange={(e) => handleFieldChange('trustee', e.target.value)}
                error={!!errors.trustee}
                helperText={errors.trustee || 'Trustee institution'}
                placeholder="e.g., Wells Fargo"
              />
            </Grid>
            
            <Grid size={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={formData.description}
                onChange={(e) => handleFieldChange('description', e.target.value)}
                helperText="Brief description of the portfolio strategy and objectives"
                placeholder="Describe the CLO investment strategy, target returns, and key characteristics..."
              />
            </Grid>
          </Grid>
        );
        
      case 1: // Financial Details
        return (
          <Grid container spacing={3}>
            <Grid size={12}>
              <Typography variant="h6" gutterBottom color="primary">
                <AttachMoney sx={{ mr: 1, verticalAlign: 'middle' }} />
                Financial Structure
              </Typography>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Deal Size"
                type="number"
                value={formData.dealSize}
                onChange={(e) => handleFieldChange('dealSize', Number(e.target.value))}
                error={!!errors.dealSize}
                helperText={errors.dealSize || 'Total deal size in currency units'}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  endAdornment: <InputAdornment position="end">USD</InputAdornment>,
                }}
                inputProps={{ min: 0, step: 1000000 }}
              />
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Currency</InputLabel>
                <Select
                  value={formData.currency}
                  onChange={(e) => handleFieldChange('currency', e.target.value)}
                  label="Currency"
                >
                  <MenuItem value="USD">USD - US Dollar</MenuItem>
                  <MenuItem value="EUR">EUR - Euro</MenuItem>
                  <MenuItem value="GBP">GBP - British Pound</MenuItem>
                  <MenuItem value="JPY">JPY - Japanese Yen</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Minimum Denomination"
                type="number"
                value={formData.minimumDenomination}
                onChange={(e) => handleFieldChange('minimumDenomination', Number(e.target.value))}
                error={!!errors.minimumDenomination}
                helperText={errors.minimumDenomination || 'Minimum investment amount'}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                inputProps={{ min: 0, step: 1000 }}
              />
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Payment Frequency</InputLabel>
                <Select
                  value={formData.paymentFrequency}
                  onChange={(e) => handleFieldChange('paymentFrequency', e.target.value)}
                  label="Payment Frequency"
                >
                  <MenuItem value="Monthly">Monthly</MenuItem>
                  <MenuItem value="Quarterly">Quarterly</MenuItem>
                  <MenuItem value="Semi-Annually">Semi-Annually</MenuItem>
                  <MenuItem value="Annually">Annually</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={12}>
              <FormControl fullWidth>
                <InputLabel>Collateral Type</InputLabel>
                <Select
                  value={formData.collateralType}
                  onChange={(e) => handleFieldChange('collateralType', e.target.value)}
                  label="Collateral Type"
                >
                  <MenuItem value="Broadly Syndicated Loans">Broadly Syndicated Loans</MenuItem>
                  <MenuItem value="Middle Market Loans">Middle Market Loans</MenuItem>
                  <MenuItem value="High Yield Bonds">High Yield Bonds</MenuItem>
                  <MenuItem value="Mixed Credit">Mixed Credit</MenuItem>
                  <MenuItem value="Structured Credit">Structured Credit</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        );
        
      case 2: // Dates & Periods
        return (
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container spacing={3}>
              <Grid size={12}>
                <Typography variant="h6" gutterBottom color="primary">
                  <CalendarToday sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Timeline & Periods
                </Typography>
              </Grid>
              
              <Grid size={{ xs: 12, sm: 6 }}>
                <DatePicker
                  label="Effective Date"
                  value={formData.effectiveDate}
                  onChange={(date) => date && handleFieldChange('effectiveDate', date)}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      error: !!errors.effectiveDate,
                      helperText: errors.effectiveDate || 'Date the CLO becomes effective',
                    },
                  }}
                />
              </Grid>
              
              <Grid size={{ xs: 12, sm: 6 }}>
                <DatePicker
                  label="Stated Maturity"
                  value={formData.statedMaturity}
                  onChange={(date) => date && handleFieldChange('statedMaturity', date)}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      error: !!errors.statedMaturity,
                      helperText: errors.statedMaturity || 'Final maturity date',
                    },
                  }}
                />
              </Grid>
              
              <Grid size={12}>
                <Divider sx={{ my: 2 }} />
              </Grid>
              
              <Grid size={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.hasRevolvingPeriod}
                      onChange={(e) => handleFieldChange('hasRevolvingPeriod', e.target.checked)}
                    />
                  }
                  label="Include Revolving Period"
                />
              </Grid>
              
              {formData.hasRevolvingPeriod && (
                <Grid size={{ xs: 12, sm: 6 }}>
                  <DatePicker
                    label="Revolving Period End"
                    value={formData.revolvingPeriodEnd}
                    onChange={(date) => handleFieldChange('revolvingPeriodEnd', date)}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: !!errors.revolvingPeriodEnd,
                        helperText: errors.revolvingPeriodEnd || 'End of revolving period',
                      },
                    }}
                  />
                </Grid>
              )}
              
              <Grid size={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.hasReinvestmentPeriod}
                      onChange={(e) => handleFieldChange('hasReinvestmentPeriod', e.target.checked)}
                    />
                  }
                  label="Include Reinvestment Period"
                />
              </Grid>
              
              {formData.hasReinvestmentPeriod && (
                <Grid size={{ xs: 12, sm: 6 }}>
                  <DatePicker
                    label="Reinvestment Period End"
                    value={formData.reinvestmentPeriodEnd}
                    onChange={(date) => handleFieldChange('reinvestmentPeriodEnd', date)}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: !!errors.reinvestmentPeriodEnd,
                        helperText: errors.reinvestmentPeriodEnd || 'End of reinvestment period',
                      },
                    }}
                  />
                </Grid>
              )}
            </Grid>
          </LocalizationProvider>
        );
        
      case 3: // Additional Details
        return (
          <Grid container spacing={3}>
            <Grid size={12}>
              <Typography variant="h6" gutterBottom color="primary">
                <Business sx={{ mr: 1, verticalAlign: 'middle' }} />
                Legal & Regulatory
              </Typography>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Rating Agency</InputLabel>
                <Select
                  value={formData.ratingAgency}
                  onChange={(e) => handleFieldChange('ratingAgency', e.target.value)}
                  label="Rating Agency"
                >
                  <MenuItem value="Moody's">Moody's</MenuItem>
                  <MenuItem value="S&P">Standard & Poor's</MenuItem>
                  <MenuItem value="Fitch">Fitch Ratings</MenuItem>
                  <MenuItem value="Multiple">Multiple Agencies</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Jurisdiction</InputLabel>
                <Select
                  value={formData.jurisdiction}
                  onChange={(e) => handleFieldChange('jurisdiction', e.target.value)}
                  label="Jurisdiction"
                >
                  <MenuItem value="United States">United States</MenuItem>
                  <MenuItem value="Cayman Islands">Cayman Islands</MenuItem>
                  <MenuItem value="Ireland">Ireland</MenuItem>
                  <MenuItem value="Luxembourg">Luxembourg</MenuItem>
                  <MenuItem value="United Kingdom">United Kingdom</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Governing Law</InputLabel>
                <Select
                  value={formData.govLaw}
                  onChange={(e) => handleFieldChange('govLaw', e.target.value)}
                  label="Governing Law"
                >
                  <MenuItem value="New York">New York</MenuItem>
                  <MenuItem value="English">English</MenuItem>
                  <MenuItem value="Delaware">Delaware</MenuItem>
                  <MenuItem value="Irish">Irish</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        );
        
      default:
        return null;
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Create New Portfolio
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Set up a new CLO portfolio with all necessary details and configurations.
        </Typography>
      </Box>

      {/* Progress Stepper */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Form Content */}
      <Card>
        <CardContent sx={{ p: 4 }}>
          {renderStepContent(activeStep)}

          {/* Form Actions */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', pt: 4, mt: 4, borderTop: 1, borderColor: 'divider' }}>
            <Button
              variant="outlined"
              startIcon={<Cancel />}
              onClick={onCancel}
              disabled={isLoading}
            >
              Cancel
            </Button>

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                disabled={activeStep === 0 || isLoading}
                onClick={handleBack}
              >
                Back
              </Button>
              
              {activeStep === steps.length - 1 ? (
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={handleSubmit}
                  disabled={isLoading}
                  size="large"
                >
                  Create Portfolio
                </Button>
              ) : (
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={isLoading}
                >
                  Next
                </Button>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Error Display */}
      {Object.keys(errors).length > 0 && (
        <Alert severity="error" sx={{ mt: 2 }}>
          Please correct the errors above before proceeding.
        </Alert>
      )}
    </Box>
  );
};

export default PortfolioCreateForm;
export type { PortfolioFormData };