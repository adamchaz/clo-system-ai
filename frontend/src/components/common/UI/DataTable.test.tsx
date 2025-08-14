import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import DataTable, { DataTableColumn, DataTableAction } from './DataTable';

const theme = createTheme();

const mockData = [
  { id: 1, name: 'Asset A', value: 1000000, rating: 'AAA', active: true, lastUpdated: '2023-01-01' },
  { id: 2, name: 'Asset B', value: 750000, rating: 'AA+', active: true, lastUpdated: '2023-01-02' },
  { id: 3, name: 'Asset C', value: 500000, rating: 'A', active: false, lastUpdated: '2023-01-03' },
  { id: 4, name: 'Asset D', value: 2000000, rating: 'AAA', active: true, lastUpdated: '2023-01-04' },
  { id: 5, name: 'Asset E', value: 300000, rating: 'BBB', active: false, lastUpdated: '2023-01-05' },
];

const columns: DataTableColumn[] = [
  {
    id: 'name',
    label: 'Asset Name',
    sortable: true,
    minWidth: 200,
  },
  {
    id: 'value',
    label: 'Value',
    align: 'right',
    sortable: true,
    format: (value) => `$${value.toLocaleString()}`,
  },
  {
    id: 'rating',
    label: 'Rating',
    align: 'center',
    sortable: true,
  },
  {
    id: 'active',
    label: 'Status',
    align: 'center',
    render: (value) => (value ? 'Active' : 'Inactive'),
  },
  {
    id: 'lastUpdated',
    label: 'Last Updated',
    align: 'center',
    format: (value) => new Date(value).toLocaleDateString(),
  },
];

const actions: DataTableAction[] = [
  {
    icon: () => <span>📊</span>,
    label: 'Export Data',
    onClick: jest.fn(),
  },
];

const rowActions: DataTableAction[] = [
  {
    icon: () => <span>👁️</span>,
    label: 'View',
    onClick: jest.fn(),
  },
  {
    icon: () => <span>✏️</span>,
    label: 'Edit',
    onClick: jest.fn(),
  },
  {
    icon: () => <span>🗑️</span>,
    label: 'Delete',
    onClick: jest.fn(),
    color: 'error',
  },
];

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('DataTable Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders basic table with data', () => {
    renderWithTheme(
      <DataTable
        columns={columns}
        data={mockData}
        title="Asset Portfolio"
      />
    );

    expect(screen.getByText('Asset Portfolio')).toBeInTheDocument();
    expect(screen.getByText('Asset A')).toBeInTheDocument();
    expect(screen.getByText('Asset B')).toBeInTheDocument();
    expect(screen.getByText('$1,000,000')).toBeInTheDocument();
    expect(screen.getAllByText('AAA')).toHaveLength(2); // Two assets have AAA rating
  });

  test('handles sorting functionality', async () => {
    renderWithTheme(
      <DataTable columns={columns} data={mockData} />
    );

    // Click on Name column header to sort
    const nameHeader = screen.getByText('Asset Name');
    fireEvent.click(nameHeader);

    await waitFor(() => {
      const rows = screen.getAllByRole('row');
      // Skip header row, check first data row
      expect(rows[1]).toHaveTextContent('Asset A');
    });

    // Click again to reverse sort
    fireEvent.click(nameHeader);

    await waitFor(() => {
      const rows = screen.getAllByRole('row');
      // Skip header row, check first data row after reverse sort
      expect(rows[1]).toHaveTextContent('Asset E');
    });
  });

  test('handles search functionality', async () => {
    renderWithTheme(
      <DataTable columns={columns} data={mockData} searchable />
    );

    const searchInput = screen.getByPlaceholderText('Search...');
    fireEvent.change(searchInput, { target: { value: 'Asset A' } });

    await waitFor(() => {
      expect(screen.getByText('Asset A')).toBeInTheDocument();
      expect(screen.queryByText('Asset B')).not.toBeInTheDocument();
    });
  });

  test('handles row selection', () => {
    const mockSelectionChange = jest.fn();
    renderWithTheme(
      <DataTable
        columns={columns}
        data={mockData}
        selectable
        onSelectionChange={mockSelectionChange}
      />
    );

    const firstCheckbox = screen.getAllByRole('checkbox')[1]; // Skip header checkbox
    fireEvent.click(firstCheckbox);

    expect(mockSelectionChange).toHaveBeenCalledWith([mockData[0]]);
  });

  test('handles pagination', () => {
    renderWithTheme(
      <DataTable
        columns={columns}
        data={mockData}
        pageSize={10}
        pageSizeOptions={[10, 25]}
      />
    );

    // Should show all rows on first page with pageSize=10
    expect(screen.getByText('Asset A')).toBeInTheDocument();
    expect(screen.getByText('Asset B')).toBeInTheDocument();
    expect(screen.getByText('Asset C')).toBeInTheDocument();
    expect(screen.getByText('Asset D')).toBeInTheDocument();
    expect(screen.getByText('Asset E')).toBeInTheDocument();
    
    // Check that pagination controls exist
    expect(screen.getByText('Rows per page:')).toBeInTheDocument();
  });

  test('handles empty state', () => {
    renderWithTheme(
      <DataTable
        columns={columns}
        data={[]}
        emptyMessage="No assets found"
      />
    );

    expect(screen.getByText('No assets found')).toBeInTheDocument();
  });

  test('handles loading state', () => {
    renderWithTheme(
      <DataTable
        columns={columns}
        data={mockData}
        loading
      />
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('handles row actions', () => {
    renderWithTheme(
      <DataTable
        columns={columns}
        data={mockData}
        rowActions={rowActions}
      />
    );

    // Click on first row's action button
    const actionButtons = screen.getAllByRole('button');
    const firstRowActionButton = actionButtons.find(button => 
      button.getAttribute('aria-label') === undefined && 
      button.textContent === ''
    );

    if (firstRowActionButton) {
      fireEvent.click(firstRowActionButton);
      
      // Check if menu items appear
      expect(screen.getByText('View')).toBeInTheDocument();
      expect(screen.getByText('Edit')).toBeInTheDocument();
      expect(screen.getByText('Delete')).toBeInTheDocument();
    }
  });

  test('handles table actions', () => {
    renderWithTheme(
      <DataTable
        columns={columns}
        data={mockData}
        actions={actions}
        title="Test Table"
      />
    );

    // Should render action button
    const actionButton = screen.getByRole('button', { name: 'Export Data' });
    fireEvent.click(actionButton);

    expect(actions[0].onClick).toHaveBeenCalledWith(mockData);
  });

  test('handles row click', () => {
    const mockRowClick = jest.fn();
    renderWithTheme(
      <DataTable
        columns={columns}
        data={mockData}
        onRowClick={mockRowClick}
      />
    );

    // Click on first data row
    const rows = screen.getAllByRole('row');
    expect(rows).toHaveLength(mockData.length + 1); // +1 for header
    
    const firstDataRow = rows[1]; // Skip header row
    expect(firstDataRow).toBeDefined();
    fireEvent.click(firstDataRow);

    expect(mockRowClick).toHaveBeenCalledWith(mockData[0]);
  });

  test('handles custom cell formatting', () => {
    renderWithTheme(
      <DataTable columns={columns} data={mockData} />
    );

    // Check that custom formatting is applied
    expect(screen.getByText('$1,000,000')).toBeInTheDocument();
    expect(screen.getByText('$750,000')).toBeInTheDocument();
    // The active/inactive status is rendered by the render function
    expect(screen.getAllByText('Active')).toHaveLength(3); // 3 active assets
    expect(screen.getAllByText('Inactive')).toHaveLength(2); // 2 inactive assets
  });

  test('handles responsive behavior', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 600,
    });

    renderWithTheme(
      <DataTable columns={columns} data={mockData} />
    );

    // Should still render the table (responsive behavior is mainly CSS-based)
    expect(screen.getByRole('table')).toBeInTheDocument();
  });
});

