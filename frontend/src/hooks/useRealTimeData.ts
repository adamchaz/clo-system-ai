/**
 * Real-time Data Hooks - TASK 12 Implementation
 * 
 * Provides comprehensive real-time data integration for CLO Management System:
 * - WebSocket connection management and status tracking
 * - Real-time portfolio and asset updates
 * - Live calculation progress monitoring
 * - System alerts and notifications
 * 
 * Part of CLO Management System - TASK 12: Real-time Data and WebSocket Integration
 * Enterprise-grade real-time system with automatic reconnection and error handling
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useAppDispatch } from './reduxHooks';
import { websocketService, WebSocketMessage } from '../services/websocketService';
import { showNotification } from '../store/slices/uiSlice';

// Connection status type
export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

// Real-time data types
export interface RealTimePortfolioData {
  dealId: string;
  totalValue: number;
  assetCount: number;
  riskMetrics: {
    var: number;
    stressTest: number;
    correlationRisk: number;
  };
  lastUpdate: string;
}

export interface RealTimeAssetUpdate {
  assetId: string;
  cusip: string;
  priceChange: number;
  newPrice: number;
  performanceChange: number;
  lastUpdate: string;
}

export interface CalculationProgress {
  calculationId: string;
  type: 'waterfall' | 'risk' | 'correlation' | 'scenario';
  progress: number;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  estimatedTime?: number;
  message?: string;
}

export interface SystemAlert {
  id: string;
  type: 'error' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
  category: 'system' | 'portfolio' | 'asset' | 'calculation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  autoHide?: boolean;
  read?: boolean; // Add read property for notification management
}

/**
 * Hook for managing WebSocket connection status
 */
export const useConnectionStatus = () => {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastConnected, setLastConnected] = useState<Date | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  
  useEffect(() => {
    const checkStatus = () => {
      const wsStatus = websocketService.getConnectionStatus();
      setStatus(wsStatus === 'connected' ? 'connected' : 
               wsStatus === 'connecting' ? 'connecting' : 'disconnected');
      
      if (wsStatus === 'connected' && status !== 'connected') {
        setLastConnected(new Date());
        setReconnectAttempts(0);
      }
    };

    // Check status initially and then periodically
    checkStatus();
    const interval = setInterval(checkStatus, 1000);
    
    return () => clearInterval(interval);
  }, [status]);

  const connect = useCallback(async () => {
    try {
      setStatus('connecting');
      await websocketService.connect();
      setStatus('connected');
      setLastConnected(new Date());
    } catch (error) {
      setStatus('error');
      setReconnectAttempts(prev => prev + 1);
    }
  }, []);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
    setStatus('disconnected');
  }, []);

  return {
    status,
    lastConnected,
    reconnectAttempts,
    connect,
    disconnect,
    isConnected: status === 'connected',
  };
};

/**
 * Hook for real-time portfolio data
 */
export const useRealTimePortfolio = (dealId: string | null) => {
  const [portfolioData, setPortfolioData] = useState<RealTimePortfolioData | null>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const subscriptionRef = useRef<string | null>(null);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!dealId) return;

    const handlePortfolioUpdate = (data: RealTimePortfolioData) => {
      setPortfolioData(data);
      dispatch(showNotification({
        message: `Portfolio ${dealId} updated`,
        type: 'info',
        autoHide: true,
      }));
    };

    // Subscribe to portfolio updates
    subscriptionRef.current = websocketService.subscribeToPortfolio(dealId, handlePortfolioUpdate);
    setIsSubscribed(true);

    return () => {
      if (subscriptionRef.current) {
        websocketService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
      setIsSubscribed(false);
    };
  }, [dealId, dispatch]);

  return {
    portfolioData,
    isSubscribed,
  };
};

/**
 * Hook for real-time asset updates
 */
