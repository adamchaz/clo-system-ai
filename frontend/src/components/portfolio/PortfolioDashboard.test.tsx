import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import PortfolioDashboard from './PortfolioDashboard';
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
    status: 'effective' as const,
    current_asset_count: 94,
    current_portfolio_balance: 642000000,
    days_to_maturity: 2372,
    created_at: '2023-06-01T00:00:00Z',
    updated_at: '2023-08-01T00:00:00Z',
  }
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

// Mock API responses
const mockApiState = {
  queries: {
    'getPortfolios(undefined)': {
      status: 'fulfilled',
      endpointName: 'getPortfolios',
      requestId: 'test-request-id',
      data: {
        data: mockPortfolios,
        success: true,
      },
    },
  },
};

describe('PortfolioDashboard', () => {
  let store: ReturnType<typeof createTestStore>;

  beforeEach(() => {
    store = createTestStore();
    // Pre-populate the store with mock data
    store.dispatch(
      cloApi.util.upsertQueryData('getPortfolios', undefined, {
        data: mockPortfolios,
        success: true,
      })
    );
  });

  const renderWithProvider = (component: React.ReactElement) => {
    return render(
      <Provider store={store}>
        {component}
      </Provider>
    );
  };

  test('renders portfolio dashboard header', () => {
    renderWithProvider(<PortfolioDashboard />);
    
    expect(screen.getByText('Portfolio Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Real-time portfolio metrics, performance tracking, and risk monitoring.')).toBeInTheDocument();
  });

  test('displays key metrics cards', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Total AUM')).toBeInTheDocument();
      expect(screen.getByText('Active Portfolios')).toBeInTheDocument();
      expect(screen.getByText('Avg Return')).toBeInTheDocument();
      expect(screen.getByText('Risk Score')).toBeInTheDocument();
    });
  });

  test('calculates and displays correct total AUM', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      // Total AUM should be (850M + 650M) / 1000000 = 1.5B (displayed as 1.5M in millions)
      const totalAUM = (850000000 + 650000000) / 1000000; // 1500
      expect(screen.getByText(`$${totalAUM.toFixed(1)}M`)).toBeInTheDocument();
    });
  });

  test('displays active portfolios count', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      // Both portfolios have status 'effective' so should show 2 active portfolios
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  test('renders tab navigation', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Performance' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Risk Monitoring' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Activity Feed' })).toBeInTheDocument();
    });
  });

  test('switches tabs correctly', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      const performanceTab = screen.getByRole('tab', { name: 'Performance' });
      fireEvent.click(performanceTab);
      
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Portfolio returns, risk metrics, and benchmark comparisons')).toBeInTheDocument();
    });
  });

  test('displays top performing assets in Overview tab', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Top Performing Assets')).toBeInTheDocument();
      expect(screen.getByText('Acme Corp Term Loan')).toBeInTheDocument();
      expect(screen.getByText('Global Industries Bond')).toBeInTheDocument();
    });
  });

  test('shows risk alerts in Risk Monitoring tab', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      const riskTab = screen.getByRole('tab', { name: 'Risk Monitoring' });
      fireEvent.click(riskTab);
      
      expect(screen.getByText('Risk Alerts & Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Concentration Risk')).toBeInTheDocument();
      expect(screen.getByText('Technology sector exposure at 32% (limit: 30%)')).toBeInTheDocument();
    });
  });

  test('displays recent activity in Activity Feed tab', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      const activityTab = screen.getByRole('tab', { name: 'Activity Feed' });
      fireEvent.click(activityTab);
      
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getByText('Asset purchase: Senior Secured Loan')).toBeInTheDocument();
      expect(screen.getByText('OC Trigger: Class A - Passed')).toBeInTheDocument();
    });
  });

  test('handles refresh button click', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);
      
      // Should trigger a refetch - we can't easily test the API call, 
      // but we can verify the button exists and is clickable
      expect(refreshButton).toBeInTheDocument();
    });
  });

  test('displays performance summary in Performance tab', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      const performanceTab = screen.getByRole('tab', { name: 'Performance' });
      fireEvent.click(performanceTab);
      
      expect(screen.getByText('Performance Summary')).toBeInTheDocument();
      expect(screen.getByText('1 Month Return')).toBeInTheDocument();
      expect(screen.getByText('3 Month Return')).toBeInTheDocument();
      expect(screen.getByText('YTD Return')).toBeInTheDocument();
      expect(screen.getByText('Volatility')).toBeInTheDocument();
    });
  });

  test('handles loading state', () => {
    const storeWithoutData = createTestStore();
    
    render(
      <Provider store={storeWithoutData}>
        <PortfolioDashboard />
      </Provider>
    );
    
    expect(screen.getByText('Loading portfolio dashboard...')).toBeInTheDocument();
  });

  test('displays export and filter buttons', async () => {
    renderWithProvider(<PortfolioDashboard />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /filter/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
    });
  });
});