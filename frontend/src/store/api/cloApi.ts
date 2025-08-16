import { createApi, fetchBaseQuery, retry } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../index';
import { authService } from '../../services/auth';

// Import new API types
import {
  // Document Management Types
  Document,
  DocumentUploadRequest,
  DocumentUpdateRequest,
  DocumentSearchRequest,
  DocumentStatsResponse,
  // Portfolio Analytics Types
  PortfolioOptimizationRequest,
  PortfolioOptimizationResult,
  PortfolioPerformanceAnalysisRequest,
  PortfolioPerformanceResult,
  PortfolioRiskAnalysisRequest,
  PortfolioRiskAnalysisResult,
  ConcentrationAnalysisRequest,
  ConcentrationAnalysisResult,
  // User Management Types
  UserManagement,
  UserCreateRequest as UserCreateRequestNew,
  UserUpdateRequest as UserUpdateRequestNew,
  UserSearchRequest,
  UserStatsResponse,
  PasswordChangeRequest,
  PasswordResetRequest,
  UserPermissionResponse,
  UserSessionResponse,
  UserActivityResponse,
  UserPreferencesRequest,
  UserPreferencesResponse,
  // Report Types
  Report,
  ReportTemplate,
  ReportCreateRequest,
  ReportGenerationProgress,
  // WebSocket Types
  WebSocketStats,
  NotificationData,
  CalculationProgressData,
  RiskAlertData,
  // Bulk Operations
  BulkOperationRequest,
  BulkOperationResponse,
} from './newApiTypes';

// Define common types (will be expanded as we build more features)
// Legacy User interface - consider migrating to UserManagement from newApiTypes.ts
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'manager' | 'analyst' | 'viewer';
  isActive: boolean;
  lastLogin?: string;
}

