/**
 * TASK 13: Advanced Data Visualization Components
 * 
 * TypeScript interfaces and types for visualization components
 */

// Base visualization types
export interface BaseVisualizationProps {
  portfolioId?: string;
  enableRealTime?: boolean;
  height?: number;
  width?: number;
  showControls?: boolean;
}

// Chart data interfaces
export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
  category?: string;
  metadata?: Record<string, any>;
}

export interface TimeSeriesData extends ChartDataPoint {
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
}

// Financial data types
export interface FinancialMetric {
  name: string;
  value: number;
  change?: number;
  changePercent?: number;
  trend?: 'up' | 'down' | 'neutral';
  benchmark?: number;
  currency?: string;
  timestamp?: string;
}

export interface RiskMetric extends FinancialMetric {
  confidenceLevel?: number;
  timeHorizon?: string;
  methodology?: string;
}

// Portfolio composition types
export interface AssetAllocation {
  category: string;
  value: number;
  weight: number;
  count?: number;
  color?: string;
  subcategories?: AssetAllocation[];
}

export interface Holding {
  symbol: string;
  name: string;
  value: number;
  weight: number;
  shares?: number;
  price?: number;
  sector?: string;
  assetType?: string;
  geography?: string;
  currency?: string;
  lastUpdate?: string;
}

// Risk analysis types
export interface VaRCalculation {
  confidenceLevel: number;
  timeHorizon: number;
  value: number;
  methodology: 'historical' | 'parametric' | 'monte_carlo';
  currency: string;
  asOf: string;
}

export interface StressTestScenario {
  id: string;
  name: string;
  description: string;
  probability: number;
  impact: number;
  portfolioValue: number;
  loss: number;
  recoveryTime?: number;
}

// Performance analysis types
export interface PerformanceMetrics {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  sortinoRatio?: number;
  maxDrawdown: number;
  winRate: number;
  alpha?: number;
  beta?: number;
  informationRatio?: number;
  trackingError?: number;
  calmarRatio?: number;
}

export interface BenchmarkData {
  symbol: string;
  name: string;
  values: TimeSeriesData[];
  metrics: PerformanceMetrics;
}

// Correlation analysis types
export interface CorrelationPair {
  asset1: string;
  asset2: string;
  correlation: number;
  pValue?: number;
  confidenceInterval?: [number, number];
  period?: string;
}

export interface CorrelationMatrixData {
  assets: string[];
  correlations: number[][];
  metadata: {
    asOf: string;
    period: string;
    method: string;
    assetTypes?: Record<string, string>;
    sectors?: Record<string, string>;
  };
}

// CLO Waterfall types
export interface WaterfallStep {
  id: string;
  name: string;
  type: 'income' | 'expense' | 'interest' | 'principal' | 'residual' | 'fees';
  priority: number;
  amount: number;
  cumulative: number;
  percentage: number;
  description: string;
  tranche?: string;
  status: 'paid' | 'deferred' | 'unpaid' | 'partial';
  dueDate?: string;
  paymentDate?: string;
}

export interface CLOTranche {
  tranche: string;
  notional: number;
  outstandingPrincipal: number;
  coupon: number;
  spread: number;
  rating: string;
  maturityDate: string;
  interestDue: number;
  principalDue: number;
  interestPaid: number;
  principalPaid: number;
  cumulativeLosses?: number;
  recoveries?: number;
}

export interface WaterfallCalculation {
  dealId: string;
  paymentDate: string;
  scenario: string;
  totalAvailableFunds: number;
  totalDistributed: number;
  remainingCash: number;
  steps: WaterfallStep[];
  tranches: CLOTranche[];
  triggers: {
    ocTests: { [key: string]: { value: number; threshold: number; passing: boolean } };
    icTests: { [key: string]: { value: number; threshold: number; passing: boolean } };
  };
  notes?: string[];
}

// Chart configuration types
export interface ChartTheme {
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    background: string;
    text: string;
  };
  fonts: {
    family: string;
    size: {
      small: number;
      medium: number;
      large: number;
    };
  };
}

export interface ChartAnimation {
  enabled: boolean;
  duration: number;
  easing: string;
  delay?: number;
}

export interface ChartExportOptions {
  format: 'png' | 'jpg' | 'pdf' | 'svg';
  filename?: string;
  quality?: number;
  width?: number;
  height?: number;
  background?: string;
}

// Real-time data types
export interface RealTimeUpdate {
  type: 'portfolio' | 'asset' | 'calculation' | 'alert';
  timestamp: string;
  data: any;
  source?: string;
}

export interface CalculationProgress {
  calculationType: 'waterfall' | 'risk' | 'correlation' | 'scenario';
  progress: number;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: string;
  endTime?: string;
  details?: string;
  errors?: string[];
}

// Error handling types
export interface VisualizationError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
  component: string;
}

// Utility types
export type TimeFrame = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'YTD' | 'All';
export type CurrencyCode = 'USD' | 'EUR' | 'GBP' | 'JPY' | 'CHF' | 'CAD';
export type AssetType = 'Equity' | 'Bond' | 'Cash' | 'Alternative' | 'Commodity' | 'Currency';
export type RiskMeasure = 'VaR' | 'CVaR' | 'Volatility' | 'Beta' | 'Duration' | 'DV01';
export type MAGScenario = 'MAG6' | 'MAG7' | 'MAG8' | 'MAG9' | 'MAG10' | 'MAG11' | 'MAG12' | 'MAG13' | 'MAG14' | 'MAG15' | 'MAG16' | 'MAG17';