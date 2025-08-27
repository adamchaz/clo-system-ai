/**
 * New API Endpoints for Backend Integration
 * Additional endpoints for Document Management, Portfolio Analytics, User Management, and Reports
 */

import { EndpointBuilder } from '@reduxjs/toolkit/query';
import { ApiResponse, PaginatedResponse } from './cloApi';
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
  ConcentrationTestRequest,
  ConcentrationTestResult,
  // User Management Types
  UserManagement,
  UserCreateRequest,
  UserUpdateRequest,
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
  // Bulk Operations
  BulkOperationRequest,
  BulkOperationResponse,
} from './newApiTypes';

// Define the new API endpoints to add to the existing cloApi
export const newApiEndpoints = (builder: EndpointBuilder<any, any, any>) => ({
  
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
  // PORTFOLIO ANALYTICS ENDPOINTS
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

  // Real Concentration Tests (using backend ConcentrationTestIntegrationService)
  runConcentrationTests: builder.mutation<ConcentrationTestResult, ConcentrationTestRequest>({
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
  // USER MANAGEMENT ENDPOINTS
  // ===========================================

  // Create user
  createUser: builder.mutation<ApiResponse<UserManagement>, UserCreateRequest>({
    query: (userData) => ({
      url: 'users/',
      method: 'POST',
      body: userData,
    }),
    invalidatesTags: ['User'],
  }),

  // Get user by ID
  getUserById: builder.query<ApiResponse<UserManagement>, string>({
    query: (userId) => `users/${userId}`,
    providesTags: (result, error, id) => [{ type: 'User' as const, id }],
  }),

  // Update user
  updateUser: builder.mutation<ApiResponse<UserManagement>, { userId: string; update: UserUpdateRequest }>({
    query: ({ userId, update }) => ({
      url: `users/${userId}`,
      method: 'PUT',
      body: update,
    }),
    invalidatesTags: (result, error, { userId }) => [{ type: 'User' as const, id: userId }],
  }),

  // Delete user
  deleteUser: builder.mutation<void, string>({
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
    providesTags: (result, error, userId) => [{ type: 'User' as const, id: userId }],
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
    providesTags: (result, error, userId) => [{ type: 'User' as const, id: userId }],
  }),

  // Get user activity
  getUserActivity: builder.query<ApiResponse<UserActivityResponse[]>, { userId: string; limit?: number }>({
    query: ({ userId, limit = 50 }) => ({
      url: `users/${userId}/activity`,
      params: { limit },
    }),
    providesTags: (result, error, { userId }) => [{ type: 'User' as const, id: userId }],
  }),

  // Get user preferences
  getUserPreferences: builder.query<ApiResponse<UserPreferencesResponse>, string>({
    query: (userId) => `users/${userId}/preferences`,
    providesTags: (result, error, userId) => [{ type: 'User' as const, id: userId }],
  }),

  // Update user preferences
  updateUserPreferences: builder.mutation<ApiResponse<UserPreferencesResponse>, { userId: string; preferences: UserPreferencesRequest }>({
    query: ({ userId, preferences }) => ({
      url: `users/${userId}/preferences`,
      method: 'PUT',
      body: preferences,
    }),
    invalidatesTags: (result, error, { userId }) => [{ type: 'User' as const, id: userId }],
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

});

export default newApiEndpoints;