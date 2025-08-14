import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Box,
  Typography,
  Avatar,
  Tooltip,
  Badge,
  useTheme,
  useMediaQuery,
  alpha,
} from '@mui/material';
import {
  ExpandLess,
  ExpandMore,
  FiberManualRecord,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { getNavigationForRole, NavigationItem } from '../../../constants/navigation';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  variant: 'permanent' | 'temporary';
  width: number;
}

interface NavigationListItemProps {
  item: NavigationItem;
  level?: number;
  collapsed?: boolean;
}

const NavigationListItem: React.FC<NavigationListItemProps> = ({ 
  item, 
  level = 0, 
  collapsed = false 
}) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);

  const isActive = location.pathname === item.path || 
    (item.children && item.children.some(child => location.pathname === child.path));

  const handleClick = () => {
    if (item.children && item.children.length > 0) {
      setOpen(!open);
    } else {
      navigate(item.path);
    }
  };

  const ItemIcon = item.icon;

  return (
    <>
      <ListItem disablePadding sx={{ display: 'block' }}>
        <Tooltip title={collapsed ? item.label : ''} placement="right">
          <ListItemButton
            onClick={handleClick}
            sx={{
              minHeight: 48,
              px: level === 0 ? 2.5 : level * 2 + 2.5,
              py: 1.5,
              borderRadius: 1,
              mx: 1,
              my: 0.5,
              backgroundColor: isActive ? alpha(theme.palette.primary.main, 0.12) : 'transparent',
              color: isActive ? 'primary.main' : 'text.primary',
              '&:hover': {
                backgroundColor: isActive 
                  ? alpha(theme.palette.primary.main, 0.16) 
                  : alpha(theme.palette.text.primary, 0.04),
              },
              ...(level > 0 && {
                pl: 4,
                '&:before': {
                  content: '""',
                  position: 'absolute',
                  left: 20,
                  top: '50%',
                  width: 4,
                  height: 4,
                  borderRadius: '50%',
                  backgroundColor: isActive ? 'primary.main' : 'text.secondary',
                  transform: 'translateY(-50%)',
                },
              }),
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 0,
                mr: collapsed ? 'auto' : 3,
                justifyContent: 'center',
                color: 'inherit',
              }}
            >
              {level === 0 ? (
                <ItemIcon fontSize="small" />
              ) : (
                <FiberManualRecord sx={{ fontSize: 8 }} />
              )}
            </ListItemIcon>
            
            {!collapsed && (
              <>
                <ListItemText
                  primary={
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: isActive ? 600 : 400,
                        fontSize: level === 0 ? '0.875rem' : '0.8125rem',
                      }}
                    >
                      {item.label}
                    </Typography>
                  }
                  sx={{ opacity: collapsed ? 0 : 1 }}
                />
                
                {item.badge && (
                  <Badge
                    badgeContent={item.badge}
                    color="error"
                    sx={{
                      '& .MuiBadge-badge': {
                        fontSize: '0.625rem',
                        height: 16,
                        minWidth: 16,
                      },
                    }}
                  />
                )}
                
                {item.children && item.children.length > 0 && (
                  <Box sx={{ ml: 1 }}>
                    {open ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
                  </Box>
                )}
              </>
            )}
          </ListItemButton>
        </Tooltip>
      </ListItem>

      {item.children && item.children.length > 0 && !collapsed && (
        <Collapse in={open} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            {item.children.map((child) => (
              <NavigationListItem
                key={child.id}
                item={child}
                level={level + 1}
                collapsed={collapsed}
              />
            ))}
          </List>
        </Collapse>
      )}
    </>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ open, onClose, variant, width }) => {
  const theme = useTheme();
  const { user, getDisplayName, getUserInitials, getPrimaryRole } = useAuth();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const navigationItems = user ? getNavigationForRole(user.roles.map(role => role.name)) : [];

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo/Brand Section */}
      <Box
        sx={{
          p: 3,
          display: 'flex',
          alignItems: 'center',
          borderBottom: 1,
          borderColor: 'divider',
          minHeight: 64,
        }}
      >
        {!isMobile && open && (
          <Box>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                color: 'primary.main',
                fontSize: '1.125rem',
                lineHeight: 1.2,
              }}
            >
              CLO System
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: 'text.secondary',
                fontSize: '0.75rem',
                letterSpacing: 0.5,
              }}
            >
              MANAGEMENT PLATFORM
            </Typography>
          </Box>
        )}
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', py: 1 }}>
        <List>
          {navigationItems.map((item) => (
            <NavigationListItem
              key={item.id}
              item={item}
              collapsed={!open && !isMobile}
            />
          ))}
        </List>
      </Box>

      {/* User Profile Section */}
      {user && (
        <Box
          sx={{
            p: 2,
            borderTop: 1,
            borderColor: 'divider',
            backgroundColor: alpha(theme.palette.primary.main, 0.04),
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              px: 1,
              py: 1.5,
              borderRadius: 1,
              backgroundColor: 'background.paper',
              boxShadow: theme.shadows[1],
            }}
          >
            <Avatar
              sx={{
                width: 40,
                height: 40,
                bgcolor: 'primary.main',
                fontSize: '0.875rem',
                fontWeight: 600,
              }}
            >
              {getUserInitials()}
            </Avatar>
            
            {(open || isMobile) && (
              <Box sx={{ ml: 2, flexGrow: 1, overflow: 'hidden' }}>
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 600,
                    lineHeight: 1.2,
                    fontSize: '0.875rem',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {getDisplayName()}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: 'text.secondary',
                    lineHeight: 1.2,
                    fontSize: '0.75rem',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {getPrimaryRole()}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      )}
    </Box>
  );

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: width,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: width,
          boxSizing: 'border-box',
          borderRight: 1,
          borderColor: 'divider',
          backgroundColor: 'background.paper',
        },
      }}
      ModalProps={{
        keepMounted: true, // Better open performance on mobile.
      }}
    >
      {drawerContent}
    </Drawer>
  );
};

export default Sidebar;