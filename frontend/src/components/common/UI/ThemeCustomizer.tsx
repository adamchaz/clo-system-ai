/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * ThemeCustomizer - Advanced theme customization system
 * 
 * Features:
 * - Real-time theme preview
 * - Custom color palette creation
 * - Multiple theme presets
 * - Dark/light mode variants
 * - Typography customization
 * - Component styling overrides
 * - Save/load custom themes
 * - Export theme configuration
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Slider,
  Switch,
  FormControlLabel,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Drawer,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Chip,
  IconButton,
  Tooltip,
  Divider,
  Alert,
  Snackbar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  useTheme,
  alpha,
  createTheme,
  ThemeProvider,
} from '@mui/material';
import {
  Palette as PaletteIcon,
  TextFields as TypographyIcon,
  Tune as TuneIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Restore as RestoreIcon,
  Preview as PreviewIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  ColorLens as ColorLensIcon,
  FormatSize as FontSizeIcon,
} from '@mui/icons-material';
import { HexColorPicker, HexColorInput } from 'react-colorful';
import { useLocalStorage } from 'react-use';
import { motion, AnimatePresence } from 'framer-motion';
import { fadeVariants, staggerContainer, staggerItem, scaleVariants } from '../Animations/variants';

// Theme configuration interface
export interface CustomThemeConfig {
  id: string;
  name: string;
  description: string;
  palette: {
    mode: 'light' | 'dark';
    primary: {
      main: string;
      light?: string;
      dark?: string;
    };
    secondary: {
      main: string;
      light?: string;
      dark?: string;
    };
    error: { main: string };
    warning: { main: string };
    info: { main: string };
    success: { main: string };
    background: {
      default: string;
      paper: string;
    };
    text: {
      primary: string;
      secondary: string;
    };
  };
  typography: {
    fontFamily: string;
    fontSize: number;
    h1: { fontSize: string };
    h2: { fontSize: string };
    h3: { fontSize: string };
    h4: { fontSize: string };
    h5: { fontSize: string };
    h6: { fontSize: string };
  };
  spacing: number;
  borderRadius: number;
  shadows: {
    elevation: number;
    blur: number;
  };
}

interface ThemeCustomizerProps {
  open: boolean;
  onClose: () => void;
  currentTheme: CustomThemeConfig;
  onThemeChange: (theme: CustomThemeConfig) => void;
}

