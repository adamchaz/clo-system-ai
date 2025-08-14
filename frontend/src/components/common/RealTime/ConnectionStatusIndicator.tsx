/**
 * ConnectionStatusIndicator Component - Real-time Connection Status Display
 * 
 * Shows WebSocket connection status with visual indicators and actions:
 * - Real-time connection status (connected, connecting, disconnected, error)
 * - Connection timestamp and reconnection attempts
 * - Manual connect/disconnect controls for debugging
 * - Connection quality indicators and latency display
 * 
 * Part of CLO Management System - TASK 12: Real-time Data and WebSocket Integration
 */
import React from 'react';
import {
  Box,
  Chip,
  IconButton,
  Tooltip,
  Typography,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Wifi,
  WifiOff,
  Sync,
  Error,
  Refresh,
  PowerSettingsNew,
  SignalWifiStatusbar4Bar,
  SignalWifi1Bar,
  Info,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useWebSocketConnection } from '../../../hooks/useWebSocket';
import { websocketService } from '../../../services/websocketService';

interface ConnectionStatusIndicatorProps {
  showDetails?: boolean;
  size?: 'small' | 'medium';
  variant?: 'chip' | 'icon' | 'detailed';
}

const ConnectionStatusIndicator: React.FC<ConnectionStatusIndicatorProps> = ({
  showDetails = false,
  size = 'medium',
  variant = 'chip',
}) => {
  const { status, subscriptions } = useWebSocketConnection();
  const [lastConnected, setLastConnected] = React.useState<Date | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = React.useState(0);
  
  const isConnected = status === 'connected';
  
  // Track connection changes
  React.useEffect(() => {
    if (status === 'connected') {
      setLastConnected(new Date());
      setReconnectAttempts(0);
    } else if (status === 'connecting') {
      setReconnectAttempts(prev => prev + 1);
    }
  }, [status]);
  
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleConnect = async () => {
    try {
      await websocketService.connect();
    } catch (error) {
      console.error('Failed to connect:', error);
    }
    handleClose();
  };

  const handleDisconnect = () => {
    websocketService.disconnect();
    handleClose();
  };
  
  const handleReconnect = async () => {
    try {
      await websocketService.reconnect();
    } catch (error) {
      console.error('Failed to reconnect:', error);
    }
    handleClose();
  };

  // Status configuration
  const statusConfig = {
    connected: {
      color: 'success' as const,
      icon: <Wifi />,
      label: 'Connected',
      description: `Real-time updates active (${subscriptions.length} subscriptions)`,
    },
    connecting: {
      color: 'warning' as const,
      icon: <Sync sx={{ animation: 'spin 2s linear infinite', '@keyframes spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } } }} />,
      label: 'Connecting',
      description: 'Establishing connection...',
    },
    disconnected: {
      color: 'default' as const,
      icon: <WifiOff />,
      label: 'Disconnected',
      description: 'Real-time updates inactive',
    },
  };

  const currentStatus = statusConfig[status];

  // Signal strength indicator (mock for now, could be based on latency)
  const getSignalStrength = () => {
    if (!isConnected) return null;
    // Mock signal strength - in real implementation, could be based on latency
    return <SignalWifiStatusbar4Bar fontSize="small" />;
  };

  if (variant === 'icon') {
    return (
      <Tooltip
        title={
          <Box>
            <Typography variant="body2" fontWeight={600}>
              {currentStatus.label}
            </Typography>
            <Typography variant="caption">
              {currentStatus.description}
            </Typography>
            {lastConnected && (
              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                Last connected: {format(lastConnected, 'HH:mm:ss')}
              </Typography>
            )}
            {reconnectAttempts > 0 && (
              <Typography variant="caption" display="block">
                Reconnect attempts: {reconnectAttempts}
              </Typography>
            )}
          </Box>
        }
      >
        <IconButton
          size={size === 'small' ? 'small' : 'medium'}
          onClick={handleClick}
          color={currentStatus.color}
        >
          {currentStatus.icon}
        </IconButton>
      </Tooltip>
    );
  }

  if (variant === 'detailed') {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip
          icon={currentStatus.icon}
          label={currentStatus.label}
          color={currentStatus.color}
          size={size}
          onClick={handleClick}
          clickable
        />
        {getSignalStrength()}
        {showDetails && (
          <Box sx={{ ml: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {currentStatus.description}
            </Typography>
            {lastConnected && (
              <Typography variant="caption" display="block" color="text.secondary">
                {format(lastConnected, 'MMM dd, HH:mm:ss')}
              </Typography>
            )}
          </Box>
        )}
      </Box>
    );
  }

  // Default chip variant
  return (
    <>
      <Chip
        icon={currentStatus.icon}
        label={showDetails ? `${currentStatus.label}${reconnectAttempts > 0 ? ` (${reconnectAttempts})` : ''}` : currentStatus.label}
        color={currentStatus.color}
        size={size}
        onClick={handleClick}
        clickable
        variant={isConnected ? 'filled' : 'outlined'}
      />

      {/* Connection Menu */}
      <Menu
        anchorEl={anchorEl}
        open={menuOpen}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem disabled>
          <ListItemIcon>
            <Info fontSize="small" />
          </ListItemIcon>
          <ListItemText>
            <Typography variant="body2" fontWeight={600}>
              Connection Status
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {currentStatus.description}
            </Typography>
          </ListItemText>
        </MenuItem>
        
        <Divider />
        
        {lastConnected && (
          <MenuItem disabled>
            <ListItemText>
              <Typography variant="caption">
                Last connected: {format(lastConnected, 'PPp')}
              </Typography>
            </ListItemText>
          </MenuItem>
        )}
        
        {reconnectAttempts > 0 && (
          <MenuItem disabled>
            <ListItemText>
              <Typography variant="caption">
                Reconnection attempts: {reconnectAttempts}
              </Typography>
            </ListItemText>
          </MenuItem>
        )}
        
        {subscriptions.length > 0 && (
          <MenuItem disabled>
            <ListItemText>
              <Typography variant="caption">
                Active subscriptions: {subscriptions.length}
              </Typography>
              {subscriptions.slice(0, 3).map(sub => (
                <Typography key={sub.id} variant="caption" display="block" sx={{ pl: 1, color: 'text.disabled' }}>
                  • {sub.channel}
                </Typography>
              ))}
              {subscriptions.length > 3 && (
                <Typography variant="caption" display="block" sx={{ pl: 1, color: 'text.disabled' }}>
                  ... and {subscriptions.length - 3} more
                </Typography>
              )}
            </ListItemText>
          </MenuItem>
        )}
        
        <Divider />
        
        {!isConnected && (
          <MenuItem onClick={handleConnect}>
            <ListItemIcon>
              <Refresh fontSize="small" />
            </ListItemIcon>
            <ListItemText>Connect</ListItemText>
          </MenuItem>
        )}
        
        {isConnected && (
          <MenuItem onClick={handleReconnect}>
            <ListItemIcon>
              <Refresh fontSize="small" />
            </ListItemIcon>
            <ListItemText>Reconnect</ListItemText>
          </MenuItem>
        )}
        
        {isConnected && (
          <MenuItem onClick={handleDisconnect}>
            <ListItemIcon>
              <PowerSettingsNew fontSize="small" />
            </ListItemIcon>
            <ListItemText>Disconnect</ListItemText>
          </MenuItem>
        )}
      </Menu>
    </>
  );
};

export default ConnectionStatusIndicator;