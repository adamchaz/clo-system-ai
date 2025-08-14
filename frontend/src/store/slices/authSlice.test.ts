import authReducer, {
  loginAsync,
  logoutAsync,
  registerAsync,
  refreshTokenAsync,
  clearError,
  setUser,
  AuthState
} from './authSlice';
import { configureStore } from '@reduxjs/toolkit';
import { AuthUser } from '../../types/auth';

// Mock the auth service
jest.mock('../../services/auth', () => ({
  authService: {
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn(),
    refreshToken: jest.fn(),
    getCurrentUser: jest.fn(),
    clearTokens: jest.fn(),
  },
}));

// Get reference to mocked service
const { authService: mockAuthService } = require('../../services/auth');

describe('authSlice', () => {
  const initialState: AuthState = {
    user: null,
    tokens: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  };

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

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should return the initial state', () => {
    expect(authReducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  test('should handle setUser', () => {
    const actual = authReducer(initialState, setUser(mockUser));
    expect(actual.user).toEqual(mockUser);
    expect(actual.isAuthenticated).toBe(true);
  });

  test('should handle clearError', () => {
    const stateWithError = { ...initialState, error: 'Some error' };
    const actual = authReducer(stateWithError, clearError());
    expect(actual.error).toBeNull();
  });

  describe('loginAsync', () => {
    test('should handle pending state', () => {
      const action = { type: loginAsync.pending.type };
      const state = authReducer(initialState, action);
      expect(state.isLoading).toBe(true);
      expect(state.error).toBeNull();
    });

    test('should handle fulfilled state', () => {
      const payload = { user: mockUser, tokens: mockTokens };
      const action = { type: loginAsync.fulfilled.type, payload };
      const state = authReducer(initialState, action);
      
      expect(state.isLoading).toBe(false);
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toEqual(mockUser);
      expect(state.tokens).toEqual(mockTokens);
      expect(state.error).toBeNull();
    });

    test('should handle rejected state', () => {
      const action = { 
        type: loginAsync.rejected.type, 
        payload: 'Login failed' 
      };
      const state = authReducer(initialState, action);
      
      expect(state.isLoading).toBe(false);
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.tokens).toBeNull();
      expect(state.error).toBe('Login failed');
    });
  });

  describe('registerAsync', () => {
    test('should handle pending state', () => {
      const action = { type: registerAsync.pending.type };
      const state = authReducer(initialState, action);
      expect(state.isLoading).toBe(true);
      expect(state.error).toBeNull();
    });

    test('should handle fulfilled state', () => {
      const payload = { user: mockUser, tokens: mockTokens };
      const action = { type: registerAsync.fulfilled.type, payload };
      const state = authReducer(initialState, action);
      
      expect(state.isLoading).toBe(false);
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toEqual(mockUser);
      expect(state.tokens).toEqual(mockTokens);
      expect(state.error).toBeNull();
    });
  });

  describe('logoutAsync', () => {
    test('should handle fulfilled state', () => {
      const authenticatedState = {
        ...initialState,
        user: mockUser,
        tokens: mockTokens,
        isAuthenticated: true,
      };
      
      const action = { type: logoutAsync.fulfilled.type };
      const state = authReducer(authenticatedState, action);
      
      expect(state.isLoading).toBe(false);
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.tokens).toBeNull();
      expect(state.error).toBeNull();
    });
  });

  describe('refreshTokenAsync', () => {
    test('should handle fulfilled state', () => {
      const newTokens = {
        accessToken: 'new-access-token',
        refreshToken: 'new-refresh-token',
      };
      
      const payload = { tokens: newTokens };
      const action = { type: refreshTokenAsync.fulfilled.type, payload };
      const state = authReducer(initialState, action);
      
      expect(state.tokens).toEqual(newTokens);
      expect(state.error).toBeNull();
    });
  });

  describe('async thunks integration', () => {
    let store: any;

    beforeEach(() => {
      store = configureStore({
        reducer: {
          auth: authReducer,
        },
      });
    });

    test('loginAsync should call auth service', async () => {
      const loginData = { email: 'test@example.com', password: 'password123' };
      mockAuthService.login.mockResolvedValue({ user: mockUser, tokens: mockTokens });

      await store.dispatch(loginAsync(loginData));

      expect(mockAuthService.login).toHaveBeenCalledWith(loginData);
    });

    test('registerAsync should call auth service', async () => {
      const registerData = { 
        email: 'test@example.com', 
        password: 'password123',
        firstName: 'Test',
        lastName: 'User',
        roles: ['portfolio_manager'] 
      };
      mockAuthService.register.mockResolvedValue({ user: mockUser, tokens: mockTokens });

      await store.dispatch(registerAsync(registerData));

      expect(mockAuthService.register).toHaveBeenCalledWith(registerData);
    });

    test('logoutAsync should call auth service', async () => {
      mockAuthService.logout.mockResolvedValue({});

      await store.dispatch(logoutAsync());

      expect(mockAuthService.logout).toHaveBeenCalled();
    });

    test('refreshTokenAsync should call auth service', async () => {
      const newTokens = {
        accessToken: 'new-access-token',
        refreshToken: 'new-refresh-token',
      };
      mockAuthService.refreshToken.mockResolvedValue({ tokens: newTokens });

      await store.dispatch(refreshTokenAsync());

      expect(mockAuthService.refreshToken).toHaveBeenCalled();
    });
  });
});