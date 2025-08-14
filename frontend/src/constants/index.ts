// Application constants

export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

// Local storage keys
export const STORAGE_KEYS = {
  TOKEN: 'clo_token',
  REFRESH_TOKEN: 'clo_refresh_token',
  USER: 'clo_user',
  THEME: 'clo_theme',
  SIDEBAR_STATE: 'clo_sidebar_state',
} as const;

// User roles and permissions
export const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  ANALYST: 'analyst',
  VIEWER: 'viewer',
} as const;

export const ROLE_LABELS = {
  [USER_ROLES.ADMIN]: 'System Administrator',
  [USER_ROLES.MANAGER]: 'Portfolio Manager',
  [USER_ROLES.ANALYST]: 'Financial Analyst',
  [USER_ROLES.VIEWER]: 'Viewer',
} as const;

// Navigation paths
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  PORTFOLIOS: '/portfolios',
  PORTFOLIO_DETAIL: '/portfolios/:id',
  ASSETS: '/assets',
  CALCULATIONS: '/calculations',
  RISK_ANALYTICS: '/risk-analytics',
  REPORTS: '/reports',
  MONITORING: '/monitoring',
  SETTINGS: '/settings',
  UNAUTHORIZED: '/unauthorized',
} as const;

// API endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    ME: '/api/v1/auth/me',
  },
  PORTFOLIOS: {
    LIST: '/portfolios',
    DETAIL: '/portfolios/:id',
    CREATE: '/portfolios',
    UPDATE: '/portfolios/:id',
    DELETE: '/portfolios/:id',
    ASSETS: '/portfolios/:id/assets',
  },
  ASSETS: {
    LIST: '/assets',
    DETAIL: '/assets/:id',
    CREATE: '/assets',
    UPDATE: '/assets/:id',
    DELETE: '/assets/:id',
    CORRELATIONS: '/assets/correlations',
  },
  CALCULATIONS: {
    WATERFALL: '/calculations/waterfall',
    STRESS_TEST: '/calculations/stress-test',
    VAR: '/calculations/var',
    SCENARIO: '/calculations/scenario',
    HISTORY: '/calculations/history',
    STATUS: '/calculations/:id/status',
  },
  MONITORING: {
    HEALTH: '/monitoring/health',
    METRICS: '/monitoring/metrics',
    ALERTS: '/monitoring/alerts',
    AUDIT: '/monitoring/audit',
  },
  REPORTS: {
    LIST: '/reports',
    GENERATE: '/reports/generate',
    DOWNLOAD: '/reports/:id/download',
    TEMPLATES: '/reports/templates',
  },
} as const;

// Data table configurations
export const TABLE_CONFIG = {
  DEFAULT_PAGE_SIZE: 25,
  PAGE_SIZE_OPTIONS: [10, 25, 50, 100],
  MAX_ROWS_WITHOUT_VIRTUALIZATION: 100,
} as const;

// Chart configurations
export const CHART_CONFIG = {
  DEFAULT_HEIGHT: 400,
  COLORS: {
    PRIMARY: '#1565c0',
    SECONDARY: '#2e7d32',
    TERTIARY: '#d32f2f',
    QUATERNARY: '#ed6c02',
    NEUTRAL: '#757575',
  },
  FINANCIAL_COLORS: {
    POSITIVE: '#2e7d32',
    NEGATIVE: '#d32f2f',
    NEUTRAL: '#757575',
  },
} as const;

// Notification settings
export const NOTIFICATION_CONFIG = {
  DEFAULT_DURATION: 5000,
  ERROR_DURATION: 10000,
  SUCCESS_DURATION: 3000,
  MAX_NOTIFICATIONS: 5,
} as const;

// Asset ratings
export const ASSET_RATINGS = {
  INVESTMENT_GRADE: ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-'],
  HIGH_YIELD: ['BB+', 'BB', 'BB-', 'B+', 'B', 'B-', 'CCC+', 'CCC', 'CCC-', 'CC', 'C'],
  DEFAULT: ['D'],
} as const;

// Industry classifications
export const INDUSTRIES = {
  TECHNOLOGY: 'Technology',
  HEALTHCARE: 'Healthcare',
  FINANCIAL: 'Financial Services',
  ENERGY: 'Energy',
  UTILITIES: 'Utilities',
  INDUSTRIALS: 'Industrials',
  MATERIALS: 'Materials',
  CONSUMER_DISCRETIONARY: 'Consumer Discretionary',
  CONSUMER_STAPLES: 'Consumer Staples',
  TELECOMMUNICATIONS: 'Telecommunications',
  REAL_ESTATE: 'Real Estate',
} as const;

// Calculation types
export const CALCULATION_TYPES = {
  WATERFALL: 'waterfall',
  STRESS_TEST: 'stress_test',
  VAR: 'var',
  SCENARIO: 'scenario',
  CONCENTRATION: 'concentration',
} as const;

// MAG versions
export const MAG_VERSIONS = [
  'Mag6', 'Mag7', 'Mag8', 'Mag9', 'Mag10',
  'Mag11', 'Mag12', 'Mag13', 'Mag14', 'Mag15',
  'Mag16', 'Mag17'
] as const;

// File upload settings
export const FILE_UPLOAD = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ACCEPTED_TYPES: {
    EXCEL: ['.xlsx', '.xls'],
    CSV: ['.csv'],
    PDF: ['.pdf'],
    IMAGES: ['.png', '.jpg', '.jpeg'],
  },
} as const;

// Form validation
export const VALIDATION = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PASSWORD_MIN_LENGTH: 8,
  NAME_MIN_LENGTH: 2,
  NAME_MAX_LENGTH: 50,
} as const;

export default {};