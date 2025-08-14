import { useCallback, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from './reduxHooks';
import { 
  loginAsync, 
  logoutAsync, 
  registerAsync,
  refreshTokenAsync,
  clearError,
  setUser
} from '../store/slices/authSlice';
import { LoginCredentials, RegisterData, UserRoleType } from '../types/auth';
import { authService } from '../services/auth';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const { user, tokens, isAuthenticated, isLoading, error } = useAppSelector(
    (state) => state.auth
  );

  // Initialize auth service interceptors
  useEffect(() => {
    authService.setupAxiosInterceptors();
  }, []);

  // Auto-refresh token on app load if refresh token exists
  useEffect(() => {
    const initializeAuth = async () => {
      const refreshToken = authService.getRefreshToken();
      if (refreshToken && !isAuthenticated) {
        try {
          await dispatch(refreshTokenAsync()).unwrap();
          // Get current user after token refresh
          const currentUser = await authService.getCurrentUser();
          if (currentUser) {
            dispatch(setUser(currentUser));
          }
        } catch (error) {
          console.error('Token refresh failed:', error);
          // Clear invalid tokens
          authService.clearTokens();
        }
      }
    };

    initializeAuth();
  }, [dispatch, isAuthenticated]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      const result = await dispatch(loginAsync(credentials)).unwrap();
      return result;
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  const register = useCallback(async (userData: RegisterData) => {
    try {
      const result = await dispatch(registerAsync(userData)).unwrap();
      return result;
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  const logout = useCallback(async () => {
    try {
      await dispatch(logoutAsync()).unwrap();
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails on server, clear local tokens
      authService.clearTokens();
    }
  }, [dispatch]);

  const refreshToken = useCallback(async () => {
    try {
      await dispatch(refreshTokenAsync()).unwrap();
    } catch (error) {
      throw error;
    }
  }, [dispatch]);

  const clearAuthError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  // Permission checking utilities
  const hasRole = useCallback((requiredRole: UserRoleType) => {
    if (!user) return false;
    const userRoles = user.roles.map(role => role.name as UserRoleType);
    return userRoles.includes(requiredRole);
  }, [user]);

  const hasAnyRole = useCallback((requiredRoles: UserRoleType[]) => {
    if (!user) return false;
    const userRoles = user.roles.map(role => role.name as UserRoleType);
    return requiredRoles.some(role => userRoles.includes(role));
  }, [user]);

  const hasPermission = useCallback((permission: string) => {
    if (!user) return false;
    const userRoles = user.roles.map(role => role.name);
    return authService.hasPermission(userRoles, permission);
  }, [user]);

  // Convenience role checks
  const isAdmin = useCallback(() => hasRole('system_admin'), [hasRole]);
  const isManager = useCallback(() => hasRole('portfolio_manager'), [hasRole]);
  const isAnalyst = useCallback(() => hasRole('financial_analyst'), [hasRole]);
  const isViewer = useCallback(() => hasRole('viewer'), [hasRole]);

  // Check if user has elevated privileges (manager or admin)
  const hasElevatedAccess = useCallback(() => 
    hasAnyRole(['portfolio_manager', 'system_admin']), 
    [hasAnyRole]
  );

  // Check if user can write/modify data
  const canWrite = useCallback(() => 
    hasAnyRole(['financial_analyst', 'portfolio_manager', 'system_admin']), 
    [hasAnyRole]
  );

  // Get user's display name
  const getDisplayName = useCallback(() => {
    if (!user) return '';
    return `${user.firstName} ${user.lastName}`;
  }, [user]);

  // Get user's primary role for display
  const getPrimaryRole = useCallback(() => {
    if (!user || user.roles.length === 0) return '';
    return user.roles[0].displayName || user.roles[0].name;
  }, [user]);

  // Get user's initials for avatar
  const getUserInitials = useCallback(() => {
    if (!user) return '';
    return `${user.firstName.charAt(0)}${user.lastName.charAt(0)}`.toUpperCase();
  }, [user]);

  return {
    // State
    user,
    tokens,
    isAuthenticated,
    isLoading,
    error,

    // Actions
    login,
    register,
    logout,
    refreshToken,
    clearAuthError,

    // Permission checks
    hasRole,
    hasAnyRole,
    hasPermission,
    isAdmin,
    isManager,
    isAnalyst,
    isViewer,
    hasElevatedAccess,
    canWrite,

    // Utilities
    getDisplayName,
    getPrimaryRole,
    getUserInitials,
  };
};