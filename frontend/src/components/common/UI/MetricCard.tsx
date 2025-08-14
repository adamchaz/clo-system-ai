import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Box,
  Typography,
  IconButton,
  Chip,
  LinearProgress,
  CircularProgress,
  Tooltip,
  alpha,
  useTheme,
  Avatar,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Info,
  Warning,
  Error,
  CheckCircle,
  ArrowUpward,
  ArrowDownward,
} from '@mui/icons-material';

export type MetricStatus = 'success' | 'warning' | 'error' | 'info' | 'neutral';
export type MetricTrend = 'up' | 'down' | 'flat';
export type MetricSize = 'small' | 'medium' | 'large';
export type MetricVariant = 'default' | 'outlined' | 'gradient';

export interface MetricCardAction {
  icon: React.ComponentType;
  label: string;
  onClick: () => void;
}

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  description?: string;
  unit?: string;
  prefix?: string;
  status?: MetricStatus;
  trend?: MetricTrend | { value: number; isPositive: boolean; period: string };
  trendValue?: number;
  trendLabel?: string;
  progress?: number; // 0-100 for progress bar
  target?: number;
  icon?: React.ReactNode;
  color?: string;
  loading?: boolean;
  error?: boolean;
  actions?: MetricCardAction[];
  onClick?: () => void;
  size?: MetricSize;
  variant?: MetricVariant;
  showTrendIcon?: boolean;
  showProgress?: boolean;
  showTarget?: boolean;
  animated?: boolean;
  className?: string;
  sx?: any;
}

const getStatusColor = (status: MetricStatus, theme: any) => {
  switch (status) {
    case 'success':
      return theme.palette.success.main;
    case 'warning':
      return theme.palette.warning.main;
    case 'error':
      return theme.palette.error.main;
    case 'info':
      return theme.palette.info.main;
    case 'neutral':
    default:
      return theme.palette.text.primary;
  }
};

const getStatusIcon = (status: MetricStatus) => {
  switch (status) {
    case 'success':
      return CheckCircle;
    case 'warning':
      return Warning;
    case 'error':
      return Error;
    case 'info':
      return Info;
    default:
      return null;
  }
};

const getTrendIcon = (trend: MetricTrend) => {
  switch (trend) {
    case 'up':
      return TrendingUp;
    case 'down':
      return TrendingDown;
    case 'flat':
    default:
      return TrendingFlat;
  }
};

const getTrendColor = (trend: MetricTrend, theme: any) => {
  switch (trend) {
    case 'up':
      return theme.palette.success.main;
    case 'down':
      return theme.palette.error.main;
    case 'flat':
    default:
      return theme.palette.text.secondary;
  }
};