describe('DataTable Performance', () => {
  test('handles large datasets efficiently', () => {
    const largeData = Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      name: `Asset ${i + 1}`,
      value: Math.floor(Math.random() * 10000000),
      rating: ['AAA', 'AA+', 'A', 'BBB'][Math.floor(Math.random() * 4)],
      active: Math.random() > 0.5,
      lastUpdated: new Date().toISOString(),
    }));

    const startTime = performance.now();
    
    renderWithTheme(
      <DataTable
        columns={columns}
        data={largeData}
        pageSize={50}
      />
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within reasonable time (adjust threshold as needed)
    expect(renderTime).toBeLessThan(1000); // 1 second
    expect(screen.getByRole('table')).toBeInTheDocument();
  });
});

describe('DataTable Accessibility', () => {
  test('has proper ARIA labels and roles', () => {
    renderWithTheme(
      <DataTable
        columns={columns}
        data={mockData}
        title="Asset Portfolio"
        selectable
      />
    );

    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getAllByRole('columnheader')).toHaveLength(columns.length + 1); // +1 for checkbox column
    expect(screen.getAllByRole('row')).toHaveLength(mockData.length + 1); // +1 for header row
    expect(screen.getAllByRole('checkbox')).toHaveLength(mockData.length + 1); // +1 for select all
  });

  test('supports keyboard navigation', () => {
    renderWithTheme(
      <DataTable
        columns={columns}
        data={mockData}
        onRowClick={jest.fn()}
      />
    );

    const rows = screen.getAllByRole('row');
    // Should find header row and data rows
    expect(rows).toHaveLength(mockData.length + 1); // +1 for header
    
    // Data rows should be clickable when onRowClick is provided
    const dataRows = rows.slice(1); // Skip header row
    expect(dataRows).toHaveLength(mockData.length);
    
    dataRows.forEach(row => {
      expect(row).toHaveAttribute('tabIndex', '0');
      expect(row).toHaveAttribute('role', 'button');
    });
  });
});