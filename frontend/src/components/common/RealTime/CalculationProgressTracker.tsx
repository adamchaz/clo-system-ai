/**
 * CalculationProgressTracker Component - Live Calculation Monitoring
 * 
 * Tracks and displays real-time progress of CLO calculations:
 * - Waterfall calculation progress with detailed steps
 * - Risk analysis and Monte Carlo simulation tracking
 * - Correlation matrix computation monitoring
 * - Scenario analysis progress with estimated completion times
 * 
 * Part of CLO Management System - TASK 12: Real-time Data and WebSocket Integration
 */
import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Collapse,
  Stack,
  Button,
  Tooltip,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Divider,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  ExpandMore,
  ExpandLess,
  Assessment,
  ShowChart,
  AccountBalance,
  ScatterPlot,
  Timer,
  CheckCircle,
  Error,
  Cancel,
  Refresh,
  Info,
  Visibility,
} from '@mui/icons-material';
import { format, formatDistanceToNow } from 'date-fns';
import { useCalculationProgress } from '../../../hooks/useRealTimeData';

interface CalculationProgressTrackerProps {
  compact?: boolean;
  showCompleted?: boolean;
  maxVisible?: number;
}

interface CalculationDetails {
  type: string;
  icon: React.ReactNode;
  color: string;
  description: string;
}

