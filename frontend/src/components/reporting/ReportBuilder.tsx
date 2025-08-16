/**
 * ReportBuilder Component - Advanced Report Creation Interface
 * 
 * Comprehensive report builder featuring:
 * - Template-based report creation with customization
 * - Dynamic parameter configuration and data source selection
 * - Multi-step wizard interface for report design
 * - Real-time preview and validation
 * - Schedule and delivery options
 * - Export format selection (PDF, Excel, CSV)
 * 
 * Integrates with Report Management APIs and WebSocket for progress tracking
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Checkbox,
  Paper,
  Stack,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  LinearProgress,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Assessment,
  Description,
  Schedule,
  Settings,
  Preview,
  Save,
  Send,
  Download,
  Add,
  Remove,
  ExpandMore,
  Info,
  Warning,
  CheckCircle,
  PlayArrow,
  Stop,
  Refresh,
  FilterList,
  DateRange,
  PictureAsPdf,
  TableChart,
  InsertChart,
  Email,
  Share,
  Repeat,
} from '@mui/icons-material';
import { format } from 'date-fns';

// Import API hooks
import {
  useGetReportTemplatesQuery,
  useCreateReportMutation,
  useGetReportProgressQuery,
} from '../../store/api/cloApi';

// Import types
import {
  ReportCreateRequest,
  ReportTemplate,
  ReportGenerationProgress,
} from '../../store/api/newApiTypes';

// Import WebSocket hooks
import { useReportUpdates } from '../../hooks/useWebSocket';

interface ReportBuilderProps {
  templateId?: string; // Optional template to start with
  onReportCreated?: (reportId: string) => void;
  onClose?: () => void;
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

const ReportTypes = [
  { value: 'portfolio_performance', label: 'Portfolio Performance', icon: <Assessment /> },
  { value: 'risk_analysis', label: 'Risk Analysis', icon: <Warning /> },
  { value: 'compliance_report', label: 'Compliance Report', icon: <CheckCircle /> },
  { value: 'waterfall_analysis', label: 'Waterfall Analysis', icon: <InsertChart /> },
  { value: 'asset_breakdown', label: 'Asset Breakdown', icon: <TableChart /> },
  { value: 'custom', label: 'Custom Report', icon: <Settings /> },
];

const ExportFormats = [
  { value: 'pdf', label: 'PDF Document', icon: <PictureAsPdf />, description: 'Professional formatted report' },
  { value: 'excel', label: 'Excel Spreadsheet', icon: <TableChart />, description: 'Data analysis and manipulation' },
  { value: 'csv', label: 'CSV Data', icon: <Description />, description: 'Raw data export' },
  { value: 'html', label: 'HTML Report', icon: <Preview />, description: 'Web-viewable report' },
];

const DeliveryMethods = [
  { value: 'download', label: 'Download', icon: <Download />, description: 'Manual download when ready' },
  { value: 'email', label: 'Email', icon: <Email />, description: 'Send via email notification' },
  { value: 'share', label: 'Share Link', icon: <Share />, description: 'Generate shareable link' },
];

const ScheduleFrequencies = [
  { value: 'once', label: 'One-time', icon: <PlayArrow /> },
  { value: 'daily', label: 'Daily', icon: <Repeat /> },
  { value: 'weekly', label: 'Weekly', icon: <Repeat /> },
  { value: 'monthly', label: 'Monthly', icon: <Repeat /> },
  { value: 'quarterly', label: 'Quarterly', icon: <Repeat /> },
];

const ReportBuilder: React.FC<ReportBuilderProps> = ({
  templateId,
  onReportCreated,
  onClose,
}) => {
  // State management
  const [activeStep, setActiveStep] = useState(0);
  const [currentTab, setCurrentTab] = useState(0);
  
  const [reportConfig, setReportConfig] = useState<any>({
    title: '',
    description: '',
    template_id: templateId || '',
    parameters: {},
    format: 'pdf',
    scheduled_delivery: {
      enabled: false,
      frequency: 'once',
      recipients: [],
      delivery_time: '',
    },
  });

  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [currentGenerationId, setCurrentGenerationId] = useState<string | null>(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // API hooks
  const { data: templatesResponse, isLoading: isLoadingTemplates } = useGetReportTemplatesQuery({});
  const [createReport, { isLoading: isCreating }] = useCreateReportMutation();
  
  const { data: progressResponse } = useGetReportProgressQuery(currentGenerationId || '', {
    skip: !currentGenerationId,
    pollingInterval: 1000,
  });

  const templates = templatesResponse?.data || [];

  // WebSocket integration for real-time progress updates
  useReportUpdates(
    currentGenerationId,
    (progressData) => {
      if (progressData.reportId === currentGenerationId) {
        setGenerationProgress(progressData.progress);
        
        if (progressData.status === 'completed') {
          setIsGenerating(false);
          setCurrentGenerationId(null);
          onReportCreated?.(progressData.reportId);
        } else if (progressData.status === 'failed') {
          setIsGenerating(false);
          setCurrentGenerationId(null);
          console.error('Report generation failed:', progressData.data);
        }
      }
    },
    !!currentGenerationId
  );

  // Initialize with template if provided
  useEffect(() => {
    if (templateId && templates.length > 0) {
      const template = templates.find(t => t.template_id === templateId);
      if (template) {
        setSelectedTemplate(template);
        setReportConfig(prev => ({
          ...prev,
          template_id: template.template_id,
          name: template.template_name || '',
          description: template.description || '',
          parameters: template.default_parameters || {},
        }));
      }
    }
  }, [templateId, templates]);

  const handleTemplateSelect = (template: ReportTemplate) => {
    setSelectedTemplate(template);
    setReportConfig(prev => ({
      ...prev,
      template_id: template.template_id,
      name: template.template_name || '',
      description: template.description || '',
      parameters: template.default_parameters || {},
    }));
  };

  const handleParameterChange = (paramKey: string, value: any) => {
    setReportConfig(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [paramKey]: value,
      },
    }));
  };

  const handleScheduleChange = (field: string, value: any) => {
    setReportConfig(prev => ({
      ...prev,
      scheduled_delivery: {
        ...prev.scheduled_delivery!,
        [field]: value,
      },
    }));
  };

  const validateReportConfig = () => {
    const errors: string[] = [];
    
    if (!reportConfig.name.trim()) {
      errors.push('Report name is required');
    }
    
    if (!reportConfig.template_id) {
      errors.push('Please select a report template');
    }
    
    if (selectedTemplate?.required_parameters) {
      selectedTemplate.required_parameters.forEach(param => {
        if (!reportConfig.parameters[param]) {
          errors.push(`Parameter "${param}" is required`);
        }
      });
    }
    
    if (reportConfig.scheduled_delivery?.enabled && reportConfig.scheduled_delivery.recipients.length === 0) {
      errors.push('At least one recipient is required for scheduled delivery');
    }
    
    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleGenerateReport = async () => {
    if (!validateReportConfig()) {
      return;
    }

    try {
      setIsGenerating(true);
      setGenerationProgress(0);
      const generationId = `gen_${Date.now()}`;
      setCurrentGenerationId(generationId);

      const result = await createReport(reportConfig).unwrap();
      
      // The actual generation ID will come from the API response
      setCurrentGenerationId(result.data.report_id);
      
    } catch (error) {
      console.error('Report generation failed:', error);
      setIsGenerating(false);
      setCurrentGenerationId(null);
    }
  };

  const handleStopGeneration = () => {
    setIsGenerating(false);
    setCurrentGenerationId(null);
    setGenerationProgress(0);
  };

  const steps = [
    'Select Template',
    'Configure Parameters',
    'Format & Delivery',
    'Schedule & Generate',
  ];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Report Builder
        </Typography>

        <Stack direction="row" spacing={2}>
          {onClose && (
            <Button variant="outlined" onClick={onClose}>
              Cancel
            </Button>
          )}
          
          <Button
            variant="outlined"
            startIcon={<Preview />}
            onClick={() => setPreviewDialogOpen(true)}
            disabled={!selectedTemplate}
          >
            Preview
          </Button>
          
          <Button
            variant="contained"
            color="error"
            startIcon={<Stop />}
            onClick={handleStopGeneration}
            disabled={!isGenerating}
          >
            Stop
          </Button>
          
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={handleGenerateReport}
            disabled={isGenerating || !selectedTemplate}
          >
            {isGenerating ? 'Generating...' : 'Generate Report'}
          </Button>
        </Stack>
      </Box>

      {/* Generation Progress */}
      {isGenerating && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Generating Report
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={generationProgress} 
              sx={{ mb: 1, height: 8, borderRadius: 4 }}
            />
            <Typography variant="body2" color="text.secondary">
              {generationProgress.toFixed(1)}% Complete - {reportConfig.name}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Please fix the following issues:
          </Typography>
          <ul style={{ margin: 0 }}>
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Configuration Panel */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card>
            <CardContent>
              <Stepper activeStep={activeStep} orientation="vertical">
                {/* Step 1: Template Selection */}
                <Step>
                  <StepLabel>Select Report Template</StepLabel>
                  <StepContent>
                    <Grid container spacing={2}>
                      {templates.map((template) => (
                        <Grid size={{ xs: 12, sm: 6 }} key={template.template_id}>
                          <Card 
                            sx={{ 
                              cursor: 'pointer',
                              border: selectedTemplate?.template_id === template.template_id ? 2 : 1,
                              borderColor: selectedTemplate?.template_id === template.template_id ? 'primary.main' : 'divider',
                            }}
                            onClick={() => handleTemplateSelect(template)}
                          >
                            <CardContent>
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <Assessment sx={{ mr: 1 }} />
                                <Typography variant="h6">
                                  {template.template_name}
                                </Typography>
                              </Box>
                              <Typography variant="body2" color="text.secondary">
                                {template.description}
                              </Typography>
                              <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                                <Chip 
                                  label={template.report_type} 
                                  size="small" 
                                  color="primary" 
                                />
                                <Chip 
                                  label={template.is_system_template ? 'System' : 'Custom'} 
                                  size="small" 
                                  color="secondary" 
                                  variant="outlined" 
                                />
                              </Stack>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                    
                    <Box sx={{ mt: 2 }}>
                      <Button 
                        variant="contained" 
                        onClick={() => setActiveStep(1)}
                        disabled={!selectedTemplate}
                      >
                        Continue
                      </Button>
                    </Box>
                  </StepContent>
                </Step>

                {/* Step 2: Parameters */}
                <Step>
                  <StepLabel>Configure Parameters</StepLabel>
                  <StepContent>
                    <Grid container spacing={3}>
                      <Grid size={12}>
                        <TextField
                          fullWidth
                          label="Report Name"
                          value={reportConfig.name}
                          onChange={(e) => setReportConfig(prev => ({ ...prev, name: e.target.value }))}
                          required
                        />
                      </Grid>
                      
                      <Grid size={12}>
                        <TextField
                          fullWidth
                          label="Description"
                          multiline
                          rows={3}
                          value={reportConfig.description}
                          onChange={(e) => setReportConfig(prev => ({ ...prev, description: e.target.value }))}
                        />
                      </Grid>
                      
                      {selectedTemplate?.required_parameters && Object.keys(selectedTemplate.required_parameters).length > 0 && (
                        <Grid size={12}>
                          <Typography variant="h6" gutterBottom>
                            Template Parameters
                          </Typography>
                          
                          <Grid container spacing={2}>
                            {Object.entries(selectedTemplate.required_parameters).map(([paramName, paramConfig]) => (
                              <Grid size={{ xs: 12, sm: 6 }} key={paramName}>
                                <TextField
                                  fullWidth
                                  label={paramName}
                                  value={reportConfig.parameters[paramName] || selectedTemplate.default_parameters?.[paramName] || ''}
                                  onChange={(e) => handleParameterChange(paramName, e.target.value)}
                                  required={true}
                                  helperText={`Required parameter: ${paramName}`}
                                />
                              </Grid>
                            ))}
                          </Grid>
                        </Grid>
                      )}
                    </Grid>
                    
                    <Box sx={{ mt: 2 }}>
                      <Button variant="contained" onClick={() => setActiveStep(2)} sx={{ mr: 1 }}>
                        Continue
                      </Button>
                      <Button onClick={() => setActiveStep(0)}>
                        Back
                      </Button>
                    </Box>
                  </StepContent>
                </Step>

                {/* Step 3: Format & Delivery */}
                <Step>
                  <StepLabel>Format & Delivery Options</StepLabel>
                  <StepContent>
                    <Grid container spacing={3}>
                      <Grid size={12}>
                        <Typography variant="h6" gutterBottom>
                          Export Format
                        </Typography>
                        <Grid container spacing={2}>
                          {ExportFormats.map((format) => (
                            <Grid size={{ xs: 12, sm: 6 }} key={format.value}>
                              <Card 
                                sx={{ 
                                  cursor: 'pointer',
                                  border: reportConfig.format === format.value ? 2 : 1,
                                  borderColor: reportConfig.format === format.value ? 'primary.main' : 'divider',
                                }}
                                onClick={() => setReportConfig(prev => ({ ...prev, format: format.value as any }))}
                              >
                                <CardContent sx={{ pb: '16px !important' }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                    {format.icon}
                                    <Typography variant="subtitle1" sx={{ ml: 1 }}>
                                      {format.label}
                                    </Typography>
                                  </Box>
                                  <Typography variant="body2" color="text.secondary">
                                    {format.description}
                                  </Typography>
                                </CardContent>
                              </Card>
                            </Grid>
                          ))}
                        </Grid>
                      </Grid>
                    </Grid>
                    
                    <Box sx={{ mt: 2 }}>
                      <Button variant="contained" onClick={() => setActiveStep(3)} sx={{ mr: 1 }}>
                        Continue
                      </Button>
                      <Button onClick={() => setActiveStep(1)}>
                        Back
                      </Button>
                    </Box>
                  </StepContent>
                </Step>

                {/* Step 4: Schedule */}
                <Step>
                  <StepLabel>Schedule & Generate</StepLabel>
                  <StepContent>
                    <Grid container spacing={3}>
                      <Grid size={12}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={reportConfig.scheduled_delivery?.enabled || false}
                              onChange={(e) => handleScheduleChange('enabled', e.target.checked)}
                            />
                          }
                          label="Enable Scheduled Delivery"
                        />
                      </Grid>
                      
                      {reportConfig.scheduled_delivery?.enabled && (
                        <>
                          <Grid size={{ xs: 12, sm: 6 }}>
                            <FormControl fullWidth>
                              <InputLabel>Frequency</InputLabel>
                              <Select
                                value={reportConfig.scheduled_delivery.frequency}
                                label="Frequency"
                                onChange={(e) => handleScheduleChange('frequency', e.target.value)}
                              >
                                {ScheduleFrequencies.map((freq) => (
                                  <MenuItem key={freq.value} value={freq.value}>
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                      {freq.icon}
                                      <Typography sx={{ ml: 1 }}>{freq.label}</Typography>
                                    </Box>
                                  </MenuItem>
                                ))}
                              </Select>
                            </FormControl>
                          </Grid>
                          
                          <Grid size={{ xs: 12, sm: 6 }}>
                            <TextField
                              fullWidth
                              label="Delivery Time"
                              type="time"
                              value={reportConfig.scheduled_delivery.delivery_time}
                              onChange={(e) => handleScheduleChange('delivery_time', e.target.value)}
                              InputLabelProps={{ shrink: true }}
                            />
                          </Grid>
                          
                          <Grid size={12}>
                            <TextField
                              fullWidth
                              label="Recipients (comma-separated emails)"
                              value={reportConfig.scheduled_delivery.recipients.join(', ')}
                              onChange={(e) => handleScheduleChange('recipients', e.target.value.split(',').map(s => s.trim()))}
                              helperText="Enter email addresses separated by commas"
                            />
                          </Grid>
                        </>
                      )}
                    </Grid>
                    
                    <Box sx={{ mt: 2 }}>
                      <Button onClick={() => setActiveStep(2)}>
                        Back
                      </Button>
                    </Box>
                  </StepContent>
                </Step>
              </Stepper>
            </CardContent>
          </Card>
        </Grid>

        {/* Preview Panel */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ position: 'sticky', top: 20 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Report Preview
              </Typography>
              
              {selectedTemplate ? (
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Template
                    </Typography>
                    <Typography variant="body1">
                      {selectedTemplate.template_name}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Name
                    </Typography>
                    <Typography variant="body1">
                      {reportConfig.name || 'Untitled Report'}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Format
                    </Typography>
                    <Chip 
                      label={reportConfig.format?.toUpperCase()}
                      size="small"
                      color="primary"
                    />
                  </Box>
                  
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">
                      Estimated Generation Time
                    </Typography>
                    <Typography variant="body1">
                      Estimated time: 30 seconds
                    </Typography>
                  </Box>
                  
                  {reportConfig.scheduled_delivery?.enabled && (
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Schedule
                      </Typography>
                      <Typography variant="body1">
                        {reportConfig.scheduled_delivery.frequency} at {reportConfig.scheduled_delivery.delivery_time}
                      </Typography>
                    </Box>
                  )}
                  
                  <Divider />
                  
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Parameters
                    </Typography>
                    {Object.entries(reportConfig.parameters).length > 0 ? (
                      <List dense>
                        {Object.entries(reportConfig.parameters).map(([key, value]) => (
                          <ListItem key={key} sx={{ px: 0 }}>
                            <ListItemText
                              primary={key}
                              secondary={String(value)}
                            />
                          </ListItem>
                        ))}
                      </List>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No parameters configured
                      </Typography>
                    )}
                  </Box>
                </Stack>
              ) : (
                <Alert severity="info">
                  Select a template to see the report preview
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ReportBuilder;