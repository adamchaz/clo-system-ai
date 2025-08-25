import React, { useState, useMemo } from 'react';
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
  Paper,
  Chip,
  IconButton,
  Collapse,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  LinearProgress,
  Alert
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  KeyboardArrowDown,
  KeyboardArrowUp,
  CheckCircle,
  Error,
  Warning,
  FileDownload,
  FilterList,
  Edit as EditIcon,
  Info as InfoIcon
} from '@mui/icons-material';

// Types
interface ConcentrationTestResult {
  testNumber: number;
  testName: string;
  category: string;
  currentValue: number;
  threshold: number;
  thresholdOperator: '<' | '>' | '≤' | '≥';
  status: 'PASS' | 'FAIL' | 'WARNING' | 'N/A';
  riskLevel: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  comments: string;
  recommendation?: string;
  numerator: number;
  denominator: number;
  lastUpdated: string;
  // Enhanced threshold properties
  thresholdSource?: 'deal' | 'default' | 'template';
  isCustomOverride?: boolean;
  effectiveDate?: string;
  magVersion?: string;
  defaultThreshold?: number;
  excessAmount?: number;
}

interface ConcentrationTestsPanelProps {
  portfolioId: string;
  concentrationData: {
    tests: ConcentrationTestResult[];
    summary: {
      totalTests: number;
      passing: number;
      failing: number;
      warnings: number;
      complianceScore: string;
    };
  };
}

// Category mapping
const categoryLabels = {
  asset_quality: 'Asset Quality Tests',
  geographic: 'Geographic Tests', 
  industry: 'Industry Tests',
  portfolio_metrics: 'Collateral Quality Tests'
};

// Status colors and icons
const statusConfig = {
  PASS: { color: 'success', icon: CheckCircle, bgcolor: '#e8f5e8' },
  FAIL: { color: 'error', icon: Error, bgcolor: '#ffebee' },
  WARNING: { color: 'warning', icon: Warning, bgcolor: '#fff3e0' },
  'N/A': { color: 'default', icon: () => null, bgcolor: '#f5f5f5' }
};

// Risk level colors
const riskColors = {
  CRITICAL: '#d32f2f',
  HIGH: '#f57c00', 
  MEDIUM: '#fbc02d',
  LOW: '#388e3c'
};

