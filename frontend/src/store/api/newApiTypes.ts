/**
 * New API Types and Interfaces for Backend Integration
 * Types for Document Management, Portfolio Analytics, User Management, and Reports
 */

// Document Management Types
export interface Document {
  document_id: string;
  filename: string;
  original_filename: string;
  title?: string;
  description?: string;
  document_type: DocumentType;
  file_size?: number;
  mime_type?: string;
  file_extension?: string;
  file_hash?: string;
  access_level: AccessLevel;
  owner_id?: string;
  portfolio_id?: string;
  tags: string[];
  status: DocumentStatus;
  version: string;
  is_latest_version: boolean;
  uploaded_at: string;
  updated_at: string;
  accessed_at?: string;
}

export type DocumentType = 
  | 'report'
  | 'legal_document'
  | 'financial_statement'
  | 'compliance_document'
  | 'asset_document'
  | 'portfolio_document'
  | 'waterfall_output'
  | 'analysis_result'
  | 'user_upload'
  | 'system_generated';

export type DocumentStatus = 
  | 'uploading'
  | 'processing'
  | 'active'
  | 'archived'
  | 'deleted'
  | 'quarantined';

export type AccessLevel = 
  | 'public'
  | 'internal'
  | 'confidential'
  | 'restricted';

export interface DocumentUploadRequest {
  title?: string;
  description?: string;
  document_type: DocumentType;
  access_level: AccessLevel;
  portfolio_id?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  tags: string[];
  metadata?: Record<string, any>;
}

