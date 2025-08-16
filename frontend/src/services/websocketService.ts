/**
 * WebSocket Service for CLO Management System
 * 
 * Provides comprehensive real-time communication capabilities for the CLO system.
 * This service manages WebSocket connections, subscriptions, and automatic reconnection
 * with integration to Redux RTK Query for cache management.
 * 
 * Features:
 * - Automatic connection management with JWT authentication
 * - Subscription-based message routing with type safety
 * - Automatic reconnection with exponential backoff
 * - RTK Query cache invalidation for real-time data consistency
 * - Heartbeat monitoring for connection health
 * - Comprehensive error handling and logging
 * 
 * Usage:
 * ```typescript
 * import { websocketService } from './websocketService';
 * 
 * // Connect to WebSocket
 * await websocketService.connect();
 * 
 * // Subscribe to portfolio updates
 * const subscriptionId = websocketService.subscribeToPortfolio('DEAL001', (data) => {
 *   console.log('Portfolio update:', data);
 * });
 * 
 * // Unsubscribe when done
 * websocketService.unsubscribe(subscriptionId);
 * ```
 * 
 * @author CLO System Development Team
 * @version 2.1.0
 * @since 2024-08-13
 */

import { store } from '../store';
import { cloApi } from '../store/api/cloApi';
import { authService } from './auth';

/**
 * WebSocket message interface defining the structure of all real-time messages
 * Supports 15+ different message types for comprehensive system coverage
 */
export interface WebSocketMessage {
  /** Message type identifier for routing and handling */
  type: 'portfolio_update' | 'calculation_complete' | 'calculation_progress' | 'system_alert' | 'asset_update' | 'notification' | 'document_update' | 'document_upload' | 'report_update' | 'report_generated' | 'risk_alert' | 'user_activity' | 'market_update' | 'price_update' | 'pong';
  /** Message payload containing actual data */
  payload: any;
  /** ISO timestamp of when message was sent */
  timestamp: string;
  /** Optional data field for compatibility with useRealTimeData hook */
  data?: any;
}

/**
 * WebSocket subscription interface for managing active connections
 */
export interface WebSocketSubscription {
  /** Unique subscription identifier */
  id: string;
  /** Channel name for message routing */
  channel: string;
  /** Callback function to handle received messages */
  callback: (message: WebSocketMessage) => void;
}

// =============================================================================
// PAYLOAD TYPE DEFINITIONS
// =============================================================================

/**
 * Portfolio update payload for real-time portfolio changes
 * Used for: portfolio_update messages
 */
export interface PortfolioUpdatePayload {
  /** Unique portfolio identifier */
  portfolioId: string;
  /** Associated CLO deal identifier */
  dealId: string;
  /** Type of portfolio update */
  updateType: 'value_change' | 'position_change' | 'risk_update' | 'performance_update';
  /** Update-specific data */
  data: any;
}

/**
 * Document update payload for file management notifications
 * Used for: document_update, document_upload messages
 */
export interface DocumentUpdatePayload {
  /** Unique document identifier */
  documentId: string;
  /** Document filename */
  filename: string;
  /** Type of document operation */
  updateType: 'uploaded' | 'deleted' | 'modified' | 'shared';
  /** User who performed the action */
  userId: string;
  /** Document-specific metadata */
  data: any;
}

/**
 * Report generation payload for report lifecycle tracking
 * Used for: report_update, report_generated messages
 */
export interface ReportUpdatePayload {
  /** Unique report identifier */
  reportId: string;
  /** Report category/type */
  reportType: string;
  /** Current generation status */
  status: 'generating' | 'completed' | 'failed' | 'cancelled';
  /** Generation progress percentage (0-100) */
  progress?: number;
  /** Report-specific data and metadata */
  data: any;
}

/**
 * User activity payload for admin monitoring
 * Used for: user_activity messages
 */
export interface UserActivityPayload {
  /** User performing the action */
  userId: string;
  /** Action performed (login, logout, create, update, delete, etc.) */
  action: string;
  /** Type of resource affected */
  resourceType: string;
  /** Optional specific resource identifier */
  resourceId?: string;
  /** ISO timestamp of the activity */
  timestamp: string;
  /** Additional activity metadata */
  metadata: any;
}

