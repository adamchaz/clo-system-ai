import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  IconButton,
  Alert,
  LinearProgress,
  useTheme,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip,
} from '@mui/material';
import {
  People,
  Security,
  Assessment,
  Warning,
  Settings,
  Refresh,
  Add,
  CheckCircle,
  Delete,
  Error,
  Info,
  Storage,
  Timeline,
} from '@mui/icons-material';
import {
  useGetSystemStatisticsQuery,
  useGetUsersQuery,
  useGetSystemAlertsQuery,
  useGetSystemHealthQuery,
  useAcknowledgeAlertMutation,
  useDismissAlertMutation,
} from '../store/api/cloApi';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  subtitle, 
  icon, 
  color = 'primary.main',
  trend 
}) => {
  const theme = useTheme();
  
  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s ease-in-out',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[8],
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: `${color}15`,
              color,
              mr: 2,
            }}
          >
            {icon}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography
              variant="h4"
              component="div"
              sx={{
                fontWeight: 700,
                lineHeight: 1.2,
                color: 'text.primary',
              }}
            >
              {value}
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  mt: 1,
                  display: 'block',
                }}
              >
                {subtitle}
              </Typography>
            )}
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography
                  variant="caption"
                  sx={{
                    color: trend.isPositive ? 'success.main' : 'error.main',
                    fontWeight: 600,
                  }}
                >
                  {trend.isPositive ? '+' : ''}{trend.value}%
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
                  vs last month
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

interface SystemHealthIndicatorProps {
  status: string;
  uptime: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
}

