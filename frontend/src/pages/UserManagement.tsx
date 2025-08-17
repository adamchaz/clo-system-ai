import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  Card,
  CardContent,
  Breadcrumbs,
  Link,
  Divider,
} from '@mui/material';
import {
  Add,
  People,
  Security,
  Home,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { User } from '../store/api/cloApi';
import UserList from '../components/admin/UserList';
import UserForm from '../components/admin/UserForm';

const UserManagement: React.FC = () => {
  const { user: currentUser, hasRole } = useAuth();
  const [userFormOpen, setUserFormOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');

  // Check if user has admin access
  const hasAdminAccess = hasRole('admin');

  // Handlers
  const handleCreateUser = useCallback(() => {
    setSelectedUser(null);
    setFormMode('create');
    setUserFormOpen(true);
  }, []);

  const handleEditUser = useCallback((user: User) => {
    setSelectedUser(user);
    setFormMode('edit');
    setUserFormOpen(true);
  }, []);

  const handleCloseUserForm = useCallback(() => {
    setUserFormOpen(false);
    setSelectedUser(null);
  }, []);

  const handleUserSelect = useCallback((user: User) => {
    // For now, just show user details in console
    // In a future implementation, this could open a user details panel
    console.log('Selected user:', user);
  }, []);

  // If user doesn't have admin access, show access denied
  if (!hasAdminAccess) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ maxWidth: 600, mx: 'auto' }}>
          <Typography variant="h6" gutterBottom>
            Access Denied
          </Typography>
          <Typography variant="body1">
            You don't have permission to access the user management system. 
            System administrator privileges are required.
          </Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Breadcrumbs */}
      <Box sx={{ mb: 3 }}>
        <Breadcrumbs aria-label="breadcrumb">
          <Link
            underline="hover"
            color="inherit"
            href="/dashboard"
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <Home sx={{ mr: 0.5 }} fontSize="inherit" />
            Dashboard
          </Link>
          <Link
            underline="hover"
            color="inherit"
            href="/monitoring"
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <Security sx={{ mr: 0.5 }} fontSize="inherit" />
            System Admin
          </Link>
          <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
            <People sx={{ mr: 0.5 }} fontSize="inherit" />
            User Management
          </Typography>
        </Breadcrumbs>
      </Box>

      {/* Page Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
        <Box>
          <Typography
            variant="h4"
            component="h1"
            sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}
          >
            User Management
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            Manage system users, roles, and permissions. Add new users or modify existing user accounts.
          </Typography>
          
          {/* Quick Stats */}
          <Box sx={{ display: 'flex', gap: 4, mt: 2 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Current User
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                {currentUser?.firstName} {currentUser?.lastName}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Your Role
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                System Administrator
              </Typography>
            </Box>
          </Box>
        </Box>

        <Button
          variant="contained"
          size="large"
          startIcon={<Add />}
          onClick={handleCreateUser}
          sx={{ px: 3, py: 1.5 }}
        >
          Create New User
        </Button>
      </Box>

      {/* Help Information */}
      <Card sx={{ mb: 4, bgcolor: 'primary.50', borderColor: 'primary.200' }} variant="outlined">
        <CardContent>
          <Typography variant="subtitle2" color="primary.main" gutterBottom sx={{ fontWeight: 600 }}>
            💡 User Management Tips
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              • <strong>System Admin:</strong> Full access to all system features and user management
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • <strong>Portfolio Manager:</strong> Can manage portfolios and execute trades
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • <strong>Financial Analyst:</strong> Can analyze data and generate reports
            </Typography>
            <Typography variant="body2" color="text.secondary">
              • <strong>Viewer:</strong> Read-only access to reports and data
            </Typography>
          </Box>
          <Divider sx={{ my: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Use the toggle switch to quickly activate/deactivate user accounts. 
            Inactive users cannot log in but their data is preserved.
          </Typography>
        </CardContent>
      </Card>

      {/* User List Component */}
      <UserList
        onUserCreate={handleCreateUser}
        onUserEdit={handleEditUser}
        onUserSelect={handleUserSelect}
      />

      {/* User Form Dialog */}
      <UserForm
        open={userFormOpen}
        onClose={handleCloseUserForm}
        user={selectedUser}
        mode={formMode}
      />
    </Box>
  );
};

export default UserManagement;