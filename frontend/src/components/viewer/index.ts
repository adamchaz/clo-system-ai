// Viewer Dashboard Components
export { default as PortfolioSummaryView } from './PortfolioSummaryView';
export { default as BasicReportsView } from './BasicReportsView';
export { default as PerformanceOverview } from './PerformanceOverview';

// Types for viewer components
export interface ViewerPermissions {
  canViewPortfolios: boolean;
  canAccessReports: boolean;
  canExportData: boolean;
  canViewPerformance: boolean;
}

export interface ViewerDashboardConfig {
  showAllPortfolios: boolean;
  enableExport: boolean;
  defaultTimeframe: '1M' | '3M' | '6M' | '1Y' | 'YTD';
  maxPortfolioDisplay: number;
}