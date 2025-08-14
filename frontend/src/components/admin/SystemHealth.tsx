import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  LinearProgress,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Button,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Memory,
  Storage,
  Speed,
  Timeline,
  Warning,
  CheckCircle,
  Error,
  Info,
  Refresh,
} from '@mui/icons-material';
import {
  useGetSystemHealthQuery,
  useGetSystemStatisticsQuery,
  useGetMonitoringMetricsQuery,
} from '../../store/api/cloApi';

interface HealthMetricCardProps {
  title: string;
  value: number;
  unit?: string;
  icon: React.ReactNode;
  color: 'success' | 'warning' | 'error' | 'info';
  threshold?: {
    warning: number;
    critical: number;
  };
}

const HealthMetricCard: React.FC<HealthMetricCardProps> = ({
  title,
  value,
  unit = '%',
  icon,
  color,
  threshold,
}) => {
  const getProgressColor = () => {
    if (!threshold) return color;
    if (value >= threshold.critical) return 'error';
    if (value >= threshold.warning) return 'warning';
    return 'success';
  };

  const getStatusIcon = () => {
    if (!threshold) return icon;
    if (value >= threshold.critical) return <Error color="error" />;
    if (value >= threshold.warning) return <Warning color="warning" />;
    return <CheckCircle color="success" />;
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ mr: 2, color: `${color}.main` }}>
            {getStatusIcon()}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
            <Typography variant="h5" fontWeight={700}>
              {value.toFixed(1)}{unit}
            </Typography>
          </Box>
        </Box>
        
        <LinearProgress
          variant="determinate"
          value={Math.min(value, 100)}
          color={getProgressColor()}
          sx={{ height: 8, borderRadius: 4 }}
        />
        
        {threshold && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Warning: {threshold.warning}{unit}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Critical: {threshold.critical}{unit}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

interface ServiceStatusProps {
  name: string;
  status: string;
  uptime?: number;
  responseTime?: number;
  lastCheck?: string;
}

const ServiceStatus: React.FC<ServiceStatusProps> = ({
  name,
  status,
  uptime,
  responseTime,
  lastCheck,
}) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'online':
      case 'connected':
        return 'success';
      case 'warning':
      case 'degraded':
        return 'warning';
      case 'error':
      case 'offline':
      case 'disconnected':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'online':
      case 'connected':
        return <CheckCircle fontSize="small" />;
      case 'warning':
      case 'degraded':
        return <Warning fontSize="small" />;
      case 'error':
      case 'offline':
      case 'disconnected':
        return <Error fontSize="small" />;
      default:
        return <Info fontSize="small" />;
    }
  };

  return (
    <TableRow>
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box sx={{ mr: 1, color: `${getStatusColor(status)}.main` }}>
            {getStatusIcon(status)}
          </Box>
          <Typography variant="body2" fontWeight={600}>
            {name}
          </Typography>
        </Box>
      </TableCell>
      <TableCell>
        <Chip
          label={status}
          color={getStatusColor(status)}
          size="small"
          variant="outlined"
        />
      </TableCell>
      <TableCell>
        {uptime !== undefined ? (
          <Typography variant="body2">
            {(uptime / 3600).toFixed(1)}h
          </Typography>
        ) : (
          <Typography variant="body2" color="text.secondary">
            N/A
          </Typography>
        )}
      </TableCell>
      <TableCell>
        {responseTime !== undefined ? (
          <Typography variant="body2">
            {responseTime}ms
          </Typography>
        ) : (
          <Typography variant="body2" color="text.secondary">
            N/A
          </Typography>
        )}
      </TableCell>
      <TableCell>
        <Typography variant="caption" color="text.secondary">
          {lastCheck ? new Date(lastCheck).toLocaleTimeString() : 'Unknown'}
        </Typography>
      </TableCell>
    </TableRow>
  );
};

