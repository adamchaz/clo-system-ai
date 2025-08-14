/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * DashboardCustomizer - Drag and drop dashboard customization
 * 
 * Features:
 * - Drag and drop dashboard widgets
 * - Resizable dashboard components
 * - Save/restore dashboard layouts
 * - Pre-defined layout templates
 * - Widget catalog and management
 * - Real-time preview of changes
 * - Responsive layout handling
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  Switch,
  FormControlLabel,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Tooltip,
  Alert,
  Snackbar,
  useTheme,
  alpha,
} from '@mui/material';
import {
  DragIndicator,
  Add as AddIcon,
  Remove as RemoveIcon,
  Settings as SettingsIcon,
  SaveAlt as SaveIcon,
  RestoreFromTrash as RestoreIcon,
  ViewModule as LayoutIcon,
  Widgets as WidgetsIcon,
  Dashboard as DashboardIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  AccountBalance as AccountBalanceIcon,
  PieChart as PieChartIcon,
  BarChart as BarChartIcon,
  Close as CloseIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { useLocalStorage } from 'react-use';
import { motion, AnimatePresence } from 'framer-motion';
import { fadeVariants, scaleVariants, staggerContainer, staggerItem } from '../Animations/variants';

// Widget types
export interface DashboardWidget {
  id: string;
  type: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  component: React.ComponentType<any>;
  defaultProps?: any;
  size: {
    width: number;
    height: number;
    minWidth?: number;
    minHeight?: number;
    maxWidth?: number;
    maxHeight?: number;
  };
  category: 'analytics' | 'portfolio' | 'risk' | 'performance' | 'system';
  isResizable?: boolean;
  isRemovable?: boolean;
}

// Layout definition
export interface DashboardLayout {
  id: string;
  name: string;
  description: string;
  widgets: Array<{
    widgetId: string;
    position: { x: number; y: number };
    size: { width: number; height: number };
    props?: any;
  }>;
  gridSize: { cols: number; rows: number };
}

interface DashboardCustomizerProps {
  currentLayout: DashboardLayout;
  availableWidgets: DashboardWidget[];
  onLayoutChange: (layout: DashboardLayout) => void;
  onWidgetAdd: (widget: DashboardWidget) => void;
  onWidgetRemove: (widgetId: string) => void;
  isCustomizing: boolean;
  onToggleCustomizing: (customizing: boolean) => void;
}

const DashboardCustomizer: React.FC<DashboardCustomizerProps> = ({
  currentLayout,
  availableWidgets,
  onLayoutChange,
  onWidgetAdd,
  onWidgetRemove,
  isCustomizing,
  onToggleCustomizing,
}) => {
  const theme = useTheme();
  const [widgetDrawerOpen, setWidgetDrawerOpen] = useState(false);
  const [layoutDialogOpen, setLayoutDialogOpen] = useState(false);
  const [savedLayouts, setSavedLayouts] = useLocalStorage<DashboardLayout[]>('dashboard-layouts', []);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' as 'info' | 'success' | 'warning' | 'error' });

  // Predefined layout templates
  const layoutTemplates: Partial<DashboardLayout>[] = [
    {
      name: 'Executive Summary',
      description: 'High-level overview with key metrics',
      widgets: [
        { widgetId: 'portfolio-summary', position: { x: 0, y: 0 }, size: { width: 6, height: 3 } },
        { widgetId: 'performance-chart', position: { x: 6, y: 0 }, size: { width: 6, height: 3 } },
        { widgetId: 'risk-metrics', position: { x: 0, y: 3 }, size: { width: 4, height: 2 } },
        { widgetId: 'alerts', position: { x: 4, y: 3 }, size: { width: 8, height: 2 } },
      ],
    },
    {
      name: 'Risk Analysis',
      description: 'Comprehensive risk monitoring',
      widgets: [
        { widgetId: 'correlation-heatmap', position: { x: 0, y: 0 }, size: { width: 8, height: 4 } },
        { widgetId: 'var-chart', position: { x: 8, y: 0 }, size: { width: 4, height: 2 } },
        { widgetId: 'stress-test', position: { x: 8, y: 2 }, size: { width: 4, height: 2 } },
        { widgetId: 'risk-alerts', position: { x: 0, y: 4 }, size: { width: 12, height: 2 } },
      ],
    },
    {
      name: 'Portfolio Performance',
      description: 'Detailed performance tracking',
      widgets: [
        { widgetId: 'performance-chart', position: { x: 0, y: 0 }, size: { width: 8, height: 3 } },
        { widgetId: 'benchmark-comparison', position: { x: 8, y: 0 }, size: { width: 4, height: 3 } },
        { widgetId: 'asset-allocation', position: { x: 0, y: 3 }, size: { width: 6, height: 3 } },
        { widgetId: 'top-performers', position: { x: 6, y: 3 }, size: { width: 6, height: 3 } },
      ],
    },
  ];

  // Handle drag end for reordering widgets
  const handleDragEnd = useCallback((result: DropResult) => {
    if (!result.destination) return;

    const items = Array.from(currentLayout.widgets);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    onLayoutChange({
      ...currentLayout,
      widgets: items,
    });
  }, [currentLayout, onLayoutChange]);

  // Save current layout
  const handleSaveLayout = useCallback(() => {
    const name = prompt('Enter layout name:');
    if (!name) return;

    const newLayout: DashboardLayout = {
      ...currentLayout,
      id: `layout-${Date.now()}`,
      name,
      description: `Custom layout created on ${new Date().toLocaleDateString()}`,
    };

    const updatedLayouts = [...(savedLayouts || []), newLayout];
    setSavedLayouts(updatedLayouts);
    
    setSnackbar({
      open: true,
      message: `Layout "${name}" saved successfully!`,
      severity: 'success',
    });
  }, [currentLayout, savedLayouts, setSavedLayouts]);

  // Load saved layout
  const handleLoadLayout = useCallback((layout: DashboardLayout) => {
    onLayoutChange(layout);
    setLayoutDialogOpen(false);
    
    setSnackbar({
      open: true,
      message: `Layout "${layout.name}" loaded successfully!`,
      severity: 'success',
    });
  }, [onLayoutChange]);

  // Apply layout template
  const handleApplyTemplate = useCallback((template: Partial<DashboardLayout>) => {
    const newLayout: DashboardLayout = {
      id: currentLayout.id,
      name: template.name || 'Custom Layout',
      description: template.description || '',
      widgets: template.widgets || [],
      gridSize: template.gridSize || { cols: 12, rows: 6 },
    };

    onLayoutChange(newLayout);
    setLayoutDialogOpen(false);
    
    setSnackbar({
      open: true,
      message: `Template "${template.name}" applied successfully!`,
      severity: 'success',
    });
  }, [currentLayout.id, onLayoutChange]);

  // Widget categories
  const widgetsByCategory = availableWidgets.reduce((acc, widget) => {
    if (!acc[widget.category]) {
      acc[widget.category] = [];
    }
    acc[widget.category].push(widget);
    return acc;
  }, {} as Record<string, DashboardWidget[]>);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'analytics': return <AnalyticsIcon />;
      case 'portfolio': return <AccountBalanceIcon />;
      case 'risk': return <PieChartIcon />;
      case 'performance': return <TrendingUpIcon />;
      case 'system': return <DashboardIcon />;
      default: return <WidgetsIcon />;
    }
  };

  return (
    <>
      {/* Customization Controls */}
      <AnimatePresence>
        {isCustomizing && (
          <motion.div
            variants={fadeVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            <Paper
              elevation={3}
              sx={{
                position: 'fixed',
                top: 80,
                right: 16,
                zIndex: theme.zIndex.speedDial,
                p: 1,
                bgcolor: alpha(theme.palette.background.paper, 0.95),
                backdropFilter: 'blur(10px)',
                borderRadius: 2,
              }}
            >
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Tooltip title="Add Widget">
                  <IconButton
                    size="small"
                    onClick={() => setWidgetDrawerOpen(true)}
                    color="primary"
                  >
                    <AddIcon />
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Layout Templates">
                  <IconButton
                    size="small"
                    onClick={() => setLayoutDialogOpen(true)}
                    color="primary"
                  >
                    <LayoutIcon />
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Save Layout">
                  <IconButton
                    size="small"
                    onClick={handleSaveLayout}
                    color="primary"
                  >
                    <SaveIcon />
                  </IconButton>
                </Tooltip>
                
                <Divider orientation="vertical" flexItem />
                
                <Tooltip title="Exit Customization">
                  <IconButton
                    size="small"
                    onClick={() => onToggleCustomizing(false)}
                  >
                    <CloseIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Paper>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Drag and Drop Context */}
      <DragDropContext onDragEnd={handleDragEnd}>
        <Droppable droppableId="dashboard">
          {(provided, snapshot) => (
            <Box
              {...provided.droppableProps}
              ref={provided.innerRef}
              sx={{
                minHeight: '100vh',
                bgcolor: snapshot.isDraggingOver ? alpha(theme.palette.primary.main, 0.05) : 'transparent',
                transition: theme.transitions.create('background-color'),
                position: 'relative',
              }}
            >
              <Grid container spacing={2} sx={{ p: 2 }}>
                {currentLayout.widgets.map((widget, index) => {
                  const widgetConfig = availableWidgets.find(w => w.id === widget.widgetId);
                  if (!widgetConfig) return null;

                  return (
                    <Draggable
                      key={widget.widgetId}
                      draggableId={widget.widgetId}
                      index={index}
                      isDragDisabled={!isCustomizing}
                    >
                      {(provided, snapshot) => (
                        <Grid
                          item
                          xs={widget.size.width}
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                        >
                          <motion.div
                            variants={scaleVariants}
                            initial="initial"
                            animate="animate"
                            whileHover={isCustomizing ? "hover" : undefined}
                            layout
                          >
                            <Paper
                              elevation={snapshot.isDragging ? 8 : 2}
                              sx={{
                                height: widget.size.height * 100,
                                position: 'relative',
                                overflow: 'hidden',
                                border: isCustomizing ? 2 : 0,
                                borderColor: 'primary.main',
                                borderStyle: 'dashed',
                              }}
                            >
                              {/* Drag Handle */}
                              {isCustomizing && (
                                <Box
                                  {...provided.dragHandleProps}
                                  sx={{
                                    position: 'absolute',
                                    top: 8,
                                    right: 8,
                                    zIndex: 10,
                                    bgcolor: alpha(theme.palette.background.paper, 0.9),
                                    borderRadius: 1,
                                    p: 0.5,
                                    cursor: 'grab',
                                    '&:active': {
                                      cursor: 'grabbing',
                                    },
                                  }}
                                >
                                  <DragIndicator fontSize="small" />
                                </Box>
                              )}

                              {/* Remove Button */}
                              {isCustomizing && widgetConfig.isRemovable && (
                                <IconButton
                                  size="small"
                                  onClick={() => onWidgetRemove(widget.widgetId)}
                                  sx={{
                                    position: 'absolute',
                                    top: 8,
                                    left: 8,
                                    zIndex: 10,
                                    bgcolor: alpha(theme.palette.error.main, 0.9),
                                    color: 'white',
                                    '&:hover': {
                                      bgcolor: theme.palette.error.dark,
                                    },
                                  }}
                                >
                                  <RemoveIcon fontSize="small" />
                                </IconButton>
                              )}

                              {/* Widget Content */}
                              <Box sx={{ p: 2, height: '100%' }}>
                                <Typography variant="h6" gutterBottom>
                                  {widgetConfig.title}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" paragraph>
                                  {widgetConfig.description}
                                </Typography>
                                
                                {/* Placeholder for actual widget component */}
                                <Box
                                  sx={{
                                    height: '60%',
                                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                                    borderRadius: 1,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                >
                                  {widgetConfig.icon}
                                </Box>
                              </Box>
                            </Paper>
                          </motion.div>
                        </Grid>
                      )}
                    </Draggable>
                  );
                })}
              </Grid>
              {provided.placeholder}
            </Box>
          )}
        </Droppable>
      </DragDropContext>

      {/* Widget Catalog Drawer */}
      <Drawer
        anchor="right"
        open={widgetDrawerOpen}
        onClose={() => setWidgetDrawerOpen(false)}
        PaperProps={{
          sx: { width: 400 },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Widget Catalog
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Drag widgets to your dashboard or click to add them
          </Typography>
        </Box>
        
        <Divider />

        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          {Object.entries(widgetsByCategory).map(([category, widgets]) => (
            <Box key={category} sx={{ p: 2 }}>
              <Typography variant="subtitle1" color="primary.main" gutterBottom>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getCategoryIcon(category)}
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </Box>
              </Typography>
              
              <Grid container spacing={1}>
                {widgets.map(widget => (
                  <Grid {...({ item: true } as any)} size={12} key={widget.id}>
                    <motion.div variants={staggerItem}>
                      <Card
                        sx={{
                          cursor: 'pointer',
                          '&:hover': {
                            bgcolor: alpha(theme.palette.primary.main, 0.05),
                          },
                        }}
                        onClick={() => onWidgetAdd(widget)}
                      >
                        <CardContent sx={{ p: 1.5 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {widget.icon}
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="body2" fontWeight="medium">
                                {widget.title}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {widget.size.width}x{widget.size.height}
                              </Typography>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                ))}
              </Grid>
            </Box>
          ))}
        </motion.div>
      </Drawer>

      {/* Layout Templates Dialog */}
      <Dialog
        open={layoutDialogOpen}
        onClose={() => setLayoutDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Dashboard Layouts
        </DialogTitle>
        
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            Choose from pre-defined templates or your saved layouts
          </Typography>

          {/* Templates */}
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Templates
          </Typography>
          <Grid container spacing={2}>
            {layoutTemplates.map((template, index) => (
              <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      {template.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {template.description}
                    </Typography>
                    <Chip
                      label={`${template.widgets?.length} widgets`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      onClick={() => handleApplyTemplate(template)}
                      startIcon={<RestoreIcon />}
                    >
                      Apply
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Saved Layouts */}
          {savedLayouts && savedLayouts.length > 0 && (
            <>
              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Saved Layouts
              </Typography>
              <Grid container spacing={2}>
                {savedLayouts.map((layout) => (
                  <Grid {...({ item: true } as any)} size={{ xs: 12, sm: 6 }} key={layout.id}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle1" gutterBottom>
                          {layout.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {layout.description}
                        </Typography>
                        <Chip
                          label={`${layout.widgets.length} widgets`}
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                      </CardContent>
                      <CardActions>
                        <Button
                          size="small"
                          onClick={() => handleLoadLayout(layout)}
                          startIcon={<RestoreIcon />}
                        >
                          Load
                        </Button>
                        <Button
                          size="small"
                          color="error"
                          onClick={() => {
                            const updated = savedLayouts.filter(l => l.id !== layout.id);
                            setSavedLayouts(updated);
                          }}
                        >
                          Delete
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setLayoutDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default DashboardCustomizer;