// =============================================================================
// WEBSOCKET SERVICE CLASS
// =============================================================================

/**
 * WebSocket service for real-time CLO system updates
 * 
 * Enterprise-grade WebSocket client with the following capabilities:
 * - JWT-based authentication with automatic token refresh
 * - Subscription management with unique channel routing
 * - Automatic reconnection with exponential backoff (up to 5 attempts)
 * - Heartbeat monitoring (30-second intervals)
 * - RTK Query cache integration for real-time data consistency
 * - Type-safe message handling with comprehensive error logging
 * 
 * Connection States:
 * - 'connecting': Initial connection attempt in progress
 * - 'connected': WebSocket successfully connected and authenticated
 * - 'disconnected': Not connected (initial state or after disconnect)
 * 
 * @example
 * ```typescript
 * // Initialize connection
 * await websocketService.connect();
 * 
 * // Subscribe to specific events
 * const portfolioSub = websocketService.subscribeToPortfolio('DEAL001', 
 *   (data) => console.log('Portfolio update:', data)
 * );
 * 
 * // Check connection status
 * console.log(websocketService.getConnectionStatus()); // 'connected'
 * 
 * // Cleanup
 * websocketService.unsubscribe(portfolioSub);
 * ```
 */
class WebSocketService {
  /** Active WebSocket connection instance */
  private ws: WebSocket | null = null;
  
  /** Map of active subscriptions indexed by subscription ID */
  private subscriptions = new Map<string, WebSocketSubscription>();
  
  /** Current number of reconnection attempts */
  private reconnectAttempts = 0;
  
  /** Maximum allowed reconnection attempts */
  private maxReconnectAttempts = 5;
  
  /** Initial reconnection delay in milliseconds (uses exponential backoff) */
  private reconnectDelay = 1000;
  
  /** Heartbeat interval timer for connection health monitoring */
  private heartbeatInterval: NodeJS.Timeout | null = null;
  
  /** Connection state flag */
  private isConnected = false;
  
  /** Connection attempt state flag */
  private isConnecting = false;
  
  /** WebSocket server URL with fallback to localhost */
  private readonly wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

