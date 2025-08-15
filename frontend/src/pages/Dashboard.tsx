import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  AccountBalance,
  Assessment,
  Security,
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  color?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  subtitle, 
  icon, 
  color = 'primary.main' 
}) => {
  const theme = useTheme();
  
  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s ease-in-out',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[8],
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: `${color}15`,
              color,
              mr: 2,
            }}
          >
            {icon}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography
              variant="h4"
              component="div"
              sx={{
                fontWeight: 700,
                lineHeight: 1.2,
                color: 'text.primary',
              }}
            >
              {value}
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              {title}
            </Typography>
            {subtitle && (
              <Typography
                variant="caption"
                sx={{
                  color: color,
                  fontWeight: 600,
                  mt: 1,
                  display: 'block',
                }}
              >
                {subtitle}
              </Typography>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const { user, getPrimaryRole } = useAuth();
  const theme = useTheme();

  const getWelcomeMessage = () => {
    const role = user?.roles?.[0]?.name || user?.role || 'viewer';
    const timeOfDay = new Date().getHours();
    const greeting = timeOfDay < 12 ? 'Good morning' : timeOfDay < 18 ? 'Good afternoon' : 'Good evening';
    
    switch (role) {
      case 'system_admin':
      case 'admin':
        return `${greeting}! System overview and user activity at a glance.`;
      case 'portfolio_manager':
      case 'manager':
        return `${greeting}! Here's your portfolio performance and risk overview.`;
      case 'financial_analyst':
      case 'analyst':
        return `${greeting}! Analytics and market insights are ready for review.`;
      case 'viewer':
        return `${greeting}! View the latest portfolio summaries and reports.`;
      default:
        return `${greeting}! Welcome to the CLO Management System.`;
    }
  };

  const getRoleSpecificMetrics = () => {
    const role = user?.roles?.[0]?.name || user?.role || 'viewer';
    
    switch (role) {
      case 'system_admin':
      case 'admin':
        return [
          {
            title: 'Active Users',
            value: '47',
            subtitle: '+3 this week',
            icon: <Security />,
            color: theme.palette.success.main,
          },
          {
            title: 'System Health',
            value: '99.8%',
            subtitle: 'Uptime',
            icon: <Assessment />,
            color: theme.palette.info.main,
          },
          {
            title: 'Active CLOs',
            value: '23',
            subtitle: '2 new this month',
            icon: <AccountBalance />,
            color: theme.palette.primary.main,
          },
          {
            title: 'Data Quality',
            value: '98.2%',
            subtitle: 'Validation score',
            icon: <TrendingUp />,
            color: theme.palette.warning.main,
          },
        ];
      
      case 'portfolio_manager':
      case 'manager':
        return [
          {
            title: 'Total AUM',
            value: '$2.4B',
            subtitle: '+2.3% MTD',
            icon: <AccountBalance />,
            color: theme.palette.primary.main,
          },
          {
            title: 'Portfolio NAV',
            value: '$1.98B',
            subtitle: '+1.8% this month',
            icon: <TrendingUp />,
            color: theme.palette.success.main,
          },
          {
            title: 'Active CLOs',
            value: '15',
            subtitle: '3 performing above target',
            icon: <Assessment />,
            color: theme.palette.info.main,
          },
          {
            title: 'Risk Score',
            value: '7.2/10',
            subtitle: 'Within target range',
            icon: <Security />,
            color: theme.palette.warning.main,
          },
        ];
      
      case 'financial_analyst':
      case 'analyst':
        return [
          {
            title: 'Analysis Queue',
            value: '12',
            subtitle: '3 urgent reviews',
            icon: <Assessment />,
            color: theme.palette.primary.main,
          },
          {
            title: 'Market Risk',
            value: 'Moderate',
            subtitle: 'Credit spreads stable',
            icon: <TrendingUp />,
            color: theme.palette.info.main,
          },
          {
            title: 'Correlation Score',
            value: '0.73',
            subtitle: 'Portfolio diversification',
            icon: <AccountBalance />,
            color: theme.palette.success.main,
          },
          {
            title: 'Stress Tests',
            value: '8/10',
            subtitle: 'Scenarios passed',
            icon: <Security />,
            color: theme.palette.warning.main,
          },
        ];
      
      case 'viewer':
      default:
        return [
          {
            title: 'Available Reports',
            value: '24',
            subtitle: '6 updated today',
            icon: <Assessment />,
            color: theme.palette.primary.main,
          },
          {
            title: 'Portfolio Value',
            value: '$1.98B',
            subtitle: 'Current NAV',
            icon: <AccountBalance />,
            color: theme.palette.info.main,
          },
          {
            title: 'Performance',
            value: '+1.8%',
            subtitle: 'Monthly return',
            icon: <TrendingUp />,
            color: theme.palette.success.main,
          },
          {
            title: 'Last Updated',
            value: '2 min',
            subtitle: 'ago',
            icon: <Security />,
            color: theme.palette.text.secondary,
          },
        ];
    }
  };

  return (
    <Box>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          component="h1"
          sx={{
            fontWeight: 700,
            color: 'text.primary',
            mb: 1,
          }}
        >
          Welcome back, {user?.firstName || user?.full_name?.split(' ')[0] || 'User'}!
        </Typography>
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ fontSize: '1.1rem' }}
        >
          {getWelcomeMessage()}
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: 'primary.main',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: 1,
            mt: 1,
            display: 'block',
          }}
        >
          {getPrimaryRole()}
        </Typography>
      </Box>

      {/* Key Metrics Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {getRoleSpecificMetrics().map((metric, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
            <MetricCard {...metric} />
          </Grid>
        ))}
      </Grid>

      {/* Quick Actions or Charts Area */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Paper
            sx={{
              p: 3,
              height: 300,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'background.paper',
              border: 1,
              borderColor: 'divider',
              borderStyle: 'dashed',
            }}
          >
            <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
              <Assessment sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6" gutterBottom>
                Interactive Charts Coming Soon
              </Typography>
              <Typography variant="body2">
                Portfolio performance and risk analytics visualization will be available in the next release.
              </Typography>
            </Box>
          </Paper>
        </Grid>
        
        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper
            sx={{
              p: 3,
              height: 300,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'background.paper',
              border: 1,
              borderColor: 'divider',
              borderStyle: 'dashed',
            }}
          >
            <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
              <TrendingUp sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <Typography variant="body2">
                Activity feed and notifications panel will be integrated here.
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;