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
  useGetUsersQuery,
} from '../../store/api/cloApi';

// Import types
import {
  UserActivityResponse,
  UserSessionResponse,
} from '../../store/api/newApiTypes';
import { User } from '../../store/api/cloApi';

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
  
  // Fetch users to get user details for activities
  const { data: usersResponse } = useGetUsersQuery({});
  const users = usersResponse?.data || [];

  const userActivity = userActivityResponse?.data || [];
  const userSessions = userSessionsResponse?.data || [];
  
  // Create user lookup map for efficient access
  const userLookup = React.useMemo(() => {
    const lookup: Record<string, User> = {};
    users.forEach(user => {
      lookup[user.id] = user;
    });
    return lookup;
  }, [users]);
  
  // Helper function to get user details from activity
  const getUserFromActivity = (activity: UserActivityResponse) => {
    return userLookup[activity.user_id] || null;
  };

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
          <Grid size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {userStats?.data?.active_users || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Sessions
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary.main">
                  {userStats?.data?.daily_active_users || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Logins Today
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  0
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Failed Attempts
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="error.main">
                  0
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
            <Grid size={{ xs: 12, md: 6 }}>
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
            
            <Grid size={{ xs: 12, md: 4 }}>
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

            <Grid size={{ xs: 12, md: 2 }}>
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
                          {(() => {
                            const user = getUserFromActivity(activity);
                            return user ? `${user.firstName?.[0] || ''}${user.lastName?.[0] || ''}` : 'U';
                          })()}
                        </Avatar>
                        <Box>
                          <Typography variant="body2">
                            {(() => {
                              const user = getUserFromActivity(activity);
                              return user ? `${user.firstName || ''} ${user.lastName || ''}`.trim() : `User ${activity.user_id}`;
                            })()}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {getUserFromActivity(activity)?.email || 'No email'}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Chip
                        icon={ActivityTypeIcons[activity.action as keyof typeof ActivityTypeIcons] || ActivityTypeIcons['login']}
                        label={ActivityTypeBadges[activity.action as keyof typeof ActivityTypeBadges]?.label || activity.action}
                        color={ActivityTypeBadges[activity.action as keyof typeof ActivityTypeBadges]?.color || 'default'}
                        size="small"
                      />
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" noWrap>
                        {JSON.stringify(activity.details) !== '{}' ? JSON.stringify(activity.details) : activity.action}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {activity.ip_address}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Computer />
                        <Typography variant="body2">
                          {activity.user_agent || 'Unknown device'}
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
              <Grid size={{ xs: 12, md: 6 }} key={index}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Avatar>
                        {(() => {
                          const user = userLookup[session.user_id];
                          return user ? `${user.firstName?.[0] || ''}${user.lastName?.[0] || ''}` : 'U';
                        })()}
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1">
                          {(() => {
                            const user = userLookup[session.user_id];
                            return user ? `${user.firstName || ''} ${user.lastName || ''}`.trim() : `User ${session.user_id}`;
                          })()}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {userLookup[session.user_id]?.email || 'No email'}
                        </Typography>
                      </Box>
                      <Chip
                        label={session.is_current ? 'Current' : 'Expired'}
                        color={session.is_current ? 'success' : 'default'}
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
                          {session.user_agent || 'Unknown device'}
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