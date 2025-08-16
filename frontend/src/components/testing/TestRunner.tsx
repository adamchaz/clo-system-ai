/**
 * TestRunner Component - Quick Integration Test Runner
 * 
 * Simple test runner for validating Option D integration:
 * - Quick API connectivity checks
 * - Basic functionality validation
 * - Component rendering tests
 * - WebSocket connection verification
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow,
  CheckCircle,
  Error,
  Info,
  Api,
  Storage,
  Security,
  Analytics,
  Description,
  Group,
  Assessment,
  NetworkCheck,
} from '@mui/icons-material';

// Import API hooks for basic testing
import {
  useGetPortfoliosQuery,
  useGetAssetsQuery,
  useGetUsersEnhancedQuery,
  useGetDocumentsQuery,
  useGetReportsQuery,
  useGetWebSocketStatsQuery,
} from '../../store/api/cloApi';

// Import WebSocket hooks
import { useWebSocketConnection } from '../../hooks/useWebSocket';

interface QuickTest {
  name: string;
  description: string;
  icon: React.ReactNode;
  status: 'pending' | 'running' | 'passed' | 'failed';
  error?: string;
}

const TestRunner: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [tests, setTests] = useState<QuickTest[]>([
    {
      name: 'Portfolio API',
      description: 'Test portfolio management endpoints',
      icon: <Assessment />,
      status: 'pending',
    },
    {
      name: 'Asset API',
      description: 'Test asset management endpoints',
      icon: <Analytics />,
      status: 'pending',
    },
    {
      name: 'User Management API',
      description: 'Test user administration endpoints',
      icon: <Group />,
      status: 'pending',
    },
    {
      name: 'Document API',
      description: 'Test document management endpoints',
      icon: <Description />,
      status: 'pending',
    },
    {
      name: 'Reporting API',
      description: 'Test report generation endpoints',
      icon: <Assessment />,
      status: 'pending',
    },
    {
      name: 'WebSocket Connection',
      description: 'Test real-time connectivity',
      icon: <NetworkCheck />,
      status: 'pending',
    },
  ]);

  // API hooks (skip initially)
  const portfolioQuery = useGetPortfoliosQuery(undefined, { skip: true });
  const assetQuery = useGetAssetsQuery({ skip: 0, limit: 1 }, { skip: true });
  const userQuery = useGetUsersEnhancedQuery({ skip: 0, limit: 1 }, { skip: true });
  const documentQuery = useGetDocumentsQuery({ skip: 0, limit: 1 }, { skip: true });
  const reportQuery = useGetReportsQuery({ skip: 0, limit: 1 }, { skip: true });
  const webSocketStatsQuery = useGetWebSocketStatsQuery(undefined, { skip: true });
  
  // WebSocket connection
  const { status } = useWebSocketConnection();
  const isConnected = status === 'connected';

  const runQuickTests = async () => {
    setIsRunning(true);
    setProgress(0);
    
    const testFunctions = [
      // Test Portfolio API
      async () => {
        try {
          await portfolioQuery.refetch();
          return { status: 'passed' as const };
        } catch (error: any) {
          return { status: 'failed' as const, error: 'Portfolio API not accessible' };
        }
      },
      
      // Test Asset API
      async () => {
        try {
          await assetQuery.refetch();
          return { status: 'passed' as const };
        } catch (error: any) {
          return { status: 'failed' as const, error: 'Asset API not accessible' };
        }
      },
      
      // Test User API
      async () => {
        try {
          await userQuery.refetch();
          return { status: 'passed' as const };
        } catch (error: any) {
          return { status: 'failed' as const, error: 'User Management API not accessible' };
        }
      },
      
      // Test Document API
      async () => {
        try {
          await documentQuery.refetch();
          return { status: 'passed' as const };
        } catch (error: any) {
          return { status: 'failed' as const, error: 'Document API not accessible' };
        }
      },
      
      // Test Report API
      async () => {
        try {
          await reportQuery.refetch();
          return { status: 'passed' as const };
        } catch (error: any) {
          return { status: 'failed' as const, error: 'Reporting API not accessible' };
        }
      },
      
      // Test WebSocket
      async () => {
        try {
          await webSocketStatsQuery.refetch();
          return { 
            status: isConnected ? 'passed' as const : 'failed' as const, 
            error: isConnected ? undefined : 'WebSocket not connected'
          };
        } catch (error: any) {
          return { status: 'failed' as const, error: 'WebSocket service not available' };
        }
      },
    ];

    for (let i = 0; i < testFunctions.length; i++) {
      setTests(prev => prev.map((test, index) => 
        index === i ? { ...test, status: 'running' } : test
      ));
      
      const result = await testFunctions[i]();
      
      setTests(prev => prev.map((test, index) => 
        index === i ? { ...test, ...result } : test
      ));
      
      setProgress(((i + 1) / testFunctions.length) * 100);
    }
    
    setIsRunning(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircle color="success" />;
      case 'failed': return <Error color="error" />;
      case 'running': return <Info color="info" />;
      default: return <Info color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'info';
      default: return 'default';
    }
  };

  const passedTests = tests.filter(t => t.status === 'passed').length;
  const totalTests = tests.length;
  const allPassed = passedTests === totalTests && !isRunning;

  return (
    <Box sx={{ width: '100%', maxWidth: 800, mx: 'auto' }}>
      <Card>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            Option D Integration Test Runner
          </Typography>
          
          <Typography variant="body2" color="text.secondary" paragraph>
            Quick validation of frontend-backend integration for all major features.
          </Typography>

          {/* Progress */}
          {isRunning && (
            <Box sx={{ mb: 3 }}>
              <LinearProgress 
                variant="determinate" 
                value={progress} 
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Testing in progress: {progress.toFixed(0)}%
              </Typography>
            </Box>
          )}

          {/* Test Results */}
          <List>
            {tests.map((test, index) => (
              <ListItem key={index} sx={{ py: 1 }}>
                <ListItemIcon>
                  {getStatusIcon(test.status)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {test.icon}
                      <Typography variant="subtitle2">
                        {test.name}
                      </Typography>
                      <Chip 
                        label={test.status} 
                        color={getStatusColor(test.status)} 
                        size="small" 
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {test.description}
                      </Typography>
                      {test.error && (
                        <Typography variant="caption" color="error">
                          {test.error}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>

          {/* Results Summary */}
          {!isRunning && totalTests > 0 && (
            <Box sx={{ mt: 3 }}>
              {allPassed ? (
                <Alert severity="success">
                  <Typography variant="h6">
                    ✅ Integration Test Passed!
                  </Typography>
                  <Typography variant="body2">
                    All {totalTests} core integration tests passed successfully. 
                    Frontend-backend integration is working correctly.
                  </Typography>
                </Alert>
              ) : (
                <Alert severity="warning">
                  <Typography variant="h6">
                    ⚠️ Some Tests Failed
                  </Typography>
                  <Typography variant="body2">
                    {passedTests} of {totalTests} tests passed. Check the failed tests above 
                    and ensure your backend services are running correctly.
                  </Typography>
                </Alert>
              )}
            </Box>
          )}

          {/* Action Button */}
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
            <Button
              variant="contained"
              size="large"
              startIcon={<PlayArrow />}
              onClick={runQuickTests}
              disabled={isRunning}
            >
              {isRunning ? 'Running Tests...' : 'Run Quick Integration Test'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default TestRunner;