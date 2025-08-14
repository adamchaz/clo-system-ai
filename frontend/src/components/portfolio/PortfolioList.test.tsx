import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import PortfolioList from './PortfolioList';
import { cloApi } from '../../store/api/cloApi';
import authReducer from '../../store/slices/authSlice';
import uiReducer from '../../store/slices/uiSlice';

// Mock portfolio data
const mockPortfolios = [
  {
    id: 'portfolio-1',
    deal_name: 'MAG CLO XIV-R',
    manager: 'Magnetar Capital',
    trustee: 'Wells Fargo',
    effective_date: '2023-01-15',
    stated_maturity: '2030-01-15',
    deal_size: 850000000,
    currency: 'USD',
    status: 'effective' as const,
    current_asset_count: 127,
    current_portfolio_balance: 823000000,
    days_to_maturity: 2190,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-08-01T00:00:00Z',
  },
  {
    id: 'portfolio-2',
    deal_name: 'MAG CLO XV',
    manager: 'Magnetar Capital',
    trustee: 'Wells Fargo',
    effective_date: '2023-06-15',
    stated_maturity: '2030-06-15',
    deal_size: 650000000,
    currency: 'USD',
    status: 'pending' as const,
    current_asset_count: 94,
    current_portfolio_balance: 642000000,
    days_to_maturity: 2372,
    created_at: '2023-06-01T00:00:00Z',
    updated_at: '2023-08-01T00:00:00Z',
  },
];

