import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Chip,
  Button,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Menu,
  MenuItem,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Person,
  Email,
  AccessTime,
  Security,
  Edit,
  Logout,
  MoreVert,
  Badge,
  History,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../../hooks/reduxHooks';
import { logoutAsync } from '../../store/slices/authSlice';
import { formatDate } from '../../utils';

interface UserProfileProps {
  compact?: boolean;
  showActions?: boolean;
  onEditProfile?: () => void;
}

const UserProfile: React.FC<UserProfileProps> = ({
  compact = false,
  showActions = true,
  onEditProfile,
}) => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);

  if (!user) {
    return null;
  }

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    try {
      await dispatch(logoutAsync()).unwrap();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setLogoutDialogOpen(false);
    }
  };

  const handleEditProfile = () => {
    handleMenuClose();
    onEditProfile?.();
  };

  const getUserInitials = () => {
    return `${user.firstName.charAt(0)}${user.lastName.charAt(0)}`.toUpperCase();
  };

  const getRoleColors = (roleName: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      'system_admin': 'error',
      'portfolio_manager': 'primary',
      'financial_analyst': 'secondary',
      'viewer': 'info',
    };
    return colors[roleName] || 'default';
  };

  if (compact) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar sx={{ bgcolor: 'primary.main' }}>
          {getUserInitials()}
        </Avatar>
        <Box>
          <Typography variant="body2" fontWeight="medium">
            {user.firstName} {user.lastName}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {user.roles[0]?.displayName || user.roles[0]?.name}
          </Typography>
        </Box>
        {showActions && (
          <>
            <IconButton onClick={handleMenuClick} size="small">
              <MoreVert />
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={handleEditProfile}>
                <ListItemIcon>
                  <Edit fontSize="small" />
                </ListItemIcon>
                <ListItemText>Edit Profile</ListItemText>
              </MenuItem>
              <MenuItem onClick={() => setLogoutDialogOpen(true)}>
                <ListItemIcon>
                  <Logout fontSize="small" />
                </ListItemIcon>
                <ListItemText>Logout</ListItemText>
              </MenuItem>
            </Menu>
          </>
        )}
      </Box>
    );
  }

  return (
    <>
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3, mb: 3 }}>
          <Avatar
            sx={{
              width: 80,
              height: 80,
              bgcolor: 'primary.main',
              fontSize: '2rem',
            }}
          >
            {getUserInitials()}
          </Avatar>
          
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Typography variant="h5" component="h2">
                {user.firstName} {user.lastName}
              </Typography>
              {showActions && (
                <IconButton onClick={handleMenuClick} size="small">
                  <MoreVert />
                </IconButton>
              )}
            </Box>
            
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {user.email}
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
              {user.roles.map((role) => (
                <Chip
                  key={role.id}
                  label={role.displayName || role.name}
                  size="small"
                  color={getRoleColors(role.name)}
                  icon={<Badge />}
                />
              ))}
            </Box>
          </Box>
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography variant="h6" gutterBottom>
              Account Information
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <Email />
                </ListItemIcon>
                <ListItemText
                  primary="Email Address"
                  secondary={user.email}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Person />
                </ListItemIcon>
                <ListItemText
                  primary="User ID"
                  secondary={user.id}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Security />
                </ListItemIcon>
                <ListItemText
                  primary="Account Status"
                  secondary={
                    <Chip 
                      label={user.isActive ? 'Active' : 'Inactive'} 
                      size="small"
                      color={user.isActive ? 'success' : 'error'}
                    />
                  }
                />
              </ListItem>
            </List>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <Typography variant="h6" gutterBottom>
              Activity
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <History />
                </ListItemIcon>
                <ListItemText
                  primary="Account Created"
                  secondary={formatDate(user.createdAt)}
                />
              </ListItem>
              {user.lastLogin && (
                <ListItem>
                  <ListItemIcon>
                    <AccessTime />
                  </ListItemIcon>
                  <ListItemText
                    primary="Last Login"
                    secondary={formatDate(user.lastLogin)}
                  />
                </ListItem>
              )}
              <ListItem>
                <ListItemIcon>
                  <Edit />
                </ListItemIcon>
                <ListItemText
                  primary="Last Updated"
                  secondary={formatDate(user.updatedAt)}
                />
              </ListItem>
            </List>
          </Grid>
        </Grid>

        {showActions && (
          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<Edit />}
              onClick={onEditProfile}
            >
              Edit Profile
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<Logout />}
              onClick={() => setLogoutDialogOpen(true)}
            >
              Logout
            </Button>
          </Box>
        )}
      </Paper>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleEditProfile}>
          <ListItemIcon>
            <Edit fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit Profile</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => setLogoutDialogOpen(true)}>
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>

      {/* Logout Confirmation Dialog */}
      <Dialog open={logoutDialogOpen} onClose={() => setLogoutDialogOpen(false)}>
        <DialogTitle>Confirm Logout</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to logout? You will need to sign in again to access the system.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLogoutDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleLogout} 
            color="error" 
            variant="contained"
          >
            Logout
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default UserProfile;