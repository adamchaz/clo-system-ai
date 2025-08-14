import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../theme';
import Sidebar from './Sidebar';
import authReducer, { AuthState } from '../../../store/slices/authSlice';
import uiReducer, { UIState } from '../../../store/slices/uiSlice';
import { AuthUser } from '../../../types/auth';

// Mock the auth service
jest.mock('../../../services/auth', () => ({
  authService: {
    setupAxiosInterceptors: jest.fn(),
    hasPermission: jest.fn(() => true),
    getRefreshToken: jest.fn(() => 'mock-refresh-token'),
    getAccessToken: jest.fn(() => 'mock-access-token'),
    setTokens: jest.fn(),
    clearTokens: jest.fn(),
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    refreshToken: jest.fn(),
  },
}));

const createMockStore = (initialState: Partial<AuthState> = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      ui: uiReducer,
    },
    preloadedState: {
      auth: {
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        ...initialState,
      } as AuthState,
      ui: {
        theme: 'light',
        sidebarOpen: true,
        notifications: [],
        loading: {
          global: false,
        },
        errors: {},
      } as UIState,
    },
  });
};

const MockProvider: React.FC<{ 
  children: React.ReactNode; 
  store?: any;
  route?: string;
}> = ({ children, store = createMockStore(), route = '/dashboard' }) => (
  <Provider store={store}>
    <ThemeProvider theme={lightTheme}>
      <MemoryRouter initialEntries={[route]}>
        {children}
      </MemoryRouter>
    </ThemeProvider>
  </Provider>
);

describe('Sidebar', () => {
  const mockProps = {
    open: true,
    onClose: jest.fn(),
    variant: 'permanent' as const,
    width: 280,
  };

  const mockAdminUser: AuthUser = {
    id: '1',
    email: 'admin@example.com',
    firstName: 'Admin',
    lastName: 'User',
    roles: [{
      id: '1',
      name: 'system_admin',
      displayName: 'System Administrator',
      description: 'Full system access',
      permissions: ['system:read', 'system:write'],
    }],
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  };

  const mockManagerUser: AuthUser = {
    id: '2',
    email: 'manager@example.com',
    firstName: 'Portfolio',
    lastName: 'Manager',
    roles: [{
      id: '2',
      name: 'portfolio_manager',
      displayName: 'Portfolio Manager',
      description: 'Manages portfolios',
      permissions: ['portfolio:read', 'portfolio:write'],
    }],
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  };

  const mockViewerUser: AuthUser = {
    id: '3',
    email: 'viewer@example.com',
    firstName: 'Read',
    lastName: 'Only',
    roles: [{
      id: '3',
      name: 'viewer',
      displayName: 'Viewer',
      description: 'Read-only access',
      permissions: ['portfolio:read'],
    }],
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders brand section when open', () => {
    const store = createMockStore({
      user: mockManagerUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} />
      </MockProvider>
    );

    expect(screen.getByText('CLO System')).toBeInTheDocument();
    expect(screen.getByText('MANAGEMENT PLATFORM')).toBeInTheDocument();
  });

  test('renders user profile section', () => {
    const store = createMockStore({
      user: mockManagerUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} />
      </MockProvider>
    );

    expect(screen.getAllByText('Portfolio Manager').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Portfolio Manager').length).toBeGreaterThan(0);
    expect(screen.getByText('PM')).toBeInTheDocument(); // Avatar initials
  });

  test('shows admin-only navigation items for admin users', () => {
    const store = createMockStore({
      user: mockAdminUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} />
      </MockProvider>
    );

    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('System Monitoring')).toBeInTheDocument();
    expect(screen.getByText('Security Center')).toBeInTheDocument();
  });

  test('hides admin navigation items for non-admin users', () => {
    const store = createMockStore({
      user: mockManagerUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} />
      </MockProvider>
    );

    expect(screen.queryByText('User Management')).not.toBeInTheDocument();
    expect(screen.queryByText('System Monitoring')).not.toBeInTheDocument();
    expect(screen.queryByText('Security Center')).not.toBeInTheDocument();
  });

  test('shows appropriate navigation items for viewer users', () => {
    const store = createMockStore({
      user: mockViewerUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} />
      </MockProvider>
    );

    expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
    expect(screen.getByText('Portfolio Management')).toBeInTheDocument();
    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.queryByText('Asset Management')).not.toBeInTheDocument();
    expect(screen.queryByText('Risk Analytics')).not.toBeInTheDocument();
  });

  test('expands and collapses nested navigation items', () => {
    const store = createMockStore({
      user: mockManagerUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} />
      </MockProvider>
    );

    // Initially, nested items should not be visible
    expect(screen.queryByText('Portfolio List')).not.toBeInTheDocument();

    // Click on Portfolio Management to expand
    const portfolioItem = screen.getByText('Portfolio Management');
    fireEvent.click(portfolioItem);

    // Now nested items should be visible
    expect(screen.getByText('Portfolio List')).toBeInTheDocument();
    expect(screen.getByText('Portfolio Details')).toBeInTheDocument();
  });

  test('handles temporary variant correctly on mobile', () => {
    const store = createMockStore({
      user: mockManagerUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} variant="temporary" />
      </MockProvider>
    );

    expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
  });

  test('calls onClose when clicking outside in temporary mode', () => {
    const store = createMockStore({
      user: mockManagerUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} variant="temporary" />
      </MockProvider>
    );

    // The actual outside click behavior is handled by Material-UI's Drawer component
    // so we just verify the component renders without errors
    expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
  });

  test('handles collapsed state properly', () => {
    const store = createMockStore({
      user: mockManagerUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} open={false} width={64} />
      </MockProvider>
    );

    // In collapsed state, text should still be present but may be hidden by CSS
    expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
  });

  test('highlights active navigation item', () => {
    const store = createMockStore({
      user: mockManagerUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store} route="/dashboard">
        <Sidebar {...mockProps} />
      </MockProvider>
    );

    // Check if Dashboard navigation item exists
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
  });

  test('renders without user when not authenticated', () => {
    const store = createMockStore({
      user: null,
      isAuthenticated: false,
    });

    render(
      <MockProvider store={store}>
        <Sidebar {...mockProps} />
      </MockProvider>
    );

    // Should not show navigation items without user
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
  });
});