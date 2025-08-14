import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../theme';
import AppLayout from './AppLayout';
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
}> = ({ children, store = createMockStore() }) => (
  <Provider store={store}>
    <ThemeProvider theme={lightTheme}>
      <MemoryRouter>
        {children}
      </MemoryRouter>
    </ThemeProvider>
  </Provider>
);

describe('AppLayout', () => {
  const mockUser: AuthUser = {
    id: '1',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    roles: [{
      id: '1',
      name: 'portfolio_manager',
      displayName: 'Portfolio Manager',
      description: 'Manages portfolios',
      permissions: ['portfolio:read', 'portfolio:write'],
    }],
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  };

  test('renders children without layout when not authenticated', () => {
    const store = createMockStore({
      isAuthenticated: false,
    });

    render(
      <MockProvider store={store}>
        <AppLayout>
          <div data-testid="test-content">Unauthenticated Content</div>
        </AppLayout>
      </MockProvider>
    );
    
    expect(screen.getByTestId('test-content')).toBeInTheDocument();
    expect(screen.queryByText('CLO System')).not.toBeInTheDocument();
  });

  test('renders full layout when authenticated', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <AppLayout>
          <div data-testid="test-content">Authenticated Content</div>
        </AppLayout>
      </MockProvider>
    );
    
    expect(screen.getByTestId('test-content')).toBeInTheDocument();
    expect(screen.getByText('CLO Management System')).toBeInTheDocument();
    expect(screen.getByText('CLO System')).toBeInTheDocument(); // From sidebar
  });

  test('renders children content in main area when authenticated', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <AppLayout>
          <div data-testid="main-content">Main Page Content</div>
        </AppLayout>
      </MockProvider>
    );
    
    expect(screen.getByTestId('main-content')).toBeInTheDocument();
  });
});