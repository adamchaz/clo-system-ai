import React, { useState, useCallback, useEffect } from 'react';
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
  Chip,
  Paper,
} from '@mui/material';
import {
  Save,
  Cancel,
  AccountBalance,
  Business,
  CalendarToday,
  AttachMoney,
  Lock,
  Edit,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format, parseISO } from 'date-fns';
import { Portfolio } from '../../store/api/cloApi';
import { PortfolioFormData } from './PortfolioCreateForm';

interface PortfolioEditFormProps {
  portfolio: Portfolio;
  onSubmit: (portfolioId: string, updates: Partial<PortfolioFormData>) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const PortfolioEditForm: React.FC<PortfolioEditFormProps> = ({
  portfolio,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<PortfolioFormData>({
    dealName: portfolio.deal_name,
    manager: portfolio.manager,
    trustee: portfolio.trustee,
    currency: portfolio.currency,
    dealSize: portfolio.deal_size,
    effectiveDate: parseISO(portfolio.effective_date),
    statedMaturity: parseISO(portfolio.stated_maturity),
    revolvingPeriodEnd: portfolio.revolving_period_end ? parseISO(portfolio.revolving_period_end) : undefined,
    reinvestmentPeriodEnd: portfolio.reinvestment_period_end ? parseISO(portfolio.reinvestment_period_end) : undefined,
    hasRevolvingPeriod: !!portfolio.revolving_period_end,
    hasReinvestmentPeriod: !!portfolio.reinvestment_period_end,
    description: '', // Portfolio description not in API yet
    ratingAgency: 'Moody\'s', // Default, would come from portfolio data in real app
    jurisdiction: 'United States', // Default, would come from portfolio data in real app
    govLaw: 'New York', // Default, would come from portfolio data in real app
    collateralType: 'Broadly Syndicated Loans', // Default, would come from portfolio data in real app
    minimumDenomination: 100000, // Default, would come from portfolio data in real app
    paymentFrequency: 'Quarterly', // Default, would come from portfolio data in real app
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [originalData, setOriginalData] = useState<PortfolioFormData>();

  // Store original data for comparison
  useEffect(() => {
    setOriginalData({ ...formData });
  }, []);

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

  // Check if field has been modified
  const isFieldModified = (field: keyof PortfolioFormData): boolean => {
    if (!originalData) return false;
    return JSON.stringify(formData[field]) !== JSON.stringify(originalData[field]);
  };

  // Get only changed fields
  const getChangedFields = (): Partial<PortfolioFormData> => {
    if (!originalData) return {};
    
    const changes: Partial<PortfolioFormData> = {};
    Object.keys(formData).forEach((key) => {
      const field = key as keyof PortfolioFormData;
      if (isFieldModified(field)) {
        (changes as any)[field] = formData[field];
      }
    });
    return changes;
  };

  // Check if some key fields are read-only after creation
  const isReadOnlyField = (field: string): boolean => {
    // In practice, certain fields like effective_date, deal_size might be read-only after deal is active
    const readOnlyFields = portfolio.status === 'effective' 
      ? ['dealName', 'effectiveDate', 'dealSize', 'currency']
      : [];
    return readOnlyFields.includes(field);
  };

  // Validation
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Basic validation
    if (!formData.dealName) newErrors.dealName = 'Deal name is required';
    if (!formData.manager) newErrors.manager = 'Manager is required';
    if (!formData.trustee) newErrors.trustee = 'Trustee is required';
    if (formData.dealSize <= 0) newErrors.dealSize = 'Deal size must be greater than 0';
    
    // Date validation
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
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Form submission
  const handleSubmit = () => {
    if (validateForm()) {
      const changes = getChangedFields();
      if (Object.keys(changes).length === 0) {
        setErrors({ form: 'No changes detected' });
        return;
      }
      onSubmit(portfolio.id, changes);
    }
  };

  const hasChanges = Object.keys(getChangedFields()).length > 0;

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <AccountBalance sx={{ mr: 2, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" component="h1">
              Edit Portfolio
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {portfolio.deal_name}
            </Typography>
          </Box>
          <Box sx={{ ml: 'auto' }}>
            <Chip
              label={portfolio.status === 'effective' ? 'Active' : portfolio.status}
              color={portfolio.status === 'effective' ? 'success' : 'default'}
              variant="outlined"
            />
          </Box>
        </Box>
        
        {portfolio.status === 'effective' && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Lock sx={{ mr: 1 }} />
              Some fields are read-only because this portfolio is currently active.
            </Box>
          </Alert>
        )}
      </Box>

      {/* Portfolio Information */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom color="primary">
            <AccountBalance sx={{ mr: 1, verticalAlign: 'middle' }} />
            Portfolio Identity
          </Typography>
          
          <Grid container spacing={3}>
            <Grid {...({ item: true } as any)} size={12}>
              <TextField
                fullWidth
                label="Deal Name"
                value={formData.dealName}
                onChange={(e) => handleFieldChange('dealName', e.target.value)}
                error={!!errors.dealName}
                helperText={errors.dealName}
                disabled={isReadOnlyField('dealName') || isLoading}
                InputProps={{
                  endAdornment: isFieldModified('dealName') && (
                    <InputAdornment position="end">
                      <Edit color="primary" fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Manager"
                value={formData.manager}
                onChange={(e) => handleFieldChange('manager', e.target.value)}
                error={!!errors.manager}
                helperText={errors.manager}
                disabled={isLoading}
                InputProps={{
                  endAdornment: isFieldModified('manager') && (
                    <InputAdornment position="end">
                      <Edit color="primary" fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Trustee"
                value={formData.trustee}
                onChange={(e) => handleFieldChange('trustee', e.target.value)}
                error={!!errors.trustee}
                helperText={errors.trustee}
                disabled={isLoading}
                InputProps={{
                  endAdornment: isFieldModified('trustee') && (
                    <InputAdornment position="end">
                      <Edit color="primary" fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid {...({ item: true } as any)} size={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={formData.description}
                onChange={(e) => handleFieldChange('description', e.target.value)}
                helperText="Portfolio description and investment strategy"
                disabled={isLoading}
                InputProps={{
                  endAdornment: isFieldModified('description') && (
                    <InputAdornment position="end">
                      <Edit color="primary" fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Financial Details */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom color="primary">
            <AttachMoney sx={{ mr: 1, verticalAlign: 'middle' }} />
            Financial Structure
          </Typography>
          
          <Grid container spacing={3}>
            <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Deal Size"
                type="number"
                value={formData.dealSize}
                onChange={(e) => handleFieldChange('dealSize', Number(e.target.value))}
                error={!!errors.dealSize}
                helperText={errors.dealSize}
                disabled={isReadOnlyField('dealSize') || isLoading}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  endAdornment: (
                    <>
                      <InputAdornment position="end">{formData.currency}</InputAdornment>
                      {isFieldModified('dealSize') && (
                        <InputAdornment position="end">
                          <Edit color="primary" fontSize="small" />
                        </InputAdornment>
                      )}
                    </>
                  ),
                }}
                inputProps={{ min: 0, step: 1000000 }}
              />
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth disabled={isReadOnlyField('currency') || isLoading}>
                <InputLabel>Currency</InputLabel>
                <Select
                  value={formData.currency}
                  onChange={(e) => handleFieldChange('currency', e.target.value)}
                  label="Currency"
                  endAdornment={isFieldModified('currency') && (
                    <InputAdornment position="end">
                      <Edit color="primary" fontSize="small" />
                    </InputAdornment>
                  )}
                >
                  <MenuItem value="USD">USD - US Dollar</MenuItem>
                  <MenuItem value="EUR">EUR - Euro</MenuItem>
                  <MenuItem value="GBP">GBP - British Pound</MenuItem>
                  <MenuItem value="JPY">JPY - Japanese Yen</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Minimum Denomination"
                type="number"
                value={formData.minimumDenomination}
                onChange={(e) => handleFieldChange('minimumDenomination', Number(e.target.value))}
                disabled={isLoading}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  endAdornment: isFieldModified('minimumDenomination') && (
                    <InputAdornment position="end">
                      <Edit color="primary" fontSize="small" />
                    </InputAdornment>
                  ),
                }}
                inputProps={{ min: 0, step: 1000 }}
              />
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth disabled={isLoading}>
                <InputLabel>Payment Frequency</InputLabel>
                <Select
                  value={formData.paymentFrequency}
                  onChange={(e) => handleFieldChange('paymentFrequency', e.target.value)}
                  label="Payment Frequency"
                  endAdornment={isFieldModified('paymentFrequency') && (
                    <InputAdornment position="end">
                      <Edit color="primary" fontSize="small" />
                    </InputAdornment>
                  )}
                >
                  <MenuItem value="Monthly">Monthly</MenuItem>
                  <MenuItem value="Quarterly">Quarterly</MenuItem>
                  <MenuItem value="Semi-Annually">Semi-Annually</MenuItem>
                  <MenuItem value="Annually">Annually</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Dates & Periods */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom color="primary">
            <CalendarToday sx={{ mr: 1, verticalAlign: 'middle' }} />
            Timeline & Periods
          </Typography>
          
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid container spacing={3}>
              <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
                <DatePicker
                  label="Effective Date"
                  value={formData.effectiveDate}
                  onChange={(date) => date && handleFieldChange('effectiveDate', date)}
                  disabled={isReadOnlyField('effectiveDate') || isLoading}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      error: !!errors.effectiveDate,
                      helperText: errors.effectiveDate,
                      InputProps: {
                        endAdornment: isFieldModified('effectiveDate') && (
                          <InputAdornment position="end">
                            <Edit color="primary" fontSize="small" />
                          </InputAdornment>
                        ),
                      },
                    },
                  }}
                />
              </Grid>
              
              <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
                <DatePicker
                  label="Stated Maturity"
                  value={formData.statedMaturity}
                  onChange={(date) => date && handleFieldChange('statedMaturity', date)}
                  disabled={isLoading}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      error: !!errors.statedMaturity,
                      helperText: errors.statedMaturity,
                      InputProps: {
                        endAdornment: isFieldModified('statedMaturity') && (
                          <InputAdornment position="end">
                            <Edit color="primary" fontSize="small" />
                          </InputAdornment>
                        ),
                      },
                    },
                  }}
                />
              </Grid>
              
              <Grid {...({ item: true } as any)} size={12}>
                <Divider />
              </Grid>
              
              <Grid {...({ item: true } as any)} size={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.hasRevolvingPeriod}
                      onChange={(e) => handleFieldChange('hasRevolvingPeriod', e.target.checked)}
                      disabled={isLoading}
                    />
                  }
                  label="Include Revolving Period"
                />
              </Grid>
              
              {formData.hasRevolvingPeriod && (
                <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
                  <DatePicker
                    label="Revolving Period End"
                    value={formData.revolvingPeriodEnd}
                    onChange={(date) => handleFieldChange('revolvingPeriodEnd', date)}
                    disabled={isLoading}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: !!errors.revolvingPeriodEnd,
                        helperText: errors.revolvingPeriodEnd,
                        InputProps: {
                          endAdornment: isFieldModified('revolvingPeriodEnd') && (
                            <InputAdornment position="end">
                              <Edit color="primary" fontSize="small" />
                            </InputAdornment>
                          ),
                        },
                      },
                    }}
                  />
                </Grid>
              )}
              
              <Grid {...({ item: true } as any)} size={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.hasReinvestmentPeriod}
                      onChange={(e) => handleFieldChange('hasReinvestmentPeriod', e.target.checked)}
                      disabled={isLoading}
                    />
                  }
                  label="Include Reinvestment Period"
                />
              </Grid>
              
              {formData.hasReinvestmentPeriod && (
                <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }}>
                  <DatePicker
                    label="Reinvestment Period End"
                    value={formData.reinvestmentPeriodEnd}
                    onChange={(date) => handleFieldChange('reinvestmentPeriodEnd', date)}
                    disabled={isLoading}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: !!errors.reinvestmentPeriodEnd,
                        helperText: errors.reinvestmentPeriodEnd,
                        InputProps: {
                          endAdornment: isFieldModified('reinvestmentPeriodEnd') && (
                            <InputAdornment position="end">
                              <Edit color="primary" fontSize="small" />
                            </InputAdornment>
                          ),
                        },
                      },
                    }}
                  />
                </Grid>
              )}
            </Grid>
          </LocalizationProvider>
        </CardContent>
      </Card>

      {/* Current Portfolio Stats */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
        <Typography variant="h6" gutterBottom>
          Current Portfolio Statistics
        </Typography>
        <Grid container spacing={3}>
          <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 3 }}>
            <Typography variant="body2" color="text.secondary">Current NAV</Typography>
            <Typography variant="h6">
              ${(portfolio.current_portfolio_balance / 1000000).toFixed(1)}M
            </Typography>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 3 }}>
            <Typography variant="body2" color="text.secondary">Asset Count</Typography>
            <Typography variant="h6">{portfolio.current_asset_count}</Typography>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 3 }}>
            <Typography variant="body2" color="text.secondary">Days to Maturity</Typography>
            <Typography variant="h6">{portfolio.days_to_maturity}</Typography>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 3 }}>
            <Typography variant="body2" color="text.secondary">Last Updated</Typography>
            <Typography variant="h6">
              {format(parseISO(portfolio.updated_at), 'MMM d, yyyy')}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Form Actions */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              {hasChanges && (
                <Typography variant="body2" color="primary">
                  {Object.keys(getChangedFields()).length} field(s) modified
                </Typography>
              )}
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<Cancel />}
                onClick={onCancel}
                disabled={isLoading}
              >
                Cancel
              </Button>
              
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={handleSubmit}
                disabled={isLoading || !hasChanges}
                size="large"
              >
                Save Changes
              </Button>
            </Box>
          </Box>

          {errors.form && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              {errors.form}
            </Alert>
          )}
          
          {Object.keys(errors).length > 0 && !errors.form && (
            <Alert severity="error" sx={{ mt: 2 }}>
              Please correct the errors above before saving.
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default PortfolioEditForm;