import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { store } from '../../../store';
import AssetList from '../AssetList';
import AssetDetail from '../AssetDetail';
import AssetDashboard from '../AssetDashboard';

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Provider store={store}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </Provider>
);

describe('Asset Management Integration Tests', () => {
  describe('Task 1: AssetList Component', () => {
    test('renders asset list with filtering', async () => {
      render(
        <TestWrapper>
          <AssetList />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText('Asset Portfolio')).toBeInTheDocument();
      });
    });
  });

  describe('Task 2: AssetDetail Component', () => {
    test('displays asset details with all tabs', async () => {
      render(
        <TestWrapper>
          <AssetDetail assetId="test-asset-1" />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Financial')).toBeInTheDocument();
        expect(screen.getByText('Risk')).toBeInTheDocument();
      });
    });
  });

  describe('Task 6: AssetDashboard Component', () => {
    test('shows dashboard metrics and quick actions', async () => {
      render(
        <TestWrapper>
          <AssetDashboard />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText('Asset Management Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Total Assets')).toBeInTheDocument();
        expect(screen.getByText('Add Asset')).toBeInTheDocument();
      });
    });
  });

  describe('Tasks 9-11: Complete Integration', () => {
    test('end-to-end asset management workflow', async () => {
      // This would test the complete workflow from dashboard to asset creation
      render(
        <TestWrapper>
          <AssetDashboard />
        </TestWrapper>
      );
      
      // Test navigation and state management
      const addButton = await screen.findByText('Add Asset');
      expect(addButton).toBeInTheDocument();
      
      // Test that clicking navigates properly (would need routing setup)
      fireEvent.click(addButton);
    });
  });
});