export interface DocumentUpdateRequest {
  title?: string;
  description?: string;
  document_type?: DocumentType;
  access_level?: AccessLevel;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface DocumentSearchRequest {
  query?: string;
  document_type?: DocumentType;
  access_level?: AccessLevel;
  portfolio_id?: string;
  owner_id?: string;
  tags?: string[];
  date_from?: string;
  date_to?: string;
  min_size?: number;
  max_size?: number;
  limit: number;
  skip: number;
}

export interface DocumentStatsResponse {
  total_documents: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  by_access_level: Record<string, number>;
  total_size: number;
  recent_uploads: Document[];
  most_accessed: Document[];
}

// Portfolio Analytics Types
export interface PortfolioOptimizationRequest {
  portfolio_id: string;
  optimization_type: OptimizationType;
  constraints: Record<string, any>;
  target_volatility?: number;
  max_risk?: number;
  risk_free_rate: number;
  max_single_asset_weight: number;
  sector_limits?: Record<string, number>;
  rating_limits?: Record<string, number>;
  include_stress_testing: boolean;
  monte_carlo_runs: number;
  optimization_horizon: number;
}

export type OptimizationType = 
  | 'risk_minimization'
  | 'return_maximization'
  | 'sharpe_ratio'
  | 'compliance_optimization'
  | 'custom';

export interface PortfolioOptimizationResult {
  portfolio_id: string;
  optimization_date: string;
  optimization_type: OptimizationType;
  success: boolean;
  iterations: number;
  convergence_achieved: boolean;
  current_metrics: Record<string, number>;
  optimized_metrics: Record<string, number>;
  improvement_summary: Record<string, number>;
  recommended_sales: Array<Record<string, any>>;
  recommended_purchases: Array<Record<string, any>>;
  trade_impact: Record<string, number>;
  current_risk_metrics: Record<string, number>;
  optimized_risk_metrics: Record<string, number>;
  constraint_violations: string[];
  constraint_adherence: Record<string, boolean>;
}

export interface PortfolioPerformanceAnalysisRequest {
  portfolio_id: string;
  analysis_period: AnalysisPeriod;
  start_date?: string;
  end_date?: string;
  benchmark_type?: BenchmarkType;
  custom_benchmark_returns?: number[];
  include_attribution: boolean;
  include_risk_decomposition: boolean;
  include_sector_analysis: boolean;
  include_rating_migration: boolean;
}

export type AnalysisPeriod = '1M' | '3M' | '6M' | '1Y' | '2Y' | 'FULL' | 'CUSTOM';
export type BenchmarkType = 'clo_index' | 'high_yield' | 'investment_grade' | 'leveraged_loans' | 'custom';

export interface PortfolioPerformanceResult {
  portfolio_id: string;
  analysis_date: string;
  analysis_period: string;
  start_date: string;
  end_date: string;
  total_return: number;
  annualized_return: number;
  cumulative_return: number;
  period_returns: Array<Record<string, any>>;
  volatility: number;
  sharpe_ratio?: number;
  max_drawdown: number;
  var_95: number;
  var_99: number;
  benchmark_return?: number;
  excess_return?: number;
  tracking_error?: number;
  information_ratio?: number;
  sector_attribution?: Record<string, number>;
  security_attribution?: Record<string, number>;
  style_attribution?: Record<string, number>;
}

export interface PortfolioRiskAnalysisRequest {
  portfolio_id: string;
  confidence_levels: number[];
  time_horizons: number[];
  stress_scenarios: string[];
  custom_shocks?: Record<string, number>;
  include_correlation_breakdown: boolean;
  correlation_threshold: number;
}

export interface PortfolioRiskAnalysisResult {
  portfolio_id: string;
  analysis_date: string;
  var_results: Record<string, Record<string, number>>;
  expected_shortfall: Record<string, Record<string, number>>;
  stress_test_results: Record<string, number>;
  worst_case_scenario: string;
  worst_case_loss: number;
  sector_risk_contribution: Record<string, number>;
  asset_risk_contribution: Record<string, number>;
  marginal_var: Record<string, number>;
  high_correlation_pairs: Array<Record<string, any>>;
  correlation_clusters: string[][];
  diversification_ratio: number;
}

export interface ConcentrationAnalysisRequest {
  portfolio_id: string;
  analysis_dimensions: string[];
  single_asset_limit: number;
  sector_limit: number;
  rating_limits?: Record<string, number>;
  calculate_hhi: boolean;
  hhi_thresholds: Record<string, number>;
}

export interface ConcentrationAnalysisResult {
  portfolio_id: string;
  analysis_date: string;
  concentration_metrics: Record<string, Record<string, any>>;
  herfindahl_indices: Record<string, number>;
  concentration_levels: Record<string, string>;
  limit_violations: Array<Record<string, any>>;
  concentration_warnings: string[];
  diversification_opportunities: Array<Record<string, any>>;
  recommended_adjustments: Array<Record<string, any>>;
}

// User Management Types
export interface UserManagement {
  user_id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRoleType;
  status: UserStatusType;
  organization?: string;
  department?: string;
  title?: string;
  manager_id?: string;
  created_at: string;
  updated_at: string;
  last_login?: string;
  login_count: number;
  timezone: string;
  language: string;
  email_notifications: boolean;
  two_factor_enabled: boolean;
  is_active: boolean;
  days_since_last_login?: number;
}

export type UserRoleType = 'admin' | 'manager' | 'analyst' | 'viewer';
export type UserStatusType = 'active' | 'inactive' | 'suspended' | 'pending_activation' | 'locked';

export interface UserCreateRequest {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: UserRoleType;
  organization?: string;
  department?: string;
  phone?: string;
  title?: string;
  manager_id?: string;
  cost_center?: string;
  location?: string;
  timezone: string;
  language: string;
  send_welcome_email: boolean;
}

export interface UserUpdateRequest {
  email?: string;
  first_name?: string;
  last_name?: string;
  role?: UserRoleType;
  organization?: string;
  department?: string;
  phone?: string;
  title?: string;
  manager_id?: string;
  cost_center?: string;
  location?: string;
  timezone?: string;
  language?: string;
  status?: UserStatusType;
  email_notifications?: boolean;
  two_factor_enabled?: boolean;
}

export interface UserSearchRequest {
  query?: string;
  role?: UserRoleType;
  status?: UserStatusType;
  organization?: string;
  department?: string;
  created_after?: string;
  created_before?: string;
  last_login_after?: string;
  last_login_before?: string;
  skip: number;
  limit: number;
  sort_by: string;
  sort_order: 'asc' | 'desc';
}

export interface UserStatsResponse {
  total_users: number;
  active_users: number;
  by_role: Record<string, number>;
  by_status: Record<string, number>;
  by_organization: Record<string, number>;
  recent_registrations: UserManagement[];
  most_active_users: UserManagement[];
  daily_active_users: number;
  weekly_active_users: number;
  monthly_active_users: number;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface UserPermissionResponse {
  user_id: string;
  effective_permissions: Permission[];
  role_permissions: Permission[];
  direct_permissions: Permission[];
  can_read: string[];
  can_write: string[];
  can_delete: string[];
  can_admin: string[];
}

export interface Permission {
  permission_id: string;
  name: string;
  description: string;
  scope: PermissionScope;
  action: ActionType;
  resource_type: string;
  resource_id?: string;
}

export type PermissionScope = 'global' | 'organization' | 'portfolio' | 'asset';
export type ActionType = 'read' | 'write' | 'delete' | 'approve' | 'export' | 'admin';

export interface UserSessionResponse {
  user_id: string;
  session_id: string;
  created_at: string;
  last_activity: string;
  ip_address: string;
  user_agent: string;
  is_current: boolean;
  expires_at: string;
}

export interface UserActivityResponse {
  activity_id: string;
  user_id: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  timestamp: string;
  ip_address?: string;
  user_agent?: string;
  details?: Record<string, any>;
}

export interface UserPreferencesRequest {
  theme?: 'light' | 'dark' | 'auto';
  language?: string;
  timezone?: string;
  date_format?: string;
  number_format?: string;
  email_notifications?: boolean;
  desktop_notifications?: boolean;
  notification_frequency?: 'real-time' | 'daily' | 'weekly' | 'never';
  dashboard_layout?: Record<string, any>;
  default_portfolio?: string;
  favorite_reports?: string[];
}

export interface UserPreferencesResponse extends UserPreferencesRequest {
  user_id: string;
  updated_at: string;
}

// Report Management Types
export interface Report {
  report_id: string;
  report_name: string;
  report_type: ReportType;
  template_id?: string;
  parameters: Record<string, any>;
  filters: Record<string, any>;
  status: ReportStatus;
  output_format: ReportFormat;
  file_size?: number;
  page_count?: number;
  requested_at: string;
  started_at?: string;
  completed_at?: string;
  expires_at?: string;
  requested_by: string;
  organization?: string;
  error_message?: string;
  error_details?: Record<string, any>;
  file_path?: string;
  content_hash?: string;
  created_at: string;
  updated_at: string;
}

export type ReportType = 
  | 'portfolio_summary'
  | 'waterfall_analysis'
  | 'risk_assessment'
  | 'compliance_report'
  | 'performance_report'
  | 'concentration_report'
  | 'cash_flow_report'
  | 'asset_listing'
  | 'liability_schedule'
  | 'custom_report';

export type ReportStatus = 
  | 'queued'
  | 'generating'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type ReportFormat = 
  | 'pdf'
  | 'excel'
  | 'csv'
  | 'json'
  | 'html';

export interface ReportTemplate {
  template_id: string;
  template_name: string;
  report_type: ReportType;
  description?: string;
  default_parameters: Record<string, any>;
  required_parameters: Record<string, any>;
  optional_parameters: Record<string, any>;
  output_format: ReportFormat;
  created_by?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  is_system_template: boolean;
  template_definition?: string;
}

export interface ReportCreateRequest {
  report_name: string;
  report_type: ReportType;
  template_id?: string;
  parameters: Record<string, any>;
  filters?: Record<string, any>;
  output_format: ReportFormat;
  expires_at?: string;
}

export interface ReportGenerationProgress {
  report_id: string;
  status: ReportStatus;
  progress: number;
  current_stage: string;
  estimated_completion?: string;
  errors?: string[];
}

// WebSocket Types
export interface WebSocketMessage {
  type: WebSocketMessageType;
  timestamp: string;
  connection_id: string;
  data: Record<string, any>;
}

export type WebSocketMessageType = 
  | 'connect'
  | 'disconnect'
  | 'ping'
  | 'pong'
  | 'portfolio_update'
  | 'asset_change'
  | 'performance_update'
  | 'calculation_start'
  | 'calculation_progress'
  | 'calculation_complete'
  | 'calculation_error'
  | 'risk_alert'
  | 'concentration_breach'
  | 'compliance_warning'
  | 'notification'
  | 'system_message'
  | 'user_message'
  | 'document_uploaded'
  | 'document_shared'
  | 'market_data_update'
  | 'rate_change';

export interface WebSocketStats {
  total_connections: number;
  unique_users: number;
  channels: number;
  connections_by_user: Record<string, number>;
  subscribers_by_channel: Record<string, number>;
}

export interface NotificationData {
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  actions?: Array<Record<string, any>>;
  id: string;
}

export interface CalculationProgressData {
  calculation_id: string;
  progress: number;
  status: string;
  timestamp: string;
}

export interface RiskAlertData {
  portfolio_id: string;
  alert_type: string;
  severity: string;
  message: string;
  data: Record<string, any>;
  timestamp: string;
}

// Bulk Operation Types
export interface BulkOperationRequest {
  item_ids: string[];
  operation: string;
  parameters?: Record<string, any>;
  reason?: string;
}

export interface BulkOperationResponse {
  total_requested: number;
  successful: number;
  failed: number;
  errors: string[];
  processed_item_ids: string[];
}