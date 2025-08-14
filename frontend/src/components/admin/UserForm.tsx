import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Button,
  Alert,
  Box,
  Typography,
  IconButton,
} from '@mui/material';
import { Close } from '@mui/icons-material';
import * as Yup from 'yup';
import FormikWrapper, { FormField, FormSection } from '../common/UI/FormikWrapper';
import {
  useCreateUserMutation,
  useUpdateUserMutation,
  User,
} from '../../store/api/cloApi';
import {
  UserCreateRequest,
  UserUpdateRequest,
} from '../../store/api/newApiTypes';

interface UserFormProps {
  open: boolean;
  onClose: () => void;
  user?: User | null; // null for create, User object for edit
  mode: 'create' | 'edit';
}

const UserForm: React.FC<UserFormProps> = ({
  open,
  onClose,
  user,
  mode,
}) => {
  const [createUser, { isLoading: createLoading, error: createError }] = useCreateUserMutation();
  const [updateUser, { isLoading: updateLoading, error: updateError }] = useUpdateUserMutation();

  const isLoading = createLoading || updateLoading;
  const error = createError || updateError;

  // Form validation schema
  const validationSchema = Yup.object().shape({
    firstName: Yup.string()
      .min(2, 'First name must be at least 2 characters')
      .max(50, 'First name must be less than 50 characters')
      .required('First name is required'),
    lastName: Yup.string()
      .min(2, 'Last name must be at least 2 characters')
      .max(50, 'Last name must be less than 50 characters')
      .required('Last name is required'),
    email: Yup.string()
      .email('Invalid email address')
      .required('Email is required'),
    role: Yup.string()
      .oneOf(['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer'])
      .required('Role is required'),
    password: mode === 'create' 
      ? Yup.string()
          .min(8, 'Password must be at least 8 characters')
          .matches(
            /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
            'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
          )
          .required('Password is required')
      : Yup.string()
          .min(8, 'Password must be at least 8 characters')
          .matches(
            /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
            'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
          )
          .nullable(),
    confirmPassword: mode === 'create'
      ? Yup.string()
          .oneOf([Yup.ref('password')], 'Passwords must match')
          .required('Please confirm your password')
      : Yup.string()
          .oneOf([Yup.ref('password')], 'Passwords must match')
          .nullable(),
    isActive: Yup.boolean(),
  });

  // Form fields configuration
  const formFields: FormField[] = [
    {
      name: 'firstName',
      type: 'text',
      label: 'First Name',
      placeholder: 'Enter first name',
      required: true,
      xs: 6,
    },
    {
      name: 'lastName',
      type: 'text',
      label: 'Last Name',
      placeholder: 'Enter last name',
      required: true,
      xs: 6,
    },
    {
      name: 'email',
      type: 'email',
      label: 'Email Address',
      placeholder: 'Enter email address',
      required: true,
      xs: 12,
    },
    {
      name: 'role',
      type: 'select',
      label: 'User Role',
      required: true,
      options: [
        {
          value: 'system_admin',
          label: 'System Administrator',
          description: 'Full system access and user management',
        },
        {
          value: 'portfolio_manager',
          label: 'Portfolio Manager',
          description: 'Manage portfolios and execute trades',
        },
        {
          value: 'financial_analyst',
          label: 'Financial Analyst',
          description: 'Analyze data and generate reports',
        },
        {
          value: 'viewer',
          label: 'Viewer',
          description: 'Read-only access to reports and data',
        },
      ],
      xs: 12,
    },
  ];

  // Add password fields for create mode or when editing password
  const passwordFields: FormField[] = [
    {
      name: 'password',
      type: 'password',
      label: mode === 'create' ? 'Password' : 'New Password (leave blank to keep current)',
      placeholder: 'Enter password',
      required: mode === 'create',
      helperText: 'Must be at least 8 characters with uppercase, lowercase, number, and special character',
      xs: 12,
    },
    {
      name: 'confirmPassword',
      type: 'password',
      label: 'Confirm Password',
      placeholder: 'Confirm password',
      required: mode === 'create',
      xs: 12,
    },
  ];

  // Add status field for edit mode
  const statusFields: FormField[] = mode === 'edit' ? [
    {
      name: 'isActive',
      type: 'switch',
      label: 'Account Active',
      description: 'Enable or disable user access to the system',
      xs: 12,
    },
  ] : [];

  // Form sections
  const formSections: FormSection[] = [
    {
      title: 'User Information',
      fields: formFields,
    },
    {
      title: 'Authentication',
      fields: passwordFields,
    },
    ...(statusFields.length > 0 ? [{
      title: 'Account Status',
      fields: statusFields,
    }] : []),
  ];

  // Initial form values
  const getInitialValues = () => {
    if (mode === 'edit' && user) {
      return {
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email,
        role: user.role,
        password: '',
        confirmPassword: '',
        isActive: user.isActive,
      };
    }
    
    return {
      firstName: '',
      lastName: '',
      email: '',
      role: '',
      password: '',
      confirmPassword: '',
      isActive: true,
    };
  };

  // Form submission handler
  const handleSubmit = async (values: any) => {
    try {
      if (mode === 'create') {
        const createData: UserCreateRequest = {
          username: values.email, // Use email as username
          first_name: values.firstName,
          last_name: values.lastName,
          email: values.email,
          role: values.role,
          password: values.password,
          timezone: 'UTC',
          language: 'en',
          send_welcome_email: true,
        };
        
        await createUser(createData).unwrap();
      } else if (mode === 'edit' && user) {
        const updateData: UserUpdateRequest = {
          first_name: values.firstName,
          last_name: values.lastName,
          email: values.email,
          role: values.role,
          status: values.isActive ? 'active' : 'inactive',
        };
        
        await updateUser({
          userId: user.id,
          data: updateData,
        }).unwrap();
      }
      
      onClose();
    } catch (error) {
      // Error is handled by the mutation hook
      console.error('Form submission error:', error);
    }
  };

  // Format error message
  const getErrorMessage = (error: any): string => {
    if (typeof error === 'string') return error;
    if (error?.data?.message) return error.data.message;
    if (error?.data?.detail) return error.data.detail;
    if (error?.message) return error.message;
    return 'An unexpected error occurred. Please try again.';
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            {mode === 'create' ? 'Create New User' : `Edit User: ${user?.firstName} ${user?.lastName}`}
          </Typography>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ pb: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {getErrorMessage(error)}
          </Alert>
        )}

        <FormikWrapper
          initialValues={getInitialValues()}
          validationSchema={validationSchema}
          onSubmit={handleSubmit}
          sections={formSections}
          loading={isLoading}
          submitButtonText={mode === 'create' ? 'Create User' : 'Update User'}
          showResetButton={true}
          resetButtonText="Reset"
          showSubmitButton={true}
          paperProps={{ elevation: 0, sx: { p: 0 } }}
          submitButtonProps={{
            sx: { minWidth: 120 }
          }}
          resetButtonProps={{
            sx: { minWidth: 120 }
          }}
        />
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Button onClick={onClose} disabled={isLoading} sx={{ mr: 1 }}>
            Cancel
          </Button>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default UserForm;