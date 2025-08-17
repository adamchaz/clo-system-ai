import React from 'react';
import {
  createBrowserRouter,
  RouterProvider,
  Navigate,
  Outlet,
} from 'react-router-dom';
import { useAppSelector } from '../hooks/reduxHooks';
import { selectIsAuthenticated, selectCurrentUser } from '../store/slices/authSlice';
import LoginPage from '../pages/LoginPage';
import ProtectedRoute from '../components/auth/ProtectedRoute';
import AppLayout from '../components/common/Layout/AppLayout';
import Dashboard from '../pages/Dashboard';
import Portfolios from '../pages/Portfolios';
import SystemAdminDashboard from '../pages/SystemAdminDashboard';
import UserManagement from '../pages/UserManagement';
import PortfolioManagerDashboard from '../pages/PortfolioManagerDashboard';
import FinancialAnalystDashboard from '../pages/FinancialAnalystDashboard';
import ViewerDashboard from '../pages/ViewerDashboard';
import PortfolioListPage from '../pages/PortfolioListPage';
import PortfolioDetail from '../components/portfolio/PortfolioDetail';
import { useParams } from 'react-router-dom';
import AssetManagement from '../components/portfolio/AssetManagement';
import RiskDashboard from '../components/portfolio/RiskDashboard';
import PerformanceTracker from '../components/portfolio/PerformanceTracker';
import {
  AssetDashboard,
  AssetList,
  AssetDetail,
  AssetCreateForm,
  AssetEditForm,
  AssetAnalysis,
} from '../components/assets';
import { 
  WaterfallAnalysis,
  ScenarioModeling,
  CorrelationAnalysis,
  CLOStructuring,
} from '../components/analytics';

