import React from 'react';
import {
  Formik,
  Form,
  Field,
  FieldProps,
  FormikProps,
  FormikConfig,
  FieldArray,
} from 'formik';
import * as Yup from 'yup';
import { DatePicker } from '@mui/x-date-pickers';
import {
  TextField,
  Select,
  MenuItem,
  FormControl,
  FormControlLabel,
  FormLabel,
  FormHelperText,
  RadioGroup,
  Radio,
  Checkbox,
  Switch,
  Autocomplete,
  Box,
  Typography,
  Button,
  IconButton,
  Divider,
  Alert,
  CircularProgress,
  InputLabel,
  Chip,
  Grid,
  Paper,
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

// Field Types
export type FormFieldType =
  | 'text'
  | 'email'
  | 'password'
  | 'number'
  | 'textarea'
  | 'select'
  | 'multiselect'
  | 'autocomplete'
  | 'radio'
  | 'checkbox'
  | 'switch'
  | 'date'
  | 'time'
  | 'datetime'
  | 'file'
  | 'array'
  | 'custom';

export interface FormOption {
  value: any;
  label: string;
  disabled?: boolean;
  description?: string;
}

export interface FormField {
  name: string;
  type: FormFieldType;
  label?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  hidden?: boolean;
  helperText?: string;
  description?: string;
  validation?: Yup.AnySchema;
  
  // Select/Radio/Autocomplete options
  options?: FormOption[] | (() => Promise<FormOption[]>);
  
  // Array field configuration
  arrayConfig?: {
    minItems?: number;
    maxItems?: number;
    itemTemplate: FormField[];
    addButtonText?: string;
    removeButtonText?: string;
  };
  
  // Custom field renderer
  render?: (props: FieldProps, fieldConfig: FormField) => React.ReactNode;
  
  // Field specific props
  multiline?: boolean;
  rows?: number;
  maxRows?: number;
  fullWidth?: boolean;
  size?: 'small' | 'medium';
  variant?: 'standard' | 'outlined' | 'filled';
  
  // Conditional display
  showIf?: (values: any) => boolean;
  
  // Grid layout
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
}

export interface FormSection {
  title?: string;
  description?: string;
  fields: FormField[];
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export interface FormikWrapperProps<T = any> extends Omit<FormikConfig<T>, 'children'> {
  fields?: FormField[];
  sections?: FormSection[];
  loading?: boolean;
  error?: string;
  successMessage?: string;
  submitButtonText?: string;
  resetButtonText?: string;
  showResetButton?: boolean;
  showSubmitButton?: boolean;
  submitButtonProps?: any;
  resetButtonProps?: any;
  formProps?: any;
  paperProps?: any;
  gridProps?: any;
  children?: (props: FormikProps<T>) => React.ReactNode;
}

// Validation schema generator
const generateValidationSchema = (fields: FormField[]): Yup.ObjectSchema<any> => {
  const schemaFields: any = {};
  
  fields.forEach(field => {
    if (field.validation) {
      schemaFields[field.name] = field.validation;
    } else {
      let validator: any;
      
      switch (field.type) {
        case 'email':
          validator = Yup.string().email('Invalid email address');
          break;
        case 'number':
          validator = Yup.number();
          break;
        case 'date':
        case 'time':
        case 'datetime':
          validator = Yup.date();
          break;
        case 'array':
          validator = Yup.array();
          if (field.arrayConfig?.minItems) {
            validator = validator.min(field.arrayConfig.minItems);
          }
          if (field.arrayConfig?.maxItems) {
            validator = validator.max(field.arrayConfig.maxItems);
          }
          break;
        default:
          validator = Yup.string();
      }
      
      if (field.required) {
        validator = validator.required(`${field.label || field.name} is required`);
      }
      
      schemaFields[field.name] = validator;
    }
  });
  
  return Yup.object().shape(schemaFields);
};

// Form field renderer
const FormFieldRenderer: React.FC<{ field: FormField; formikProps: FormikProps<any> }> = ({
  field,
  formikProps,
}) => {
  const { values, errors, touched, setFieldValue, setFieldTouched } = formikProps;
  
  // Check conditional display
  if (field.showIf && !field.showIf(values)) {
    return null;
  }
  
  const fieldError = touched[field.name] && errors[field.name];
  const hasError = Boolean(fieldError);
  
  const commonProps = {
    name: field.name,
    disabled: field.disabled,
    required: field.required,
    size: field.size || 'medium',
    variant: field.variant || 'outlined',
    fullWidth: field.fullWidth !== false,
    error: hasError,
    helperText: hasError ? String(fieldError) : field.helperText,
  };

  const renderField = (fieldProps: FieldProps) => {
    if (field.render) {
      return field.render(fieldProps, field);
    }

    const { field: formikField } = fieldProps;

    switch (field.type) {
      case 'text':
      case 'email':
      case 'password':
        return (
          <TextField
            {...commonProps}
            {...formikField}
            type={field.type}
            label={field.label}
            placeholder={field.placeholder}
          />
        );

      case 'number':
        return (
          <TextField
            {...commonProps}
            {...formikField}
            type="number"
            label={field.label}
            placeholder={field.placeholder}
            onChange={(e) => {
              const value = e.target.value === '' ? null : Number(e.target.value);
              setFieldValue(field.name, value);
            }}
          />
        );

      case 'textarea':
        return (
          <TextField
            {...commonProps}
            {...formikField}
            label={field.label}
            placeholder={field.placeholder}
            multiline
            rows={field.rows || 4}
            maxRows={field.maxRows}
          />
        );

      case 'select':
        return (
          <FormControl {...commonProps}>
            <InputLabel>{field.label}</InputLabel>
            <Select
              {...formikField}
              label={field.label}
            >
              {Array.isArray(field.options) && field.options.map((option: FormOption) => (
                <MenuItem
                  key={String(option.value)}
                  value={option.value}
                  disabled={option.disabled}
                >
                  <Box>
                    <Typography>{option.label}</Typography>
                    {option.description && (
                      <Typography variant="caption" color="text.secondary">
                        {option.description}
                      </Typography>
                    )}
                  </Box>
                </MenuItem>
              ))}
            </Select>
            {field.helperText && (
              <FormHelperText>{field.helperText}</FormHelperText>
            )}
          </FormControl>
        );

      case 'multiselect':
        return (
          <FormControl {...commonProps}>
            <InputLabel>{field.label}</InputLabel>
            <Select
              {...formikField}
              multiple
              label={field.label}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as any[]).map((value) => {
                    const options = Array.isArray(field.options) ? field.options : [];
                    const option = options.find((opt: FormOption) => opt.value === value);
                    return (
                      <Chip key={String(value)} label={option?.label || value} size="small" />
                    );
                  })}
                </Box>
              )}
            >
              {Array.isArray(field.options) && field.options.map((option: FormOption) => (
                <MenuItem
                  key={String(option.value)}
                  value={option.value}
                  disabled={option.disabled}
                >
                  <Checkbox checked={formikField.value?.includes(option.value) || false} />
                  <Box sx={{ ml: 1 }}>
                    <Typography>{option.label}</Typography>
                    {option.description && (
                      <Typography variant="caption" color="text.secondary">
                        {option.description}
                      </Typography>
                    )}
                  </Box>
                </MenuItem>
              ))}
            </Select>
            {field.helperText && (
              <FormHelperText>{field.helperText}</FormHelperText>
            )}
          </FormControl>
        );

      case 'autocomplete':
        return (
          <Autocomplete
            options={Array.isArray(field.options) ? field.options : []}
            getOptionLabel={(option) => option.label}
            value={(() => {
              const options = Array.isArray(field.options) ? field.options : [];
              return options.find((opt: FormOption) => opt.value === formikField.value) || null;
            })()}
            onChange={(_, newValue) => {
              setFieldValue(field.name, newValue?.value || null);
            }}
            onBlur={() => setFieldTouched(field.name, true)}
            disabled={field.disabled}
            renderInput={(params) => (
              <TextField
                {...params}
                {...commonProps}
                label={field.label}
                placeholder={field.placeholder}
              />
            )}
          />
        );

      case 'radio':
        return (
          <FormControl component="fieldset" error={hasError}>
            <FormLabel component="legend">{field.label}</FormLabel>
            <RadioGroup
              {...formikField}
              onChange={(e) => setFieldValue(field.name, e.target.value)}
            >
              {Array.isArray(field.options) && field.options.map((option: FormOption) => (
                <FormControlLabel
                  key={String(option.value)}
                  value={option.value}
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography>{option.label}</Typography>
                      {option.description && (
                        <Typography variant="caption" color="text.secondary">
                          {option.description}
                        </Typography>
                      )}
                    </Box>
                  }
                  disabled={option.disabled || field.disabled}
                />
              ))}
            </RadioGroup>
            {field.helperText && (
              <FormHelperText>{field.helperText}</FormHelperText>
            )}
          </FormControl>
        );

      case 'checkbox':
        return (
          <FormControlLabel
            control={
              <Checkbox
                {...formikField}
                checked={Boolean(formikField.value)}
                onChange={(e) => setFieldValue(field.name, e.target.checked)}
              />
            }
            label={
              <Box>
                <Typography>{field.label}</Typography>
                {field.description && (
                  <Typography variant="caption" color="text.secondary">
                    {field.description}
                  </Typography>
                )}
              </Box>
            }
            disabled={field.disabled}
          />
        );

      case 'switch':
        return (
          <FormControlLabel
            control={
              <Switch
                {...formikField}
                checked={Boolean(formikField.value)}
                onChange={(e) => setFieldValue(field.name, e.target.checked)}
              />
            }
            label={
              <Box>
                <Typography>{field.label}</Typography>
                {field.description && (
                  <Typography variant="caption" color="text.secondary">
                    {field.description}
                  </Typography>
                )}
              </Box>
            }
            disabled={field.disabled}
          />
        );

      case 'date':
        return (
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label={field.label}
              value={formikField.value || null}
              onChange={(newValue) => setFieldValue(field.name, newValue)}
              disabled={field.disabled}
              slots={{
                textField: (params: any) => (
                  <TextField {...params} {...commonProps} />
                )
              }}
            />
          </LocalizationProvider>
        );

      case 'array':
        return (
          <FieldArray name={field.name}>
            {({ push, remove }) => (
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="subtitle2">{field.label}</Typography>
                  <Button
                    startIcon={<AddIcon />}
                    onClick={() => {
                      const template = field.arrayConfig?.itemTemplate || [];
                      const defaultItem = template.reduce((acc, field) => {
                        acc[field.name] = field.type === 'array' ? [] : '';
                        return acc;
                      }, {} as any);
                      push(defaultItem);
                    }}
                    size="small"
                    disabled={Boolean(
                      field.disabled ||
                      (field.arrayConfig?.maxItems && formikField.value?.length >= field.arrayConfig.maxItems)
                    )}
                  >
                    {field.arrayConfig?.addButtonText || 'Add Item'}
                  </Button>
                </Box>

                {formikField.value?.map((_: any, index: number) => (
                  <Paper key={index} sx={{ p: 2, mb: 2, position: 'relative' }}>
                    <IconButton
                      onClick={() => remove(index)}
                      size="small"
                      sx={{ position: 'absolute', top: 8, right: 8 }}
                      disabled={Boolean(
                        field.disabled ||
                        (field.arrayConfig?.minItems && formikField.value.length <= field.arrayConfig.minItems)
                      )}
                    >
                      <RemoveIcon />
                    </IconButton>

                    <Grid container spacing={2}>
                      {field.arrayConfig?.itemTemplate.map((itemField) => (
                        <Grid
                          key={itemField.name}
                          {...({ item: true } as any)}
                          xs={itemField.xs || 12}
                          sm={itemField.sm}
                          md={itemField.md}
                          lg={itemField.lg}
                          xl={itemField.xl}
                        >
                          <FormFieldRenderer
                            field={{
                              ...itemField,
                              name: `${field.name}.${index}.${itemField.name}`,
                            }}
                            formikProps={formikProps}
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </Paper>
                ))}

                {field.helperText && (
                  <FormHelperText error={hasError}>{field.helperText}</FormHelperText>
                )}
              </Box>
            )}
          </FieldArray>
        );

      default:
        return (
          <TextField
            {...commonProps}
            {...formikField}
            label={field.label}
            placeholder={field.placeholder}
          />
        );
    }
  };

  return (
    <Box sx={{ mb: 2 }}>
      {field.description && (
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <InfoIcon sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
          <Typography variant="caption" color="text.secondary">
            {field.description}
          </Typography>
        </Box>
      )}
      
      <Field name={field.name} key={field.name}>
        {renderField}
      </Field>
    </Box>
  );
};