const formatValue = (value: string | number, unit?: string, prefix?: string): string => {
  if (typeof value === 'number') {
    // Format large numbers with appropriate suffixes
    const formatNumber = (num: number) => {
      const formatted = num.toFixed(1);
      return formatted.endsWith('.0') ? formatted.slice(0, -2) : formatted;
    };

    if (Math.abs(value) >= 1e9) {
      return `${prefix || ''}${formatNumber(value / 1e9)}B${unit || ''}`;
    } else if (Math.abs(value) >= 1e6) {
      return `${prefix || ''}${formatNumber(value / 1e6)}M${unit || ''}`;
    } else if (Math.abs(value) >= 1e3) {
      return `${prefix || ''}${formatNumber(value / 1e3)}K${unit || ''}`;
    } else {
      return `${prefix || ''}${value.toLocaleString()}${unit || ''}`;
    }
  }
  
  return `${prefix || ''}${value}${unit || ''}`;
};

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  description,
  unit,
  prefix,
  status = 'neutral',
  trend,
  trendValue,
  trendLabel,
  progress,
  target,
  icon: IconComponent,
  color,
  loading = false,
  error = false,
  actions = [],
  onClick,
  size = 'medium',
  variant = 'default',
  showTrendIcon = true,
  showProgress = false,
  showTarget = false,
  animated = true,
  className,
  sx = {},
}) => {
  const theme = useTheme();
  
  const statusColor = color || getStatusColor(status, theme);
  const StatusIcon = getStatusIcon(status);
  
  // Handle trend - can be simple enum or complex object
  const trendType: MetricTrend | null = typeof trend === 'object' && trend !== null 
    ? (trend.isPositive ? 'up' : 'down')
    : trend as MetricTrend || null;
  
  const TrendIcon = trendType ? getTrendIcon(trendType) : null;
  const trendColor = trendType ? getTrendColor(trendType, theme) : theme.palette.text.secondary;
  
  const isClickable = Boolean(onClick);
  const hasError = error || status === 'error';
  
  // Size configurations
  const sizeConfig = {
    small: {
      padding: 2,
      titleVariant: 'body2' as const,
      valueVariant: 'h6' as const,
      iconSize: 32,
      cardMinHeight: 120,
    },
    medium: {
      padding: 3,
      titleVariant: 'body1' as const,
      valueVariant: 'h4' as const,
      iconSize: 40,
      cardMinHeight: 160,
    },
    large: {
      padding: 4,
      titleVariant: 'h6' as const,
      valueVariant: 'h3' as const,
      iconSize: 48,
      cardMinHeight: 200,
    },
  };
  
  const config = sizeConfig[size];
  
  // Card styling based on variant
  const getCardSx = () => {
    const baseSx = {
      minHeight: config.cardMinHeight,
      transition: theme.transitions.create(['transform', 'box-shadow'], {
        duration: theme.transitions.duration.short,
      }),
      cursor: isClickable ? 'pointer' : 'default',
      position: 'relative',
      overflow: 'hidden',
      ...(isClickable && {
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: theme.shadows[8],
        },
      }),
      ...sx,
    };

    switch (variant) {
      case 'outlined':
        return {
          ...baseSx,
          border: `2px solid ${statusColor}`,
          backgroundColor: alpha(statusColor, 0.02),
        };
      case 'gradient':
        return {
          ...baseSx,
          background: `linear-gradient(135deg, ${alpha(statusColor, 0.1)} 0%, ${alpha(statusColor, 0.05)} 100%)`,
          borderLeft: `4px solid ${statusColor}`,
        };
      default:
        return {
          ...baseSx,
          borderLeft: `4px solid ${statusColor}`,
        };
    }
  };

  return (
    <Card
      className={className}
      sx={getCardSx()}
      onClick={onClick}
      elevation={variant === 'outlined' ? 0 : 1}
    >
      {loading && (
        <LinearProgress
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 2,
          }}
        />
      )}
      
      <CardContent sx={{ p: config.padding, pb: actions.length > 0 ? 2 : config.padding }}>
        {/* Header with Title and Icon */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography
              variant={config.titleVariant}
              color="text.secondary"
              gutterBottom
              noWrap
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                color="text.secondary"
                display="block"
                sx={{ opacity: 0.8 }}
              >
                {subtitle}
              </Typography>
            )}
          </Box>
          
          {(IconComponent || StatusIcon) && (
            <Box sx={{ ml: 2 }}>
              {IconComponent ? (
                <Avatar
                  sx={{
                    bgcolor: alpha(statusColor, 0.1),
                    color: statusColor,
                    width: config.iconSize,
                    height: config.iconSize,
                  }}
                >
                  {IconComponent}
                </Avatar>
              ) : StatusIcon ? (
                <StatusIcon sx={{ color: statusColor, fontSize: config.iconSize * 0.8 }} />
              ) : null}
            </Box>
          )}
        </Box>

        {/* Main Value */}
        <Box sx={{ mb: 2 }}>
          {loading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={20} />
              <Typography variant={config.valueVariant} color="text.secondary">
                Loading...
              </Typography>
            </Box>
          ) : hasError ? (
            <Typography variant={config.valueVariant} color="error">
              Error
            </Typography>
          ) : (
            <Typography
              variant={config.valueVariant}
              fontWeight="bold"
              color={statusColor}
              sx={{
                ...(animated && {
                  transition: theme.transitions.create('color', {
                    duration: theme.transitions.duration.short,
                  }),
                }),
              }}
            >
              {formatValue(value, unit, prefix)}
            </Typography>
          )}
        </Box>

        {/* Trend Information */}
        {(trend || trendValue !== undefined) && !loading && !hasError && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            {trend && showTrendIcon && TrendIcon && (
              <TrendIcon
                sx={{
                  color: trendColor,
                  fontSize: 16,
                }}
              />
            )}
            {trendValue !== undefined && (
              <Chip
                label={`${trendValue > 0 ? '+' : ''}${trendValue}${trendLabel || '%'}`}
                size="small"
                sx={{
                  bgcolor: alpha(trendColor, 0.1),
                  color: trendColor,
                  fontSize: '0.75rem',
                  height: 20,
                }}
              />
            )}
          </Box>
        )}

        {/* Progress Bar */}
        {showProgress && progress !== undefined && !loading && !hasError && (
          <Box sx={{ mt: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                Progress
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {Math.round(progress)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                height: 6,
                borderRadius: 3,
                bgcolor: alpha(statusColor, 0.1),
                '& .MuiLinearProgress-bar': {
                  bgcolor: statusColor,
                  borderRadius: 3,
                },
              }}
            />
          </Box>
        )}

        {/* Target Information */}
        {showTarget && target !== undefined && !loading && !hasError && (
          <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Target: {formatValue(target, unit, prefix)}
            </Typography>
            {typeof value === 'number' && (
              <Chip
                icon={value >= target ? <ArrowUpward /> : <ArrowDownward />}
                label={`${Math.abs(((value - target) / target) * 100).toFixed(1)}%`}
                size="small"
                color={value >= target ? 'success' : 'error'}
                variant="outlined"
                sx={{ height: 20, fontSize: '0.7rem' }}
              />
            )}
          </Box>
        )}

        {/* Description */}
        {description && !loading && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              mt: 1,
              display: 'block',
              opacity: 0.8,
              lineHeight: 1.3,
            }}
          >
            {description}
          </Typography>
        )}
      </CardContent>

      {/* Actions */}
      {actions.length > 0 && (
        <CardActions sx={{ px: config.padding, py: 1, justifyContent: 'flex-end' }}>
          {actions.map((action, index) => (
            <Tooltip key={index} title={action.label}>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  action.onClick();
                }}
                sx={{ color: statusColor }}
              >
                <action.icon />
              </IconButton>
            </Tooltip>
          ))}
        </CardActions>
      )}
    </Card>
  );
};

export default MetricCard;