// Legacy ProtectedRoute wrapper for existing route configuration
// This will be replaced in future tasks with the new ProtectedRoute component
const LegacyProtectedRoute: React.FC<{
  requiredRoles?: string[];
  children?: React.ReactNode;
}> = ({ requiredRoles = [], children }) => {
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const currentUser = useAppSelector(selectCurrentUser);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Convert legacy role names to new role names
  const convertLegacyRoles = (roles: string[]) => {
    const roleMap: Record<string, string> = {
      'admin': 'system_admin',
      'manager': 'portfolio_manager',
      'analyst': 'financial_analyst',
      'viewer': 'viewer',
    };
    return roles.map(role => roleMap[role] || role);
  };

  // Check role-based access if roles are specified
  if (requiredRoles.length > 0 && currentUser) {
    const convertedRoles = convertLegacyRoles(requiredRoles);
    const userRoles = currentUser.roles?.map(r => r.name) || [];
    const hasRequiredRole = convertedRoles.some(role => userRoles.includes(role));
    
    if (!hasRequiredRole) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return children ? <>{children}</> : <Outlet />;
};

// Public Route Component (redirects authenticated users)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Role-based route configurations
const getRoleBasedDefaultRoute = (role: string): string => {
  switch (role) {
    case 'system_admin':
      return '/monitoring';
    case 'admin':
      return '/monitoring';
    case 'manager':
    case 'portfolio_manager':
      return '/portfolios';
    case 'analyst':
    case 'financial_analyst':
      return '/analytics';
    case 'viewer':
      return '/reports';
    default:
      return '/dashboard';
  }
};

// Temporary placeholder components
const PlaceholderPage: React.FC<{ title: string }> = ({ title }) => (
  <div style={{ padding: '20px', textAlign: 'center' }}>
    <h1>{title}</h1>
    <p>This page will be implemented in upcoming tasks.</p>
  </div>
);

const UnauthorizedPage = () => (
  <PlaceholderPage title="Access Denied" />
);

// Smart Dashboard Component - shows appropriate dashboard based on user role
const SmartDashboard: React.FC = () => {
  const currentUser = useAppSelector(selectCurrentUser);
  
  if (!currentUser) {
    return <Dashboard />;
  }
  
  const userRole = currentUser.roles?.[0]?.name;
  
  switch (userRole) {
    case 'system_admin':
    case 'admin':
      return <SystemAdminDashboard />;
    case 'portfolio_manager':
    case 'manager':
      return <PortfolioManagerDashboard />;
    case 'financial_analyst':
    case 'analyst':
      return <FinancialAnalystDashboard />;
    case 'viewer':
      return <ViewerDashboard />;
    default:
      return <Dashboard />;
  }
};

// Portfolio management page wrappers
const RiskDashboardPage: React.FC = () => {
  return <RiskDashboard />;
};

const PortfolioDetailPage: React.FC = () => {
  const { portfolioId } = useParams<{ portfolioId: string }>();
  if (!portfolioId) {
    return <div>Portfolio ID not found</div>;
  }
  return <PortfolioDetail portfolioId={portfolioId} />;
};

// Router configuration
const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <PublicRoute>
        <LoginPage />
      </PublicRoute>
    ),
  },
  {
    path: '/unauthorized',
    element: <UnauthorizedPage />,
  },
  {
    path: '/',
    element: (
      <LegacyProtectedRoute>
        <AppLayout>
          <Outlet />
        </AppLayout>
      </LegacyProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <SmartDashboard />,
      },
      {
        path: 'portfolios',
        children: [
          {
            index: true,
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer']}>
                <Portfolios />
              </ProtectedRoute>
            ),
          },
          {
            path: 'list',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer']}>
                <PortfolioListPage />
              </ProtectedRoute>
            ),
          },
          {
            path: 'details/:portfolioId',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer']}>
                <PortfolioDetailPage />
              </ProtectedRoute>
            ),
          },
          {
            path: 'risk',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <RiskDashboardPage />
              </ProtectedRoute>
            ),
          },
          {
            path: 'performance',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <PerformanceTracker />
              </ProtectedRoute>
            ),
          },
        ],
      },
      {
        path: 'assets',
        children: [
          {
            index: true,
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <AssetDashboard />
              </ProtectedRoute>
            ),
          },
          {
            path: 'list',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer']}>
                <AssetList />
              </ProtectedRoute>
            ),
          },
          {
            path: 'create',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager']}>
                <AssetCreateForm />
              </ProtectedRoute>
            ),
          },
          {
            path: ':assetId',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer']}>
                <AssetDetail />
              </ProtectedRoute>
            ),
          },
          {
            path: ':assetId/edit',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <AssetEditForm />
              </ProtectedRoute>
            ),
          },
          {
            path: ':assetId/analysis',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <AssetAnalysis />
              </ProtectedRoute>
            ),
          },
          {
            path: 'portfolio/:portfolioId',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <AssetManagement />
              </ProtectedRoute>
            ),
          },
          {
            path: 'analysis',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <AssetDashboard />
              </ProtectedRoute>
            ),
          },
        ],
      },
      {
        path: 'analytics',
        children: [
          {
            index: true,
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <RiskDashboardPage />
              </ProtectedRoute>
            ),
          },
          {
            path: 'risk',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <RiskDashboardPage />
              </ProtectedRoute>
            ),
          },
          {
            path: 'scenarios',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <ScenarioModeling />
              </ProtectedRoute>
            ),
          },
          {
            path: 'correlation',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <CorrelationAnalysis />
              </ProtectedRoute>
            ),
          },
          {
            path: 'structuring',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <CLOStructuring />
              </ProtectedRoute>
            ),
          },
        ],
      },
      {
        path: 'waterfall',
        element: (
          <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
            <WaterfallAnalysis />
          </ProtectedRoute>
        ),
      },
      {
        path: 'reports',
        children: [
          {
            index: true,
            element: <PlaceholderPage title="Reports" />,
          },
          {
            path: 'builder',
            element: (
              <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager', 'financial_analyst']}>
                <PlaceholderPage title="Report Builder" />
              </ProtectedRoute>
            ),
          },
          {
            path: 'gallery',
            element: <PlaceholderPage title="Report Gallery" />,
          },
        ],
      },
      {
        path: 'users',
        element: (
          <ProtectedRoute requiredRoles={['system_admin']}>
            <UserManagement />
          </ProtectedRoute>
        ),
      },
      {
        path: 'monitoring',
        element: (
          <ProtectedRoute requiredRoles={['system_admin']}>
            <SystemAdminDashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'security',
        element: (
          <ProtectedRoute requiredRoles={['system_admin']}>
            <PlaceholderPage title="Security Center" />
          </ProtectedRoute>
        ),
      },
      {
        path: 'settings',
        element: (
          <ProtectedRoute requiredRoles={['system_admin', 'portfolio_manager']}>
            <PlaceholderPage title="Settings" />
          </ProtectedRoute>
        ),
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);

const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;
export { getRoleBasedDefaultRoute };