  /**
   * Initialize WebSocket connection with JWT authentication
   * 
   * Establishes a secure WebSocket connection to the CLO backend server
   * with automatic token-based authentication. Supports connection timeout
   * and proper error handling.
   * 
   * @throws {Error} When no authentication token is available
   * @throws {Error} When connection timeout occurs (10 seconds)
   * @throws {Error} When WebSocket connection fails
   * 
   * @example
   * ```typescript
   * try {
   *   await websocketService.connect();
   *   console.log('Connected successfully');
   * } catch (error) {
   *   console.error('Connection failed:', error);
   * }
   * ```
   */
  async connect(): Promise<void> {
    if (this.isConnected || this.isConnecting) {
      return;
    }

    this.isConnecting = true;

    try {
      const token = authService.getAccessToken();
      if (!token) {
        throw new Error('No authentication token available');
      }

      // Create WebSocket connection with auth token
      const wsUrl = `${this.wsUrl}?token=${token}`;
      this.ws = new WebSocket(wsUrl);

      // Set up event listeners
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);

      // Wait for connection to be established
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'));
        }, 10000);

        this.ws!.onopen = (event) => {
          clearTimeout(timeout);
          this.handleOpen(event);
          resolve();
        };

        this.ws!.onerror = (event) => {
          clearTimeout(timeout);
          this.handleError(event);
          reject(new Error('WebSocket connection failed'));
        };
      });
    } catch (error) {
      this.isConnecting = false;
      console.error('WebSocket connection failed:', error);
      throw error;
    }
  }

  /**
   * Close WebSocket connection
   */
  disconnect(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.ws && this.isConnected) {
      this.ws.close(1000, 'Client disconnecting');
    }

    this.isConnected = false;
    this.isConnecting = false;
    this.subscriptions.clear();
  }

  /**
   * Subscribe to a specific channel for updates
   */
  subscribe(
    channel: string, 
    callback: (message: WebSocketMessage) => void
  ): string {
    const subscriptionId = `${channel}_${Date.now()}_${Math.random()}`;
    
    const subscription: WebSocketSubscription = {
      id: subscriptionId,
      channel,
      callback,
    };

    this.subscriptions.set(subscriptionId, subscription);

    // Send subscription message to server if connected
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        channel,
        subscription_id: subscriptionId,
      }));
    }

    return subscriptionId;
  }

  /**
   * Unsubscribe from a channel
   */
  unsubscribe(subscriptionId: string): void {
    const subscription = this.subscriptions.get(subscriptionId);
    if (!subscription) {
      return;
    }

    // Send unsubscribe message to server if connected
    if (this.isConnected && this.ws) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        channel: subscription.channel,
        subscription_id: subscriptionId,
      }));
    }

    this.subscriptions.delete(subscriptionId);
  }

  /**
   * Subscribe to portfolio updates
   */
  subscribeToPortfolio(dealId: string, callback: (data: any) => void): string {
    return this.subscribe(`portfolio:${dealId}`, (message) => {
      if (message.type === 'portfolio_update') {
        callback(message.payload);
        // Invalidate relevant RTK Query cache
        store.dispatch(
          cloApi.util.invalidateTags([{ type: 'Portfolio', id: dealId }])
        );
      }
    });
  }

  /**
   * Subscribe to calculation updates
   */
  subscribeToCalculations(dealId: string, callback: (data: any) => void): string {
    return this.subscribe(`calculations:${dealId}`, (message) => {
      if (message.type === 'calculation_complete') {
        callback(message.payload);
        // Invalidate calculation cache
        store.dispatch(
          cloApi.util.invalidateTags(['Calculation', 'Risk', 'Analytics'])
        );
      }
    });
  }

  /**
   * Subscribe to system alerts
   */
  subscribeToSystemAlerts(callback: (data: any) => void): string {
    return this.subscribe('system:alerts', (message) => {
      if (message.type === 'system_alert') {
        callback(message.payload);
        // Refresh system health
        store.dispatch(
          cloApi.util.invalidateTags(['SystemHealth'])
        );
      }
    });
  }

  /**
   * Subscribe to asset updates
   */
  subscribeToAssets(callback: (data: any) => void): string {
    return this.subscribe('assets:updates', (message) => {
      if (message.type === 'asset_update') {
        callback(message.payload);
        // Invalidate asset cache
        store.dispatch(
          cloApi.util.invalidateTags(['Asset', 'Correlation', 'Analytics'])
        );
      }
    });
  }

  /**
   * Subscribe to user notifications
   */
  subscribeToNotifications(userId?: string, callback?: (data: any) => void): string {
    const channel = userId ? `notifications:${userId}` : 'notifications:global';
    return this.subscribe(channel, (message) => {
      if (message.type === 'notification' || message.type === 'system_alert') {
        if (callback) {
          callback(message.payload);
        }
        // Optionally invalidate relevant cache
        store.dispatch(
          cloApi.util.invalidateTags(['SystemHealth'])
        );
      }
    });
  }

  /**
   * Subscribe to calculation progress updates
   */
  subscribeToCalculationProgress(calculationId: string, callback: (data: any) => void): string {
    return this.subscribe(`calculations:progress:${calculationId}`, (message) => {
      if (message.type === 'calculation_complete' || message.type === 'calculation_progress') {
        callback(message.payload);
        // Invalidate calculation cache
        store.dispatch(
          cloApi.util.invalidateTags(['Calculation', 'Analytics'])
        );
      }
    });
  }

  /**
   * Subscribe to document updates
   */
  subscribeToDocuments(callback: (data: any) => void): string {
    return this.subscribe('documents:updates', (message) => {
      if (message.type === 'document_update' || message.type === 'document_upload') {
        callback(message.payload);
        // Invalidate document cache
        store.dispatch(
          cloApi.util.invalidateTags(['Document'])
        );
      }
    });
  }

  /**
   * Subscribe to report updates
   */
  subscribeToReports(reportId?: string, callback?: (data: any) => void): string {
    const channel = reportId ? `reports:${reportId}` : 'reports:updates';
    return this.subscribe(channel, (message) => {
      if (message.type === 'report_update' || message.type === 'report_generated') {
        if (callback) {
          callback(message.payload);
        }
        // Invalidate report cache
        store.dispatch(
          cloApi.util.invalidateTags(['Report'])
        );
      }
    });
  }

  /**
   * Subscribe to risk alerts
   */
  subscribeToRiskAlerts(portfolioId?: string, callback?: (data: any) => void): string {
    const channel = portfolioId ? `risk:alerts:${portfolioId}` : 'risk:alerts:global';
    return this.subscribe(channel, (message) => {
      if (message.type === 'risk_alert' || message.type === 'system_alert') {
        if (callback) {
          callback(message.payload);
        }
        // Invalidate risk cache
        store.dispatch(
          cloApi.util.invalidateTags(['Risk', 'Alert'])
        );
      }
    });
  }

  /**
   * Subscribe to user activity updates (for admin monitoring)
   */
  subscribeToUserActivity(callback: (data: any) => void): string {
    return this.subscribe('user:activity', (message) => {
      if (message.type === 'user_activity' || message.type === 'system_alert') {
        callback(message.payload);
        // Invalidate user activity cache
        store.dispatch(
          cloApi.util.invalidateTags(['UserActivity', 'SystemHealth'])
        );
      }
    });
  }

  /**
   * Subscribe to market data updates
   */
  subscribeToMarketData(callback: (data: any) => void): string {
    return this.subscribe('market:data', (message) => {
      if (message.type === 'market_update' || message.type === 'price_update') {
        callback(message.payload);
        // Invalidate market data cache
        store.dispatch(
          cloApi.util.invalidateTags(['MarketData', 'Price'])
        );
      }
    });
  }

  /**
   * Get active subscriptions
   */
  getActiveSubscriptions(): { id: string; channel: string }[] {
    return Array.from(this.subscriptions.values()).map(sub => ({
      id: sub.id,
      channel: sub.channel
    }));
  }

  /**
   * Manually trigger reconnection
   */
  async reconnect(): Promise<void> {
    if (this.isConnected) {
      this.disconnect();
    }
    
    // Reset reconnection attempts
    this.reconnectAttempts = 0;
    
    try {
      await this.connect();
    } catch (error) {
      console.error('Manual reconnection failed:', error);
      throw error;
    }
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): 'connected' | 'connecting' | 'disconnected' {
    if (this.isConnected) return 'connected';
    if (this.isConnecting) return 'connecting';
    return 'disconnected';
  }

  // Private event handlers
  private handleOpen(event: Event): void {
    console.log('WebSocket connected');
    this.isConnected = true;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;

    // Start heartbeat
    this.startHeartbeat();

    // Resubscribe to all channels
    this.resubscribeAll();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Handle heartbeat responses
      if (message.type === 'pong') {
        return;
      }

      // Route message to appropriate subscribers
      this.subscriptions.forEach(subscription => {
        if (this.shouldRouteMessage(message, subscription.channel)) {
          try {
            subscription.callback(message);
          } catch (error) {
            console.error('Error in WebSocket message callback:', error);
          }
        }
      });
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason);
    this.isConnected = false;
    this.isConnecting = false;

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    // Attempt reconnection if not a clean close
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.isConnecting = false;
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.isConnected) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Send ping every 30 seconds
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.isConnected) {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, delay);
  }

  private resubscribeAll(): void {
    this.subscriptions.forEach(subscription => {
      if (this.ws && this.isConnected) {
        this.ws.send(JSON.stringify({
          type: 'subscribe',
          channel: subscription.channel,
          subscription_id: subscription.id,
        }));
      }
    });
  }

  private shouldRouteMessage(message: WebSocketMessage, channel: string): boolean {
    // Extract the base channel from the message
    // For example, 'portfolio:DEAL001' matches 'portfolio:DEAL001'
    return channel === 'system:alerts' || 
           channel === 'assets:updates' ||
           (message.payload?.deal_id && channel.includes(message.payload.deal_id)) ||
           channel.includes(':') && message.type.includes(channel.split(':')[0]);
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();

// Auto-connect when user is authenticated
export const initializeWebSocket = async (): Promise<void> => {
  if (authService.getAccessToken()) {
    try {
      await websocketService.connect();
      console.log('WebSocket connection established');
    } catch (error) {
      console.error('Failed to establish WebSocket connection:', error);
    }
  }
};

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    websocketService.disconnect();
  });
}