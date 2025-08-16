import axios from 'axios';
import { AuthUser, LoginCredentials, RegisterData, AuthTokens } from '../types/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

export class AuthService {
  private static instance: AuthService;
  private baseURL: string;

  private constructor() {
    this.baseURL = `${API_BASE_URL}/api/v1/auth`;
  }

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  // Login user and return tokens
  async login(credentials: LoginCredentials): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    try {
      // Convert to FormData as expected by backend
      const formData = new FormData();
      formData.append('username', credentials.email);
      formData.append('password', credentials.password);
      
      const response = await axios.post(`${this.baseURL}/token`, formData);
      const { user: backendUser, access_token, refresh_token, token_type } = response.data;
      
      // Transform backend user to frontend AuthUser format
      const user: AuthUser = {
        id: backendUser.id,
        email: backendUser.email,
        firstName: backendUser.full_name.split(' ')[0] || '',
        lastName: backendUser.full_name.split(' ').slice(1).join(' ') || '',
        roles: [{ 
          id: backendUser.role, 
          name: backendUser.role, 
          displayName: backendUser.role, 
          description: '', 
          permissions: [] 
        }],
        isActive: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      const tokens = { accessToken: access_token, refreshToken: refresh_token };
      
      // Store tokens in localStorage
      this.setTokens(tokens);
      
      return { user, tokens };
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  }

  // Register new user
  async register(userData: RegisterData): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    try {
      const response = await axios.post(`${this.baseURL}/register`, userData);
      const { user, access_token, refresh_token } = response.data;
      
      const tokens = { accessToken: access_token, refreshToken: refresh_token };
      
      // Store tokens in localStorage
      this.setTokens(tokens);
      
      return { user, tokens };
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  }

  // Refresh access token
  async refreshToken(): Promise<AuthTokens | null> {
    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post(`${this.baseURL}/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token: new_refresh_token } = response.data;
      const tokens = { 
        accessToken: access_token, 
        refreshToken: new_refresh_token || refreshToken 
      };
      
      this.setTokens(tokens);
      return tokens;
    } catch (error) {
      // If refresh fails, clear tokens and redirect to login
      this.clearTokens();
      return null;
    }
  }

  // Get current user profile
  async getCurrentUser(): Promise<AuthUser | null> {
    try {
      const token = this.getAccessToken();
      if (!token) {
        return null;
      }

      const response = await axios.get(`${this.baseURL}/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      return response.data;
    } catch (error) {
      this.clearTokens();
      return null;
    }
  }

  // Logout user
  async logout(): Promise<void> {
    try {
      const refreshToken = this.getRefreshToken();
      if (refreshToken) {
        await axios.post(`${this.baseURL}/logout`, {
          refresh_token: refreshToken,
        });
      }
    } catch (error) {
      console.warn('Logout API call failed:', error);
    } finally {
      this.clearTokens();
    }
  }

  // Check if user has specific permission
  hasPermission(userRoles: string[], requiredPermission: string): boolean {
    const rolePermissions: Record<string, string[]> = {
      'system_admin': [
        'system:read', 'system:write', 'system:delete',
        'user:read', 'user:write', 'user:delete',
        'portfolio:read', 'portfolio:write', 'portfolio:delete',
        'analytics:read', 'analytics:write',
        'reporting:read', 'reporting:write'
      ],
      'portfolio_manager': [
        'portfolio:read', 'portfolio:write',
        'analytics:read', 'analytics:write',
        'reporting:read', 'reporting:write'
      ],
      'financial_analyst': [
        'portfolio:read',
        'analytics:read', 'analytics:write',
        'reporting:read'
      ],
      'viewer': [
        'portfolio:read',
        'analytics:read',
        'reporting:read'
      ]
    };

    return userRoles.some(role => 
      rolePermissions[role]?.includes(requiredPermission)
    );
  }

  // Token management methods
  private setTokens(tokens: AuthTokens): void {
    localStorage.setItem('accessToken', tokens.accessToken);
    if (tokens.refreshToken) {
      localStorage.setItem('refreshToken', tokens.refreshToken);
    }
  }

  getAccessToken(): string | null {
    return localStorage.getItem('accessToken');
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refreshToken');
  }

  clearTokens(): void {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  // Setup axios interceptors for automatic token management
  setupAxiosInterceptors(): void {
    // Request interceptor to add token
    axios.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            await this.refreshToken();
            const newToken = this.getAccessToken();
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return axios(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            this.clearTokens();
            window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );
  }
}

export const authService = AuthService.getInstance();