const ThemeCustomizer: React.FC<ThemeCustomizerProps> = ({
  open,
  onClose,
  currentTheme,
  onThemeChange,
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [previewTheme, setPreviewTheme] = useState<CustomThemeConfig>(currentTheme);
  const [savedThemes, setSavedThemes] = useLocalStorage<CustomThemeConfig[]>('custom-themes', []);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' as 'info' | 'success' | 'warning' | 'error' });

  // Color picker states
  const [activeColorPicker, setActiveColorPicker] = useState<string | null>(null);
  const [colorPickerValue, setColorPickerValue] = useState('#000000');

  // Predefined theme presets
  const themePresets: CustomThemeConfig[] = [
    {
      id: 'default-light',
      name: 'CLO Default Light',
      description: 'Standard light theme for professional use',
      palette: {
        mode: 'light',
        primary: { main: '#1976d2' },
        secondary: { main: '#dc004e' },
        error: { main: '#f44336' },
        warning: { main: '#ff9800' },
        info: { main: '#2196f3' },
        success: { main: '#4caf50' },
        background: { default: '#fafafa', paper: '#ffffff' },
        text: { primary: '#212121', secondary: '#757575' },
      },
      typography: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        fontSize: 14,
        h1: { fontSize: '2.5rem' },
        h2: { fontSize: '2rem' },
        h3: { fontSize: '1.75rem' },
        h4: { fontSize: '1.5rem' },
        h5: { fontSize: '1.25rem' },
        h6: { fontSize: '1rem' },
      },
      spacing: 8,
      borderRadius: 4,
      shadows: { elevation: 1, blur: 3 },
    },
    {
      id: 'default-dark',
      name: 'CLO Default Dark',
      description: 'Standard dark theme for extended use',
      palette: {
        mode: 'dark',
        primary: { main: '#90caf9' },
        secondary: { main: '#f48fb1' },
        error: { main: '#f44336' },
        warning: { main: '#ff9800' },
        info: { main: '#2196f3' },
        success: { main: '#4caf50' },
        background: { default: '#121212', paper: '#1e1e1e' },
        text: { primary: '#ffffff', secondary: '#b3b3b3' },
      },
      typography: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        fontSize: 14,
        h1: { fontSize: '2.5rem' },
        h2: { fontSize: '2rem' },
        h3: { fontSize: '1.75rem' },
        h4: { fontSize: '1.5rem' },
        h5: { fontSize: '1.25rem' },
        h6: { fontSize: '1rem' },
      },
      spacing: 8,
      borderRadius: 4,
      shadows: { elevation: 8, blur: 4 },
    },
    {
      id: 'financial-blue',
      name: 'Financial Blue',
      description: 'Professional blue theme for financial applications',
      palette: {
        mode: 'light',
        primary: { main: '#0d47a1' },
        secondary: { main: '#ff6f00' },
        error: { main: '#d32f2f' },
        warning: { main: '#f57c00' },
        info: { main: '#1976d2' },
        success: { main: '#388e3c' },
        background: { default: '#f8f9fa', paper: '#ffffff' },
        text: { primary: '#1a237e', secondary: '#5c6bc0' },
      },
      typography: {
        fontFamily: '"Inter", "Roboto", sans-serif',
        fontSize: 14,
        h1: { fontSize: '2.5rem' },
        h2: { fontSize: '2rem' },
        h3: { fontSize: '1.75rem' },
        h4: { fontSize: '1.5rem' },
        h5: { fontSize: '1.25rem' },
        h6: { fontSize: '1rem' },
      },
      spacing: 8,
      borderRadius: 8,
      shadows: { elevation: 2, blur: 6 },
    },
    {
      id: 'green-finance',
      name: 'Green Finance',
      description: 'Nature-inspired theme for sustainable finance',
      palette: {
        mode: 'light',
        primary: { main: '#2e7d32' },
        secondary: { main: '#ff8f00' },
        error: { main: '#c62828' },
        warning: { main: '#f57c00' },
        info: { main: '#0277bd' },
        success: { main: '#388e3c' },
        background: { default: '#f1f8e9', paper: '#ffffff' },
        text: { primary: '#1b5e20', secondary: '#4caf50' },
      },
      typography: {
        fontFamily: '"Source Sans Pro", "Roboto", sans-serif',
        fontSize: 15,
        h1: { fontSize: '2.5rem' },
        h2: { fontSize: '2rem' },
        h3: { fontSize: '1.75rem' },
        h4: { fontSize: '1.5rem' },
        h5: { fontSize: '1.25rem' },
        h6: { fontSize: '1rem' },
      },
      spacing: 10,
      borderRadius: 12,
      shadows: { elevation: 3, blur: 8 },
    },
  ];

  // Create Material-UI theme from config
  const createMuiTheme = useCallback((config: CustomThemeConfig) => {
    return createTheme({
      palette: {
        mode: config.palette.mode,
        primary: config.palette.primary,
        secondary: config.palette.secondary,
        error: config.palette.error,
        warning: config.palette.warning,
        info: config.palette.info,
        success: config.palette.success,
        background: config.palette.background,
        text: config.palette.text,
      },
      typography: {
        fontFamily: config.typography.fontFamily,
        fontSize: config.typography.fontSize,
        h1: { fontSize: config.typography.h1.fontSize },
        h2: { fontSize: config.typography.h2.fontSize },
        h3: { fontSize: config.typography.h3.fontSize },
        h4: { fontSize: config.typography.h4.fontSize },
        h5: { fontSize: config.typography.h5.fontSize },
        h6: { fontSize: config.typography.h6.fontSize },
      },
      spacing: config.spacing,
      shape: {
        borderRadius: config.borderRadius,
      },
      shadows: Array.from({ length: 25 }, (_, i) => 
        i === 0 ? 'none' : `0px ${i * config.shadows.elevation}px ${i * config.shadows.blur}px rgba(0,0,0,0.12)`
      ) as any,
    });
  }, []);

  const muiPreviewTheme = useMemo(() => createMuiTheme(previewTheme), [previewTheme, createMuiTheme]);

  // Update preview theme
  const updatePreviewTheme = useCallback((updates: Partial<CustomThemeConfig>) => {
    setPreviewTheme(prev => ({
      ...prev,
      ...updates,
    }));
  }, []);

  // Color picker handlers
  const handleColorChange = useCallback((colorPath: string, color: string) => {
    const pathParts = colorPath.split('.');
    const updates: any = {};
    let current = updates;
    
    for (let i = 0; i < pathParts.length - 1; i++) {
      current[pathParts[i]] = {};
      current = current[pathParts[i]];
    }
    current[pathParts[pathParts.length - 1]] = color;
    
    updatePreviewTheme(updates);
  }, [updatePreviewTheme]);

  // Apply theme
  const handleApplyTheme = useCallback(() => {
    onThemeChange(previewTheme);
    setSnackbar({
      open: true,
      message: 'Theme applied successfully!',
      severity: 'success',
    });
  }, [previewTheme, onThemeChange]);

  // Save theme
  const handleSaveTheme = useCallback(() => {
    const name = prompt('Enter theme name:');
    if (!name) return;

    const newTheme: CustomThemeConfig = {
      ...previewTheme,
      id: `custom-${Date.now()}`,
      name,
      description: `Custom theme created on ${new Date().toLocaleDateString()}`,
    };

    const updatedThemes = [...(savedThemes || []), newTheme];
    setSavedThemes(updatedThemes);
    
    setSnackbar({
      open: true,
      message: `Theme "${name}" saved successfully!`,
      severity: 'success',
    });
  }, [previewTheme, savedThemes, setSavedThemes]);

  // Load preset theme
  const handleLoadPreset = useCallback((preset: CustomThemeConfig) => {
    setPreviewTheme(preset);
    setSnackbar({
      open: true,
      message: `Preset "${preset.name}" loaded!`,
      severity: 'info',
    });
  }, []);

  // Export theme
  const handleExportTheme = useCallback(() => {
    const dataStr = JSON.stringify(previewTheme, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `theme-${previewTheme.name.toLowerCase().replace(/\s+/g, '-')}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }, [previewTheme]);

  // Color picker component
  const ColorPickerField: React.FC<{
    label: string;
    value: string;
    onChange: (color: string) => void;
    colorPath: string;
  }> = ({ label, value, onChange, colorPath }) => (
    <Box sx={{ mb: 2 }}>
      <Typography variant="body2" gutterBottom>{label}</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box
          sx={{
            width: 40,
            height: 40,
            bgcolor: value,
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            cursor: 'pointer',
          }}
          onClick={() => {
            setActiveColorPicker(colorPath);
            setColorPickerValue(value);
          }}
        />
        <TextField
          size="small"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          sx={{ flex: 1 }}
        />
      </Box>
    </Box>
  );

  // Tab panels
  const TabPanel: React.FC<{ children: React.ReactNode; value: number; index: number }> = ({
    children,
    value,
    index,
  }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );

  return (
    <>
      <Drawer
        anchor="right"
        open={open}
        onClose={onClose}
        PaperProps={{
          sx: { width: 450 },
        }}
      >
        <motion.div
          variants={fadeVariants}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Theme Customizer</Typography>
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
          
          <Divider />

          {/* Preview Section */}
          <ThemeProvider theme={muiPreviewTheme}>
            <Box sx={{ p: 2, bgcolor: 'background.default', color: 'text.primary' }}>
              <Typography variant="h6" gutterBottom>Preview</Typography>
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" color="primary">
                    Sample Card
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    This is how your theme will look with different components.
                  </Typography>
                  <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                    <Button variant="contained" size="small">Primary</Button>
                    <Button variant="outlined" size="small">Secondary</Button>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </ThemeProvider>

          <Divider />

          {/* Action Buttons */}
          <Box sx={{ p: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={<PreviewIcon />}
              onClick={handleApplyTheme}
              size="small"
            >
              Apply
            </Button>
            <Button
              variant="outlined"
              startIcon={<SaveIcon />}
              onClick={handleSaveTheme}
              size="small"
            >
              Save
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExportTheme}
              size="small"
            >
              Export
            </Button>
          </Box>

          <Divider />

          {/* Tabs */}
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} variant="scrollable">
            <Tab icon={<PaletteIcon />} label="Colors" />
            <Tab icon={<TypographyIcon />} label="Typography" />
            <Tab icon={<TuneIcon />} label="Spacing" />
            <Tab icon={<RestoreIcon />} label="Presets" />
          </Tabs>

          {/* Colors Tab */}
          <TabPanel value={activeTab} index={0}>
            <motion.div
              variants={staggerContainer}
              initial="initial"
              animate="animate"
            >
              {/* Mode Toggle */}
              <motion.div variants={staggerItem}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={previewTheme.palette.mode === 'dark'}
                      onChange={(e) => updatePreviewTheme({
                        palette: {
                          ...previewTheme.palette,
                          mode: e.target.checked ? 'dark' : 'light'
                        }
                      })}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {previewTheme.palette.mode === 'dark' ? <DarkModeIcon /> : <LightModeIcon />}
                      Dark Mode
                    </Box>
                  }
                />
              </motion.div>

              <Divider sx={{ my: 2 }} />

              {/* Primary Colors */}
              <motion.div variants={staggerItem}>
                <Typography variant="subtitle1" gutterBottom>Primary Colors</Typography>
                <ColorPickerField
                  label="Primary Main"
                  value={previewTheme.palette.primary.main}
                  onChange={(color) => handleColorChange('palette.primary.main', color)}
                  colorPath="palette.primary.main"
                />
              </motion.div>

              {/* Secondary Colors */}
              <motion.div variants={staggerItem}>
                <Typography variant="subtitle1" gutterBottom>Secondary Colors</Typography>
                <ColorPickerField
                  label="Secondary Main"
                  value={previewTheme.palette.secondary.main}
                  onChange={(color) => handleColorChange('palette.secondary.main', color)}
                  colorPath="palette.secondary.main"
                />
              </motion.div>

              {/* Status Colors */}
              <motion.div variants={staggerItem}>
                <Typography variant="subtitle1" gutterBottom>Status Colors</Typography>
                <ColorPickerField
                  label="Error"
                  value={previewTheme.palette.error.main}
                  onChange={(color) => handleColorChange('palette.error.main', color)}
                  colorPath="palette.error.main"
                />
                <ColorPickerField
                  label="Warning"
                  value={previewTheme.palette.warning.main}
                  onChange={(color) => handleColorChange('palette.warning.main', color)}
                  colorPath="palette.warning.main"
                />
                <ColorPickerField
                  label="Success"
                  value={previewTheme.palette.success.main}
                  onChange={(color) => handleColorChange('palette.success.main', color)}
                  colorPath="palette.success.main"
                />
              </motion.div>

              {/* Background Colors */}
              <motion.div variants={staggerItem}>
                <Typography variant="subtitle1" gutterBottom>Background Colors</Typography>
                <ColorPickerField
                  label="Background Default"
                  value={previewTheme.palette.background.default}
                  onChange={(color) => handleColorChange('palette.background.default', color)}
                  colorPath="palette.background.default"
                />
                <ColorPickerField
                  label="Paper Background"
                  value={previewTheme.palette.background.paper}
                  onChange={(color) => handleColorChange('palette.background.paper', color)}
                  colorPath="palette.background.paper"
                />
              </motion.div>
            </motion.div>
          </TabPanel>

          {/* Typography Tab */}
          <TabPanel value={activeTab} index={1}>
            <motion.div
              variants={staggerContainer}
              initial="initial"
              animate="animate"
            >
              <motion.div variants={staggerItem}>
                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>Font Family</InputLabel>
                  <Select
                    value={previewTheme.typography.fontFamily}
                    onChange={(e) => updatePreviewTheme({
                      typography: {
                        ...previewTheme.typography,
                        fontFamily: e.target.value as string
                      }
                    })}
                  >
                    <MenuItem value='"Roboto", "Helvetica", "Arial", sans-serif'>Roboto</MenuItem>
                    <MenuItem value='"Inter", "Roboto", sans-serif'>Inter</MenuItem>
                    <MenuItem value='"Source Sans Pro", "Roboto", sans-serif'>Source Sans Pro</MenuItem>
                    <MenuItem value='"Poppins", "Roboto", sans-serif'>Poppins</MenuItem>
                    <MenuItem value='"Open Sans", "Roboto", sans-serif'>Open Sans</MenuItem>
                  </Select>
                </FormControl>
              </motion.div>

              <motion.div variants={staggerItem}>
                <Typography gutterBottom>Base Font Size</Typography>
                <Slider
                  value={previewTheme.typography.fontSize}
                  onChange={(_, value) => updatePreviewTheme({
                    typography: {
                      ...previewTheme.typography,
                      fontSize: value as number
                    }
                  })}
                  min={12}
                  max={18}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </motion.div>
            </motion.div>
          </TabPanel>

          {/* Spacing Tab */}
          <TabPanel value={activeTab} index={2}>
            <motion.div
              variants={staggerContainer}
              initial="initial"
              animate="animate"
            >
              <motion.div variants={staggerItem}>
                <Typography gutterBottom>Spacing Unit</Typography>
                <Slider
                  value={previewTheme.spacing}
                  onChange={(_, value) => updatePreviewTheme({ spacing: value as number })}
                  min={4}
                  max={16}
                  step={2}
                  marks
                  valueLabelDisplay="auto"
                />
              </motion.div>

              <motion.div variants={staggerItem}>
                <Typography gutterBottom>Border Radius</Typography>
                <Slider
                  value={previewTheme.borderRadius}
                  onChange={(_, value) => updatePreviewTheme({ borderRadius: value as number })}
                  min={0}
                  max={20}
                  step={2}
                  marks
                  valueLabelDisplay="auto"
                />
              </motion.div>

              <motion.div variants={staggerItem}>
                <Typography gutterBottom>Shadow Elevation</Typography>
                <Slider
                  value={previewTheme.shadows.elevation}
                  onChange={(_, value) => updatePreviewTheme({
                    shadows: { ...previewTheme.shadows, elevation: value as number }
                  })}
                  min={1}
                  max={5}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </motion.div>
            </motion.div>
          </TabPanel>

          {/* Presets Tab */}
          <TabPanel value={activeTab} index={3}>
            <motion.div
              variants={staggerContainer}
              initial="initial"
              animate="animate"
            >
              <Typography variant="subtitle1" gutterBottom>Built-in Presets</Typography>
              <Grid container spacing={2}>
                {themePresets.map((preset) => (
                  <Grid size={12} key={preset.id}>
                    <motion.div variants={staggerItem}>
                      <Card>
                        <CardContent sx={{ pb: 1 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            {preset.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {preset.description}
                          </Typography>
                          <Box sx={{ mt: 1, display: 'flex', gap: 0.5 }}>
                            <Box
                              sx={{
                                width: 16,
                                height: 16,
                                bgcolor: preset.palette.primary.main,
                                borderRadius: '50%',
                                border: 1,
                                borderColor: 'divider',
                              }}
                            />
                            <Box
                              sx={{
                                width: 16,
                                height: 16,
                                bgcolor: preset.palette.secondary.main,
                                borderRadius: '50%',
                                border: 1,
                                borderColor: 'divider',
                              }}
                            />
                            {preset.palette.mode === 'dark' && (
                              <Chip label="Dark" size="small" />
                            )}
                          </Box>
                        </CardContent>
                        <CardActions>
                          <Button
                            size="small"
                            onClick={() => handleLoadPreset(preset)}
                          >
                            Load
                          </Button>
                        </CardActions>
                      </Card>
                    </motion.div>
                  </Grid>
                ))}
              </Grid>

              {/* Saved Themes */}
              {savedThemes && savedThemes.length > 0 && (
                <>
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
                    Saved Themes
                  </Typography>
                  <Grid container spacing={2}>
                    {savedThemes.map((savedTheme) => (
                      <Grid size={12} key={savedTheme.id}>
                        <motion.div variants={staggerItem}>
                          <Card>
                            <CardContent sx={{ pb: 1 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                {savedTheme.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {savedTheme.description}
                              </Typography>
                            </CardContent>
                            <CardActions>
                              <Button
                                size="small"
                                onClick={() => handleLoadPreset(savedTheme)}
                              >
                                Load
                              </Button>
                              <Button
                                size="small"
                                color="error"
                                onClick={() => {
                                  const updated = savedThemes.filter(t => t.id !== savedTheme.id);
                                  setSavedThemes(updated);
                                }}
                              >
                                Delete
                              </Button>
                            </CardActions>
                          </Card>
                        </motion.div>
                      </Grid>
                    ))}
                  </Grid>
                </>
              )}
            </motion.div>
          </TabPanel>
        </motion.div>
      </Drawer>

      {/* Color Picker Popover */}
      <AnimatePresence>
        {activeColorPicker && (
          <motion.div
            variants={fadeVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: theme.zIndex.modal,
              backgroundColor: alpha(theme.palette.background.default, 0.8),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
            onTap={() => setActiveColorPicker(null)}
          >
            <div onClick={(e) => e.stopPropagation()}>
              <motion.div
                variants={scaleVariants}
              >
              <Paper elevation={8} sx={{ p: 3 }}>
                <HexColorPicker
                  color={colorPickerValue}
                  onChange={(color) => {
                    setColorPickerValue(color);
                    handleColorChange(activeColorPicker, color);
                  }}
                />
                <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                  <HexColorInput
                    color={colorPickerValue}
                    onChange={(color) => {
                      setColorPickerValue(color);
                      handleColorChange(activeColorPicker, color);
                    }}
                    prefixed
                    style={{
                      padding: '8px',
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: '4px',
                      fontSize: '14px',
                      fontFamily: 'monospace',
                    }}
                  />
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => setActiveColorPicker(null)}
                  >
                    Done
                  </Button>
                </Box>
              </Paper>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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

export default ThemeCustomizer;