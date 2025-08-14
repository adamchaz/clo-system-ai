import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import * as Yup from 'yup';
import FormikWrapper, { FormField, FormSection } from './FormikWrapper';

const theme = createTheme();

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        {component}
      </LocalizationProvider>
    </ThemeProvider>
  );
};

const basicFields: FormField[] = [
  {
    name: 'firstName',
    type: 'text',
    label: 'First Name',
    required: true,
    placeholder: 'Enter first name',
  },
  {
    name: 'lastName',
    type: 'text',
    label: 'Last Name',
    required: true,
  },
  {
    name: 'email',
    type: 'email',
    label: 'Email',
    required: true,
  },
  {
    name: 'age',
    type: 'number',
    label: 'Age',
  },
];

const selectField: FormField = {
  name: 'country',
  type: 'select',
  label: 'Country',
  options: [
    { value: 'us', label: 'United States' },
    { value: 'uk', label: 'United Kingdom' },
    { value: 'ca', label: 'Canada' },
  ],
};

const multiselectField: FormField = {
  name: 'skills',
  type: 'multiselect',
  label: 'Skills',
  options: [
    { value: 'js', label: 'JavaScript' },
    { value: 'python', label: 'Python' },
    { value: 'react', label: 'React' },
    { value: 'node', label: 'Node.js' },
  ],
};

const radioField: FormField = {
  name: 'experience',
  type: 'radio',
  label: 'Experience Level',
  options: [
    { value: 'junior', label: 'Junior (0-2 years)' },
    { value: 'mid', label: 'Mid (3-5 years)' },
    { value: 'senior', label: 'Senior (5+ years)' },
  ],
};

const checkboxField: FormField = {
  name: 'newsletter',
  type: 'checkbox',
  label: 'Subscribe to newsletter',
};

const arrayField: FormField = {
  name: 'projects',
  type: 'array',
  label: 'Projects',
  arrayConfig: {
    minItems: 1,
    maxItems: 3,
    addButtonText: 'Add Project',
    itemTemplate: [
      {
        name: 'name',
        type: 'text',
        label: 'Project Name',
        required: true,
        xs: 6,
      },
      {
        name: 'description',
        type: 'textarea',
        label: 'Description',
        xs: 6,
      },
    ],
  },
};

const sections: FormSection[] = [
  {
    title: 'Personal Information',
    description: 'Please provide your personal details',
    fields: [
      basicFields[0], // firstName
      basicFields[1], // lastName
      basicFields[2], // email
    ],
  },
  {
    title: 'Professional Information',
    fields: [
      selectField,
      radioField,
      multiselectField,
    ],
  },
];

