// Common types used throughout the application

export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

export type UserRole = 'admin' | 'manager' | 'analyst' | 'viewer';

export interface UserPermissions {
  canViewPortfolios: boolean;
  canEditPortfolios: boolean;
  canCreatePortfolios: boolean;
  canDeletePortfolios: boolean;
  canExecuteCalculations: boolean;
  canViewSystemMetrics: boolean;
  canManageUsers: boolean;
  canExportData: boolean;
  canViewReports: boolean;
  canCreateReports: boolean;
}

export interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon: React.ComponentType;
  requiredRoles?: UserRole[];
  children?: NavigationItem[];
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

export interface PaginationParams {
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface FilterParams {
  search?: string;
  filters: Record<string, any>;
}

export interface ListResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// Financial data types
export interface FinancialMetric {
  label: string;
  value: number;
  formatted: string;
  change?: number;
  changeFormatted?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
  category?: string;
}

export interface PerformanceData {
  nav: ChartDataPoint[];
  irr: ChartDataPoint[];
  moic: ChartDataPoint[];
  yield: ChartDataPoint[];
}

// Asset specific types
export interface AssetFilter {
  rating?: string[];
  industry?: string[];
  country?: string[];
  maturityRange?: {
    start: string;
    end: string;
  };
  parAmountRange?: {
    min: number;
    max: number;
  };
}

// Portfolio specific types
export interface PortfolioSummary {
  totalAssets: number;
  totalValue: number;
  avgRating: string;
  maturityProfile: {
    short: number;
    medium: number;
    long: number;
  };
  industryDiversification: {
    name: string;
    percentage: number;
  }[];
}

// Calculation types
export interface CalculationRequest {
  portfolioId: string;
  calculationType: 'waterfall' | 'stress_test' | 'var' | 'scenario';
  parameters: Record<string, any>;
  magVersion?: string;
}

export interface CalculationResult {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  startTime: string;
  endTime?: string;
  results?: Record<string, any>;
  error?: string;
}

export default {};