const ConcentrationTestsPanel: React.FC<ConcentrationTestsPanelProps> = ({
  portfolioId,
  concentrationData
}) => {
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [groupByCategory, setGroupByCategory] = useState(true);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  // Filter and search tests
  const filteredTests = useMemo(() => {
    return concentrationData.tests.filter(test => {
      const matchesCategory = filterCategory === 'all' || test.category === filterCategory;
      const matchesStatus = filterStatus === 'all' || test.status === filterStatus;
      const matchesSearch = test.testName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           test.testNumber.toString().includes(searchTerm);
      
      return matchesCategory && matchesStatus && matchesSearch;
    });
  }, [concentrationData.tests, filterCategory, filterStatus, searchTerm]);

  // Group tests by category
  const groupedTests = useMemo(() => {
    if (!groupByCategory) return { all: filteredTests };
    
    return filteredTests.reduce((acc, test) => {
      if (!acc[test.category]) acc[test.category] = [];
      acc[test.category].push(test);
      return acc;
    }, {} as Record<string, ConcentrationTestResult[]>);
  }, [filteredTests, groupByCategory]);

  const toggleRowExpansion = (testNumber: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(testNumber)) {
      newExpanded.delete(testNumber);
    } else {
      newExpanded.add(testNumber);
    }
    setExpandedRows(newExpanded);
  };

  const formatValue = (value: number, isPercentage: boolean = true) => {
    if (isPercentage) {
      return `${(value * 100).toFixed(1)}%`;
    }
    return value.toFixed(2);
  };

  const getThresholdDisplay = (test: ConcentrationTestResult) => {
    const formattedThreshold = formatValue(test.threshold);
    return `${test.thresholdOperator} ${formattedThreshold}`;
  };

  const StatusIcon = ({ status }: { status: string }) => {
    const config = statusConfig[status as keyof typeof statusConfig];
    const IconComponent = config.icon;
    return IconComponent ? <IconComponent fontSize="small" color={config.color as any} /> : null;
  };

  const TestRow = ({ test }: { test: ConcentrationTestResult }) => {
    const isExpanded = expandedRows.has(test.testNumber);
    const config = statusConfig[test.status];
    
    return (
      <>
        <TableRow 
          sx={{ 
            backgroundColor: config.bgcolor,
            '&:hover': { backgroundColor: `${config.bgcolor}dd` }
          }}
        >
          <TableCell>
            <Box display="flex" alignItems="center" gap={1}>
              <IconButton
                size="small"
                onClick={() => toggleRowExpansion(test.testNumber)}
              >
                {isExpanded ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
              </IconButton>
              {test.testNumber}
            </Box>
          </TableCell>
          <TableCell>
            <Box display="flex" alignItems="center" gap={1}>
              <StatusIcon status={test.status} />
              <Chip 
                label={test.status} 
                size="small" 
                color={config.color as any}
                variant="outlined"
              />
            </Box>
          </TableCell>
          <TableCell>
            <Typography variant="body2" fontWeight={test.status === 'FAIL' ? 'bold' : 'normal'}>
              {test.testName}
            </Typography>
          </TableCell>
          <TableCell align="right">
            <Typography 
              variant="body2" 
              color={test.status === 'FAIL' ? 'error' : 'text.primary'}
              fontWeight={test.status === 'FAIL' ? 'bold' : 'normal'}
            >
              {formatValue(test.currentValue)}
            </Typography>
          </TableCell>
          <TableCell align="right">
            <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
              <Typography variant="body2">
                {getThresholdDisplay(test)}
              </Typography>
              {test.isCustomOverride && (
                <Chip 
                  size="small" 
                  label="Custom" 
                  color="primary" 
                  variant="outlined"
                />
              )}
            </Box>
          </TableCell>
          <TableCell>
            <Box display="flex" alignItems="center" gap={1}>
              <Chip 
                size="small" 
                label={test.thresholdSource?.toUpperCase() || 'DEFAULT'}
                color={test.thresholdSource === 'deal' ? 'primary' : 'default'}
                variant="outlined"
              />
              {test.magVersion && (
                <Chip 
                  size="small" 
                  label={test.magVersion} 
                  variant="outlined"
                />
              )}
            </Box>
            {test.effectiveDate && (
              <Typography variant="caption" color="text.secondary" display="block">
                Since: {new Date(test.effectiveDate).toLocaleDateString()}
              </Typography>
            )}
          </TableCell>
          <TableCell>
            <Chip 
              label={test.riskLevel} 
              size="small"
              sx={{ 
                backgroundColor: riskColors[test.riskLevel],
                color: 'white',
                fontWeight: 'bold'
              }}
            />
          </TableCell>
          <TableCell align="center">
            <Tooltip title="Edit Threshold">
              <IconButton 
                size="small" 
                color="primary"
                onClick={() => {
                  // Would navigate to threshold editor or open dialog
                  // TODO: Open threshold editor dialog for test: test.testNumber
                }}
              >
                <EditIcon />
              </IconButton>
            </Tooltip>
            {test.isCustomOverride && (
              <Tooltip title="Custom threshold in use">
                <IconButton size="small" color="info">
                  <InfoIcon />
                </IconButton>
              </Tooltip>
            )}
          </TableCell>
          <TableCell>
            <Typography variant="body2" color="text.secondary">
              {test.comments}
            </Typography>
          </TableCell>
        </TableRow>
        
        {/* Expandable Detail Row */}
        <TableRow>
          <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={9}>
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              <Box margin={2}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Test Details - {test.testName}
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={2}>
                      <Box flexGrow={1} minWidth={300}>
                        <Typography variant="body2" color="text.secondary">
                          <strong>Calculation:</strong>
                        </Typography>
                        <Typography variant="body2">
                          Numerator: {test.numerator.toLocaleString()}
                        </Typography>
                        <Typography variant="body2">
                          Denominator: {test.denominator.toLocaleString()}
                        </Typography>
                        <Typography variant="body2">
                          Result: {test.numerator.toLocaleString()} ÷ {test.denominator.toLocaleString()} = {formatValue(test.currentValue)}
                        </Typography>
                      </Box>
                      <Box flexGrow={1} minWidth={300}>
                        {test.recommendation && (
                          <>
                            <Typography variant="body2" color="text.secondary">
                              <strong>Recommendation:</strong>
                            </Typography>
                            <Typography variant="body2">
                              {test.recommendation}
                            </Typography>
                          </>
                        )}
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          <strong>Last Updated:</strong> {new Date(test.lastUpdated).toLocaleDateString()}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      </>
    );
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight="bold">
          Concentration Tests - {portfolioId}
        </Typography>
        <Box display="flex" gap={1}>
          <Button variant="outlined" startIcon={<FileDownload />}>
            Export
          </Button>
          <Button variant="outlined" startIcon={<FilterList />}>
            Settings
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Box display="flex" flexWrap="wrap" gap={2} mb={3}>
        <Box flexGrow={1} minWidth={200}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="success.main" fontWeight="bold">
                {concentrationData.summary.passing}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                PASSING
              </Typography>
              <Typography variant="body2" color="success.main">
                ✅ {((concentrationData.summary.passing / concentrationData.summary.totalTests) * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box flexGrow={1} minWidth={200}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="error.main" fontWeight="bold">
                {concentrationData.summary.failing}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                FAILING
              </Typography>
              <Typography variant="body2" color="error.main">
                ❌ {((concentrationData.summary.failing / concentrationData.summary.totalTests) * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box flexGrow={1} minWidth={200}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="warning.main" fontWeight="bold">
                {concentrationData.summary.warnings}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                AT RISK
              </Typography>
              <Typography variant="body2" color="warning.main">
                ⚠️ {((concentrationData.summary.warnings / concentrationData.summary.totalTests) * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Box>
        <Box flexGrow={1} minWidth={200}>
          <Card>
            <CardContent>
              <Typography variant="h4" fontWeight="bold">
                {concentrationData.summary.complianceScore}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                COMPLIANCE SCORE
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={(concentrationData.summary.passing / concentrationData.summary.totalTests) * 100}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Alert for failed tests */}
      {concentrationData.summary.failing > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {concentrationData.summary.failing} concentration test{concentrationData.summary.failing > 1 ? 's' : ''} failing - 
          immediate attention required to maintain compliance.
        </Alert>
      )}

      {/* Filters */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" flexWrap="wrap" gap={2} alignItems="center">
            <Box flexGrow={1} minWidth={200}>
              <FormControl fullWidth size="small">
                <InputLabel>Category</InputLabel>
                <Select
                  value={filterCategory}
                  label="Category"
                  onChange={(e) => setFilterCategory(e.target.value)}
                >
                  <MenuItem value="all">All Categories</MenuItem>
                  {Object.entries(categoryLabels).map(([key, label]) => (
                    <MenuItem key={key} value={key}>{label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            <Box flexGrow={1} minWidth={200}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filterStatus}
                  label="Status"
                  onChange={(e) => setFilterStatus(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="PASS">Pass</MenuItem>
                  <MenuItem value="FAIL">Fail</MenuItem>
                  <MenuItem value="WARNING">Warning</MenuItem>
                  <MenuItem value="N/A">N/A</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box flexGrow={1} minWidth={250}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search tests..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </Box>
            <Box minWidth={150}>
              <Button
                variant={groupByCategory ? "contained" : "outlined"}
                onClick={() => setGroupByCategory(!groupByCategory)}
                fullWidth
              >
                Group by Category
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Results Table */}
      {groupByCategory ? (
        // Grouped by category
        <Box>
          {Object.entries(groupedTests).map(([category, tests]) => (
            <Accordion key={category} defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">
                  {categoryLabels[category as keyof typeof categoryLabels] || 'Other'} ({tests.length} tests)
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Test #</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Test Name</TableCell>
                        <TableCell align="right">Current</TableCell>
                        <TableCell align="right">Threshold</TableCell>
                        <TableCell>Source</TableCell>
                        <TableCell>Risk</TableCell>
                        <TableCell align="center">Actions</TableCell>
                        <TableCell>Comments</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {tests.map((test) => (
                        <TestRow key={test.testNumber} test={test} />
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      ) : (
        // Single table view
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Test #</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Test Name</TableCell>
                <TableCell align="right">Current</TableCell>
                <TableCell align="right">Threshold</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Risk</TableCell>
                <TableCell align="center">Actions</TableCell>
                <TableCell>Comments</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredTests.map((test) => (
                <TestRow key={test.testNumber} test={test} />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {filteredTests.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            No concentration tests match the current filters.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default ConcentrationTestsPanel;