// Create test store
const createTestStore = () => {
  return configureStore({
    reducer: {
      [cloApi.reducerPath]: cloApi.reducer,
      auth: authReducer,
      ui: uiReducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(cloApi.middleware),
  });
};

describe('PortfolioList', () => {
  let store: ReturnType<typeof createTestStore>;
  const mockCallbacks = {
    onPortfolioSelect: jest.fn(),
    onPortfolioEdit: jest.fn(),
    onPortfolioCreate: jest.fn(),
    onPortfolioView: jest.fn(),
  };

  beforeEach(() => {
    store = createTestStore();
    store.dispatch(
      cloApi.util.upsertQueryData('getPortfolios', undefined, {
        data: mockPortfolios,
        success: true,
      })
    );
    jest.clearAllMocks();
  });

  const renderWithProvider = (props = {}) => {
    return render(
      <Provider store={store}>
        <PortfolioList {...mockCallbacks} {...props} />
      </Provider>
    );
  };

  test('renders portfolio list header', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      expect(screen.getByText('Portfolio Management')).toBeInTheDocument();
      expect(screen.getByText('Manage and monitor your CLO portfolios')).toBeInTheDocument();
    });
  });

  test('displays create portfolio button', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      const createButton = screen.getByRole('button', { name: /create portfolio/i });
      expect(createButton).toBeInTheDocument();
      
      fireEvent.click(createButton);
      expect(mockCallbacks.onPortfolioCreate).toHaveBeenCalled();
    });
  });

  test('renders portfolio table with correct headers', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      expect(screen.getByText('Portfolio Name')).toBeInTheDocument();
      expect(screen.getByText('Manager')).toBeInTheDocument();
      expect(screen.getByText('Deal Size')).toBeInTheDocument();
      expect(screen.getByText('Current NAV')).toBeInTheDocument();
      expect(screen.getByText('Performance')).toBeInTheDocument();
      expect(screen.getByText('Assets')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Maturity')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });
  });

  test('displays portfolio data correctly', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      expect(screen.getByText('MAG CLO XIV-R')).toBeInTheDocument();
      expect(screen.getByText('MAG CLO XV')).toBeInTheDocument();
      expect(screen.getByText('Magnetar Capital')).toBeInTheDocument();
      expect(screen.getByText('$850.0M')).toBeInTheDocument();
      expect(screen.getByText('$650.0M')).toBeInTheDocument();
    });
  });

  test('shows correct status chips', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });
  });

  test('calculates performance correctly', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      // Performance = ((current_balance / deal_size) - 1) * 100
      // For portfolio-1: ((823000000 / 850000000) - 1) * 100 = -3.18%
      // For portfolio-2: ((642000000 / 650000000) - 1) * 100 = -1.23%
      expect(screen.getByText('-3.18%')).toBeInTheDocument();
      expect(screen.getByText('-1.23%')).toBeInTheDocument();
    });
  });

  test('search functionality works', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText('Search portfolios...');
      fireEvent.change(searchInput, { target: { value: 'XIV' } });
      
      // Should show MAG CLO XIV-R but not MAG CLO XV
      expect(screen.getByText('MAG CLO XIV-R')).toBeInTheDocument();
      expect(screen.queryByText('MAG CLO XV')).not.toBeInTheDocument();
    });
  });

  test('status filter works', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      const statusSelect = screen.getByDisplayValue('All Status');
      fireEvent.mouseDown(statusSelect);
      
      const activeOption = screen.getByText('Active');
      fireEvent.click(activeOption);
      
      // Should only show active (effective) portfolios
      expect(screen.getByText('MAG CLO XIV-R')).toBeInTheDocument();
      expect(screen.queryByText('MAG CLO XV')).not.toBeInTheDocument();
    });
  });

  test('manager filter works', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      const managerSelect = screen.getByDisplayValue('All Managers');
      fireEvent.mouseDown(managerSelect);
      
      const magnetarOption = screen.getByText('Magnetar Capital');
      fireEvent.click(magnetarOption);
      
      // Both portfolios should still be visible as both have same manager
      expect(screen.getByText('MAG CLO XIV-R')).toBeInTheDocument();
      expect(screen.getByText('MAG CLO XV')).toBeInTheDocument();
    });
  });

  test('sorting functionality works', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      const dealSizeHeader = screen.getByText('Deal Size');
      fireEvent.click(dealSizeHeader);
      
      // After sorting by deal size ascending, MAG CLO XV ($650M) should come first
      const rows = screen.getAllByRole('row');
      expect(rows[2]).toHaveTextContent('MAG CLO XV'); // Index 2 because header is row 0, and there might be other rows
    });
  });

  test('displays summary stats', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      expect(screen.getByText('Total Portfolios')).toBeInTheDocument();
      expect(screen.getByText('Total AUM')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Total Assets')).toBeInTheDocument();
      
      // Should show 2 total portfolios
      expect(screen.getByText('2')).toBeInTheDocument();
      
      // Should show 1 active portfolio (only one has status 'effective')
      expect(screen.getByText('1')).toBeInTheDocument();
      
      // Total assets should be 127 + 94 = 221
      expect(screen.getByText('221')).toBeInTheDocument();
    });
  });

  test('pagination works', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      // Should show pagination controls
      expect(screen.getByText('Rows per page:')).toBeInTheDocument();
      expect(screen.getByText('1–2 of 2')).toBeInTheDocument();
    });
  });

  test('handles portfolio row click', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      const portfolioRow = screen.getByText('MAG CLO XIV-R').closest('tr');
      fireEvent.click(portfolioRow!);
      
      expect(mockCallbacks.onPortfolioSelect).toHaveBeenCalledWith(mockPortfolios[0]);
    });
  });

  test('displays action buttons', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      const viewButtons = screen.getAllByRole('button', { name: /view details/i });
      expect(viewButtons).toHaveLength(2);
      
      fireEvent.click(viewButtons[0]);
      expect(mockCallbacks.onPortfolioView).toHaveBeenCalledWith(mockPortfolios[0]);
    });
  });

  test('opens context menu on more actions click', async () => {
    renderWithProvider();
    
    await waitFor(() => {
      const moreButtons = screen.getAllByRole('button', { name: /more actions/i });
      fireEvent.click(moreButtons[0]);
      
      expect(screen.getByText('View Details')).toBeInTheDocument();
      expect(screen.getByText('Edit Portfolio')).toBeInTheDocument();
      expect(screen.getByText('Risk Analysis')).toBeInTheDocument();
      expect(screen.getByText('Export Data')).toBeInTheDocument();
      expect(screen.getByText('Delete')).toBeInTheDocument();
    });
  });

  test('handles loading state', () => {
    const storeWithoutData = createTestStore();
    
    render(
      <Provider store={storeWithoutData}>
        <PortfolioList {...mockCallbacks} />
      </Provider>
    );
    
    expect(screen.getByText('Loading portfolios...')).toBeInTheDocument();
  });

  test('displays empty state when no portfolios', () => {
    const emptyStore = createTestStore();
    emptyStore.dispatch(
      cloApi.util.upsertQueryData('getPortfolios', undefined, {
        data: [],
        success: true,
      })
    );
    
    render(
      <Provider store={emptyStore}>
        <PortfolioList {...mockCallbacks} />
      </Provider>
    );
    
    expect(screen.getByText('No portfolios found')).toBeInTheDocument();
    expect(screen.getByText('Create your first portfolio to get started')).toBeInTheDocument();
  });
});