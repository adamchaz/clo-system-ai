/**
 * Real-time Components Export - TASK 12 Implementation
 * 
 * Central export for all real-time WebSocket-enabled components:
 * - ConnectionStatusIndicator: WebSocket connection management
 * - RealTimeNotifications: Live alerts and notification system  
 * - CalculationProgressTracker: Live calculation monitoring
 * 
 * Part of CLO Management System - TASK 12: Real-time Data and WebSocket Integration
 */

export { default as ConnectionStatusIndicator } from './ConnectionStatusIndicator';
export { default as RealTimeNotifications } from './RealTimeNotifications';
export { default as CalculationProgressTracker } from './CalculationProgressTracker';

// Re-export real-time hooks for convenience
export {
  useConnectionStatus,
  useRealTimePortfolio,
  useRealTimeAssets,
  useCalculationProgress,
  useSystemAlerts,
  useRealTime,
} from '../../../hooks/useRealTimeData';

// Export real-time types
export type {
  ConnectionStatus,
  RealTimePortfolioData,
  RealTimeAssetUpdate,
  CalculationProgress,
  SystemAlert,
} from '../../../hooks/useRealTimeData';