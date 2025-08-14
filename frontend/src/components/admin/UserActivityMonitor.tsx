/**
 * UserActivityMonitor Component - Real-time User Activity Monitoring
 * 
 * Provides comprehensive user activity monitoring including:
 * - Live user session tracking
 * - User activity logs and timelines
 * - Login/logout events monitoring
 * - User permission changes tracking
 * - Security event notifications
 * - Activity analytics and insights
 * 
 * Integrates with User Management APIs and WebSocket for real-time updates
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Alert,
  Stack,
  IconButton,
  Tooltip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  LinearProgress,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Person,
  Security,
  Login,
  Logout,
  Visibility,
  Warning,
  Info,
  Error,
  CheckCircle,
  Schedule,
  Computer,
  Smartphone,
  Tablet,
  LocationOn,
  VpnKey,
  Settings,
  Refresh,
  Search,
  FilterList,
  Timeline,
  Analytics,
  Notifications,
  Close,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';

// Import API hooks
import {
  useGetUserActivityQuery,
  useGetUserSessionsQuery,
  useGetUserStatsQuery,
} from '../../store/api/cloApi';

// Import types
import {
  UserActivityResponse,
  UserSessionResponse,
} from '../../store/api/newApiTypes';

// Import WebSocket hooks
import { useUserActivity } from '../../hooks/useWebSocket';

interface UserActivityMonitorProps {
  userId?: string; // If provided, show activity for specific user
  showAllUsers?: boolean; // Show activity for all users
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index} role="tabpanel">
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const ActivityTypeIcons = {
  login: <Login color="success" />,
  logout: <Logout color="info" />,
  password_change: <VpnKey color="warning" />,
  permission_change: <Settings color="info" />,
  security_event: <Security color="error" />,
  data_access: <Visibility color="info" />,
  system_access: <Computer color="primary" />,
};

const ActivityTypeBadges = {
  login: { color: 'success' as const, label: 'Login' },
  logout: { color: 'info' as const, label: 'Logout' },
  password_change: { color: 'warning' as const, label: 'Password Change' },
  permission_change: { color: 'info' as const, label: 'Permission Change' },
  security_event: { color: 'error' as const, label: 'Security Event' },
  data_access: { color: 'primary' as const, label: 'Data Access' },
  system_access: { color: 'secondary' as const, label: 'System Access' },
};

const DeviceIcons = {
  desktop: <Computer />,
  mobile: <Smartphone />,
  tablet: <Tablet />,
};

const UserActivityMonitor: React.FC<UserActivityMonitorProps> = ({
  userId,
  showAllUsers = true,
}) => {
  // State management
  const [currentTab, setCurrentTab] = useState(0);
  const [activityFilter, setActivityFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedActivity, setSelectedActivity] = useState<any>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [realtimeActivities, setRealtimeActivities] = useState<any[]>([]);

  // API hooks
  const { data: userActivityResponse, isLoading: isLoadingActivity, refetch: refetchActivity } = 
    useGetUserActivityQuery({
      userId: userId || 'all',
      limit: pageSize,
    }, { skip: !userId });

  const { data: userSessionsResponse, isLoading: isLoadingSessions, refetch: refetchSessions } = 
    useGetUserSessionsQuery(userId || 'all');

  const { data: userStats } = useGetUserStatsQuery();

  const userActivity = userActivityResponse?.data || [];
  const userSessions = userSessionsResponse?.data || [];

  // WebSocket integration for real-time activity updates
  useUserActivity((activityData) => {
    setRealtimeActivities(prev => [activityData, ...prev.slice(0, 19)]); // Keep last 20 activities
    refetchActivity();
    refetchSessions();
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleActivityClick = (activity: any) => {
    setSelectedActivity(activity);
    setDetailDialogOpen(true);
  };

  const getActivitySeverity = (activityType: string) => {
    switch (activityType) {
      case 'security_event':
        return 'error';
      case 'password_change':
      case 'permission_change':
        return 'warning';
      case 'login':
        return 'success';
      default:
        return 'info';
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    if (durationMs < 60000) return `${Math.floor(durationMs / 1000)}s`;
    if (durationMs < 3600000) return `${Math.floor(durationMs / 60000)}m`;
    return `${Math.floor(durationMs / 3600000)}h ${Math.floor((durationMs % 3600000) / 60000)}m`;
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          User Activity Monitor
          {realtimeActivities.length > 0 && (
            <Badge badgeContent={realtimeActivities.length} color="error" sx={{ ml: 2 }}>
              <Notifications />
            </Badge>
          )}
        </Typography>

        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => {
              refetchActivity();
              refetchSessions();
            }}
          >
            Refresh
          </Button>
        </Stack>
      </Box>

      {/* Real-time Activity Alert */}
      {realtimeActivities.length > 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Live Activity Feed ({realtimeActivities.length} recent events)
          </Typography>
          <Typography variant="body2">
            Latest: {realtimeActivities[0]?.description} - {format(new Date(), 'PPp')}
          </Typography>
        </Alert>
      )}

      {/* Activity Statistics */}
      {userStats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid {...({ item: true } as any)} size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {(userStats.data as any).current_sessions || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Sessions
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary.main">
                  {(userStats.data as any).total_logins_today || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Logins Today
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {(userStats.data as any).failed_login_attempts || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Failed Attempts
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid {...({ item: true } as any)} size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="error.main">
                  {(userStats.data as any).security_events || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Security Events
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Search and Filter */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                placeholder="Search activity logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            
            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 4 }}>
              <FormControl fullWidth>
                <InputLabel>Activity Type</InputLabel>
                <Select
                  value={activityFilter}
                  label="Activity Type"
                  onChange={(e) => setActivityFilter(e.target.value)}
                >
                  <MenuItem value="">All Types</MenuItem>
                  {Object.entries(ActivityTypeBadges).map(([type, config]) => (
                    <MenuItem key={type} value={type}>
                      {config.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid {...({ item: true } as any)} size={{ xs: 12, md: 2 }}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<FilterList />}
                onClick={() => {
                  setSearchQuery('');
                  setActivityFilter('');
                }}
              >
                Clear
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Loading Indicator */}
      {(isLoadingActivity || isLoadingSessions) && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress />
        </Box>
      )}

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange}>
            <Tab label="Activity Log" icon={<Timeline />} />
            <Tab label="Active Sessions" icon={<Person />} />
            <Tab label="Security Events" icon={<Security />} />
          </Tabs>
        </Box>

        {/* Activity Log Tab */}
        <TabPanel value={currentTab} index={0}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Activity</TableCell>
                  <TableCell>Details</TableCell>
                  <TableCell>IP Address</TableCell>
                  <TableCell>Device</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {userActivity.map((activity, index) => (
                  <TableRow 
                    key={index} 
                    hover 
                    sx={{ cursor: 'pointer' }}
                    onClick={() => handleActivityClick(activity)}
                  >
                    <TableCell>
                      <Typography variant="body2">
                        {format(new Date(activity.timestamp), 'PPp')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDistanceToNow(new Date(activity.timestamp))} ago
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar sx={{ width: 32, height: 32, fontSize: 14 }}>
                          {(activity as any).user_name?.charAt(0) || 'U'}
                        </Avatar>
                        <Box>
                          <Typography variant="body2">{(activity as any).user_name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {(activity as any).user_email}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Chip
                        icon={ActivityTypeIcons[(activity as any).activity_type as keyof typeof ActivityTypeIcons] || ActivityTypeIcons['login']}
                        label={ActivityTypeBadges[(activity as any).activity_type as keyof typeof ActivityTypeBadges]?.label || (activity as any).activity_type || activity.action}
                        color={ActivityTypeBadges[(activity as any).activity_type as keyof typeof ActivityTypeBadges]?.color || 'default'}
                        size="small"
                      />
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" noWrap>
                        {(activity as any).description || activity.details || 'No description'}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {activity.ip_address}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {DeviceIcons[(activity as any).device_type as keyof typeof DeviceIcons] || <Computer />}
                        <Typography variant="body2">
                          {(activity as any).device_info || activity.user_agent || 'Unknown device'}
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {/* Pagination */}
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <Pagination
              count={Math.ceil(((userActivityResponse as any)?.total || userActivityResponse?.data?.length || 0) / pageSize)}
              page={currentPage}
              onChange={(e, page) => setCurrentPage(page)}
              color="primary"
            />
          </Box>
        </TabPanel>

        {/* Active Sessions Tab */}
        <TabPanel value={currentTab} index={1}>
          <Grid container spacing={2}>
            {userSessions.map((session, index) => (
              <Grid {...({ item: true } as any)} size={{ xs: 12, md: 6 }} key={index}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Avatar>
                        {(session as any).user_name?.charAt(0) || 'U'}
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1">
                          {(session as any).user_name || 'Unknown User'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {(session as any).user_email || 'No email'}
                        </Typography>
                      </Box>
                      <Chip
                        label={(session as any).is_active ? 'Active' : 'Inactive'}
                        color={(session as any).is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                    
                    <Stack spacing={1}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Schedule fontSize="small" />
                        <Typography variant="body2">
                          Started: {format(new Date(session.created_at), 'PPp')}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Computer fontSize="small" />
                        <Typography variant="body2">
                          {(session as any).device_info || 'Unknown device'}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LocationOn fontSize="small" />
                        <Typography variant="body2" fontFamily="monospace">
                          {session.ip_address}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Timeline fontSize="small" />
                        <Typography variant="body2">
                          Duration: {formatDuration(session.created_at, session.last_activity)}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Security Events Tab */}
        <TabPanel value={currentTab} index={2}>
          <Alert severity="info">
            Security events monitoring and detailed security analytics will be displayed here.
            This includes failed login attempts, suspicious activities, and security violations.
          </Alert>
        </TabPanel>
      </Card>

      {/* Activity Detail Dialog */}
      <Dialog open={detailDialogOpen} onClose={() => setDetailDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Activity Details
          <IconButton onClick={() => setDetailDialogOpen(false)}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedActivity && (
            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Activity Type
                </Typography>
                <Chip
                  icon={ActivityTypeIcons[selectedActivity.activity_type as keyof typeof ActivityTypeIcons]}
                  label={ActivityTypeBadges[selectedActivity.activity_type as keyof typeof ActivityTypeBadges]?.label}
                  color={ActivityTypeBadges[selectedActivity.activity_type as keyof typeof ActivityTypeBadges]?.color}
                />
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Timestamp
                </Typography>
                <Typography variant="body1">
                  {format(new Date(selectedActivity.timestamp), 'PPpp')}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Description
                </Typography>
                <Typography variant="body1">
                  {selectedActivity.description}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  User Information
                </Typography>
                <Typography variant="body1">
                  {selectedActivity.user_name} ({selectedActivity.user_email})
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  IP Address & Device
                </Typography>
                <Typography variant="body1" fontFamily="monospace">
                  {selectedActivity.ip_address}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedActivity.device_info}
                </Typography>
              </Box>
              
              {selectedActivity.additional_data && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    Additional Information
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" fontFamily="monospace">
                      {JSON.stringify(selectedActivity.additional_data, null, 2)}
                    </Typography>
                  </Paper>
                </Box>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserActivityMonitor;