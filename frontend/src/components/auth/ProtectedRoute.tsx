import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, Typography, Paper, Button } from '@mui/material';
import { Lock } from '@mui/icons-material';
import { useAppSelector } from '../../hooks/reduxHooks';
import { UserRoleType, ProtectedRouteProps } from '../../types/auth';
import { authService } from '../../services/auth';

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
  requiredPermission,
  fallbackPath = '/login',
}) => {
  const location = useLocation();
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);

  // Check if user is authenticated
  if (!isAuthenticated || !user) {
    return (
      <Navigate 
        to={fallbackPath} 
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  // Check role-based access
  if (requiredRoles && requiredRoles.length > 0) {
    const userRoles = user.roles.map(role => role.name as UserRoleType);
    const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));
    
    if (!hasRequiredRole) {
      return <AccessDeniedPage requiredRoles={requiredRoles} userRoles={userRoles} />;
    }
  }

  // Check permission-based access
  if (requiredPermission) {
    const userRoles = user.roles.map(role => role.name);
    const hasPermission = authService.hasPermission(userRoles, requiredPermission);
    
    if (!hasPermission) {
      return <AccessDeniedPage requiredPermission={requiredPermission} />;
    }
  }

  return <>{children}</>;
};

interface AccessDeniedPageProps {
  requiredRoles?: UserRoleType[];
  requiredPermission?: string;
  userRoles?: UserRoleType[];
}

const AccessDeniedPage: React.FC<AccessDeniedPageProps> = ({
  requiredRoles,
  requiredPermission,
  userRoles,
}) => {
  const handleGoBack = () => {
    window.history.back();
  };

  const handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        backgroundColor: 'background.default',
        p: 3,
      }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          maxWidth: 500,
          textAlign: 'center',
        }}
      >
        <Box sx={{ mb: 3 }}>
          <Lock 
            color="error" 
            sx={{ fontSize: 64, mb: 2 }} 
          />
          <Typography variant="h4" color="error" gutterBottom>
            Access Denied
          </Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body1" color="text.secondary" paragraph>
            You don't have permission to access this resource.
          </Typography>

          {requiredRoles && (
            <Box sx={{ mt: 2, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary">
                <strong>Required Role(s):</strong> {requiredRoles.join(', ')}
              </Typography>
              {userRoles && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  <strong>Your Role(s):</strong> {userRoles.join(', ')}
                </Typography>
              )}
            </Box>
          )}

          {requiredPermission && (
            <Box sx={{ mt: 2, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2" color="text.secondary">
                <strong>Required Permission:</strong> {requiredPermission}
              </Typography>
            </Box>
          )}
        </Box>

        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            variant="outlined"
            onClick={handleGoBack}
          >
            Go Back
          </Button>
          <Button
            variant="contained"
            onClick={handleGoHome}
          >
            Go to Dashboard
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default ProtectedRoute;