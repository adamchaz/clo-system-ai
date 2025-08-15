/**
 * TopBar Component - Enhanced with Real-time Integration
 * 
 * Main application navigation bar with integrated real-time features:
 * - Live WebSocket connection status indicator
 * - Real-time notifications and alerts system
 * - User profile management and theme controls
 * - Breadcrumb navigation with dynamic updates
 * 
 * Part of CLO Management System - TASK 12: Real-time Data and WebSocket Integration
 */
import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Breadcrumbs,
  Link,
  Badge,
  Menu,
  MenuItem,
  Avatar,
  Tooltip,
  Divider,
  ListItemIcon,
  ListItemText,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications,
  Logout,
  Settings,
  Person,
  Brightness4,
  Brightness7,
  NavigateNext,
} from '@mui/icons-material';
import { useLocation, Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { useAppSelector, useAppDispatch } from '../../../hooks/reduxHooks';
import { toggleTheme } from '../../../store/slices/uiSlice';
import { getBreadcrumbs } from '../../../constants/navigation';
import { 
  ConnectionStatusIndicator,
  RealTimeNotifications,
} from '../RealTime';

interface TopBarProps {
  onMenuClick: () => void;
  sidebarOpen: boolean;
}

const TopBar: React.FC<TopBarProps> = ({ onMenuClick, sidebarOpen }) => {
  const theme = useTheme();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const { user, logout, getDisplayName, getUserInitials } = useAuth();
  const currentTheme = useAppSelector((state) => state.ui.theme);
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleProfileMenuClose();
    await logout();
  };

  const handleThemeToggle = () => {
    dispatch(toggleTheme());
  };

  const breadcrumbs = getBreadcrumbs(location.pathname);

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: 'background.paper',
        color: 'text.primary',
        boxShadow: 1,
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <Toolbar>
        {/* Menu Button */}
        <IconButton
          color="inherit"
          aria-label="open drawer"
          onClick={onMenuClick}
          edge="start"
          sx={{
            marginRight: 2,
            display: { sm: sidebarOpen ? 'none' : 'block' },
          }}
        >
          <MenuIcon />
        </IconButton>

        {/* App Title and Breadcrumbs */}
        <Box sx={{ flexGrow: 1 }}>
          {isMobile ? (
            <Typography variant="h6" noWrap component="div">
              CLO System
            </Typography>
          ) : (
            <Box>
              <Typography
                variant="h6"
                component="div"
                sx={{
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  color: 'primary.main',
                  mb: 0.5,
                }}
              >
                CLO Management System
              </Typography>
              
              {breadcrumbs.length > 0 && (
                <Breadcrumbs
                  aria-label="breadcrumb"
                  separator={<NavigateNext fontSize="small" />}
                  sx={{
                    fontSize: '0.875rem',
                    '& .MuiBreadcrumbs-separator': {
                      color: 'text.secondary',
                    },
                  }}
                >
                  <Link
                    component={RouterLink}
                    to="/dashboard"
                    color="inherit"
                    underline="hover"
                  >
                    Dashboard
                  </Link>
                  {breadcrumbs.map((crumb, index) => {
                    const isLast = index === breadcrumbs.length - 1;
                    return isLast ? (
                      <Typography key={crumb.id} color="text.primary">
                        {crumb.label}
                      </Typography>
                    ) : (
                      <Link
                        key={crumb.id}
                        component={RouterLink}
                        to={crumb.path}
                        color="inherit"
                        underline="hover"
                      >
                        {crumb.label}
                      </Link>
                    );
                  })}
                </Breadcrumbs>
              )}
            </Box>
          )}
        </Box>

        {/* Theme Toggle */}
        <Tooltip title="Toggle theme">
          <IconButton
            color="inherit"
            onClick={handleThemeToggle}
            sx={{ mx: 1 }}
          >
            {currentTheme === 'dark' ? <Brightness7 /> : <Brightness4 />}
          </IconButton>
        </Tooltip>

        {/* Real-time Connection Status */}
        <ConnectionStatusIndicator variant="icon" size="medium" />

        {/* Real-time Notifications */}
        <RealTimeNotifications maxVisible={5} autoHideDelay={5000} />

        {/* User Profile */}
        <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
          {!isMobile && user && (
            <Box sx={{ mr: 2, textAlign: 'right' }}>
              <Typography variant="body2" sx={{ lineHeight: 1.2 }}>
                {getDisplayName()}
              </Typography>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ lineHeight: 1.2 }}
              >
                {user.roles?.[0]?.displayName || 'User'}
              </Typography>
            </Box>
          )}
          
          <Tooltip title="Account settings">
            <IconButton
              onClick={handleProfileMenuOpen}
              size="small"
              sx={{ ml: 1 }}
              aria-controls={anchorEl ? 'account-menu' : undefined}
              aria-haspopup="true"
              aria-expanded={anchorEl ? 'true' : undefined}
            >
              <Avatar
                sx={{
                  width: 36,
                  height: 36,
                  bgcolor: 'primary.main',
                  fontSize: '0.875rem',
                }}
              >
                {getUserInitials()}
              </Avatar>
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>

      {/* Profile Menu */}
      <Menu
        anchorEl={anchorEl}
        id="account-menu"
        open={Boolean(anchorEl)}
        onClose={handleProfileMenuClose}
        onClick={handleProfileMenuClose}
        PaperProps={{
          elevation: 3,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            minWidth: 200,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem component={RouterLink} to="/profile">
          <ListItemIcon>
            <Person fontSize="small" />
          </ListItemIcon>
          <ListItemText>Profile</ListItemText>
        </MenuItem>
        
        <MenuItem component={RouterLink} to="/settings">
          <ListItemIcon>
            <Settings fontSize="small" />
          </ListItemIcon>
          <ListItemText>Settings</ListItemText>
        </MenuItem>
        
        <Divider />
        
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <Logout fontSize="small" />
          </ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>

    </AppBar>
  );
};

export default TopBar;