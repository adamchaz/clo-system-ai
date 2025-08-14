// Base props for analytics components
export interface BaseAnalyticsProps {
  portfolioId?: string;
  onPortfolioChange?: (portfolioId: string) => void;
}

// Component-specific props
export interface WaterfallAnalysisProps extends BaseAnalyticsProps {
  // Additional waterfall-specific props can be added here
}

export interface ScenarioModelingProps extends BaseAnalyticsProps {
  // Additional scenario modeling-specific props can be added here  
}

export interface CorrelationAnalysisProps extends BaseAnalyticsProps {
  // Additional correlation analysis-specific props can be added here
}

export interface CLOStructuringProps {
  dealId?: string;
  onDealChange?: (dealId: string) => void;
}

// Analytics data types
export interface WaterfallStep {
  step: number;
  description: string;
  amount: number;
  cumulativeAmount: number;
  status: 'paid' | 'partial' | 'unpaid';
  priority: number;
}

export interface ScenarioResult {
  scenarioName: string;
  defaultRate: number;
  recoveryRate: number;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  probability: number;
  status: 'completed' | 'running' | 'failed';
}

export interface CorrelationData {
  asset1: string;
  asset2: string;
  correlation: number;
  pValue: number;
  significance: 'high' | 'medium' | 'low';
}

export interface TrancheStructure {
  id: string;
  name: string;
  rating: string;
  size: number;
  coupon: number;
  spread: number;
  subordination: number;
  maturity: string;
  callable: boolean;
}