/**
 * RealTimeNotifications Component - Live Notification System
 * 
 * Displays real-time notifications with different priority levels:
 * - Toast notifications for immediate alerts
 * - Persistent notification center for important updates
 * - Real-time asset price changes and portfolio updates
 * - System alerts and calculation completion notifications
 * 
 * Part of CLO Management System - TASK 12: Real-time Data and WebSocket Integration
 */
import React, { useState, useMemo } from 'react';
import {
  Box,
  Badge,
  IconButton,
  Drawer,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Button,
  Chip,
  Alert,
  Divider,
  Tooltip,
  Paper,
  Stack,
  Avatar,
} from '@mui/material';
import {
  Notifications,
  NotificationsActive,
  Close,
  CheckCircle,
  Warning,
  Error,
  Info,
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Assessment,
  Schedule,
  Clear,
  MarkAsUnread,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';
import { 
  useSystemAlerts, 
  useUserNotifications, 
  useAssetUpdates,
  useRiskAlerts,
  useWebSocketConnection 
} from '../../../hooks/useWebSocket';
import { useAppSelector } from '../../../store/hooks';
import { NotificationData, RiskAlertData } from '../../../store/api/newApiTypes';

interface RealTimeNotificationsProps {
  maxVisible?: number;
  autoHideDelay?: number;
  showAssetUpdates?: boolean;
}

const RealTimeNotifications: React.FC<RealTimeNotificationsProps> = ({
  maxVisible = 5,
  autoHideDelay = 5000,
  showAssetUpdates: showAssetUpdatesProp = true,
}) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showToasts, setShowToasts] = useState(true);
  const [showAssetUpdates, setShowAssetUpdates] = useState(showAssetUpdatesProp);
  
  // Get current user info
  const currentUser = useAppSelector(state => state.auth.user);
  const { status: connectionStatus } = useWebSocketConnection();
  
  // Local state for managing notifications
  const [notifications, setNotifications] = useState<any[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // WebSocket subscriptions
  useSystemAlerts((alertData) => {
    const notification = {
      id: `system_${Date.now()}`,
      type: alertData.severity || 'info',
      title: alertData.title || 'System Alert',
      message: alertData.message,
      timestamp: new Date().toISOString(),
      category: 'system',
      severity: alertData.severity || 'medium',
      read: false,
    };
    
    setNotifications(prev => [notification, ...prev].slice(0, 50)); // Keep last 50
    setUnreadCount(prev => prev + 1);
  });
  
  useUserNotifications(currentUser?.id || null, (notificationData: NotificationData) => {
    const notification = {
      id: notificationData.id,
      type: notificationData.severity,
      title: notificationData.title,
      message: notificationData.message,
      timestamp: new Date().toISOString(),
      category: 'user',
      severity: notificationData.severity || 'medium',
      read: false,
    };
    
    setNotifications(prev => [notification, ...prev].slice(0, 50));
    setUnreadCount(prev => prev + 1);
  });
  
  useRiskAlerts(null, (riskData: RiskAlertData) => {
    const notification = {
      id: `risk_${riskData.portfolio_id}_${Date.now()}`,
      type: riskData.severity,
      title: `Risk Alert - ${riskData.alert_type}`,
      message: riskData.message,
      timestamp: riskData.timestamp,
      category: 'risk',
      severity: riskData.severity || 'medium',
      read: false,
    };
    
    setNotifications(prev => [notification, ...prev].slice(0, 50));
    setUnreadCount(prev => prev + 1);
  });
  
  useAssetUpdates((assetData) => {
    if (showAssetUpdates) {
      const notification = {
        id: `asset_${Date.now()}`,
        type: 'info',
        title: 'Asset Update',
        message: `Asset ${assetData.cusip || 'Unknown'} has been updated`,
        timestamp: new Date().toISOString(),
        category: 'asset',
        severity: 'low',
        read: false,
      };
      
      setNotifications(prev => [notification, ...prev].slice(0, 50));
      setUnreadCount(prev => prev + 1);
    }
  });

  // Sort notifications by timestamp
  const allNotifications = useMemo(() => {
    return notifications.sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [notifications]);

  const criticalAlerts = notifications.filter(n => ['critical', 'high'].includes(n.severity) && !n.read);
  const hasUnread = unreadCount > 0 || criticalAlerts.length > 0;

  const getNotificationIcon = (type: string, category: string) => {
    if (category === 'asset') {
      return <AccountBalance />;
    }
    
    switch (type) {
      case 'success':
        return <CheckCircle color="success" />;
      case 'warning':
        return <Warning color="warning" />;
      case 'error':
        return <Error color="error" />;
      default:
        return <Info color="info" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  const getSeverityChip = (severity: string) => {
    const config = {
      critical: { color: 'error' as const, label: 'Critical' },
      high: { color: 'error' as const, label: 'High' },
      medium: { color: 'warning' as const, label: 'Medium' },
      low: { color: 'default' as const, label: 'Low' },
    };
    
    const severityConfig = config[severity as keyof typeof config] || config.low;
    
    return (
      <Chip
        label={severityConfig.label}
        color={severityConfig.color}
        size="small"
        variant="outlined"
      />
    );
  };

  const handleToggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  const markAsRead = (notificationId: string) => {
    setNotifications(prev => prev.map(n => n.id === notificationId ? { ...n, read: true } : n));
    setUnreadCount(prev => Math.max(0, prev - 1));
  };
  
  const dismissAlert = (notificationId: string) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId));
    const notification = notifications.find(n => n.id === notificationId);
    if (notification && !notification.read) {
      setUnreadCount(prev => Math.max(0, prev - 1));
    }
  };
  
  const handleMarkAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  const handleClearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  return (
    <>
      {/* Notification Icon Button */}
      <Tooltip title="Notifications">
        <IconButton 
          onClick={handleToggleDrawer}
          color={hasUnread ? 'primary' : 'default'}
        >
          <Badge 
            badgeContent={unreadCount} 
            color="error"
            overlap="circular"
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            {hasUnread ? <NotificationsActive /> : <Notifications />}
          </Badge>
        </IconButton>
      </Tooltip>

      {/* Critical Alerts Toast */}
      {showToasts && criticalAlerts.length > 0 && (
        <Box
          sx={{
            position: 'fixed',
            top: 80,
            right: 16,
            zIndex: 1400,
            maxWidth: 400,
          }}
        >
          <Stack spacing={1}>
            {criticalAlerts.slice(0, maxVisible).map((alert) => (
              <Alert
                key={alert.id}
                severity={getNotificationColor(alert.type)}
                action={
                  <IconButton
                    size="small"
                    onClick={() => dismissAlert(alert.id)}
                  >
                    <Close fontSize="small" />
                  </IconButton>
                }
                sx={{ 
                  boxShadow: 3,
                  '& .MuiAlert-message': {
                    width: '100%',
                  },
                }}
              >
                <Box>
                  <Typography variant="body2" fontWeight={600}>
                    {alert.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {alert.message}
                  </Typography>
                </Box>
              </Alert>
            ))}
          </Stack>
        </Box>
      )}

      {/* Notification Drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={handleToggleDrawer}
        PaperProps={{
          sx: { width: 400 },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6">
                Notifications ({unreadCount})
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Connection: {connectionStatus}
              </Typography>
            </Box>
            <Box>
              <Tooltip title="Mark All Read">
                <IconButton size="small" onClick={handleMarkAllRead}>
                  <MarkAsUnread fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Clear All">
                <IconButton size="small" onClick={handleClearAll}>
                  <Clear fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Close">
                <IconButton size="small" onClick={handleToggleDrawer}>
                  <Close fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {/* Toggle Controls */}
          <Box sx={{ mb: 2 }}>
            <Button
              size="small"
              variant={showToasts ? 'contained' : 'outlined'}
              onClick={() => setShowToasts(!showToasts)}
              sx={{ mr: 1 }}
            >
              Toast Alerts: {showToasts ? 'On' : 'Off'}
            </Button>
            <Button
              size="small"
              variant={showAssetUpdates ? 'contained' : 'outlined'}
              onClick={() => setShowAssetUpdates(!showAssetUpdates)}
            >
              Asset Updates: {showAssetUpdates ? 'On' : 'Off'}
            </Button>
          </Box>
          
          {connectionStatus !== 'connected' && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              WebSocket connection is {connectionStatus}. Some notifications may be delayed.
            </Alert>
          )}

          <Divider sx={{ mb: 2 }} />
        </Box>

        {/* Notifications List */}
        {allNotifications.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Notifications sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              No notifications
            </Typography>
          </Box>
        ) : (
          <List sx={{ flex: 1, overflow: 'auto' }}>
            {allNotifications.map((notification, index) => (
              <React.Fragment key={notification.id}>
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    bgcolor: notification.read ? 'transparent' : 'action.hover',
                    cursor: 'pointer',
                  }}
                  onClick={() => markAsRead(notification.id)}
                >
                  <ListItemIcon>
                    <Avatar sx={{ width: 32, height: 32 }}>
                      {getNotificationIcon(notification.type, notification.category)}
                    </Avatar>
                  </ListItemIcon>
                  
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Typography variant="body2" fontWeight={600}>
                          {notification.title}
                        </Typography>
                        {getSeverityChip(notification.severity)}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          {notification.message}
                        </Typography>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                          <Chip
                            label={notification.category}
                            size="small"
                            variant="outlined"
                          />
                          <Typography variant="caption" color="text.secondary">
                            {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                  
                  <ListItemSecondaryAction>
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        dismissAlert(notification.id);
                      }}
                    >
                      <Close fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
                
                {index < allNotifications.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Drawer>
    </>
  );
};

export default RealTimeNotifications;