describe('FormikWrapper Component', () => {
  const mockSubmit = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    test('renders form with basic fields', () => {
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '', lastName: '', email: '', age: '' }}
          onSubmit={mockSubmit}
          fields={basicFields}
        />
      );

      expect(screen.getByLabelText('First Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Last Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Age')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
    });

    test('renders form with sections', () => {
      renderWithProviders(
        <FormikWrapper
          initialValues={{
            firstName: '',
            lastName: '',
            email: '',
            country: '',
            experience: '',
            skills: [],
          }}
          onSubmit={mockSubmit}
          sections={sections}
        />
      );

      expect(screen.getByText('Personal Information')).toBeInTheDocument();
      expect(screen.getByText('Please provide your personal details')).toBeInTheDocument();
      expect(screen.getByText('Professional Information')).toBeInTheDocument();
    });
  });

  describe('Field Types', () => {
    test('handles text input', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[0]]}
        />
      );

      const input = screen.getByLabelText('First Name');
      await user.type(input, 'John');
      expect(input).toHaveValue('John');
    });

    test('handles email input with validation', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ email: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[2]]}
        />
      );

      const emailInput = screen.getByLabelText('Email');
      await user.type(emailInput, 'invalid-email');
      await user.tab(); // Trigger blur event

      await waitFor(() => {
        expect(screen.getByText('Invalid email address')).toBeInTheDocument();
      });
    });

    test('handles number input', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ age: null }}
          onSubmit={mockSubmit}
          fields={[basicFields[3]]}
        />
      );

      const numberInput = screen.getByLabelText('Age');
      await user.type(numberInput, '25');
      expect(numberInput).toHaveValue(25);
    });

    test('handles select field', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ country: '' }}
          onSubmit={mockSubmit}
          fields={[selectField]}
        />
      );

      const select = screen.getByLabelText('Country');
      await user.click(select);
      
      const usOption = screen.getByText('United States');
      await user.click(usOption);

      expect(select).toHaveTextContent('United States');
    });

    test('handles multiselect field', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ skills: [] }}
          onSubmit={mockSubmit}
          fields={[multiselectField]}
        />
      );

      const multiSelect = screen.getByLabelText('Skills');
      await user.click(multiSelect);

      const jsOption = screen.getByText('JavaScript');
      await user.click(jsOption);

      const reactOption = screen.getByText('React');
      await user.click(reactOption);

      // Close dropdown
      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
        expect(screen.getByText('React')).toBeInTheDocument();
      });
    });

    test('handles radio field', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ experience: '' }}
          onSubmit={mockSubmit}
          fields={[radioField]}
        />
      );

      const juniorRadio = screen.getByLabelText('Junior (0-2 years)');
      await user.click(juniorRadio);

      expect(juniorRadio).toBeChecked();
    });

    test('handles checkbox field', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ newsletter: false }}
          onSubmit={mockSubmit}
          fields={[checkboxField]}
        />
      );

      const checkbox = screen.getByLabelText('Subscribe to newsletter');
      await user.click(checkbox);

      expect(checkbox).toBeChecked();
    });

    test('handles textarea field', async () => {
      const user = userEvent;
      const textareaField: FormField = {
        name: 'description',
        type: 'textarea',
        label: 'Description',
        rows: 4,
      };

      renderWithProviders(
        <FormikWrapper
          initialValues={{ description: '' }}
          onSubmit={mockSubmit}
          fields={[textareaField]}
        />
      );

      const textarea = screen.getByLabelText('Description');
      await user.type(textarea, 'This is a description');

      expect(textarea).toHaveValue('This is a description');
    });
  });

  describe('Array Fields', () => {
    test('handles array field with add/remove functionality', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ projects: [{ name: '', description: '' }] }}
          onSubmit={mockSubmit}
          fields={[arrayField]}
        />
      );

      expect(screen.getByText('Projects')).toBeInTheDocument();
      expect(screen.getByText('Add Project')).toBeInTheDocument();

      // Add a new project
      const addButton = screen.getByText('Add Project');
      await user.click(addButton);

      const projectNameInputs = screen.getAllByLabelText('Project Name');
      expect(projectNameInputs).toHaveLength(2);

      // Fill in project details
      await user.type(projectNameInputs[0], 'Project 1');
      
      const descriptionInputs = screen.getAllByLabelText('Description');
      await user.type(descriptionInputs[0], 'First project description');

      expect(projectNameInputs[0]).toHaveValue('Project 1');
      expect(descriptionInputs[0]).toHaveValue('First project description');
    });

    test('enforces array min/max limits', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ projects: [{ name: '', description: '' }] }}
          onSubmit={mockSubmit}
          fields={[arrayField]}
        />
      );

      // Add maximum allowed projects
      const addButton = screen.getByText('Add Project');
      await user.click(addButton); // 2 projects
      await user.click(addButton); // 3 projects (max)

      // Button should be disabled now
      expect(addButton).toBeDisabled();

      const projectNameInputs = screen.getAllByLabelText('Project Name');
      expect(projectNameInputs).toHaveLength(3);
    });
  });

  describe('Form Validation', () => {
    test('shows validation errors for required fields', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '', email: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[0], basicFields[2]]}
        />
      );

      const submitButton = screen.getByRole('button', { name: 'Submit' });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('First Name is required')).toBeInTheDocument();
        expect(screen.getByText('Email is required')).toBeInTheDocument();
      });

      expect(mockSubmit).not.toHaveBeenCalled();
    });

    test('uses custom validation schema', async () => {
      const user = userEvent;
      const validationSchema = Yup.object().shape({
        firstName: Yup.string()
          .min(2, 'Name must be at least 2 characters')
          .required('First name is required'),
      });

      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '' }}
          onSubmit={mockSubmit}
          validationSchema={validationSchema}
          fields={[basicFields[0]]}
        />
      );

      const input = screen.getByLabelText('First Name');
      await user.type(input, 'A');
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText('Name must be at least 2 characters')).toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    test('submits form with valid data', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '', lastName: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[0], basicFields[1]]}
        />
      );

      await user.type(screen.getByLabelText('First Name'), 'John');
      await user.type(screen.getByLabelText('Last Name'), 'Doe');

      const submitButton = screen.getByRole('button', { name: 'Submit' });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockSubmit).toHaveBeenCalledWith(
          { firstName: 'John', lastName: 'Doe' },
          expect.any(Object)
        );
      });
    });

    test('shows loading state during submission', async () => {
      const user = userEvent;
      const slowSubmit = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));

      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: 'John' }}
          onSubmit={slowSubmit}
          fields={[basicFields[0]]}
          loading
        />
      );

      expect(screen.getByText('Submitting...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Submitting...' })).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    test('displays form-level error', () => {
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[0]]}
          error="Form submission failed"
        />
      );

      expect(screen.getByText('Form submission failed')).toBeInTheDocument();
    });

    test('displays success message', () => {
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[0]]}
          successMessage="Form submitted successfully"
        />
      );

      expect(screen.getByText('Form submitted successfully')).toBeInTheDocument();
    });
  });

  describe('Form Actions', () => {
    test('handles form reset', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '', lastName: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[0], basicFields[1]]}
          showResetButton
        />
      );

      // Fill form
      await user.type(screen.getByLabelText('First Name'), 'John');
      await user.type(screen.getByLabelText('Last Name'), 'Doe');

      // Reset form
      const resetButton = screen.getByRole('button', { name: 'Reset' });
      await user.click(resetButton);

      expect(screen.getByLabelText('First Name')).toHaveValue('');
      expect(screen.getByLabelText('Last Name')).toHaveValue('');
    });

    test('customizes button text', () => {
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[0]]}
          submitButtonText="Save Changes"
          resetButtonText="Clear Form"
        />
      );

      expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Clear Form' })).toBeInTheDocument();
    });

    test('hides buttons when specified', () => {
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[0]]}
          showSubmitButton={false}
          showResetButton={false}
        />
      );

      expect(screen.queryByRole('button', { name: 'Submit' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Reset' })).not.toBeInTheDocument();
    });
  });

  describe('Conditional Fields', () => {
    test('shows/hides fields based on conditions', async () => {
      const user = userEvent;
      const conditionalFields: FormField[] = [
        {
          name: 'hasExperience',
          type: 'checkbox',
          label: 'I have experience',
        },
        {
          name: 'yearsOfExperience',
          type: 'number',
          label: 'Years of Experience',
          showIf: (values) => values.hasExperience,
        },
      ];

      renderWithProviders(
        <FormikWrapper
          initialValues={{ hasExperience: false, yearsOfExperience: '' }}
          onSubmit={mockSubmit}
          fields={conditionalFields}
        />
      );

      // Field should be hidden initially
      expect(screen.queryByLabelText('Years of Experience')).not.toBeInTheDocument();

      // Check the checkbox
      await user.click(screen.getByLabelText('I have experience'));

      // Field should now be visible
      await waitFor(() => {
        expect(screen.getByLabelText('Years of Experience')).toBeInTheDocument();
      });
    });
  });

  describe('Custom Rendering', () => {
    test('uses custom field renderer', () => {
      const customField: FormField = {
        name: 'custom',
        type: 'custom',
        label: 'Custom Field',
        render: () => <div data-testid="custom-field">Custom Content</div>,
      };

      renderWithProviders(
        <FormikWrapper
          initialValues={{ custom: '' }}
          onSubmit={mockSubmit}
          fields={[customField]}
        />
      );

      expect(screen.getByTestId('custom-field')).toBeInTheDocument();
      expect(screen.getByText('Custom Content')).toBeInTheDocument();
    });

    test('uses custom children renderer', () => {
      renderWithProviders(
        <FormikWrapper
          initialValues={{ test: '' }}
          onSubmit={mockSubmit}
        >
          {(formikProps) => (
            <div data-testid="custom-form">
              <input
                name="test"
                value={formikProps.values.test}
                onChange={formikProps.handleChange}
              />
              <div>Custom form content</div>
            </div>
          )}
        </FormikWrapper>
      );

      expect(screen.getByTestId('custom-form')).toBeInTheDocument();
      expect(screen.getByText('Custom form content')).toBeInTheDocument();
    });
  });

  describe('Grid Layout', () => {
    test('applies grid layout to fields', () => {
      const gridFields: FormField[] = [
        { ...basicFields[0], xs: 6 },
        { ...basicFields[1], xs: 6 },
        { ...basicFields[2], xs: 12 },
      ];

      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '', lastName: '', email: '' }}
          onSubmit={mockSubmit}
          fields={gridFields}
        />
      );

      // Fields should be rendered (grid layout is CSS-based)
      expect(screen.getByLabelText('First Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Last Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper form structure and labels', () => {
      renderWithProviders(
        <FormikWrapper
          initialValues={{ firstName: '', email: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[0], basicFields[2]]}
        />
      );

      expect(screen.getByRole('form')).toBeInTheDocument();
      expect(screen.getByLabelText('First Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
    });

    test('associates error messages with form fields', async () => {
      const user = userEvent;
      renderWithProviders(
        <FormikWrapper
          initialValues={{ email: '' }}
          onSubmit={mockSubmit}
          fields={[basicFields[2]]}
        />
      );

      const emailInput = screen.getByLabelText('Email');
      await user.type(emailInput, 'invalid');
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText('Invalid email address')).toBeInTheDocument();
        expect(emailInput).toHaveAttribute('aria-invalid', 'true');
      });
    });
  });

  describe('Performance', () => {
    test('renders efficiently with many fields', () => {
      const manyFields: FormField[] = Array.from({ length: 20 }, (_, i) => ({
        name: `field${i}`,
        type: 'text',
        label: `Field ${i + 1}`,
      }));

      const startTime = performance.now();

      renderWithProviders(
        <FormikWrapper
          initialValues={manyFields.reduce((acc, field) => ({ ...acc, [field.name]: '' }), {})}
          onSubmit={mockSubmit}
          fields={manyFields}
        />
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      expect(renderTime).toBeLessThan(200); // 200ms threshold
      expect(screen.getByLabelText('Field 1')).toBeInTheDocument();
      expect(screen.getByLabelText('Field 20')).toBeInTheDocument();
    });
  });
});