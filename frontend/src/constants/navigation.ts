import {
  Dashboard,
  Business as Portfolio,
  AccountBalance,
  Analytics,
  Assessment,
  Settings,
  People,
  MonitorHeart,
  TrendingUp,
  PieChart,
  TableChart,
  Description,
  Security,
  Insights,
  Add,
} from '@mui/icons-material';
import { UserRoleType } from '../types/auth';

export interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon: React.ComponentType<any>;
  roles: UserRoleType[];
  children?: NavigationItem[];
  badge?: string | number;
  description?: string;
}

export const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    path: '/dashboard',
    icon: Dashboard,
    roles: ['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer'],
    description: 'Overview of portfolio performance and key metrics',
  },
  {
    id: 'portfolios',
    label: 'Portfolio Management',
    path: '/portfolios',
    icon: Portfolio,
    roles: ['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer'],
    description: 'Manage and monitor CLO portfolios',
    children: [
      {
        id: 'portfolio-list',
        label: 'Portfolio List',
        path: '/portfolios/list',
        icon: TableChart,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer'],
      },
      {
        id: 'portfolio-details',
        label: 'Portfolio Details',
        path: '/portfolios/details',
        icon: Insights,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer'],
      },
      {
        id: 'portfolio-risk',
        label: 'Risk Dashboard',
        path: '/portfolios/risk',
        icon: Assessment,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
      },
      {
        id: 'portfolio-performance',
        label: 'Performance Tracker',
        path: '/portfolios/performance',
        icon: TrendingUp,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
      },
    ],
  },
  {
    id: 'assets',
    label: 'Asset Management',
    path: '/assets',
    icon: AccountBalance,
    roles: ['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer'],
    description: 'Manage individual assets and analyze performance',
    children: [
      {
        id: 'asset-dashboard',
        label: 'Asset Dashboard',
        path: '/assets',
        icon: Dashboard,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
      },
      {
        id: 'asset-list',
        label: 'Asset List',
        path: '/assets/list',
        icon: TableChart,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer'],
      },
      {
        id: 'asset-create',
        label: 'Add New Asset',
        path: '/assets/create',
        icon: Add,
        roles: ['system_admin', 'portfolio_manager'],
      },
      {
        id: 'asset-analysis',
        label: 'Portfolio Analysis',
        path: '/assets/analysis',
        icon: Analytics,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
      },
    ],
  },
  {
    id: 'analytics',
    label: 'Risk Analytics',
    path: '/analytics',
    icon: Analytics,
    roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
    description: 'Advanced risk analysis and stress testing',
    children: [
      {
        id: 'risk-analysis',
        label: 'Risk Analysis',
        path: '/analytics/risk',
        icon: Assessment,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
      },
      {
        id: 'scenario-modeling',
        label: 'Scenario Modeling',
        path: '/analytics/scenarios',
        icon: TrendingUp,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
      },
      {
        id: 'correlation-analysis',
        label: 'Correlation Analysis',
        path: '/analytics/correlation',
        icon: PieChart,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
      },
      {
        id: 'clo-structuring',
        label: 'CLO Structuring',
        path: '/analytics/structuring',
        icon: Assessment,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
      },
    ],
  },
  {
    id: 'waterfall',
    label: 'Waterfall Analysis',
    path: '/waterfall',
    icon: Assessment,
    roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
    description: 'CLO waterfall calculations and distribution analysis',
  },
  {
    id: 'reports',
    label: 'Reports',
    path: '/reports',
    icon: Description,
    roles: ['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer'],
    description: 'Generate and view analytical reports',
    children: [
      {
        id: 'report-builder',
        label: 'Report Builder',
        path: '/reports/builder',
        icon: TableChart,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst'],
      },
      {
        id: 'report-gallery',
        label: 'Report Gallery',
        path: '/reports/gallery',
        icon: PieChart,
        roles: ['system_admin', 'portfolio_manager', 'financial_analyst', 'viewer'],
      },
    ],
  },
  {
    id: 'users',
    label: 'User Management',
    path: '/users',
    icon: People,
    roles: ['system_admin'],
    description: 'Manage system users and permissions',
  },
  {
    id: 'monitoring',
    label: 'System Monitoring',
    path: '/monitoring',
    icon: MonitorHeart,
    roles: ['system_admin'],
    description: 'Monitor system health and performance',
  },
  {
    id: 'security',
    label: 'Security Center',
    path: '/security',
    icon: Security,
    roles: ['system_admin'],
    description: 'Security settings and audit logs',
  },
  {
    id: 'settings',
    label: 'Settings',
    path: '/settings',
    icon: Settings,
    roles: ['system_admin', 'portfolio_manager'],
    description: 'Application settings and configuration',
  },
];

export const getNavigationForRole = (userRoles: string[]): NavigationItem[] => {
  return NAVIGATION_ITEMS.filter(item =>
    item.roles.some(role => userRoles.includes(role))
  ).map(item => ({
    ...item,
    children: item.children?.filter(child =>
      child.roles.some(role => userRoles.includes(role))
    ),
  }));
};

export const findNavigationItem = (path: string): NavigationItem | null => {
  const findInItems = (items: NavigationItem[]): NavigationItem | null => {
    for (const item of items) {
      if (item.path === path) return item;
      if (item.children) {
        const found = findInItems(item.children);
        if (found) return found;
      }
    }
    return null;
  };

  return findInItems(NAVIGATION_ITEMS);
};

export const getBreadcrumbs = (path: string): NavigationItem[] => {
  const breadcrumbs: NavigationItem[] = [];
  const segments = path.split('/').filter(Boolean);
  let currentPath = '';

  for (const segment of segments) {
    currentPath += `/${segment}`;
    const item = findNavigationItem(currentPath);
    if (item) {
      breadcrumbs.push(item);
    }
  }

  return breadcrumbs;
};