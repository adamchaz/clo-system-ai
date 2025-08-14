import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Chip,
  IconButton,
  Button,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Badge,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Warning,
  Error,
  Info,
  CheckCircle,
  Delete,
  Visibility,
  FilterList,
  Search,
  Refresh,
  NotificationsActive,
  NotificationsOff,
  Archive,
  ClearAll,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';
import {
  useGetSystemAlertsQuery,
  useAcknowledgeAlertMutation,
  useDismissAlertMutation,
  SystemAlert,
} from '../../store/api/cloApi';

interface AlertFilters {
  type: string;
  acknowledged: boolean | null;
  search: string;
}

interface AlertDetailsDialogProps {
  open: boolean;
  onClose: () => void;
  alert: SystemAlert | null;
}

const AlertDetailsDialog: React.FC<AlertDetailsDialogProps> = ({
  open,
  onClose,
  alert,
}) => {
  if (!alert) return null;

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <Error color="error" />;
      case 'warning':
        return <Warning color="warning" />;
      case 'info':
      default:
        return <Info color="info" />;
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
      default:
        return 'info';
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {getAlertIcon(alert.type)}
          <Typography variant="h6" sx={{ ml: 1 }}>
            Alert Details
          </Typography>
          <Chip
            label={alert.type.toUpperCase()}
            color={getAlertColor(alert.type)}
            size="small"
            sx={{ ml: 'auto' }}
          />
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            {alert.title}
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            {alert.message}
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Alert ID:
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {alert.id}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Source:
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {alert.source}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Timestamp:
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {format(new Date(alert.timestamp), 'PPpp')}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Time Ago:
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Status:
            </Typography>
            <Chip
              label={alert.acknowledged ? 'Acknowledged' : 'Pending'}
              color={alert.acknowledged ? 'success' : 'warning'}
              size="small"
            />
          </Box>
        </Box>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

interface AlertCenterProps {
  compact?: boolean; // For dashboard display
  maxItems?: number; // For dashboard display
}

const AlertCenter: React.FC<AlertCenterProps> = ({ 
  compact = false, 
  maxItems 
}) => {
  // State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(compact ? 5 : 25);
  const [filters, setFilters] = useState<AlertFilters>({
    type: '',
    acknowledged: null,
    search: '',
  });
  const [selectedAlert, setSelectedAlert] = useState<SystemAlert | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  // API hooks
  const {
    data: alertsData,
    isLoading,
    error,
    refetch,
  } = useGetSystemAlertsQuery({
    skip: page * rowsPerPage,
    limit: maxItems || rowsPerPage,
    type: filters.type || undefined,
    acknowledged: filters.acknowledged ?? undefined,
  });

  const [acknowledgeAlert, { isLoading: acknowledgeLoading }] = useAcknowledgeAlertMutation();
  const [dismissAlert, { isLoading: dismissLoading }] = useDismissAlertMutation();

  // Handlers
  const handleChangePage = useCallback((event: unknown, newPage: number) => {
    setPage(newPage);
  }, []);

  const handleChangeRowsPerPage = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  }, []);

  const handleFilterChange = useCallback((field: keyof AlertFilters, value: any) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPage(0);
  }, []);

  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    // Update filters based on tab
    switch (newValue) {
      case 0: // All
        handleFilterChange('acknowledged', null);
        break;
      case 1: // Pending
        handleFilterChange('acknowledged', false);
        break;
      case 2: // Acknowledged
        handleFilterChange('acknowledged', true);
        break;
    }
  }, [handleFilterChange]);

  const handleViewDetails = useCallback((alert: SystemAlert) => {
    setSelectedAlert(alert);
    setDetailsOpen(true);
  }, []);

  const handleAcknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId).unwrap();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  }, [acknowledgeAlert]);

  const handleDismissAlert = useCallback(async (alertId: string) => {
    try {
      await dismissAlert(alertId).unwrap();
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
    }
  }, [dismissAlert]);

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <Error color="error" fontSize="small" />;
      case 'warning':
        return <Warning color="warning" fontSize="small" />;
      case 'info':
      default:
        return <Info color="info" fontSize="small" />;
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
      default:
        return 'info';
    }
  };

  const getAlertCounts = () => {
    const allAlerts = alertsData?.data || [];
    return {
      total: allAlerts.length,
      pending: allAlerts.filter(alert => !alert.acknowledged).length,
      acknowledged: allAlerts.filter(alert => alert.acknowledged).length,
    };
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Failed to load system alerts. Please check your connection and try again.
      </Alert>
    );
  }

  const counts = getAlertCounts();

  // Compact view for dashboard
  if (compact) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <NotificationsActive color="warning" sx={{ mr: 1 }} />
              <Typography variant="h6">System Alerts</Typography>
            </Box>
            <Badge badgeContent={counts.pending} color="error">
              <Button size="small" onClick={() => refetch()}>
                <Refresh fontSize="small" />
              </Button>
            </Badge>
          </Box>

          <List dense>
            {isLoading ? (
              <ListItem>
                <ListItemText primary="Loading alerts..." />
              </ListItem>
            ) : alertsData?.data?.length === 0 ? (
              <ListItem>
                <ListItemText 
                  primary="No active alerts" 
                  secondary="System is operating normally"
                />
              </ListItem>
            ) : (
              alertsData?.data?.slice(0, maxItems || 5).map((alert) => (
                <ListItem key={alert.id} divider>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', width: '100%' }}>
                    {getAlertIcon(alert.type)}
                    <Box sx={{ ml: 1, flexGrow: 1 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {alert.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                      </Typography>
                    </Box>
                    <ListItemSecondaryAction>
                      <IconButton
                        size="small"
                        onClick={() => handleViewDetails(alert)}
                      >
                        <Visibility fontSize="small" />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </Box>
                </ListItem>
              ))
            )}
          </List>
        </CardContent>
      </Card>
    );
  }

  // Full view for dedicated alert management page
  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Alert Center
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Monitor and manage system alerts and notifications
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Refresh />}
              onClick={() => refetch()}
              disabled={isLoading}
            >
              Refresh
            </Button>
          </Box>
        </Box>

        {/* Tabs */}
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 2 }}>
          <Tab 
            label={
              <Badge badgeContent={counts.total} color="primary" showZero>
                All Alerts
              </Badge>
            } 
          />
          <Tab 
            label={
              <Badge badgeContent={counts.pending} color="error">
                Pending
              </Badge>
            } 
          />
          <Tab 
            label={
              <Badge badgeContent={counts.acknowledged} color="success">
                Acknowledged
              </Badge>
            } 
          />
        </Tabs>

        {/* Filters */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
          <TextField
            size="small"
            placeholder="Search alerts..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 250 }}
          />
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Type</InputLabel>
            <Select
              value={filters.type}
              onChange={(e) => handleFilterChange('type', e.target.value)}
              label="Type"
            >
              <MenuItem value="">All Types</MenuItem>
              <MenuItem value="error">Error</MenuItem>
              <MenuItem value="warning">Warning</MenuItem>
              <MenuItem value="info">Info</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Alerts Table */}
        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Alert</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Timestamp</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    Loading alerts...
                  </TableCell>
                </TableRow>
              ) : alertsData?.data?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      No alerts found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                alertsData?.data?.map((alert) => (
                  <TableRow key={alert.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getAlertIcon(alert.type)}
                        <Chip
                          label={alert.type}
                          color={getAlertColor(alert.type)}
                          size="small"
                          variant="outlined"
                          sx={{ ml: 1 }}
                        />
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>
                          {alert.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {alert.message.length > 100 
                            ? `${alert.message.substring(0, 100)}...` 
                            : alert.message
                          }
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2">
                        {alert.source}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Box>
                        <Typography variant="body2">
                          {format(new Date(alert.timestamp), 'MMM dd, HH:mm')}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Chip
                        label={alert.acknowledged ? 'Acknowledged' : 'Pending'}
                        color={alert.acknowledged ? 'success' : 'warning'}
                        size="small"
                        icon={alert.acknowledged ? <CheckCircle /> : <Warning />}
                      />
                    </TableCell>
                    
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5 }}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => handleViewDetails(alert)}
                          >
                            <Visibility fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        
                        {!alert.acknowledged && (
                          <Tooltip title="Acknowledge">
                            <IconButton
                              size="small"
                              onClick={() => handleAcknowledgeAlert(alert.id)}
                              disabled={acknowledgeLoading}
                              color="success"
                            >
                              <CheckCircle fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        <Tooltip title="Dismiss">
                          <IconButton
                            size="small"
                            onClick={() => handleDismissAlert(alert.id)}
                            disabled={dismissLoading}
                            color="error"
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={alertsData?.total || 0}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />

        {/* Alert Details Dialog */}
        <AlertDetailsDialog
          open={detailsOpen}
          onClose={() => setDetailsOpen(false)}
          alert={selectedAlert}
        />
      </CardContent>
    </Card>
  );
};

export default AlertCenter;