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
} from '@mui/icons-material';
import { ConcentrationTestItem } from '../../store/api/newApiTypes';
import { 
  getTestDefinition, 
  getTestName, 
  getTestCategory,
  formatTestValue,
  getThresholdSymbol 
} from '../../utils/concentrationTestMappings';

interface ConcentrationTestsPanelProps {
  portfolioId: string;
  concentrationData: {
    tests: ConcentrationTestItem[];
    summary: {
      totalTests: number;
      passing: number;
      failing: number;
      warnings: number;
      complianceScore: string;
    };
  };
}

// Category mapping - get from test definitions based on test number
const getCategoryFromTestName = (testName: string | undefined | null, testNumber?: number): string => {
  // Always use test number to get category from definitions
  if (testNumber !== undefined) {
    return getTestCategory(testNumber);
  }
  // Fallback to name-based categorization if no test number
  if (!testName) return 'collateral_quality';
  const lowerName = testName.toLowerCase();
  if (lowerName.includes('asset') || lowerName.includes('quality')) return 'asset_quality';
  if (lowerName.includes('geographic') || lowerName.includes('country')) return 'geographic';
  if (lowerName.includes('industry') || lowerName.includes('sector')) return 'industry';
  return 'collateral_quality';
};

const categoryLabels = {
  asset_quality: 'Asset Quality Tests',
  geographic: 'Geographic Tests', 
  industry: 'Industry Tests',
  collateral_quality: 'Collateral Quality Tests'
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
      const testCategory = getCategoryFromTestName(test.test_name, test.test_number);
      const matchesCategory = filterCategory === 'all' || testCategory === filterCategory;
      const matchesStatus = filterStatus === 'all' || test.pass_fail === filterStatus;
      // Use the proper test name from data or mappings
      const displayName = test.test_name || getTestName(test.test_number);
      const matchesSearch = displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           test.test_number.toString().includes(searchTerm);
      
      return matchesCategory && matchesStatus && matchesSearch;
    });
  }, [concentrationData.tests, filterCategory, filterStatus, searchTerm]);

  // Group tests by category
  const groupedTests = useMemo(() => {
    if (!groupByCategory) return { all: filteredTests };
    
    return filteredTests.reduce((acc, test) => {
      const category = getCategoryFromTestName(test.test_name, test.test_number);
      if (!acc[category]) acc[category] = [];
      acc[category].push(test);
      return acc;
    }, {} as Record<string, ConcentrationTestItem[]>);
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

  const getThresholdDisplay = (test: ConcentrationTestItem) => {
    const testDef = getTestDefinition(test.test_number);
    const symbol = getThresholdSymbol(test.test_number);
    const formattedThreshold = testDef?.displayFormat === 'percentage' 
      ? `${(test.threshold * 100).toFixed(1)}%`
      : testDef?.displayFormat === 'ratio' 
        ? `${test.threshold.toFixed(2)}x`
        : test.threshold.toFixed(2);
    return `${symbol} ${formattedThreshold}`;
  };

  const StatusIcon = ({ status }: { status: string }) => {
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig['N/A'];
    const IconComponent = config.icon;
    return IconComponent ? <IconComponent fontSize="small" color={config.color as any} /> : null;
  };

  const TestRow = ({ test }: { test: ConcentrationTestItem }) => {
    const isExpanded = expandedRows.has(test.test_number);
    // Default to N/A config if pass_fail doesn't match known statuses
    const config = statusConfig[test.pass_fail as keyof typeof statusConfig] || statusConfig['N/A'];
    
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
                onClick={() => toggleRowExpansion(test.test_number)}
              >
                {isExpanded ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
              </IconButton>
              {test.test_number}
            </Box>
          </TableCell>
          <TableCell>
            <Box display="flex" alignItems="center" gap={1}>
              <StatusIcon status={test.pass_fail} />
              <Chip 
                label={test.pass_fail} 
                size="small" 
                color={config.color as any}
                variant="outlined"
              />
            </Box>
          </TableCell>
          <TableCell>
            <Typography variant="body2" fontWeight={test.pass_fail === 'FAIL' ? 'bold' : 'normal'}>
              {test.test_name || getTestName(test.test_number)}
            </Typography>
          </TableCell>
          <TableCell align="right">
            <Typography 
              variant="body2" 
              color={test.pass_fail === 'FAIL' ? 'error' : 'text.primary'}
              fontWeight={test.pass_fail === 'FAIL' ? 'bold' : 'normal'}
            >
              {formatTestValue(test.result, test.test_number)}
            </Typography>
          </TableCell>
          <TableCell align="right">
            <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1}>
              <Typography variant="body2">
                {getThresholdDisplay(test)}
              </Typography>
              {test.threshold_source === 'deal' && (
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
                label={test.threshold_source?.toUpperCase() || 'DEFAULT'}
                color={test.threshold_source === 'deal' ? 'primary' : 'default'}
                variant="outlined"
              />
            </Box>
          </TableCell>
          <TableCell>
            <Chip 
              label={test.pass_fail === 'FAIL' ? 'HIGH' : 'LOW'} 
              size="small"
              sx={{ 
                backgroundColor: test.pass_fail === 'FAIL' ? riskColors.HIGH : riskColors.LOW,
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
                  // TODO: Open threshold editor dialog for test: test.test_number
                }}
              >
                <EditIcon />
              </IconButton>
            </Tooltip>
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
                      Test Details - {test.test_name || 'Unnamed Test'}
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
                          Result: {test.numerator.toLocaleString()} ÷ {test.denominator.toLocaleString()} = {formatValue(test.result)}
                        </Typography>
                      </Box>
                      <Box flexGrow={1} minWidth={300}>
                        <Typography variant="body2" color="text.secondary">
                          <strong>Threshold Source:</strong> {test.threshold_source || 'Default'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          <strong>Status:</strong> {test.pass_fail}
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
                        <TestRow key={test.test_number} test={test} />
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
                <TestRow key={test.test_number} test={test} />
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