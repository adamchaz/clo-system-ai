import React from 'react';
import { Box, Typography, Tooltip, IconButton } from '@mui/material';
import { Lock, Info } from '@mui/icons-material';
import { useAppSelector } from '../../hooks/reduxHooks';
import { UserRoleType } from '../../types/auth';
import { authService } from '../../services/auth';

interface PermissionGateProps {
  children: React.ReactNode;
  requiredRoles?: UserRoleType[];
  requiredPermission?: string;
  fallback?: React.ReactNode;
  showFallback?: boolean;
  tooltipMessage?: string;
}

const PermissionGate: React.FC<PermissionGateProps> = ({
  children,
  requiredRoles,
  requiredPermission,
  fallback = null,
  showFallback = false,
  tooltipMessage,
}) => {
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);

  // If not authenticated, don't show anything
  if (!isAuthenticated || !user) {
    return showFallback ? <>{fallback}</> : null;
  }

  const userRoles = user.roles.map(role => role.name as UserRoleType);
  let hasAccess = true;

  // Check role-based access
  if (requiredRoles && requiredRoles.length > 0) {
    hasAccess = requiredRoles.some(role => userRoles.includes(role));
  }

  // Check permission-based access
  if (hasAccess && requiredPermission) {
    const userRoleNames = user.roles.map(role => role.name);
    hasAccess = authService.hasPermission(userRoleNames, requiredPermission);
  }

  if (hasAccess) {
    return <>{children}</>;
  }

  // If access is denied, show fallback or nothing
  if (showFallback && fallback) {
    return <>{fallback}</>;
  }

  if (showFallback) {
    const message = tooltipMessage || 
      `Access restricted. Required: ${requiredRoles?.join(', ') || requiredPermission || 'special permissions'}`;

    return (
      <Tooltip title={message} arrow>
        <Box
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 1,
            p: 1,
            borderRadius: 1,
            backgroundColor: 'grey.100',
            color: 'text.disabled',
            cursor: 'not-allowed',
          }}
        >
          <Lock fontSize="small" />
          <Typography variant="body2">
            Restricted Access
          </Typography>
          <IconButton size="small" disabled>
            <Info fontSize="small" />
          </IconButton>
        </Box>
      </Tooltip>
    );
  }

  return null;
};

// Convenience components for common permission patterns
export const AdminOnly: React.FC<Omit<PermissionGateProps, 'requiredRoles'>> = (props) => (
  <PermissionGate {...props} requiredRoles={['admin']} />
);

export const ManagerOrAdmin: React.FC<Omit<PermissionGateProps, 'requiredRoles'>> = (props) => (
  <PermissionGate {...props} requiredRoles={['manager', 'admin']} />
);

export const AnalystAndAbove: React.FC<Omit<PermissionGateProps, 'requiredRoles'>> = (props) => (
  <PermissionGate 
    {...props} 
    requiredRoles={['analyst', 'manager', 'admin']} 
  />
);

export const AuthenticatedOnly: React.FC<Omit<PermissionGateProps, 'requiredRoles' | 'requiredPermission'>> = (props) => {
  const { isAuthenticated } = useAppSelector((state) => state.auth);
  
  if (!isAuthenticated) {
    return props.showFallback ? <>{props.fallback}</> : null;
  }
  
  return <>{props.children}</>;
};

export default PermissionGate;