import React from 'react';
import {
  Box,
  Chip,
  Avatar,
  Typography,
  Tooltip,
  CircularProgress,
  IconButton,
  Badge,
  alpha,
  keyframes,
  useTheme,
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Warning,
  Info,
  Schedule,
  Cancel,
  HelpOutline,
  Refresh,
  Circle,
  FiberManualRecord,
  SignalCellular4Bar,
  SignalCellular3Bar,
  SignalCellular2Bar,
  SignalCellular1Bar,
  SignalCellularOff,
} from '@mui/icons-material';

export type StatusType = 
  | 'online' | 'offline' | 'error' | 'warning' | 'info'
  | 'success' | 'pending' | 'loading' | 'unknown'
  | 'healthy' | 'degraded' | 'critical' | 'maintenance'
  | 'active' | 'inactive' | 'matured' | 'defaulted';

export type StatusVariant = 
  | 'dot' | 'chip' | 'badge' | 'icon' | 'signal' | 'detailed';

export type StatusSize = 'small' | 'medium' | 'large';

export interface StatusIndicatorProps {
  status: StatusType;
  variant?: StatusVariant;
  size?: StatusSize;
  label?: string;
  description?: string;
  timestamp?: string | Date;
  showLabel?: boolean;
  showTimestamp?: boolean;
  showRefresh?: boolean;
  animated?: boolean;
  clickable?: boolean;
  count?: number;
  maxCount?: number;
  color?: string;
  onRefresh?: () => void;
  onClick?: () => void;
  className?: string;
  sx?: any;
}

