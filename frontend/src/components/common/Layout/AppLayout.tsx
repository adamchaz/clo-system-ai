import React, { useEffect } from 'react';
import { Box, CssBaseline, useTheme, useMediaQuery } from '@mui/material';
import { useAuth } from '../../../hooks/useAuth';
import { useAppSelector, useAppDispatch } from '../../../hooks/reduxHooks';
import { setSidebarOpen } from '../../../store/slices/uiSlice';
import TopBar from './TopBar';
import Sidebar from './Sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

const DRAWER_WIDTH = 280;
const DRAWER_WIDTH_COLLAPSED = 64;

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { isAuthenticated, isLoading } = useAuth();
  const sidebarOpen = useAppSelector((state) => state.ui.sidebarOpen);
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Handle responsive sidebar behavior
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      // On mobile, close sidebar when switching from larger screen
      dispatch(setSidebarOpen(false));
    }
  }, [isMobile, dispatch]);

  const handleDrawerToggle = () => {
    dispatch(setSidebarOpen(!sidebarOpen));
  };

  // Don't render layout for unauthenticated users
  if (!isAuthenticated || isLoading) {
    return <>{children}</>;
  }

  const drawerWidth = isMobile 
    ? DRAWER_WIDTH 
    : sidebarOpen 
    ? DRAWER_WIDTH 
    : DRAWER_WIDTH_COLLAPSED;

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />
      
      {/* Top Navigation Bar */}
      <TopBar 
        onMenuClick={handleDrawerToggle}
        sidebarOpen={sidebarOpen && !isMobile}
      />

      {/* Sidebar Navigation */}
      <Sidebar
        open={sidebarOpen}
        onClose={handleDrawerToggle}
        variant={isMobile ? 'temporary' : 'permanent'}
        width={drawerWidth}
      />

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: {
            xs: '100%',
            md: `calc(100% - ${drawerWidth}px)`,
          },
          ml: {
            xs: 0,
            md: `${drawerWidth}px`,
          },
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
          backgroundColor: 'background.default',
          minHeight: '100vh',
          pt: 8, // Account for TopBar height
        }}
      >
        {/* Content Container */}
        <Box
          sx={{
            p: {
              xs: 2,
              sm: 3,
            },
            height: 'calc(100vh - 64px)',
            overflow: 'auto',
          }}
        >
          {/* Page Content */}
          <Box
            sx={{
              maxWidth: '100%',
              mx: 'auto',
            }}
          >
            {children}
          </Box>
        </Box>

        {/* Optional: Floating Action Button Area */}
        <Box
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: theme.zIndex.speedDial,
          }}
        >
          {/* FAB components can be added here later */}
        </Box>
      </Box>
    </Box>
  );
};

export default AppLayout;