const FormikWrapper = <T extends Record<string, any>>({
  fields = [],
  sections = [],
  loading = false,
  error,
  successMessage,
  submitButtonText = 'Submit',
  resetButtonText = 'Reset',
  showResetButton = true,
  showSubmitButton = true,
  submitButtonProps = {},
  resetButtonProps = {},
  formProps = {},
  paperProps = {},
  gridProps = {},
  children,
  ...formikProps
}: FormikWrapperProps<T>) => {
  // Generate validation schema if not provided
  const validationSchema = formikProps.validationSchema || (
    (fields.length > 0 || sections.length > 0) 
      ? generateValidationSchema([
          ...fields,
          ...sections.flatMap(section => section.fields)
        ])
      : undefined
  );

  return (
    <Paper elevation={1} sx={{ p: 3, ...paperProps }}>
      <Formik
        {...formikProps}
        validationSchema={validationSchema}
      >
        {(formikBag) => (
          <Form {...formProps}>
            {/* Error Alert */}
            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            {/* Success Alert */}
            {successMessage && (
              <Alert severity="success" sx={{ mb: 3 }}>
                {successMessage}
              </Alert>
            )}

            {/* Custom children renderer */}
            {children && children(formikBag)}

            {/* Field sections */}
            {sections.map((section, sectionIndex) => (
              <Box key={sectionIndex} sx={{ mb: 4 }}>
                {section.title && (
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    {section.title}
                  </Typography>
                )}
                {section.description && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {section.description}
                  </Typography>
                )}
                <Grid container spacing={2} {...gridProps}>
                  {section.fields.map((field) => (
                    <Grid
                      key={field.name}
                      {...({ item: true } as any)}
                      xs={field.xs || 12}
                      sm={field.sm}
                      md={field.md}
                      lg={field.lg}
                      xl={field.xl}
                    >
                      <FormFieldRenderer field={field} formikProps={formikBag} />
                    </Grid>
                  ))}
                </Grid>
                {sectionIndex < sections.length - 1 && <Divider sx={{ my: 3 }} />}
              </Box>
            ))}

            {/* Standalone fields */}
            {fields.length > 0 && (
              <Grid container spacing={2} {...gridProps}>
                {fields.map((field) => (
                  <Grid
                    key={field.name}
                    {...({ item: true } as any)}
                    xs={field.xs || 12}
                    sm={field.sm}
                    md={field.md}
                    lg={field.lg}
                    xl={field.xl}
                  >
                    <FormFieldRenderer field={field} formikProps={formikBag} />
                  </Grid>
                ))}
              </Grid>
            )}

            {/* Action Buttons */}
            {(showSubmitButton || showResetButton) && (
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 3 }}>
                {showResetButton && (
                  <Button
                    type="button"
                    variant="outlined"
                    onClick={() => formikBag.resetForm()}
                    disabled={loading || !formikBag.dirty}
                    {...resetButtonProps}
                  >
                    {resetButtonText}
                  </Button>
                )}
                
                {showSubmitButton && (
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={loading || !formikBag.isValid}
                    startIcon={loading ? <CircularProgress size={20} /> : undefined}
                    {...submitButtonProps}
                  >
                    {loading ? 'Submitting...' : submitButtonText}
                  </Button>
                )}
              </Box>
            )}
          </Form>
        )}
      </Formik>
    </Paper>
  );
};

export default FormikWrapper;