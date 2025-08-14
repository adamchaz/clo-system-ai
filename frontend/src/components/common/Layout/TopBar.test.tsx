import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { ThemeProvider } from '@mui/material/styles';
import { lightTheme } from '../../../theme';
import TopBar from './TopBar';
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

describe('TopBar', () => {
  const mockProps = {
    onMenuClick: jest.fn(),
    sidebarOpen: true,
  };

  const mockUser: AuthUser = {
    id: '1',
    email: 'test@example.com',
    firstName: 'John',
    lastName: 'Doe',
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

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders basic topbar elements', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <TopBar {...mockProps} />
      </MockProvider>
    );

    expect(screen.getByText('CLO Management System')).toBeInTheDocument();
    expect(screen.getByLabelText('open drawer')).toBeInTheDocument();
    expect(screen.getByLabelText('Notifications')).toBeInTheDocument();
    expect(screen.getByLabelText('Account settings')).toBeInTheDocument();
  });

  test('displays user information when authenticated', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <TopBar {...mockProps} />
      </MockProvider>
    );

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Portfolio Manager')).toBeInTheDocument();
    expect(screen.getByText('JD')).toBeInTheDocument(); // Avatar initials
  });

  test('calls onMenuClick when menu button is clicked', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <TopBar {...mockProps} />
      </MockProvider>
    );

    const menuButton = screen.getByLabelText('open drawer');
    fireEvent.click(menuButton);

    expect(mockProps.onMenuClick).toHaveBeenCalledTimes(1);
  });

  test('opens profile menu when user avatar is clicked', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <TopBar {...mockProps} />
      </MockProvider>
    );

    const avatarButton = screen.getByLabelText('Account settings');
    fireEvent.click(avatarButton);

    // Check if profile menu items appear
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  test('opens notification menu when notification icon is clicked', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <TopBar {...mockProps} />
      </MockProvider>
    );

    const notificationButton = screen.getByLabelText('Notifications');
    fireEvent.click(notificationButton);

    expect(screen.getByText('Notifications')).toBeInTheDocument();
  });

  test('displays breadcrumbs for nested routes', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store} route="/portfolios/list">
        <TopBar {...mockProps} />
      </MockProvider>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  test('shows theme toggle button', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <TopBar {...mockProps} />
      </MockProvider>
    );

    const themeButton = screen.getByTitle('Toggle theme');
    expect(themeButton).toBeInTheDocument();
  });

  test('adapts layout for mobile screens', () => {
    // Mock window.matchMedia for mobile breakpoint
    const mockMatchMedia = jest.fn();
    mockMatchMedia.mockReturnValue({
      matches: true,
      addListener: jest.fn(),
      removeListener: jest.fn(),
    });
    window.matchMedia = mockMatchMedia;

    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <MockProvider store={store}>
        <TopBar {...mockProps} />
      </MockProvider>
    );

    expect(screen.getByText('CLO System')).toBeInTheDocument();
  });

  test('handles sidebar open/closed state correctly', () => {
    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    const { rerender } = render(
      <MockProvider store={store}>
        <TopBar {...mockProps} sidebarOpen={true} />
      </MockProvider>
    );

    expect(screen.getByLabelText('open drawer')).toBeInTheDocument();

    rerender(
      <MockProvider store={store}>
        <TopBar {...mockProps} sidebarOpen={false} />
      </MockProvider>
    );

    expect(screen.getByLabelText('open drawer')).toBeInTheDocument();
  });
});