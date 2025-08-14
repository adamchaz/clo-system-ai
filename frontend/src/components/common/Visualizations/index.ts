/**
 * TASK 13: Advanced Data Visualization Components
 * 
 * Comprehensive visualization component library for CLO Management System
 * 
 * Components:
 * - CorrelationHeatmap: Interactive D3.js correlation matrix visualization
 * - RiskVisualization: VaR, stress testing, and risk analytics
 * - PerformanceChart: Time series performance analysis with benchmarking
 * - PortfolioComposition: Asset allocation and sector distribution charts
 * - WaterfallChart: CLO payment waterfall visualization with MAG scenarios
 * 
 * Features:
 * - Real-time data integration with WebSocket updates
 * - Interactive D3.js and Recharts visualizations
 * - Export functionality for all charts
 * - TypeScript interfaces for type safety
 * - Responsive design with Material-UI integration
 */

// Component exports
export { default as CorrelationHeatmap } from './CorrelationHeatmap';
export type { CorrelationHeatmapProps, CorrelationData, CorrelationMatrix } from './CorrelationHeatmap';

export { default as RiskVisualization } from './RiskVisualization';
export type { RiskVisualizationProps } from './RiskVisualization';

export { default as PerformanceChart } from './PerformanceChart';
export type { PerformanceChartProps } from './PerformanceChart';

export { default as PortfolioComposition } from './PortfolioComposition';
export type { PortfolioCompositionProps } from './PortfolioComposition';

export { default as WaterfallChart } from './WaterfallChart';
export type { WaterfallChartProps } from './WaterfallChart';

// Re-export common visualization types
export * from './types';