export interface Portfolio {
  id: string;
  deal_name: string;
  manager: string;
  trustee: string;
  effective_date: string;
  stated_maturity: string;
  revolving_period_end?: string;
  reinvestment_period_end?: string;
  deal_size: number;
  currency: string;
  status: 'effective' | 'inactive' | 'pending';
  current_asset_count: number;
  current_portfolio_balance: number;
  days_to_maturity: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioSummary {
  portfolio: Portfolio;
  assets: Asset[];
  waterfall_summary: WaterfallSummary;
  risk_metrics: RiskMetrics;
  compliance_status: ComplianceStatus;
}

export interface WaterfallSummary {
  mag_version: string;
  payment_date: string;
  total_cash_available: number;
  expenses: number;
  interest_payments: number;
  principal_payments: number;
  excess_spread: number;
  equity_distribution: number;
}

export interface RiskMetrics {
  portfolio_value: number;
  weighted_average_life: number;
  average_rating: string;
  concentration_metrics: Record<string, number>;
  oc_ratios: Record<string, number>;
  ic_ratios: Record<string, number>;
}

export interface ComplianceStatus {
  oc_tests_passing: boolean;
  ic_tests_passing: boolean;
  concentration_tests_passing: boolean;
  failed_tests: string[];
  warnings: string[];
}

export interface Asset {
  id: string;
  cusip: string;
  isin?: string;
  asset_name?: string;
  asset_description?: string;
  asset_type: string;
  current_balance?: number;
  original_balance?: number;
  par_amount?: number;
  current_price?: number;
  purchase_price?: number;
  purchase_date?: string;
  coupon_rate?: number;
  spread?: number;
  maturity_date?: string;
  final_maturity?: string;
  current_rating?: string;
  rating?: string;
  sector?: string;
  industry?: string;
  country?: string;
  issuer: string;
  days_to_maturity?: number;
  yield_to_maturity?: number;
  duration?: number;
  convexity?: number;
  default_probability?: number;
  recovery_rate?: number;
  lgd?: number;
  ead?: number;
  performance_1d?: number;
  performance_30d?: number;
  performance_ytd?: number;
  status: 'active' | 'inactive' | 'matured' | 'defaulted';
  last_updated?: string;
  created_at: string;
  updated_at: string;
}

export interface AssetCorrelation {
  assetId: string;
  asset_id_1: string;
  asset_id_2: string;
  cusip: string;
  issuer: string;
  correlation: number;
  pValue: number;
  significance: 'high' | 'medium' | 'low' | 'none';
  last_updated: string;
}

export interface AssetStats {
  total_assets: number;
  by_type: Record<string, number>;
  by_rating: Record<string, number>;
  correlations_available: number;
}

export interface AssetRiskMetrics {
  asset_id: string;
  var_95: number;
  var_99: number;
  expected_shortfall: number;
  portfolio_contribution: number;
  marginal_var: number;
  component_var: number;
  concentration_risk: number;
  stress_test_results: {
    recession_scenario: number;
    rating_downgrade: number;
    interest_rate_shock: number;
    credit_spread: number;
  };
  calculated_at: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface WaterfallRequest {
  deal_id: string;
  payment_date: string;
  mag_version?: string;
  scenario_overrides?: Record<string, any>;
}

export interface WaterfallResult {
  deal_id: string;
  payment_date: string;
  mag_version: string;
  total_cash_available: number;
  payment_details: WaterfallPayment[];
  liabilities: LiabilityPayment[];
  remaining_cash: number;
  calculation_timestamp: string;
}

export interface WaterfallPayment {
  step: number;
  description: string;
  amount: number;
  cumulative_amount: number;
}

export interface LiabilityPayment {
  liability_id: string;
  liability_name: string;
  interest_payment: number;
  principal_payment: number;
  remaining_balance: number;
}

export interface RiskAnalyticsRequest {
  deal_id: string;
  risk_type: 'var' | 'stress_test' | 'scenario_analysis';
  confidence_level?: number;
  time_horizon?: number;
  scenario_parameters?: Record<string, any>;
}

export interface RiskAnalyticsResult {
  deal_id: string;
  risk_type: string;
  var_95: number;
  var_99: number;
  expected_shortfall: number;
  stress_test_results?: StressTestResult[];
  calculation_timestamp: string;
}

export interface StressTestResult {
  scenario_name: string;
  portfolio_loss: number;
  equity_loss: number;
  rating_downgrades: number;
}

export interface SystemHealth {
  status: string;
  uptime: number;
  active_users: number;
  system_alerts: number;
  database_status: string;
  redis_status: string;
  background_jobs: number;
}

export interface MonitoringMetrics {
  api_response_times: Record<string, number>;
  error_rates: Record<string, number>;
  active_calculations: number;
  memory_usage: number;
  cpu_usage: number;
}

// Removed duplicate UserCreateRequest and UserUpdateRequest interfaces
// Now using UserCreateRequest as UserCreateRequestNew and UserUpdateRequest as UserUpdateRequestNew from newApiTypes.ts

export interface SystemAlert {
  id: string;
  type: 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  source: string;
}

export interface AuditLogEntry {
  id: string;
  user_id: string;
  user_email: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  timestamp: string;
  ip_address: string;
}

export interface SystemConfiguration {
  id: string;
  key: string;
  value: any;
  description: string;
  category: string;
  updated_by: string;
  updated_at: string;
}

// Performance tracking interfaces
export interface PerformanceData {
  date: string;
  portfolio_return: number;
  benchmark_return: number;
  cumulative_return: number;
  daily_return: number;
  volatility: number;
}

export interface PerformanceMetrics {
  total_return: number;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  beta: number;
  alpha: number;
  information_ratio: number;
  tracking_error: number;
}

export interface BenchmarkData {
  name: string;
  return_1m: number;
  return_3m: number;
  return_6m: number;
  return_1y: number;
  return_3y: number;
  volatility: number;
  sharpe_ratio: number;
}

export interface PortfolioPerformanceHistory {
  deal_id: string;
  performance_data: PerformanceData[];
  performance_metrics: PerformanceMetrics;
  benchmark_comparison: BenchmarkData;
}

// Enhanced error handling types
export interface ApiError {
  status: number;
  data: {
    message?: string;
    detail?: string;
    error?: string;
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

// Enhanced base query with retry and error handling
const baseQueryWithRetry = retry(
  fetchBaseQuery({
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8001/api/v1/',
    prepareHeaders: (headers, { getState }) => {
      // Get token from Redux store first, fallback to authService
      const reduxToken = (getState() as RootState).auth.tokens?.accessToken;
      const serviceToken = authService.getAccessToken();
      const token = reduxToken || serviceToken;
      
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      
      headers.set('content-type', 'application/json');
      headers.set('x-client-version', '1.0.0');
      headers.set('x-requested-with', 'CLO-Frontend');
      
      return headers;
    },
    // Enhanced error handling
    validateStatus: (response, result) => {
      return response.status === 200 && !result.error;
    },
  }),
  {
    maxRetries: 3 as any,
    retryCondition: (error: any, args: any, { attempt }: any) => {
      // Retry on network errors or 5xx server errors
      if ('status' in error) {
        const status = error.status as number;
        return status >= 500 || status === 429; // Server errors or rate limiting
      }
      // Retry on network errors (fetch errors)
      return error.name === 'TypeError' && attempt < 3;
    },
  }
);

// Create the main API slice
export const cloApi = createApi({
  reducerPath: 'cloApi',
  baseQuery: baseQueryWithRetry,
  tagTypes: [
    'User',
    'Portfolio', 
    'Asset',
    'Waterfall',
    'Risk',
    'Scenario',
    'Calculation',
    'SystemHealth',
    'Report',
    'Correlation',
    'Analytics',
    'SystemAlert',
    'AuditLog',
    'SystemConfig',
    'WaterfallAnalysis',
    'ScenarioModeling',
    'CorrelationAnalysis',
    'CLOStructuring',
    'RiskAnalytics',
    'ModelValidation',
    // New tag types
    'Document',
    'ReportTemplate',
    'WebSocket',
    'UserPermission',
    'UserSession',
    'UserActivity',
    'UserPreferences',
    'Alert',
    'MarketData',
    'Price'
  ],
  endpoints: (builder) => ({
    // Authentication endpoints
    login: builder.mutation<ApiResponse<LoginResponse>, LoginRequest>({
      query: (credentials) => {
        const formData = new FormData();
        formData.append('username', credentials.email);
        formData.append('password', credentials.password);
        
        return {
          url: 'auth/token',
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: ['User'],
    }),

    logout: builder.mutation<ApiResponse<void>, void>({
      query: () => ({
        url: 'auth/logout',
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),

    getCurrentUser: builder.query<ApiResponse<User>, void>({
      query: () => 'auth/me',
      providesTags: ['User'],
    }),

    // Portfolio endpoints
    getPortfolios: builder.query<ApiResponse<Portfolio[]>, void>({
      query: () => 'portfolios',
      providesTags: ['Portfolio'],
    }),

    getPortfolio: builder.query<ApiResponse<Portfolio>, string>({
      query: (id) => `portfolios/${id}`,
      providesTags: (result, error, id) => [{ type: 'Portfolio', id }],
    }),

    // Asset endpoints
    getAssets: builder.query<PaginatedResponse<Asset>, { 
      skip?: number; 
      limit?: number; 
      asset_type?: string; 
      rating?: string; 
      sector?: string;
      industry?: string;
      deal_id?: string;
      portfolio_id?: string;
      search?: string;
    }>({
      query: ({ skip = 0, limit = 100, asset_type, rating, sector, industry, deal_id, portfolio_id, search }) => ({
        url: 'assets',
        params: { skip, limit, asset_type, rating, sector, industry, deal_id, portfolio_id, search },
      }),
      providesTags: ['Asset'],
    }),

    getAsset: builder.query<ApiResponse<Asset>, string>({
      query: (assetId) => `assets/${assetId}`,
      providesTags: (result, error, id) => [{ type: 'Asset', id }],
    }),

    getAssetCorrelations: builder.query<ApiResponse<AssetCorrelation[]>, { assetId: string; limit?: number; threshold?: number; period?: string }>({
      query: ({ assetId, limit = 50, threshold, period }) => ({
        url: `assets/${assetId}/correlations`,
        params: { limit, threshold, period },
      }),
      providesTags: ['Correlation'],
    }),

    getAssetStats: builder.query<AssetStats, void>({
      query: () => 'assets/stats/summary',
      providesTags: ['Asset', 'Analytics'],
    }),

    // Asset management mutations
    createAsset: builder.mutation<ApiResponse<Asset>, Partial<Asset>>({
      query: (assetData) => ({
        url: 'assets',
        method: 'POST',
        body: assetData,
      }),
      invalidatesTags: ['Asset', 'Analytics'],
    }),

    updateAsset: builder.mutation<ApiResponse<Asset>, { id: string; updates: Partial<Asset> }>({
      query: ({ id, updates }) => ({
        url: `assets/${id}`,
        method: 'PUT',
        body: updates,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Asset', id },
        'Asset',
        'Analytics',
      ],
    }),

    deleteAsset: builder.mutation<ApiResponse<void>, string>({
      query: (id) => ({
        url: `assets/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Asset', id },
        'Asset',
        'Analytics',
      ],
    }),

    getAssetRiskMetrics: builder.query<ApiResponse<AssetRiskMetrics>, { assetId: string; horizon?: number; confidence?: number }>({
      query: ({ assetId, horizon = 30, confidence = 95 }) => ({
        url: `assets/${assetId}/risk-metrics`,
        params: { horizon, confidence },
      }),
      providesTags: (result, error, { assetId }) => [
        { type: 'Asset', id: assetId },
        'Risk',
      ],
    }),

    // Portfolio endpoints
    getPortfolioSummary: builder.query<PortfolioSummary, string>({
      query: (dealId) => `portfolios/${dealId}/summary`,
      providesTags: (result, error, id) => [{ type: 'Portfolio', id }, 'Asset', 'Analytics'],
    }),

    // Waterfall calculation endpoints
    calculateWaterfall: builder.mutation<WaterfallResult, WaterfallRequest>({
      query: (request) => ({
        url: 'waterfall/calculate',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Calculation', 'Analytics'],
    }),

    getWaterfallHistory: builder.query<WaterfallResult[], { dealId: string; limit?: number }>({
      query: ({ dealId, limit = 10 }) => ({
        url: 'waterfall/history',
        params: { deal_id: dealId, limit },
      }),
      providesTags: ['Calculation'],
    }),

    // Risk analytics endpoints
    calculateRisk: builder.mutation<RiskAnalyticsResult, RiskAnalyticsRequest>({
      query: (request) => ({
        url: 'risk/calculate',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Risk', 'Analytics'],
    }),

    getRiskHistory: builder.query<RiskAnalyticsResult[], { dealId: string; riskType?: string; limit?: number }>({
      query: ({ dealId, riskType, limit = 10 }) => ({
        url: 'risk/history',
        params: { deal_id: dealId, risk_type: riskType, limit },
      }),
      providesTags: ['Risk'],
    }),

    // Scenario management endpoints
    getScenarios: builder.query<any[], { dealId?: string; scenarioType?: string }>({
      query: ({ dealId, scenarioType }) => ({
        url: 'scenarios',
        params: { deal_id: dealId, scenario_type: scenarioType },
      }),
      providesTags: ['Scenario'],
    }),

    createScenario: builder.mutation<any, { name: string; description: string; parameters: Record<string, any> }>({
      query: (scenario) => ({
        url: 'scenarios',
        method: 'POST',
        body: scenario,
      }),
      invalidatesTags: ['Scenario'],
    }),

    // Monitoring endpoints
    getMonitoringMetrics: builder.query<MonitoringMetrics, void>({
      query: () => 'monitoring/metrics',
      providesTags: ['SystemHealth'],
    }),

    // System health endpoint
    getSystemHealth: builder.query<SystemHealth, void>({
      query: () => 'monitoring/health',
      providesTags: ['SystemHealth'],
    }),

    // User management endpoints (Admin only)
    getUsers: builder.query<PaginatedResponse<User>, { skip?: number; limit?: number; search?: string; role?: string; isActive?: boolean }>({
      query: ({ skip = 0, limit = 50, search, role, isActive }) => ({
        url: 'admin/users',
        params: { skip, limit, search, role, is_active: isActive },
      }),
      providesTags: ['User'],
    }),

    createUser: builder.mutation<ApiResponse<User>, UserCreateRequestNew>({
      query: (userData) => ({
        url: 'admin/users',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: ['User'],
    }),

    updateUser: builder.mutation<ApiResponse<User>, { userId: string; data: UserUpdateRequestNew }>({
      query: ({ userId, data }) => ({
        url: `admin/users/${userId}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['User'],
    }),

    deleteUser: builder.mutation<ApiResponse<void>, string>({
      query: (userId) => ({
        url: `admin/users/${userId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['User'],
    }),

    // System alerts endpoints (Admin only)
    getSystemAlerts: builder.query<PaginatedResponse<SystemAlert>, { skip?: number; limit?: number; type?: string; acknowledged?: boolean }>({
      query: ({ skip = 0, limit = 50, type, acknowledged }) => ({
        url: 'admin/alerts',
        params: { skip, limit, type, acknowledged },
      }),
      providesTags: ['SystemAlert'],
    }),

    acknowledgeAlert: builder.mutation<ApiResponse<SystemAlert>, string>({
      query: (alertId) => ({
        url: `admin/alerts/${alertId}/acknowledge`,
        method: 'POST',
      }),
      invalidatesTags: ['SystemAlert'],
    }),

    dismissAlert: builder.mutation<ApiResponse<void>, string>({
      query: (alertId) => ({
        url: `admin/alerts/${alertId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['SystemAlert'],
    }),

    // Audit log endpoints (Admin only)
    getAuditLogs: builder.query<PaginatedResponse<AuditLogEntry>, { skip?: number; limit?: number; userId?: string; action?: string; resource?: string; startDate?: string; endDate?: string }>({
      query: ({ skip = 0, limit = 100, userId, action, resource, startDate, endDate }) => ({
        url: 'admin/audit-logs',
        params: { skip, limit, user_id: userId, action, resource, start_date: startDate, end_date: endDate },
      }),
      providesTags: ['AuditLog'],
    }),

    exportAuditLogs: builder.mutation<any, { startDate: string; endDate: string; format?: 'csv' | 'xlsx' }>({
      query: ({ startDate, endDate, format = 'csv' }) => ({
        url: 'admin/audit-logs/export',
        method: 'POST',
        body: { start_date: startDate, end_date: endDate, format },
      }),
    }),

    // System configuration endpoints (Admin only)
    getSystemConfigurations: builder.query<PaginatedResponse<SystemConfiguration>, { skip?: number; limit?: number; category?: string }>({
      query: ({ skip = 0, limit = 100, category }) => ({
        url: 'admin/config',
        params: { skip, limit, category },
      }),
      providesTags: ['SystemConfig'],
    }),

    updateSystemConfiguration: builder.mutation<ApiResponse<SystemConfiguration>, { configId: string; value: any }>({
      query: ({ configId, value }) => ({
        url: `admin/config/${configId}`,
        method: 'PUT',
        body: { value },
      }),
      invalidatesTags: ['SystemConfig'],
    }),

    // System statistics endpoints (Admin only)
    getSystemStatistics: builder.query<{
      totalUsers: number;
      activeUsers: number;
      totalPortfolios: number;
      totalAssets: number;
      calculationsToday: number;
      systemUptime: number;
      diskUsage: number;
      memoryUsage: number;
      cpuUsage: number;
    }, void>({
      query: () => 'admin/statistics',
      providesTags: ['SystemHealth'],
    }),

    getUserActivityReport: builder.query<{
      date: string;
      activeUsers: number;
      newUsers: number;
      loginAttempts: number;
      failedLogins: number;
    }[], { days?: number }>({
      query: ({ days = 30 }) => ({
        url: 'admin/reports/user-activity',
        params: { days },
      }),
      providesTags: ['AuditLog'],
    }),

    // Performance tracking endpoints
    getPerformanceHistory: builder.query<PortfolioPerformanceHistory, { 
      dealId: string; 
      period?: string; 
      benchmark?: string;
    }>({
      query: ({ dealId, period = '1Y', benchmark = 'market' }) => ({
        url: `portfolios/${dealId}/performance`,
        params: { period, benchmark },
      }),
      providesTags: (result, error, { dealId }) => [
        { type: 'Portfolio', id: dealId },
        'Analytics'
      ],
    }),

    getPortfolioMetrics: builder.query<PerformanceMetrics, { 
      dealId: string; 
      period?: string;
    }>({
      query: ({ dealId, period = '1Y' }) => ({
        url: `portfolios/${dealId}/metrics`,
        params: { period },
      }),
      providesTags: (result, error, { dealId }) => [
        { type: 'Portfolio', id: dealId },
        'Analytics'
      ],
    }),

    getBenchmarkData: builder.query<BenchmarkData[], { benchmarkType?: string }>({
      query: ({ benchmarkType }) => ({
        url: 'benchmarks',
        params: { type: benchmarkType },
      }),
      providesTags: ['Analytics'],
    }),

    // Portfolio asset management endpoints
    addAssetToPortfolio: builder.mutation<ApiResponse<void>, { 
      portfolioId: string; 
      assetId: string; 
      allocation?: number;
    }>({
      query: ({ portfolioId, assetId, allocation }) => ({
        url: `portfolios/${portfolioId}/assets`,
        method: 'POST',
        body: { asset_id: assetId, allocation },
      }),
      invalidatesTags: ['Portfolio', 'Asset'],
    }),

    removeAssetFromPortfolio: builder.mutation<ApiResponse<void>, { 
      portfolioId: string; 
      assetId: string;
    }>({
      query: ({ portfolioId, assetId }) => ({
        url: `portfolios/${portfolioId}/assets/${assetId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Portfolio', 'Asset'],
    }),

    updateAssetAllocation: builder.mutation<ApiResponse<void>, { 
      portfolioId: string; 
      assetId: string;
      allocation: number;
    }>({
      query: ({ portfolioId, assetId, allocation }) => ({
        url: `portfolios/${portfolioId}/assets/${assetId}`,
        method: 'PUT',
        body: { allocation },
      }),
      invalidatesTags: ['Portfolio', 'Asset'],
    }),

    // Portfolio creation and management
    createPortfolio: builder.mutation<ApiResponse<Portfolio>, {
      deal_name: string;
      manager: string;
      trustee: string;
      effective_date: string;
      stated_maturity: string;
      deal_size: number;
      currency: string;
      revolving_period_end?: string;
      reinvestment_period_end?: string;
    }>({
      query: (portfolioData) => ({
        url: 'portfolios',
        method: 'POST',
        body: portfolioData,
      }),
      invalidatesTags: ['Portfolio'],
    }),

    updatePortfolio: builder.mutation<ApiResponse<Portfolio>, {
      portfolioId: string;
      data: Partial<Portfolio>;
    }>({
      query: ({ portfolioId, data }) => ({
        url: `portfolios/${portfolioId}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: ['Portfolio'],
    }),

    deletePortfolio: builder.mutation<ApiResponse<void>, string>({
      query: (portfolioId) => ({
        url: `portfolios/${portfolioId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Portfolio'],
    }),

    // Enhanced asset operations
    bulkUpdateAssets: builder.mutation<ApiResponse<void>, {
      portfolioId: string;
      operations: Array<{
        assetId: string;
        operation: 'add' | 'remove' | 'update';
        data?: any;
      }>;
    }>({
      query: ({ portfolioId, operations }) => ({
        url: `portfolios/${portfolioId}/assets/bulk`,
        method: 'POST',
        body: { operations },
      }),
      invalidatesTags: ['Portfolio', 'Asset'],
    }),

    exportPortfolioAssets: builder.mutation<any, {
      portfolioId: string;
      format?: 'csv' | 'xlsx';
      filters?: Record<string, any>;
    }>({
      query: ({ portfolioId, format = 'csv', filters }) => ({
        url: `portfolios/${portfolioId}/assets/export`,
        method: 'POST',
        body: { format, filters },
      }),
    }),

    exportPerformanceReport: builder.mutation<any, {
      portfolioId: string;
      period: string;
      format?: 'pdf' | 'xlsx';
    }>({
      query: ({ portfolioId, period, format = 'pdf' }) => ({
        url: `portfolios/${portfolioId}/performance/export`,
        method: 'POST',
        body: { period, format },
      }),
    }),

    // === FINANCIAL ANALYST ENDPOINTS ===
    
    // Waterfall Analysis
    getWaterfallAnalysis: builder.query<any, {
      portfolioId: string;
      waterfallVersion?: string;
      paymentDate?: string;
    }>({
      query: ({ portfolioId, waterfallVersion, paymentDate }) => ({
        url: `analytics/waterfall/${portfolioId}`,
        params: { waterfallVersion, paymentDate },
      }),
      providesTags: ['WaterfallAnalysis'],
    }),

    runWaterfallCalculation: builder.mutation<any, {
      portfolioId: string;
      waterfallVersion: string;
      paymentDate: string;
      assumptions?: Record<string, any>;
    }>({
      query: (params) => ({
        url: 'analytics/waterfall/calculate',
        method: 'POST',
        body: params,
      }),
      invalidatesTags: ['WaterfallAnalysis'],
    }),

    getWaterfallScenarios: builder.query<any[], { portfolioId: string }>({
      query: ({ portfolioId }) => ({
        url: `analytics/waterfall/${portfolioId}/scenarios`,
      }),
      providesTags: ['WaterfallAnalysis'],
    }),

    // Scenario Modeling
    getScenarioAnalysis: builder.query<any[], { portfolioId: string }>({
      query: ({ portfolioId }) => ({
        url: `analytics/scenarios/${portfolioId}`,
      }),
      providesTags: ['ScenarioModeling'],
    }),

    runMonteCarloSimulation: builder.mutation<any, {
      portfolioId: string;
      iterations: number;
      timeHorizon: number;
      confidenceLevel: number;
      parameters: Record<string, any>;
    }>({
      query: (params) => ({
        url: 'analytics/scenarios/montecarlo',
        method: 'POST',
        body: params,
      }),
      invalidatesTags: ['ScenarioModeling'],
    }),

    runStressTest: builder.mutation<any, {
      portfolioId: string;
      stressScenario: string;
      parameters: Record<string, any>;
    }>({
      query: (params) => ({
        url: 'analytics/scenarios/stress-test',
        method: 'POST',
        body: params,
      }),
      invalidatesTags: ['ScenarioModeling'],
    }),

    saveScenarioConfig: builder.mutation<any, {
      name: string;
      description: string;
      portfolioId: string;
      config: Record<string, any>;
    }>({
      query: (scenario) => ({
        url: 'analytics/scenarios/config',
        method: 'POST',
        body: scenario,
      }),
      invalidatesTags: ['ScenarioModeling'],
    }),

    // Correlation Analysis
    getCorrelationMatrix: builder.query<any, {
      portfolioId: string;
      timeWindow?: string;
      analysisType?: string;
    }>({
      query: ({ portfolioId, timeWindow = '1Y', analysisType = 'pearson' }) => ({
        url: `analytics/correlation/${portfolioId}/matrix`,
        params: { timeWindow, analysisType },
      }),
      providesTags: ['CorrelationAnalysis'],
    }),

    getHighCorrelationPairs: builder.query<any[], {
      portfolioId: string;
      threshold?: number;
    }>({
      query: ({ portfolioId, threshold = 0.7 }) => ({
        url: `analytics/correlation/${portfolioId}/high-correlations`,
        params: { threshold },
      }),
      providesTags: ['CorrelationAnalysis'],
    }),

    getRiskFactorAnalysis: builder.query<any[], { portfolioId: string }>({
      query: ({ portfolioId }) => ({
        url: `analytics/correlation/${portfolioId}/risk-factors`,
      }),
      providesTags: ['CorrelationAnalysis'],
    }),

    getDiversificationMetrics: builder.query<any, { portfolioId: string }>({
      query: ({ portfolioId }) => ({
        url: `analytics/correlation/${portfolioId}/diversification`,
      }),
      providesTags: ['CorrelationAnalysis'],
    }),

    // CLO Structuring & Optimization
    getCLOStructure: builder.query<any, { dealId: string }>({
      query: ({ dealId }) => ({
        url: `analytics/structuring/${dealId}`,
      }),
      providesTags: ['CLOStructuring'],
    }),

    optimizeCLOStructure: builder.mutation<any, {
      dealId: string;
      constraints: Array<{
        type: string;
        minValue?: number;
        maxValue?: number;
        weight: number;
      }>;
      objectives: Record<string, number>;
    }>({
      query: (params) => ({
        url: 'analytics/structuring/optimize',
        method: 'POST',
        body: params,
      }),
      invalidatesTags: ['CLOStructuring'],
    }),

    validateStructuringConstraints: builder.mutation<any, {
      dealId: string;
      trancheStructure: Array<{
        name: string;
        size: number;
        coupon: number;
        rating: string;
      }>;
    }>({
      query: (params) => ({
        url: 'analytics/structuring/validate',
        method: 'POST',
        body: params,
      }),
    }),

    updateTrancheStructure: builder.mutation<any, {
      dealId: string;
      tranches: Array<{
        id: string;
        name: string;
        size: number;
        coupon: number;
        spread: number;
        rating: string;
      }>;
    }>({
      query: ({ dealId, tranches }) => ({
        url: `analytics/structuring/${dealId}/tranches`,
        method: 'PUT',
        body: { tranches },
      }),
      invalidatesTags: ['CLOStructuring'],
    }),

    // Advanced Risk Analytics
    getVaRAnalysis: builder.query<any, {
      portfolioId: string;
      confidenceLevel?: number;
      timeHorizon?: number;
    }>({
      query: ({ portfolioId, confidenceLevel = 95, timeHorizon = 1 }) => ({
        url: `analytics/risk/${portfolioId}/var`,
        params: { confidenceLevel, timeHorizon },
      }),
      providesTags: ['RiskAnalytics'],
    }),

    getBacktestResults: builder.query<any[], {
      portfolioId: string;
      modelType: string;
      period?: string;
    }>({
      query: ({ portfolioId, modelType, period = '1Y' }) => ({
        url: `analytics/backtest/${portfolioId}`,
        params: { modelType, period },
      }),
      providesTags: ['ModelValidation'],
    }),

    runModelValidation: builder.mutation<any, {
      portfolioId: string;
      modelType: string;
      validationPeriod: string;
      parameters: Record<string, any>;
    }>({
      query: (params) => ({
        url: 'analytics/validation/run',
        method: 'POST',
        body: params,
      }),
      invalidatesTags: ['ModelValidation'],
    }),

    // Export functionality for analysts
    exportWaterfallAnalysis: builder.mutation<any, {
      portfolioId: string;
      format?: 'pdf' | 'xlsx';
    }>({
      query: ({ portfolioId, format = 'pdf' }) => ({
        url: `analytics/waterfall/${portfolioId}/export`,
        method: 'POST',
        body: { format },
      }),
    }),

    exportCorrelationMatrix: builder.mutation<any, {
      portfolioId: string;
      format?: 'csv' | 'xlsx';
    }>({
      query: ({ portfolioId, format = 'xlsx' }) => ({
        url: `analytics/correlation/${portfolioId}/export`,
        method: 'POST',
        body: { format },
      }),
    }),

    exportScenarioResults: builder.mutation<any, {
      portfolioId: string;
      scenarioIds: string[];
      format?: 'pdf' | 'xlsx';
    }>({
      query: ({ portfolioId, scenarioIds, format = 'pdf' }) => ({
        url: `analytics/scenarios/${portfolioId}/export`,
        method: 'POST',
        body: { scenarioIds, format },
      }),
    }),

    // ===========================================
    // DOCUMENT MANAGEMENT ENDPOINTS
    // ===========================================
    
    // Upload document
    uploadDocument: builder.mutation<ApiResponse<Document>, { file: File; metadata: DocumentUploadRequest }>({
      query: ({ file, metadata }) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', metadata.title || '');
        formData.append('description', metadata.description || '');
        formData.append('document_type', metadata.document_type);
        formData.append('access_level', metadata.access_level);
        formData.append('portfolio_id', metadata.portfolio_id || '');
        formData.append('related_entity_type', metadata.related_entity_type || '');
        formData.append('related_entity_id', metadata.related_entity_id || '');
        formData.append('tags', JSON.stringify(metadata.tags));
        
        return {
          url: 'documents/upload',
          method: 'POST',
          body: formData,
          formData: true,
        };
      },
      invalidatesTags: ['Document'],
    }),

    // Get document by ID
    getDocument: builder.query<ApiResponse<Document>, string>({
      query: (documentId) => `documents/${documentId}`,
      providesTags: (result, error, id) => [{ type: 'Document' as const, id }],
    }),

    // Download document
    downloadDocument: builder.mutation<Blob, string>({
      query: (documentId) => ({
        url: `documents/${documentId}/download`,
        method: 'GET',
        responseHandler: (response) => response.blob(),
      }),
    }),

    // Update document metadata
    updateDocument: builder.mutation<ApiResponse<Document>, { documentId: string; update: DocumentUpdateRequest }>({
      query: ({ documentId, update }) => ({
        url: `documents/${documentId}`,
        method: 'PUT',
        body: update,
      }),
      invalidatesTags: (result, error, { documentId }) => [{ type: 'Document' as const, id: documentId }],
    }),

    // Delete document
    deleteDocument: builder.mutation<void, string>({
      query: (documentId) => ({
        url: `documents/${documentId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, documentId) => [{ type: 'Document' as const, id: documentId }],
    }),

    // List documents
    getDocuments: builder.query<PaginatedResponse<Document>, {
      skip?: number;
      limit?: number;
      document_type?: string;
      access_level?: string;
      portfolio_id?: string;
      owner_id?: string;
    }>({
      query: ({ skip = 0, limit = 50, document_type, access_level, portfolio_id, owner_id }) => ({
        url: 'documents/',
        params: { skip, limit, document_type, access_level, portfolio_id, owner_id },
      }),
      providesTags: ['Document'],
    }),

    // Search documents
    searchDocuments: builder.mutation<ApiResponse<Document[]>, DocumentSearchRequest>({
      query: (searchParams) => ({
        url: 'documents/search',
        method: 'POST',
        body: searchParams,
      }),
      invalidatesTags: ['Document'],
    }),

    // Get document statistics
    getDocumentStats: builder.query<ApiResponse<DocumentStatsResponse>, void>({
      query: () => 'documents/stats/summary',
      providesTags: ['Document'],
    }),

    // Bulk document operations
    bulkDocumentOperation: builder.mutation<BulkOperationResponse, BulkOperationRequest>({
      query: (operation) => ({
        url: 'documents/bulk',
        method: 'POST',
        body: operation,
      }),
      invalidatesTags: ['Document'],
    }),

    // ===========================================
    // ENHANCED PORTFOLIO ANALYTICS ENDPOINTS
    // ===========================================

    // Portfolio optimization
    optimizePortfolio: builder.mutation<PortfolioOptimizationResult, PortfolioOptimizationRequest>({
      query: (request) => ({
        url: `portfolio-analytics/${request.portfolio_id}/optimize`,
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Portfolio', 'Analytics'],
    }),

    // Performance analysis
    analyzePerformance: builder.mutation<PortfolioPerformanceResult, PortfolioPerformanceAnalysisRequest>({
      query: (request) => ({
        url: `portfolio-analytics/${request.portfolio_id}/performance`,
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Portfolio', 'Analytics'],
    }),

    // Risk analysis
    analyzeRisk: builder.mutation<PortfolioRiskAnalysisResult, PortfolioRiskAnalysisRequest>({
      query: (request) => ({
        url: `portfolio-analytics/${request.portfolio_id}/risk`,
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Portfolio', 'Risk'],
    }),

    // Concentration analysis
    analyzeConcentration: builder.mutation<ConcentrationAnalysisResult, ConcentrationAnalysisRequest>({
      query: (request) => ({
        url: `portfolio-analytics/${request.portfolio_id}/concentration`,
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Portfolio', 'Analytics'],
    }),

    // Get portfolio analytics statistics
    getAnalyticsStats: builder.query<any, void>({
      query: () => 'portfolio-analytics/stats',
      providesTags: ['Analytics'],
    }),

    // Quick portfolio metrics
    getQuickPortfolioMetrics: builder.query<any, string>({
      query: (portfolioId) => `portfolio-analytics/${portfolioId}/quick-metrics`,
      providesTags: (result, error, portfolioId) => [{ type: 'Portfolio' as const, id: portfolioId }],
    }),

    // Generate portfolio alerts
    generatePortfolioAlerts: builder.mutation<any, string>({
      query: (portfolioId) => ({
        url: `portfolio-analytics/${portfolioId}/alerts`,
        method: 'POST',
      }),
    }),

    // ===========================================
    // ENHANCED USER MANAGEMENT ENDPOINTS
    // ===========================================

    // Create user (enhanced)
    createUserEnhanced: builder.mutation<ApiResponse<UserManagement>, UserCreateRequestNew>({
      query: (userData) => ({
        url: 'users/',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: ['User'],
    }),

    // Get user by ID (enhanced)
    getUserById: builder.query<ApiResponse<UserManagement>, string>({
      query: (userId) => `users/${userId}`,
      providesTags: (result, error, id) => [{ type: 'User' as const, id }],
    }),

    // Update user (enhanced)
    updateUserEnhanced: builder.mutation<ApiResponse<UserManagement>, { userId: string; update: UserUpdateRequestNew }>({
      query: ({ userId, update }) => ({
        url: `users/${userId}`,
        method: 'PUT',
        body: update,
      }),
      invalidatesTags: (result, error, { userId }) => [{ type: 'User' as const, id: userId }],
    }),

    // Delete user (enhanced)
    deleteUserEnhanced: builder.mutation<void, string>({
      query: (userId) => ({
        url: `users/${userId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, userId) => [{ type: 'User' as const, id: userId }],
    }),

    // List users (enhanced)
    getUsersEnhanced: builder.query<PaginatedResponse<UserManagement>, {
      skip?: number;
      limit?: number;
      role?: string;
      status?: string;
      organization?: string;
      department?: string;
    }>({
      query: ({ skip = 0, limit = 50, role, status, organization, department }) => ({
        url: 'users/',
        params: { skip, limit, role, status, organization, department },
      }),
      providesTags: ['User'],
    }),

    // Search users
    searchUsers: builder.mutation<PaginatedResponse<UserManagement>, UserSearchRequest>({
      query: (searchParams) => ({
        url: 'users/search',
        method: 'POST',
        body: searchParams,
      }),
    }),

    // Change password
    changePassword: builder.mutation<{ message: string }, PasswordChangeRequest>({
      query: (passwordData) => ({
        url: 'users/change-password',
        method: 'POST',
        body: passwordData,
      }),
    }),

    // Reset password
    resetPassword: builder.mutation<{ message: string }, PasswordResetRequest>({
      query: (resetData) => ({
        url: 'users/reset-password',
        method: 'POST',
        body: resetData,
      }),
    }),

    // Get user permissions
    getUserPermissions: builder.query<ApiResponse<UserPermissionResponse>, string>({
      query: (userId) => `users/${userId}/permissions`,
      providesTags: (result, error, userId) => [{ type: 'UserPermission' as const, id: userId }],
    }),

    // Get user statistics
    getUserStats: builder.query<ApiResponse<UserStatsResponse>, void>({
      query: () => 'users/stats/summary',
      providesTags: ['User'],
    }),

    // Bulk user operations
    bulkUserOperation: builder.mutation<BulkOperationResponse, BulkOperationRequest>({
      query: (operation) => ({
        url: 'users/bulk',
        method: 'POST',
        body: operation,
      }),
      invalidatesTags: ['User'],
    }),

    // Get user sessions
    getUserSessions: builder.query<ApiResponse<UserSessionResponse[]>, string>({
      query: (userId) => `users/${userId}/sessions`,
      providesTags: (result, error, userId) => [{ type: 'UserSession' as const, id: userId }],
    }),

    // Get user activity
    getUserActivity: builder.query<ApiResponse<UserActivityResponse[]>, { userId: string; limit?: number }>({
      query: ({ userId, limit = 50 }) => ({
        url: `users/${userId}/activity`,
        params: { limit },
      }),
      providesTags: (result, error, { userId }) => [{ type: 'UserActivity' as const, id: userId }],
    }),

    // Get user preferences
    getUserPreferences: builder.query<ApiResponse<UserPreferencesResponse>, string>({
      query: (userId) => `users/${userId}/preferences`,
      providesTags: (result, error, userId) => [{ type: 'UserPreferences' as const, id: userId }],
    }),

    // Update user preferences
    updateUserPreferences: builder.mutation<ApiResponse<UserPreferencesResponse>, { userId: string; preferences: UserPreferencesRequest }>({
      query: ({ userId, preferences }) => ({
        url: `users/${userId}/preferences`,
        method: 'PUT',
        body: preferences,
      }),
      invalidatesTags: (result, error, { userId }) => [{ type: 'UserPreferences' as const, id: userId }],
    }),

    // Impersonate user (admin only)
    impersonateUser: builder.mutation<any, string>({
      query: (userId) => ({
        url: `users/impersonate/${userId}`,
        method: 'POST',
      }),
    }),

    // ===========================================
    // REPORT MANAGEMENT ENDPOINTS
    // ===========================================

    // Create report
    createReport: builder.mutation<ApiResponse<Report>, ReportCreateRequest>({
      query: (reportData) => ({
        url: 'reports/',
        method: 'POST',
        body: reportData,
      }),
      invalidatesTags: ['Report'],
    }),

    // Get report by ID
    getReportById: builder.query<ApiResponse<Report>, string>({
      query: (reportId) => `reports/${reportId}`,
      providesTags: (result, error, id) => [{ type: 'Report' as const, id }],
    }),

    // List reports
    getReports: builder.query<PaginatedResponse<Report>, {
      skip?: number;
      limit?: number;
      status?: string;
      report_type?: string;
      requested_by?: string;
    }>({
      query: ({ skip = 0, limit = 50, status, report_type, requested_by }) => ({
        url: 'reports/',
        params: { skip, limit, status, report_type, requested_by },
      }),
      providesTags: ['Report'],
    }),

    // Download report
    downloadReport: builder.mutation<Blob, string>({
      query: (reportId) => ({
        url: `reports/${reportId}/download`,
        method: 'GET',
        responseHandler: (response) => response.blob(),
      }),
    }),

    // Get report generation progress
    getReportProgress: builder.query<ApiResponse<ReportGenerationProgress>, string>({
      query: (reportId) => `reports/${reportId}/progress`,
      providesTags: (result, error, reportId) => [{ type: 'Report' as const, id: reportId }],
    }),

    // Cancel report generation
    cancelReport: builder.mutation<void, string>({
      query: (reportId) => ({
        url: `reports/${reportId}/cancel`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, reportId) => [{ type: 'Report' as const, id: reportId }],
    }),

    // Delete report
    deleteReport: builder.mutation<void, string>({
      query: (reportId) => ({
        url: `reports/${reportId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, reportId) => [{ type: 'Report' as const, id: reportId }],
    }),

    // Get report templates
    getReportTemplates: builder.query<PaginatedResponse<ReportTemplate>, {
      skip?: number;
      limit?: number;
      report_type?: string;
    }>({
      query: ({ skip = 0, limit = 50, report_type }) => ({
        url: 'reports/templates/',
        params: { skip, limit, report_type },
      }),
      providesTags: ['ReportTemplate'],
    }),

    // Get report template by ID
    getReportTemplate: builder.query<ApiResponse<ReportTemplate>, string>({
      query: (templateId) => `reports/templates/${templateId}`,
      providesTags: (result, error, id) => [{ type: 'ReportTemplate' as const, id }],
    }),

    // Get report statistics
    getReportStats: builder.query<any, void>({
      query: () => 'reports/stats/summary',
      providesTags: ['Report'],
    }),

    // ===========================================
    // WEBSOCKET MANAGEMENT ENDPOINTS
    // ===========================================

    // Get WebSocket statistics
    getWebSocketStats: builder.query<ApiResponse<WebSocketStats>, void>({
      query: () => 'websocket/stats',
      providesTags: ['WebSocket'],
    }),

    // Broadcast message (admin only)
    broadcastMessage: builder.mutation<any, { title: string; message: string; severity?: string }>({
      query: (messageData) => ({
        url: 'websocket/broadcast',
        method: 'POST',
        body: messageData,
      }),
    }),

    // Send user notification
    sendUserNotification: builder.mutation<any, { userId: string; title: string; message: string; severity?: string }>({
      query: ({ userId, ...notificationData }) => ({
        url: `websocket/notify/${userId}`,
        method: 'POST',
        body: notificationData,
      }),
    }),

    // Notify portfolio subscribers
    notifyPortfolioSubscribers: builder.mutation<any, { portfolioId: string; type: string; data: Record<string, any> }>({
      query: ({ portfolioId, ...updateData }) => ({
        url: `websocket/portfolio/${portfolioId}/notify`,
        method: 'POST',
        body: updateData,
      }),
    }),

    // Update calculation progress
    updateCalculationProgress: builder.mutation<any, { calculationId: string; progress: number; status: string; userId?: string }>({
      query: ({ calculationId, ...progressData }) => ({
        url: `websocket/calculation/${calculationId}/progress`,
        method: 'POST',
        body: progressData,
      }),
    }),

    // Send risk alert
    sendRiskAlert: builder.mutation<any, { portfolioId: string; type: string; severity: string; message: string; data?: Record<string, any> }>({
      query: (alertData) => ({
        url: 'websocket/risk-alert',
        method: 'POST',
        body: alertData,
      }),
    }),

    // List WebSocket channels
    getWebSocketChannels: builder.query<any, void>({
      query: () => 'websocket/channels',
      providesTags: ['WebSocket'],
    }),
  }),
});

// Export hooks for use in components
export const {
  // Authentication hooks
  useLoginMutation,
  useLogoutMutation,
  useGetCurrentUserQuery,
  
  // Portfolio hooks
  useGetPortfoliosQuery,
  useGetPortfolioQuery,
  useGetPortfolioSummaryQuery,
  
  // Asset hooks
  useGetAssetsQuery,
  useGetAssetQuery,
  useGetAssetCorrelationsQuery,
  useGetAssetStatsQuery,
  useCreateAssetMutation,
  useUpdateAssetMutation,
  useDeleteAssetMutation,
  useGetAssetRiskMetricsQuery,
  
  // Waterfall calculation hooks
  useCalculateWaterfallMutation,
  useGetWaterfallHistoryQuery,
  
  // Risk analytics hooks
  useCalculateRiskMutation,
  useGetRiskHistoryQuery,
  
  // Scenario hooks
  useGetScenariosQuery,
  useCreateScenarioMutation,
  
  // Monitoring hooks
  useGetSystemHealthQuery,
  useGetMonitoringMetricsQuery,
  
  // Admin user management hooks
  useGetUsersQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeleteUserMutation,
  
  // Admin system alerts hooks
  useGetSystemAlertsQuery,
  useAcknowledgeAlertMutation,
  useDismissAlertMutation,
  
  // Admin audit log hooks
  useGetAuditLogsQuery,
  useExportAuditLogsMutation,
  
  // Admin system configuration hooks
  useGetSystemConfigurationsQuery,
  useUpdateSystemConfigurationMutation,
  
  // Admin statistics and reporting hooks
  useGetSystemStatisticsQuery,
  useGetUserActivityReportQuery,
  
  // Performance tracking hooks
  useGetPerformanceHistoryQuery,
  useGetPortfolioMetricsQuery,
  useGetBenchmarkDataQuery,
  
  // Portfolio management hooks
  useCreatePortfolioMutation,
  useUpdatePortfolioMutation,
  useDeletePortfolioMutation,
  
  // Portfolio asset management hooks
  useAddAssetToPortfolioMutation,
  useRemoveAssetFromPortfolioMutation,
  useUpdateAssetAllocationMutation,
  useBulkUpdateAssetsMutation,
  
  // Export hooks
  useExportPortfolioAssetsMutation,
  useExportPerformanceReportMutation,
  
  // === FINANCIAL ANALYST HOOKS ===
  
  // Waterfall analysis hooks
  useGetWaterfallAnalysisQuery,
  useRunWaterfallCalculationMutation,
  useGetWaterfallScenariosQuery,
  
  // Scenario modeling hooks
  useGetScenarioAnalysisQuery,
  useRunMonteCarloSimulationMutation,
  useRunStressTestMutation,
  useSaveScenarioConfigMutation,
  
  // Correlation analysis hooks
  useGetCorrelationMatrixQuery,
  useGetHighCorrelationPairsQuery,
  useGetRiskFactorAnalysisQuery,
  useGetDiversificationMetricsQuery,
  
  // CLO structuring hooks
  useGetCLOStructureQuery,
  useOptimizeCLOStructureMutation,
  useValidateStructuringConstraintsMutation,
  useUpdateTrancheStructureMutation,
  
  // Advanced risk analytics hooks
  useGetVaRAnalysisQuery,
  useGetBacktestResultsQuery,
  useRunModelValidationMutation,
  
  // Export hooks for analysts
  useExportWaterfallAnalysisMutation,
  useExportCorrelationMatrixMutation,
  useExportScenarioResultsMutation,
  
  // === NEW BACKEND API HOOKS ===
  
  // Document Management hooks
  useUploadDocumentMutation,
  useGetDocumentQuery,
  useDownloadDocumentMutation,
  useUpdateDocumentMutation,
  useDeleteDocumentMutation,
  useGetDocumentsQuery,
  useSearchDocumentsMutation,
  useGetDocumentStatsQuery,
  useBulkDocumentOperationMutation,
  
  // Enhanced Portfolio Analytics hooks
  useOptimizePortfolioMutation,
  useAnalyzePerformanceMutation,
  useAnalyzeRiskMutation,
  useAnalyzeConcentrationMutation,
  useGetAnalyticsStatsQuery,
  useGetQuickPortfolioMetricsQuery,
  useGeneratePortfolioAlertsMutation,
  
  // Enhanced User Management hooks
  useCreateUserEnhancedMutation,
  useGetUserByIdQuery,
  useUpdateUserEnhancedMutation,
  useDeleteUserEnhancedMutation,
  useGetUsersEnhancedQuery,
  useSearchUsersMutation,
  useChangePasswordMutation,
  useResetPasswordMutation,
  useGetUserPermissionsQuery,
  useGetUserStatsQuery,
  useBulkUserOperationMutation,
  useGetUserSessionsQuery,
  useGetUserActivityQuery,
  useGetUserPreferencesQuery,
  useUpdateUserPreferencesMutation,
  useImpersonateUserMutation,
  
  // Report Management hooks
  useCreateReportMutation,
  useGetReportByIdQuery,
  useGetReportsQuery,
  useDownloadReportMutation,
  useGetReportProgressQuery,
  useCancelReportMutation,
  useDeleteReportMutation,
  useGetReportTemplatesQuery,
  useGetReportTemplateQuery,
  useGetReportStatsQuery,
  
  // WebSocket Management hooks
  useGetWebSocketStatsQuery,
  useBroadcastMessageMutation,
  useSendUserNotificationMutation,
  useNotifyPortfolioSubscribersMutation,
  useUpdateCalculationProgressMutation,
  useSendRiskAlertMutation,
  useGetWebSocketChannelsQuery,
} = cloApi;

// Selector helpers for complex data transformations
export const selectPortfolioById = (portfolioId: string) => (state: any) =>
  cloApi.endpoints.getPortfolio.select(portfolioId)(state);

export const selectAssetById = (assetId: string) => (state: any) =>
  cloApi.endpoints.getAsset.select(assetId)(state);

// Cache utilities
export const invalidatePortfolioCache = (dispatch: any, portfolioId?: string) => {
  if (portfolioId) {
    dispatch(cloApi.util.invalidateTags([{ type: 'Portfolio', id: portfolioId }]));
  } else {
    dispatch(cloApi.util.invalidateTags(['Portfolio']));
  }
};

export const invalidateAssetCache = (dispatch: any) => {
  dispatch(cloApi.util.invalidateTags(['Asset', 'Correlation', 'Analytics']));
};

export const invalidateCalculationCache = (dispatch: any) => {
  dispatch(cloApi.util.invalidateTags(['Calculation', 'Risk', 'Analytics']));
};