const CalculationProgressTracker: React.FC<CalculationProgressTrackerProps> = ({
  compact = false,
  showCompleted = false,
  maxVisible = 5,
}) => {
  const [expanded, setExpanded] = useState(!compact);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedCalculation, setSelectedCalculation] = useState(null);
  
  const {
    calculations,
    getActiveCalculations,
    clearCompleted,
  } = useCalculationProgress();

  const calculationTypes: Record<string, CalculationDetails> = {
    waterfall: {
      type: 'waterfall',
      icon: <AccountBalance />,
      color: '#1976d2',
      description: 'CLO Waterfall Calculation',
    },
    risk: {
      type: 'risk',
      icon: <Assessment />,
      color: '#d32f2f',
      description: 'Risk Analytics & VaR',
    },
    correlation: {
      type: 'correlation',
      icon: <ScatterPlot />,
      color: '#7b1fa2',
      description: 'Correlation Matrix Analysis',
    },
    scenario: {
      type: 'scenario',
      icon: <ShowChart />,
      color: '#f57c00',
      description: 'Scenario Analysis & Monte Carlo',
    },
  };

  const activeCalculations = getActiveCalculations();
  const visibleCalculations = useMemo(() => {
    let filtered = showCompleted 
      ? calculations 
      : calculations.filter(calc => calc.status === 'running');
    
    return filtered.slice(0, maxVisible);
  }, [calculations, showCompleted, maxVisible]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <PlayArrow color="primary" />;
      case 'completed':
        return <CheckCircle color="success" />;
      case 'failed':
        return <Error color="error" />;
      case 'cancelled':
        return <Cancel color="warning" />;
      default:
        return <Timer />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'primary';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatEstimatedTime = (seconds: number | undefined) => {
    if (!seconds) return 'Unknown';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const handleViewDetails = (calculation: any) => {
    setSelectedCalculation(calculation);
    setDetailDialogOpen(true);
  };

  if (compact && activeCalculations.length === 0) {
    return null;
  }

  return (
    <>
      <Card variant="outlined">
        <CardContent sx={{ pb: compact ? 2 : 3 }}>
          {/* Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant={compact ? "body2" : "h6"} fontWeight={600}>
                Running Calculations
              </Typography>
              <Badge badgeContent={activeCalculations.length} color="primary">
                <Assessment fontSize="small" />
              </Badge>
            </Box>
            
            <Box>
              {!compact && (
                <Tooltip title="Clear Completed">
                  <IconButton size="small" onClick={clearCompleted}>
                    <Refresh fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
              <Tooltip title={expanded ? "Collapse" : "Expand"}>
                <IconButton size="small" onClick={() => setExpanded(!expanded)}>
                  {expanded ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {/* Quick Status */}
          {!expanded && activeCalculations.length > 0 && (
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {activeCalculations.slice(0, 3).map((calc) => {
                const details = calculationTypes[calc.type] || calculationTypes.waterfall;
                return (
                  <Chip
                    key={calc.calculationId}
                    icon={details.icon as React.ReactElement}
                    label={`${calc.progress}%`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                );
              })}
              {activeCalculations.length > 3 && (
                <Chip 
                  label={`+${activeCalculations.length - 3} more`} 
                  size="small" 
                  variant="outlined" 
                />
              )}
            </Box>
          )}

          {/* Detailed View */}
          <Collapse in={expanded}>
            {visibleCalculations.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <Assessment sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  No active calculations
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Start a waterfall or risk calculation to see progress here
                </Typography>
              </Box>
            ) : (
              <Stack spacing={2}>
                {visibleCalculations.map((calculation) => {
                  const details = calculationTypes[calculation.type] || calculationTypes.waterfall;
                  const isActive = calculation.status === 'running';
                  
                  return (
                    <Card key={calculation.calculationId} variant="outlined" sx={{ p: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                        <Avatar 
                          sx={{ 
                            bgcolor: details.color, 
                            width: 40, 
                            height: 40,
                          }}
                        >
                          {details.icon}
                        </Avatar>
                        
                        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                            <Box>
                              <Typography variant="body2" fontWeight={600}>
                                {details.description}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                ID: {calculation.calculationId}
                              </Typography>
                            </Box>
                            
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip
                                icon={getStatusIcon(calculation.status)}
                                label={calculation.status}
                                size="small"
                                color={getStatusColor(calculation.status)}
                                variant="outlined"
                              />
                              <Tooltip title="View Details">
                                <IconButton 
                                  size="small" 
                                  onClick={() => handleViewDetails(calculation)}
                                >
                                  <Visibility fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </Box>
                          
                          {/* Progress Bar */}
                          {isActive && (
                            <Box sx={{ mb: 1 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                <Typography variant="caption" color="text.secondary">
                                  Progress: {calculation.progress}%
                                </Typography>
                                {calculation.estimatedTime && (
                                  <Typography variant="caption" color="text.secondary">
                                    ETA: {formatEstimatedTime(calculation.estimatedTime)}
                                  </Typography>
                                )}
                              </Box>
                              <LinearProgress 
                                variant="determinate" 
                                value={calculation.progress} 
                                sx={{ 
                                  height: 8, 
                                  borderRadius: 4,
                                  bgcolor: 'grey.200',
                                  '& .MuiLinearProgress-bar': {
                                    borderRadius: 4,
                                  },
                                }}
                              />
                            </Box>
                          )}
                          
                          {/* Status Message */}
                          {calculation.message && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              {calculation.message}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </Card>
                  );
                })}
                
                {/* Show More Button */}
                {calculations.length > maxVisible && (
                  <Button
                    variant="text"
                    onClick={() => setDetailDialogOpen(true)}
                    startIcon={<Info />}
                    sx={{ alignSelf: 'center' }}
                  >
                    View All ({calculations.length}) Calculations
                  </Button>
                )}
              </Stack>
            )}
          </Collapse>
        </CardContent>
      </Card>

      {/* Calculation Details Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Assessment />
            {selectedCalculation ? 'Calculation Details' : 'All Calculations'}
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {selectedCalculation ? (
            <Box>
              {/* Single calculation details */}
              <Typography variant="body2" paragraph>
                Detailed view of calculation {(selectedCalculation as any).calculationId}
              </Typography>
              {/* Add more detailed information here */}
            </Box>
          ) : (
            <List>
              {calculations.map((calc, index) => (
                <React.Fragment key={calc.calculationId}>
                  <ListItem>
                    <ListItemIcon>
                      {calculationTypes[calc.type]?.icon || <Assessment />}
                    </ListItemIcon>
                    <ListItemText
                      primary={calculationTypes[calc.type]?.description || calc.type}
                      secondary={`Status: ${calc.status} | Progress: ${calc.progress}%`}
                    />
                    <Chip
                      label={calc.status}
                      size="small"
                      color={getStatusColor(calc.status)}
                      variant="outlined"
                    />
                  </ListItem>
                  {index < calculations.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default CalculationProgressTracker;