export const useRealTimeAssets = () => {
  const [assetUpdates, setAssetUpdates] = useState<RealTimeAssetUpdate[]>([]);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const subscriptionRef = useRef<string | null>(null);
  const dispatch = useAppDispatch();

  useEffect(() => {
    const handleAssetUpdate = (data: RealTimeAssetUpdate) => {
      setAssetUpdates(prev => {
        // Keep only last 100 updates for performance
        const updates = [data, ...prev.slice(0, 99)];
        return updates;
      });

      // Show notification for significant price changes
      if (Math.abs(data.priceChange) > 5) { // 5% change threshold
        dispatch(showNotification({
          message: `${data.cusip} price ${data.priceChange > 0 ? 'increased' : 'decreased'} by ${Math.abs(data.priceChange).toFixed(2)}%`,
          type: data.priceChange > 0 ? 'success' : 'warning',
          autoHide: true,
        }));
      }
    };

    subscriptionRef.current = websocketService.subscribeToAssets(handleAssetUpdate);
    setIsSubscribed(true);

    return () => {
      if (subscriptionRef.current) {
        websocketService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
      setIsSubscribed(false);
    };
  }, [dispatch]);

  const getAssetUpdate = useCallback((assetId: string) => {
    return assetUpdates.find(update => update.assetId === assetId);
  }, [assetUpdates]);

  const clearUpdates = useCallback(() => {
    setAssetUpdates([]);
  }, []);

  return {
    assetUpdates,
    isSubscribed,
    getAssetUpdate,
    clearUpdates,
  };
};

/**
 * Hook for real-time calculation progress
 */
export const useCalculationProgress = () => {
  const [calculations, setCalculations] = useState<Map<string, CalculationProgress>>(new Map());
  const subscriptionRef = useRef<string | null>(null);
  const dispatch = useAppDispatch();

  useEffect(() => {
    const handleCalculationUpdate = (data: CalculationProgress) => {
      setCalculations(prev => {
        const newCalculations = new Map(prev);
        newCalculations.set(data.calculationId, data);
        return newCalculations;
      });

      // Show completion notifications
      if (data.status === 'completed') {
        dispatch(showNotification({
          message: `${data.type} calculation completed successfully`,
          type: 'success',
          autoHide: true,
        }));
      } else if (data.status === 'failed') {
        dispatch(showNotification({
          message: `${data.type} calculation failed: ${data.message || 'Unknown error'}`,
          type: 'error',
          autoHide: false,
        }));
      }
    };

    subscriptionRef.current = websocketService.subscribeToCalculations('all', handleCalculationUpdate);

    return () => {
      if (subscriptionRef.current) {
        websocketService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
    };
  }, [dispatch]);

  const getCalculation = useCallback((calculationId: string) => {
    return calculations.get(calculationId);
  }, [calculations]);

  const getActiveCalculations = useCallback(() => {
    return Array.from(calculations.values()).filter(calc => calc.status === 'running');
  }, [calculations]);

  const clearCompleted = useCallback(() => {
    setCalculations(prev => {
      const newCalculations = new Map();
      prev.forEach((calc, id) => {
        if (calc.status === 'running') {
          newCalculations.set(id, calc);
        }
      });
      return newCalculations;
    });
  }, []);

  return {
    calculations: Array.from(calculations.values()),
    getCalculation,
    getActiveCalculations,
    clearCompleted,
  };
};

/**
 * Hook for system alerts and notifications
 */
export const useSystemAlerts = () => {
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const subscriptionRef = useRef<string | null>(null);
  const dispatch = useAppDispatch();

  useEffect(() => {
    const handleSystemAlert = (data: SystemAlert) => {
      setAlerts(prev => {
        // Keep only last 50 alerts for performance
        const newAlerts = [data, ...prev.slice(0, 49)];
        return newAlerts;
      });

      setUnreadCount(prev => prev + 1);

      // Show UI notification based on severity
      dispatch(showNotification({
        message: data.message,
        type: data.type,
        autoHide: data.severity === 'low' || data.autoHide,
      }));
    };

    subscriptionRef.current = websocketService.subscribeToSystemAlerts(handleSystemAlert);

    return () => {
      if (subscriptionRef.current) {
        websocketService.unsubscribe(subscriptionRef.current);
        subscriptionRef.current = null;
      }
    };
  }, [dispatch]);

  const markAsRead = useCallback((alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, read: true } : alert
    ));
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);

  const markAllAsRead = useCallback(() => {
    setAlerts(prev => prev.map(alert => ({ ...alert, read: true })));
    setUnreadCount(0);
  }, []);

  const dismissAlert = useCallback((alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);

  const clearAll = useCallback(() => {
    setAlerts([]);
    setUnreadCount(0);
  }, []);

  const getCriticalAlerts = useCallback(() => {
    return alerts.filter(alert => alert.severity === 'critical');
  }, [alerts]);

  return {
    alerts,
    unreadCount,
    markAsRead,
    markAllAsRead,
    dismissAlert,
    clearAll,
    getCriticalAlerts,
  };
};

/**
 * Combined hook for all real-time functionality
 */
export const useRealTime = (dealId?: string) => {
  const connectionStatus = useConnectionStatus();
  const portfolioData = useRealTimePortfolio(dealId || null);
  const assetUpdates = useRealTimeAssets();
  const calculationProgress = useCalculationProgress();
  const systemAlerts = useSystemAlerts();

  // Auto-connect when component mounts
  useEffect(() => {
    if (!connectionStatus.isConnected && connectionStatus.status === 'disconnected') {
      connectionStatus.connect();
    }
  }, [connectionStatus]);

  return {
    connection: connectionStatus,
    portfolio: portfolioData,
    assets: assetUpdates,
    calculations: calculationProgress,
    alerts: systemAlerts,
  };
};