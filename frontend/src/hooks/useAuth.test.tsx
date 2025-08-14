import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { useAuth } from './useAuth';
import authReducer, { AuthState } from '../store/slices/authSlice';
import { AuthUser, UserRole } from '../types/auth';

// Mock the auth service
jest.mock('../services/auth', () => ({
  authService: {
    setupAxiosInterceptors: jest.fn(),
    getRefreshToken: jest.fn(() => null),
    clearTokens: jest.fn(),
    hasPermission: jest.fn((roles: string[], permission: string) => {
      const rolePermissions: Record<string, string[]> = {
        'system_admin': ['system:read', 'system:write', 'user:read', 'portfolio:write'],
        'portfolio_manager': ['portfolio:read', 'portfolio:write'],
        'financial_analyst': ['portfolio:read', 'analytics:read'],
        'viewer': ['portfolio:read'],
      };
      return roles.some(role => rolePermissions[role]?.includes(permission));
    }),
  },
}));

// Get reference to the mocked auth service after the mock
const { authService: mockAuthService } = require('../services/auth');

const createMockStore = (initialState: Partial<AuthState> = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
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
    },
  });
};

const wrapper = (store: any) => ({ children }: { children: React.ReactNode }) => (
  <Provider store={store}>{children}</Provider>
);

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('returns initial auth state', () => {
    const store = createMockStore();
    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) });

    expect(result.current.user).toBeNull();
    expect(result.current.tokens).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test('returns authenticated state when user is logged in', () => {
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

    const mockTokens = {
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
    };

    const store = createMockStore({
      user: mockUser,
      tokens: mockTokens,
      isAuthenticated: true,
    });

    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.tokens).toEqual(mockTokens);
    expect(result.current.isAuthenticated).toBe(true);
  });

  test('role checking functions work correctly', () => {
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

    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) });

    expect(result.current.hasRole('portfolio_manager')).toBe(true);
    expect(result.current.hasRole('system_admin')).toBe(false);
    expect(result.current.isManager()).toBe(true);
    expect(result.current.isAdmin()).toBe(false);
    expect(result.current.hasElevatedAccess()).toBe(true);
    expect(result.current.canWrite()).toBe(true);
  });

  test('permission checking works correctly', () => {
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

    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    // Mock the permission checking with specific return values
    mockAuthService.hasPermission
      .mockReturnValueOnce(true)  // portfolio:write should return true
      .mockReturnValueOnce(false); // system:write should return false

    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) });

    // Test permission checking
    const hasPortfolioWrite = result.current.hasPermission('portfolio:write');
    const hasSystemWrite = result.current.hasPermission('system:write');
    
    // Verify the mock was called with correct arguments
    expect(mockAuthService.hasPermission).toHaveBeenCalledWith(['portfolio_manager'], 'portfolio:write');
    expect(mockAuthService.hasPermission).toHaveBeenCalledWith(['portfolio_manager'], 'system:write');
    
    // Test the permission results
    expect(typeof result.current.hasPermission).toBe('function');
    expect(hasPortfolioWrite).toBe(true);
    expect(hasSystemWrite).toBe(false);
  });

  test('utility functions work correctly', () => {
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

    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) });

    expect(result.current.getDisplayName()).toBe('John Doe');
    expect(result.current.getPrimaryRole()).toBe('Portfolio Manager');
    expect(result.current.getUserInitials()).toBe('JD');
  });

  test('returns empty values when user is not authenticated', () => {
    const store = createMockStore();
    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) });

    expect(result.current.hasRole('portfolio_manager')).toBe(false);
    expect(result.current.hasPermission('portfolio:read')).toBe(false);
    expect(result.current.getDisplayName()).toBe('');
    expect(result.current.getPrimaryRole()).toBe('');
    expect(result.current.getUserInitials()).toBe('');
  });

  test('handles multiple roles correctly', () => {
    const mockUser: AuthUser = {
      id: '1',
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      roles: [
        {
          id: '1',
          name: 'financial_analyst',
          displayName: 'Financial Analyst',
          description: 'Analyzes finances',
          permissions: ['portfolio:read', 'analytics:read'],
        },
        {
          id: '2',
          name: 'portfolio_manager',
          displayName: 'Portfolio Manager',
          description: 'Manages portfolios',
          permissions: ['portfolio:read', 'portfolio:write'],
        },
      ],
      isActive: true,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    };

    const store = createMockStore({
      user: mockUser,
      isAuthenticated: true,
    });

    const { result } = renderHook(() => useAuth(), { wrapper: wrapper(store) });

    expect(result.current.hasAnyRole(['financial_analyst', 'viewer'])).toBe(true);
    expect(result.current.hasAnyRole(['system_admin', 'viewer'])).toBe(false);
    expect(result.current.getPrimaryRole()).toBe('Financial Analyst'); // Returns first role
  });
});