const SystemHealthIndicator: React.FC<SystemHealthIndicatorProps> = ({
  status,
  uptime,
  cpuUsage,
  memoryUsage,
  diskUsage,
}) => {
  const getStatusColor = (status: string) => {
    if (!status) return 'info';
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'info';
    }
  };

  const getUsageColor = (usage: number) => {
    if (usage < 70) return 'success';
    if (usage < 85) return 'warning';
    return 'error';
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Assessment color="primary" sx={{ mr: 1 }} />
          <Typography variant="h6">System Health</Typography>
          <Chip
            label={status}
            color={getStatusColor(status)}
            size="small"
            sx={{ ml: 'auto' }}
          />
        </Box>
        
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Uptime: {Math.floor(uptime / 3600)}h {Math.floor((uptime % 3600) / 60)}m
            </Typography>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                CPU Usage
              </Typography>
              <LinearProgress
                variant="determinate"
                value={cpuUsage}
                color={getUsageColor(cpuUsage)}
                sx={{ mt: 0.5 }}
              />
              <Typography variant="caption" color="text.secondary">
                {cpuUsage.toFixed(1)}%
              </Typography>
            </Box>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Memory Usage
              </Typography>
              <LinearProgress
                variant="determinate"
                value={memoryUsage}
                color={getUsageColor(memoryUsage)}
                sx={{ mt: 0.5 }}
              />
              <Typography variant="caption" color="text.secondary">
                {memoryUsage.toFixed(1)}%
              </Typography>
            </Box>
          </Grid>
          
          <Grid size={{ xs: 12, sm: 6 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Disk Usage
              </Typography>
              <LinearProgress
                variant="determinate"
                value={diskUsage}
                color={getUsageColor(diskUsage)}
                sx={{ mt: 0.5 }}
              />
              <Typography variant="caption" color="text.secondary">
                {diskUsage.toFixed(1)}%
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

const SystemAdminDashboard: React.FC = () => {
  const theme = useTheme();

  // API queries
  const {
    data: systemStats,
    isLoading: statsLoading,
    error: statsError,
  } = useGetSystemStatisticsQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: systemHealth,
    isLoading: healthLoading,
  } = useGetSystemHealthQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: recentUsersData,
  } = useGetUsersQuery({ limit: 5, skip: 0 }, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: alertsData,
  } = useGetSystemAlertsQuery({ limit: 10, acknowledged: false }, {
    refetchOnMountOrArgChange: true,
  });

  const [acknowledgeAlert] = useAcknowledgeAlertMutation();
  const [dismissAlert] = useDismissAlertMutation();

  const handleRefresh = () => {
    window.location.reload();
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId).unwrap();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const handleDismissAlert = async (alertId: string) => {
    try {
      await dismissAlert(alertId).unwrap();
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <Error color="error" />;
      case 'warning':
        return <Warning color="warning" />;
      default:
        return <Info color="info" />;
    }
  };

  if (statsLoading || healthLoading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <LinearProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Loading system dashboard...
        </Typography>
      </Box>
    );
  }

  if (statsError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load system statistics. Please check your connection and try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography
            variant="h4"
            component="h1"
            sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}
          >
            System Administration
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor system health, manage users, and configure system settings.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Settings />}
            href="/admin/settings"
          >
            System Settings
          </Button>
        </Box>
      </Box>

      {/* System Metrics Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Total Users"
            value={systemStats?.totalUsers || 0}
            subtitle={`${systemStats?.activeUsers || 0} active`}
            icon={<People />}
            color={theme.palette.primary.main}
            trend={{ value: 5.2, isPositive: true }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Active Portfolios"
            value={systemStats?.totalPortfolios || 0}
            subtitle="CLO management"
            icon={<Assessment />}
            color={theme.palette.success.main}
            trend={{ value: 2.1, isPositive: true }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Total Assets"
            value={(systemStats?.totalAssets || 0).toLocaleString()}
            subtitle="Under management"
            icon={<Storage />}
            color={theme.palette.info.main}
            trend={{ value: 0.8, isPositive: true }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <MetricCard
            title="Calculations Today"
            value={systemStats?.calculationsToday || 0}
            subtitle="Waterfall runs"
            icon={<Timeline />}
            color={theme.palette.warning.main}
            trend={{ value: -3.2, isPositive: false }}
          />
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* System Health */}
        <Grid size={{ xs: 12, lg: 6 }}>
          {systemHealth && (
            <SystemHealthIndicator
              status={systemHealth.status || 'unknown'}
              uptime={systemHealth.uptime || 0}
              cpuUsage={systemStats?.cpuUsage || 0}
              memoryUsage={systemStats?.memoryUsage || 0}
              diskUsage={systemStats?.diskUsage || 0}
            />
          )}
        </Grid>

        {/* Recent Alerts */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Warning color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">System Alerts</Typography>
                </Box>
                <Chip
                  label={`${alertsData?.data?.length || 0} active`}
                  color="warning"
                  size="small"
                />
              </Box>
              
              <List dense>
                {alertsData?.data?.slice(0, 5).map((alert) => (
                  <ListItem key={alert.id} divider>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', width: '100%' }}>
                      {getAlertIcon(alert.type)}
                      <Box sx={{ ml: 1, flexGrow: 1 }}>
                        <Typography variant="body2" fontWeight={600}>
                          {alert.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {alert.message}
                        </Typography>
                        <Box sx={{ mt: 0.5 }}>
                          <Chip
                            label={alert.type}
                            size="small"
                            variant="outlined"
                            sx={{ mr: 1 }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {new Date(alert.timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                        <Tooltip title="Acknowledge">
                          <IconButton
                            size="small"
                            onClick={() => handleAcknowledgeAlert(alert.id)}
                          >
                            <CheckCircle color="success" fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Dismiss">
                          <IconButton
                            size="small"
                            onClick={() => handleDismissAlert(alert.id)}
                          >
                            <Delete color="error" fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                  </ListItem>
                )) || (
                  <ListItem>
                    <ListItemText
                      primary="No active alerts"
                      secondary="System is operating normally"
                    />
                  </ListItem>
                )}
              </List>
              
              {(alertsData?.data?.length || 0) > 5 && (
                <Box sx={{ textAlign: 'center', mt: 2 }}>
                  <Button size="small" href="/admin/alerts">
                    View All Alerts
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Users */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <People color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Recent Users</Typography>
                </Box>
                <Button
                  size="small"
                  startIcon={<Add />}
                  href="/admin/users/new"
                >
                  Add User
                </Button>
              </Box>
              
              <List dense>
                {recentUsersData?.data?.map((user) => (
                  <ListItem key={user.id} divider>
                    <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                      {user.firstName[0]}{user.lastName[0]}
                    </Avatar>
                    <ListItemText
                      primary={`${user.firstName} ${user.lastName}`}
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            {user.email}
                          </Typography>
                          <Chip
                            label={user.role}
                            size="small"
                            variant="outlined"
                            sx={{ mt: 0.5 }}
                          />
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Chip
                        label={user.isActive ? 'Active' : 'Inactive'}
                        color={user.isActive ? 'success' : 'default'}
                        size="small"
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                )) || (
                  <ListItem>
                    <ListItemText primary="No users found" />
                  </ListItem>
                )}
              </List>
              
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Button size="small" href="/admin/users">
                  Manage All Users
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid size={{ xs: 12, lg: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Settings sx={{ mr: 1 }} />
                Quick Actions
              </Typography>
              
              <Grid container spacing={2}>
                <Grid size={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<People />}
                    href="/admin/users"
                    sx={{ justifyContent: 'flex-start' }}
                  >
                    User Management
                  </Button>
                </Grid>
                <Grid size={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Security />}
                    href="/admin/audit"
                    sx={{ justifyContent: 'flex-start' }}
                  >
                    Audit Logs
                  </Button>
                </Grid>
                <Grid size={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Assessment />}
                    href="/admin/reports"
                    sx={{ justifyContent: 'flex-start' }}
                  >
                    System Reports
                  </Button>
                </Grid>
                <Grid size={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Settings />}
                    href="/admin/config"
                    sx={{ justifyContent: 'flex-start' }}
                  >
                    Configuration
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SystemAdminDashboard;