// Animation keyframes
const pulse = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
`;

const blink = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.3; }
  100% { opacity: 1; }
`;

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  variant = 'dot',
  size = 'medium',
  label,
  description,
  timestamp,
  showLabel = true,
  showTimestamp = false,
  showRefresh = false,
  animated = true,
  clickable = false,
  count,
  maxCount = 99,
  color: customColor,
  onRefresh,
  onClick,
  className,
  sx = {},
}) => {
  const theme = useTheme();

  // Status configuration
  const statusConfig = {
    online: {
      color: theme.palette.success.main,
      icon: CheckCircle,
      label: label || 'Online',
      bgColor: theme.palette.success.light,
    },
    offline: {
      color: theme.palette.grey[500],
      icon: Cancel,
      label: label || 'Offline',
      bgColor: theme.palette.grey[200],
    },
    error: {
      color: theme.palette.error.main,
      icon: Error,
      label: label || 'Error',
      bgColor: theme.palette.error.light,
    },
    warning: {
      color: theme.palette.warning.main,
      icon: Warning,
      label: label || 'Warning',
      bgColor: theme.palette.warning.light,
    },
    info: {
      color: theme.palette.info.main,
      icon: Info,
      label: label || 'Info',
      bgColor: theme.palette.info.light,
    },
    success: {
      color: theme.palette.success.main,
      icon: CheckCircle,
      label: label || 'Success',
      bgColor: theme.palette.success.light,
    },
    pending: {
      color: theme.palette.warning.main,
      icon: Schedule,
      label: label || 'Pending',
      bgColor: theme.palette.warning.light,
    },
    loading: {
      color: theme.palette.primary.main,
      icon: CircularProgress,
      label: label || 'Loading',
      bgColor: theme.palette.primary.light,
    },
    unknown: {
      color: theme.palette.grey[400],
      icon: HelpOutline,
      label: label || 'Unknown',
      bgColor: theme.palette.grey[100],
    },
    healthy: {
      color: theme.palette.success.main,
      icon: CheckCircle,
      label: label || 'Healthy',
      bgColor: theme.palette.success.light,
    },
    degraded: {
      color: theme.palette.warning.main,
      icon: Warning,
      label: label || 'Degraded',
      bgColor: theme.palette.warning.light,
    },
    critical: {
      color: theme.palette.error.main,
      icon: Error,
      label: label || 'Critical',
      bgColor: theme.palette.error.light,
    },
    maintenance: {
      color: theme.palette.info.main,
      icon: Schedule,
      label: label || 'Maintenance',
      bgColor: theme.palette.info.light,
    },
    // Asset status configurations
    active: {
      color: theme.palette.success.main,
      icon: CheckCircle,
      label: label || 'Active',
      bgColor: theme.palette.success.light,
    },
    inactive: {
      color: theme.palette.grey[500],
      icon: Cancel,
      label: label || 'Inactive',
      bgColor: theme.palette.grey[200],
    },
    matured: {
      color: theme.palette.info.main,
      icon: Schedule,
      label: label || 'Matured',
      bgColor: theme.palette.info.light,
    },
    defaulted: {
      color: theme.palette.error.main,
      icon: Error,
      label: label || 'Defaulted',
      bgColor: theme.palette.error.light,
    },
  };

  const config = statusConfig[status] || statusConfig.unknown;
  const finalColor = customColor || config.color;
  const IconComponent = config.icon;

  // Size configurations
  const sizeConfig = {
    small: { dot: 8, icon: 16, chip: 'small' as const, avatar: 24 },
    medium: { dot: 12, icon: 20, chip: 'medium' as const, avatar: 32 },
    large: { dot: 16, icon: 24, chip: 'medium' as const, avatar: 40 },
  };

  const sizes = sizeConfig[size];

  // Animation styles
  const getAnimationStyle = () => {
    if (!animated) return {};
    
    switch (status) {
      case 'loading':
        return { animation: `${spin} 1s linear infinite` };
      case 'pending':
        return { animation: `${pulse} 1.5s ease-in-out infinite` };
      case 'error':
      case 'critical':
        return { animation: `${blink} 1s ease-in-out infinite` };
      default:
        return {};
    }
  };

  // Format timestamp
  const formatTimestamp = (ts?: string | Date) => {
    if (!ts) return '';
    const date = new Date(ts);
    return date.toLocaleString();
  };

  // Render different variants
  const renderVariant = () => {
    switch (variant) {
      case 'dot':
        return (
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 1,
              cursor: clickable ? 'pointer' : 'default',
              ...sx,
            }}
            onClick={onClick}
            className={className}
          >
            <FiberManualRecord
              sx={{
                fontSize: sizes.dot,
                color: finalColor,
                ...getAnimationStyle(),
              }}
            />
            {showLabel && config.label && (
              <Typography variant="body2" color="text.primary">
                {config.label}
              </Typography>
            )}
          </Box>
        );

      case 'chip':
        const chipElement = (
          <Chip
            icon={status === 'loading' ? undefined : <IconComponent sx={{ fontSize: '16px !important' }} />}
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {status === 'loading' && (
                  <CircularProgress size={14} sx={{ mr: 0.5 }} />
                )}
                {config.label}
                {count !== undefined && ` (${count > maxCount ? `${maxCount}+` : count})`}
              </Box>
            }
            size={sizes.chip}
            variant="outlined"
            sx={{
              borderColor: finalColor,
              color: finalColor,
              backgroundColor: alpha(finalColor, 0.1),
              cursor: clickable ? 'pointer' : 'default',
              ...getAnimationStyle(),
              ...sx,
            }}
            onClick={onClick}
            className={className}
          />
        );
        
        return count !== undefined && count > 0 ? (
          <Badge badgeContent={count > maxCount ? `${maxCount}+` : count} color="error">
            {chipElement}
          </Badge>
        ) : chipElement;

      case 'badge':
        return (
          <Badge
            badgeContent={
              <Circle
                sx={{
                  fontSize: sizes.dot,
                  color: finalColor,
                  ...getAnimationStyle(),
                }}
              />
            }
            sx={{
              cursor: clickable ? 'pointer' : 'default',
              ...sx,
            }}
            onClick={onClick}
            className={className}
          >
            {showLabel && (
              <Typography variant="body2" color="text.primary">
                {config.label}
              </Typography>
            )}
          </Badge>
        );

      case 'icon':
        return (
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 1,
              cursor: clickable ? 'pointer' : 'default',
              ...sx,
            }}
            onClick={onClick}
            className={className}
          >
            {status === 'loading' ? (
              <CircularProgress size={sizes.icon} sx={{ color: finalColor }} />
            ) : (
              <IconComponent
                sx={{
                  fontSize: sizes.icon,
                  color: finalColor,
                  ...getAnimationStyle(),
                }}
              />
            )}
            {showLabel && config.label && (
              <Typography variant="body2" color="text.primary">
                {config.label}
              </Typography>
            )}
          </Box>
        );

      case 'signal':
        const getSignalIcon = () => {
          switch (status) {
            case 'online':
            case 'healthy':
            case 'success':
              return SignalCellular4Bar;
            case 'warning':
            case 'degraded':
              return SignalCellular3Bar;
            case 'error':
              return SignalCellular2Bar;
            case 'critical':
              return SignalCellular1Bar;
            case 'offline':
            default:
              return SignalCellularOff;
          }
        };
        
        const SignalIcon = getSignalIcon();
        
        return (
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 1,
              cursor: clickable ? 'pointer' : 'default',
              ...sx,
            }}
            onClick={onClick}
            className={className}
          >
            <SignalIcon
              sx={{
                fontSize: sizes.icon,
                color: finalColor,
                ...getAnimationStyle(),
              }}
            />
            {showLabel && config.label && (
              <Typography variant="body2" color="text.primary">
                {config.label}
              </Typography>
            )}
          </Box>
        );

      case 'detailed':
        return (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 1.5,
              p: 2,
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              backgroundColor: alpha(finalColor, 0.05),
              cursor: clickable ? 'pointer' : 'default',
              ...sx,
            }}
            onClick={onClick}
            className={className}
          >
            <Avatar
              sx={{
                bgcolor: alpha(finalColor, 0.2),
                color: finalColor,
                width: sizes.avatar,
                height: sizes.avatar,
                ...getAnimationStyle(),
              }}
            >
              {status === 'loading' ? (
                <CircularProgress size={sizes.icon} sx={{ color: finalColor }} />
              ) : (
                <IconComponent sx={{ fontSize: sizes.icon }} />
              )}
            </Avatar>
            
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Typography variant="subtitle2" color="text.primary">
                  {config.label}
                </Typography>
                {count !== undefined && (
                  <Chip
                    label={count > maxCount ? `${maxCount}+` : count}
                    size="small"
                    color={status === 'error' ? 'error' : 'default'}
                  />
                )}
              </Box>
              
              {description && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {description}
                </Typography>
              )}
              
              {showTimestamp && timestamp && (
                <Typography variant="caption" color="text.secondary">
                  {formatTimestamp(timestamp)}
                </Typography>
              )}
            </Box>
            
            {showRefresh && onRefresh && (
              <IconButton size="small" onClick={(e) => { e.stopPropagation(); onRefresh(); }}>
                <Refresh fontSize="small" />
              </IconButton>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Tooltip 
      title={description || (showTimestamp && timestamp ? formatTimestamp(timestamp) : '')}
      disableHoverListener={variant === 'detailed' || (!description && !showTimestamp)}
    >
      <span>{renderVariant()}</span>
    </Tooltip>
  );
};

export default StatusIndicator;