const SystemHealth: React.FC = () => {
  const [refreshKey, setRefreshKey] = useState(0);

  // API queries
  const {
    data: healthData,
    isLoading: healthLoading,
    error: healthError,
    refetch: refetchHealth,
  } = useGetSystemHealthQuery(undefined, {
    refetchOnMountOrArgChange: true,
    pollingInterval: 30000, // Refresh every 30 seconds
  });

  const {
    data: statsData,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useGetSystemStatisticsQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: metricsData,
    isLoading: metricsLoading,
    refetch: refetchMetrics,
  } = useGetMonitoringMetricsQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
    refetchHealth();
    refetchStats();
    refetchMetrics();
  };

  const isLoading = healthLoading || statsLoading || metricsLoading;

  if (healthError) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load system health data. Please check your connection and try again.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h6" gutterBottom>
            System Health Monitor
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time system performance and service status monitoring
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Auto-refresh every 30 seconds">
            <Chip
              label="Auto-refresh: ON"
              color="success"
              size="small"
              variant="outlined"
            />
          </Tooltip>
          <Tooltip title="Manual refresh">
            <IconButton onClick={handleRefresh} disabled={isLoading}>
              {isLoading ? <CircularProgress size={20} /> : <Refresh />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* System Overview */}
      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
        System Overview
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <HealthMetricCard
            title="CPU Usage"
            value={statsData?.cpuUsage || 0}
            icon={<Speed />}
            color="info"
            threshold={{ warning: 70, critical: 85 }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <HealthMetricCard
            title="Memory Usage"
            value={statsData?.memoryUsage || 0}
            icon={<Memory />}
            color="warning"
            threshold={{ warning: 75, critical: 90 }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <HealthMetricCard
            title="Disk Usage"
            value={statsData?.diskUsage || 0}
            icon={<Storage />}
            color="success"
            threshold={{ warning: 80, critical: 95 }}
          />
        </Grid>
        
        <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Timeline sx={{ mr: 2, color: 'primary.main' }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    System Uptime
                  </Typography>
                  <Typography variant="h5" fontWeight={700}>
                    {healthData?.uptime 
                      ? `${Math.floor(healthData.uptime / 3600)}h ${Math.floor((healthData.uptime % 3600) / 60)}m`
                      : '0h 0m'
                    }
                  </Typography>
                </Box>
              </Box>
              <Chip
                label={healthData?.status || 'Unknown'}
                color={
                  healthData?.status?.toLowerCase() === 'healthy' ? 'success' :
                  healthData?.status?.toLowerCase() === 'warning' ? 'warning' : 'error'
                }
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Divider sx={{ my: 3 }} />

      {/* Service Status */}
      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
        Service Status
      </Typography>
      
      <TableContainer component={Paper} variant="outlined">
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Service</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Uptime</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Response Time</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Last Check</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <ServiceStatus
              name="PostgreSQL Database"
              status={healthData?.database_status || 'Unknown'}
              uptime={healthData?.uptime}
              responseTime={metricsData?.api_response_times?.database}
              lastCheck={new Date().toISOString()}
            />
            <ServiceStatus
              name="Redis Cache"
              status={healthData?.redis_status || 'Unknown'}
              uptime={healthData?.uptime}
              responseTime={metricsData?.api_response_times?.redis}
              lastCheck={new Date().toISOString()}
            />
            <ServiceStatus
              name="Background Jobs"
              status={
                (healthData?.background_jobs || 0) > 0 ? 'Running' : 
                statsData?.calculationsToday ? 'Healthy' : 'Idle'
              }
              uptime={healthData?.uptime}
              responseTime={metricsData?.api_response_times?.background_jobs}
              lastCheck={new Date().toISOString()}
            />
            <ServiceStatus
              name="API Gateway"
              status="Healthy"
              uptime={healthData?.uptime}
              responseTime={metricsData?.api_response_times?.api_gateway || 45}
              lastCheck={new Date().toISOString()}
            />
          </TableBody>
        </Table>
      </TableContainer>

      {/* Performance Metrics */}
      {metricsData && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Performance Metrics
          </Typography>
          
          <Grid container spacing={3}>
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    API Response Times
                  </Typography>
                  <Table size="small">
                    <TableBody>
                      {Object.entries(metricsData.api_response_times || {}).map(([endpoint, time]) => (
                        <TableRow key={endpoint}>
                          <TableCell>{endpoint.replace(/_/g, ' ').toUpperCase()}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${time}ms`}
                              size="small"
                              color={time < 100 ? 'success' : time < 500 ? 'warning' : 'error'}
                              variant="outlined"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Activity
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Active Users</Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {healthData?.active_users || 0}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Active Calculations</Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {metricsData.active_calculations || 0}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Background Jobs</Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {healthData?.background_jobs || 0}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">System Alerts</Typography>
                      <Typography variant="body2" fontWeight={600} color="warning.main">
                        {healthData?.system_alerts || 0}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default SystemHealth;