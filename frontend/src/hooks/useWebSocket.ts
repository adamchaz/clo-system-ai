/**
 * React hooks for WebSocket integration
 * Provides easy-to-use hooks for components to subscribe to real-time updates
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { 
  websocketService, 
  WebSocketMessage,
  PortfolioUpdatePayload,
  DocumentUpdatePayload,
  ReportUpdatePayload,
  UserActivityPayload
} from '../services/websocketService';
import {
  NotificationData,
  CalculationProgressData,
  RiskAlertData
} from '../store/api/newApiTypes';

// Connection status hook
export const useWebSocketConnection = () => {
  const [status, setStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');
  const [subscriptions, setSubscriptions] = useState<{ id: string; channel: string }[]>([]);

  useEffect(() => {
    // Set up polling for connection status
    const interval = setInterval(() => {
      setStatus(websocketService.getConnectionStatus());
      setSubscriptions(websocketService.getActiveSubscriptions());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const reconnect = useCallback(() => {
    websocketService.reconnect();
  }, []);

  return {
    status,
    subscriptions,
    reconnect
  };
};

// Generic subscription hook
export const useWebSocketSubscription = <T = any>(
  channel: string,
  callback: (data: T) => void,
  dependencies: any[] = [],
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);
  const callbackRef = useRef(callback);

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Subscribe to the channel
    subscriptionIdRef.current = websocketService.subscribe(channel, (message) => {
      callbackRef.current(message as T);
    });

    // Cleanup subscription on unmount or dependency change
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [channel, enabled, ...dependencies]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// Portfolio updates hook
export const usePortfolioUpdates = (
  portfolioId: string | null,
  callback: (data: PortfolioUpdatePayload) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!portfolioId || !enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToPortfolio(portfolioId, callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [portfolioId, enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// Calculation progress hook
export const useCalculationProgress = (
  calculationId: string | null,
  callback: (data: CalculationProgressData) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!calculationId || !enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToCalculationProgress(calculationId, callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [calculationId, enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// Document updates hook
export const useDocumentUpdates = (
  callback: (data: DocumentUpdatePayload) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToDocuments(callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// Report updates hook
export const useReportUpdates = (
  reportId: string | null,
  callback: (data: ReportUpdatePayload) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToReports(reportId || undefined, callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [reportId, enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// Risk alerts hook
export const useRiskAlerts = (
  portfolioId: string | null,
  callback: (data: RiskAlertData) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToRiskAlerts(portfolioId || undefined, callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [portfolioId, enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// User notifications hook
export const useUserNotifications = (
  userId: string | null,
  callback: (data: NotificationData) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToNotifications(userId || undefined, callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [userId, enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// System alerts hook
export const useSystemAlerts = (
  callback: (data: any) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToSystemAlerts(callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// User activity hook (for admin)
export const useUserActivity = (
  callback: (data: UserActivityPayload) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToUserActivity(callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// Asset updates hook
export const useAssetUpdates = (
  callback: (data: any) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToAssets(callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// Market data updates hook
export const useMarketDataUpdates = (
  callback: (data: any) => void,
  enabled: boolean = true
) => {
  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    subscriptionIdRef.current = websocketService.subscribeToMarketData(callback);

    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
        subscriptionIdRef.current = null;
      }
    };
  }, [enabled]);

  useEffect(() => {
    return () => {
      if (subscriptionIdRef.current) {
        websocketService.unsubscribe(subscriptionIdRef.current);
      }
    };
  }, []);
};

// Real-time data hook with state management
export const useRealTimeData = <T = any>(
  channel: string,
  initialData: T | null = null,
  enabled: boolean = true
) => {
  const [data, setData] = useState<T | null>(initialData);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useWebSocketSubscription<WebSocketMessage>(
    channel,
    useCallback((message: WebSocketMessage) => {
      setData(message.data || message.payload);
      setLastUpdate(message.timestamp);
    }, []),
    [],
    enabled
  );

  useEffect(() => {
    const interval = setInterval(() => {
      setIsConnected(websocketService.getConnectionStatus() === 'connected');
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return {
    data,
    lastUpdate,
    isConnected,
    refresh: () => {
      // Could trigger a manual refresh if needed
      console.log(`Refresh requested for channel: ${channel}`);
    }
  };
};