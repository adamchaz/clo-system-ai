import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  CircularProgress,
  Tabs,
  Tab,
  Paper,
  Grid,
  Divider,
  InputAdornment,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Edit as EditIcon,
  History as HistoryIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { format, parseISO } from 'date-fns';

// Types
interface ConcentrationThreshold {
  testId: number;
  testNumber: number;
  testName: string;
  testCategory: string;
  resultType: string;
  thresholdValue: number;
  thresholdSource: string;
  isCustomOverride: boolean;
  effectiveDate: string;
  expiryDate?: string;
  magVersion?: string;
  defaultThreshold?: number;
}

interface ThresholdHistory {
  id: number;
  thresholdValue: number;
  effectiveDate: string;
  expiryDate?: string;
  magVersion?: string;
  ratingAgency?: string;
  notes?: string;
  createdBy?: number;
  createdAt: string;
  updatedAt: string;
}

interface ConcentrationThresholdManagerProps {
  dealId: string;
  analysisDate?: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`threshold-tabpanel-${index}`}
      aria-labelledby={`threshold-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ConcentrationThresholdManager: React.FC<ConcentrationThresholdManagerProps> = ({
  dealId,
  analysisDate = '2016-03-23'
}) => {
  // State
  const [thresholds, setThresholds] = useState<ConcentrationThreshold[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  
  // Dialog states
  const [editingThreshold, setEditingThreshold] = useState<ConcentrationThreshold | null>(null);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [selectedThresholdHistory, setSelectedThresholdHistory] = useState<ThresholdHistory[]>([]);
  
  // Form states
  const [newThresholdValue, setNewThresholdValue] = useState<number>(0);
  const [effectiveDate, setEffectiveDate] = useState<Date>(new Date());
  const [expiryDate, setExpiryDate] = useState<Date | null>(null);
  const [magVersion, setMagVersion] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [isUpdating, setIsUpdating] = useState(false);
  
  // Filter states
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [showCustomOnly, setShowCustomOnly] = useState(false);

  // Mock API functions (would be replaced with actual API calls)
  const fetchThresholds = async () => {
    setLoading(true);
    setError(null);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock data
      const mockThresholds: ConcentrationThreshold[] = [
        {
          testId: 1,
          testNumber: 4,
          testName: 'Single Obligor Maximum',
          testCategory: 'obligor',
          resultType: 'percentage',
          thresholdValue: 2.0,
          thresholdSource: 'default',
          isCustomOverride: false,
          effectiveDate: analysisDate,
          defaultThreshold: 2.0,
        },
        {
          testId: 2,
          testNumber: 40,
          testName: 'CCC-Rated Obligations Maximum',
          testCategory: 'rating',
          resultType: 'percentage',
          thresholdValue: 7.5,
          thresholdSource: 'deal',
          isCustomOverride: true,
          effectiveDate: '2016-01-01',
          expiryDate: '2016-12-31',
          magVersion: 'MAG17',
          defaultThreshold: 7.5,
        },
        {
          testId: 3,
          testNumber: 29,
          testName: 'Covenant-Lite Assets Maximum',
          testCategory: 'covenant',
          resultType: 'percentage',
          thresholdValue: 7.5,
          thresholdSource: 'default',
          isCustomOverride: false,
          effectiveDate: analysisDate,
          defaultThreshold: 7.5,
        },
        {
          testId: 4,
          testNumber: 36,
          testName: 'Weighted Average Rating Factor Maximum',
          testCategory: 'portfolio',
          resultType: 'rating_factor',
          thresholdValue: 2720,
          thresholdSource: 'deal',
          isCustomOverride: true,
          effectiveDate: '2016-02-15',
          magVersion: 'MAG17',
          defaultThreshold: 2720,
        },
      ];
      
      setThresholds(mockThresholds);
    } catch (err) {
      setError('Failed to load thresholds');
      console.error('Error fetching thresholds:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditThreshold = (threshold: ConcentrationThreshold) => {
    setEditingThreshold(threshold);
    setNewThresholdValue(threshold.thresholdValue);
    setEffectiveDate(parseISO(threshold.effectiveDate));
    setExpiryDate(threshold.expiryDate ? parseISO(threshold.expiryDate) : null);
    setMagVersion(threshold.magVersion || '');
    setNotes('');
  };

  const handleSaveThreshold = async () => {
    if (!editingThreshold) return;

    setIsUpdating(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update local state (in real app, refetch from server)
      setThresholds(prev => prev.map(t => 
        t.testId === editingThreshold.testId
          ? {
              ...t,
              thresholdValue: newThresholdValue,
              effectiveDate: effectiveDate.toISOString().split('T')[0],
              expiryDate: expiryDate?.toISOString().split('T')[0],
              magVersion: magVersion || undefined,
              isCustomOverride: true,
              thresholdSource: 'deal'
            }
          : t
      ));
      
      setEditingThreshold(null);
    } catch (err) {
      setError('Failed to update threshold');
      console.error('Error updating threshold:', err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleViewHistory = async (threshold: ConcentrationThreshold) => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Mock history data
      const mockHistory: ThresholdHistory[] = [
        {
          id: 1,
          thresholdValue: threshold.thresholdValue,
          effectiveDate: threshold.effectiveDate,
          expiryDate: threshold.expiryDate,
          magVersion: threshold.magVersion,
          notes: 'Initial threshold setting',
          createdAt: '2016-01-01T00:00:00Z',
          updatedAt: '2016-01-01T00:00:00Z',
        },
      ];
      
      setSelectedThresholdHistory(mockHistory);
      setHistoryDialogOpen(true);
    } catch (err) {
      setError('Failed to load threshold history');
    } finally {
      setLoading(false);
    }
  };

  const getThresholdSourceColor = (source: string) => {
    switch (source) {
      case 'deal': return 'primary';
      case 'default': return 'default';
      case 'template': return 'secondary';
      default: return 'default';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: any } = {
      'obligor': 'error',
      'industry': 'warning',
      'rating': 'info',
      'geographic': 'success',
      'asset_type': 'secondary',
      'portfolio': 'primary',
    };
    return colors[category] || 'default';
  };

  const formatThresholdValue = (value: number, type: string) => {
    switch (type) {
      case 'percentage':
        return `${value}%`;
      case 'rating_factor':
        return value.toFixed(0);
      case 'years':
        return `${value} years`;
      case 'absolute':
        return value.toFixed(2);
      default:
        return value.toString();
    }
  };

  const getFilteredThresholds = () => {
    return thresholds.filter(threshold => {
      if (categoryFilter !== 'all' && threshold.testCategory !== categoryFilter) return false;
      if (sourceFilter !== 'all' && threshold.thresholdSource !== sourceFilter) return false;
      if (showCustomOnly && !threshold.isCustomOverride) return false;
      return true;
    });
  };

  // Load thresholds on component mount
  React.useEffect(() => {
    fetchThresholds();
  }, [dealId, analysisDate]);

  const categories = Array.from(new Set(thresholds.map(t => t.testCategory)));
  const sources = Array.from(new Set(thresholds.map(t => t.thresholdSource)));

  if (loading && thresholds.length === 0) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader
          title="Concentration Test Thresholds"
          subheader={`Deal: ${dealId} • Analysis Date: ${format(parseISO(analysisDate), 'MMM dd, yyyy')}`}
          action={
            <Button
              variant="outlined"
              startIcon={<TrendingUpIcon />}
              onClick={fetchThresholds}
              disabled={loading}
            >
              Refresh
            </Button>
          }
        />
        <CardContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
            <Tab label="Threshold Management" icon={<EditIcon />} />
            <Tab label="Analytics" icon={<AssessmentIcon />} />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            {/* Filters */}
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box display="flex" flexWrap="wrap" gap={2} alignItems="center">
                <Box minWidth={200}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={categoryFilter}
                      label="Category"
                      onChange={(e) => setCategoryFilter(e.target.value)}
                    >
                      <MenuItem value="all">All Categories</MenuItem>
                      {categories.map(category => (
                        <MenuItem key={category} value={category}>
                          {category.charAt(0).toUpperCase() + category.slice(1)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                <Box minWidth={200}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Source</InputLabel>
                    <Select
                      value={sourceFilter}
                      label="Source"
                      onChange={(e) => setSourceFilter(e.target.value)}
                    >
                      <MenuItem value="all">All Sources</MenuItem>
                      {sources.map(source => (
                        <MenuItem key={source} value={source}>
                          {source.charAt(0).toUpperCase() + source.slice(1)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>
                <Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={showCustomOnly}
                        onChange={(e) => setShowCustomOnly(e.target.checked)}
                      />
                    }
                    label="Custom Only"
                  />
                </Box>
                <Box flexGrow={1}>
                  <Typography variant="body2" color="text.secondary">
                    Showing {getFilteredThresholds().length} of {thresholds.length} tests
                  </Typography>
                </Box>
              </Box>
            </Paper>

            {/* Threshold Table */}
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Test #</TableCell>
                    <TableCell>Test Name</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Threshold</TableCell>
                    <TableCell>Source</TableCell>
                    <TableCell>Effective Date</TableCell>
                    <TableCell>MAG Version</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {getFilteredThresholds().map((threshold) => (
                    <TableRow key={threshold.testId} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {threshold.testNumber}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2">{threshold.testName}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {threshold.resultType.replace('_', ' ')}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={threshold.testCategory}
                          color={getCategoryColor(threshold.testCategory)}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Box display="flex" alignItems="center" justifyContent="flex-end">
                          <Typography variant="body2" fontWeight="bold">
                            {formatThresholdValue(threshold.thresholdValue, threshold.resultType)}
                          </Typography>
                          {threshold.isCustomOverride && (
                            <Chip
                              size="small"
                              label="Custom"
                              color="primary"
                              variant="outlined"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={threshold.thresholdSource.toUpperCase()}
                          color={getThresholdSourceColor(threshold.thresholdSource)}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {format(parseISO(threshold.effectiveDate), 'MMM dd, yyyy')}
                        </Typography>
                        {threshold.expiryDate && (
                          <Typography variant="caption" color="text.secondary" display="block">
                            Expires: {format(parseISO(threshold.expiryDate), 'MMM dd, yyyy')}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {threshold.magVersion ? (
                          <Chip size="small" label={threshold.magVersion} variant="outlined" />
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Box display="flex" gap={1}>
                          <Tooltip title="Edit Threshold">
                            <IconButton
                              size="small"
                              onClick={() => handleEditThreshold(threshold)}
                              color="primary"
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="View History">
                            <IconButton
                              size="small"
                              onClick={() => handleViewHistory(threshold)}
                              color="default"
                            >
                              <HistoryIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {/* Analytics Panel */}
            <Box display="flex" flexWrap="wrap" gap={3}>
              <Box flexGrow={1} minWidth={300}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Threshold Summary
                  </Typography>
                  <Box display="flex" flexDirection="column" gap={1}>
                    <Box display="flex" justifyContent="space-between">
                      <Typography>Total Tests:</Typography>
                      <Typography fontWeight="bold">{thresholds.length}</Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography>Custom Overrides:</Typography>
                      <Typography fontWeight="bold" color="primary.main">
                        {thresholds.filter(t => t.isCustomOverride).length}
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography>Default Thresholds:</Typography>
                      <Typography fontWeight="bold">
                        {thresholds.filter(t => !t.isCustomOverride).length}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              </Box>
              <Box flexGrow={1} minWidth={300}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Category Distribution
                  </Typography>
                  {categories.map(category => {
                    const count = thresholds.filter(t => t.testCategory === category).length;
                    return (
                      <Box key={category} display="flex" justifyContent="space-between" mb={1}>
                        <Typography>{category.charAt(0).toUpperCase() + category.slice(1)}:</Typography>
                        <Typography fontWeight="bold">{count}</Typography>
                      </Box>
                    );
                  })}
                </Paper>
              </Box>
            </Box>
          </TabPanel>
        </CardContent>
      </Card>

      {/* Threshold Edit Dialog */}
      <Dialog
        open={editingThreshold !== null}
        onClose={() => setEditingThreshold(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <EditIcon />
            Edit Threshold: {editingThreshold?.testName}
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box display="flex" flexWrap="wrap" gap={2}>
              <Box flexGrow={1} minWidth={300}>
                <TextField
                  label="Threshold Value"
                  type="number"
                  value={newThresholdValue}
                  onChange={(e) => setNewThresholdValue(Number(e.target.value))}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        {editingThreshold?.resultType === 'percentage' ? '%' : 
                         editingThreshold?.resultType === 'years' ? 'years' : ''}
                      </InputAdornment>
                    )
                  }}
                  fullWidth
                />
              </Box>
              <Box flexGrow={1} minWidth={300}>
                <FormControl fullWidth>
                  <InputLabel>MAG Version</InputLabel>
                  <Select
                    value={magVersion}
                    label="MAG Version"
                    onChange={(e) => setMagVersion(e.target.value)}
                  >
                    <MenuItem value="">None</MenuItem>
                    <MenuItem value="MAG6">MAG6</MenuItem>
                    <MenuItem value="MAG14">MAG14</MenuItem>
                    <MenuItem value="MAG17">MAG17</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </Box>

            <Box display="flex" flexWrap="wrap" gap={2}>
              <Box flexGrow={1} minWidth={300}>
                <DatePicker
                  label="Effective Date"
                  value={effectiveDate}
                  onChange={(date) => setEffectiveDate(date || new Date())}
                  slots={{
                    textField: TextField,
                  }}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                    },
                  }}
                />
              </Box>
              <Box flexGrow={1} minWidth={300}>
                <DatePicker
                  label="Expiry Date (Optional)"
                  value={expiryDate}
                  onChange={(date) => setExpiryDate(date)}
                  slots={{
                    textField: TextField,
                  }}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                    },
                  }}
                />
              </Box>
            </Box>

            <TextField
              label="Notes"
              multiline
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Reason for threshold change..."
              fullWidth
            />

            {editingThreshold?.isCustomOverride && (
              <Alert severity="info" icon={<InfoIcon />}>
                This test already has a custom threshold. Updating will create a new override.
              </Alert>
            )}

            {editingThreshold?.defaultThreshold && 
             editingThreshold.defaultThreshold !== newThresholdValue && (
              <Alert severity="warning">
                New value ({formatThresholdValue(newThresholdValue, editingThreshold.resultType)}) 
                differs from default ({formatThresholdValue(editingThreshold.defaultThreshold, editingThreshold.resultType)})
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setEditingThreshold(null)}
            startIcon={<CancelIcon />}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveThreshold}
            variant="contained"
            disabled={isUpdating}
            startIcon={isUpdating ? <CircularProgress size={16} /> : <SaveIcon />}
          >
            {isUpdating ? 'Saving...' : 'Save Threshold'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* History Dialog */}
      <Dialog
        open={historyDialogOpen}
        onClose={() => setHistoryDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <HistoryIcon />
            Threshold History
          </Box>
        </DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Value</TableCell>
                  <TableCell>Effective Date</TableCell>
                  <TableCell>Expiry Date</TableCell>
                  <TableCell>MAG Version</TableCell>
                  <TableCell>Notes</TableCell>
                  <TableCell>Created</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {selectedThresholdHistory.map((history) => (
                  <TableRow key={history.id}>
                    <TableCell>{history.thresholdValue}</TableCell>
                    <TableCell>
                      {format(parseISO(history.effectiveDate), 'MMM dd, yyyy')}
                    </TableCell>
                    <TableCell>
                      {history.expiryDate ? 
                        format(parseISO(history.expiryDate), 'MMM dd, yyyy') : '-'}
                    </TableCell>
                    <TableCell>{history.magVersion || '-'}</TableCell>
                    <TableCell>{history.notes || '-'}</TableCell>
                    <TableCell>
                      {format(parseISO(history.createdAt), 'MMM dd, yyyy HH:mm')}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ConcentrationThresholdManager;