import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  IconButton,
} from '@mui/material';
import {
  Add,
  Visibility,
  Edit,
  TrendingUp,
  TrendingDown,
  AccountBalance,
} from '@mui/icons-material';

// Mock data for portfolios
const mockPortfolios = [
  {
    id: 1,
    name: 'MAG CLO XIV-R',
    type: 'Revolving Credit',
    totalValue: '$850M',
    nav: '$823M',
    performance: '+2.3%',
    trend: 'up',
    assets: 127,
    status: 'Active',
    manager: 'Magnetar Capital',
  },
  {
    id: 2,
    name: 'MAG CLO XV',
    type: 'Static Pool',
    totalValue: '$650M',
    nav: '$642M',
    performance: '+1.8%',
    trend: 'up',
    assets: 94,
    status: 'Active',
    manager: 'Magnetar Capital',
  },
  {
    id: 3,
    name: 'MAG CLO XIII-R',
    type: 'Revolving Credit',
    totalValue: '$720M',
    nav: '$698M',
    performance: '-0.5%',
    trend: 'down',
    assets: 112,
    status: 'In Refinancing',
    manager: 'Magnetar Capital',
  },
];

const Portfolios: React.FC = () => {
  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography
            variant="h4"
            component="h1"
            sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}
          >
            Portfolio Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor and manage CLO portfolios across different structures and strategies.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          sx={{ px: 3, py: 1.5 }}
        >
          Create Portfolio
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalance color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" component="div">
                  Total AUM
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                $2.22B
              </Typography>
              <Typography variant="body2" color="success.main">
                +5.2% YTD
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUp color="success" sx={{ mr: 1 }} />
                <Typography variant="h6" component="div">
                  Active CLOs
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                3
              </Typography>
              <Typography variant="body2" color="text.secondary">
                All performing
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6" component="div">
                  Avg Performance
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main' }}>
                +1.9%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This quarter
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6" component="div">
                  Total Assets
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                333
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Underlying loans
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Portfolio Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Portfolio Name</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Total Value</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>NAV</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Performance</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Assets</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mockPortfolios.map((portfolio) => (
                <TableRow key={portfolio.id} hover>
                  <TableCell>
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {portfolio.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {portfolio.manager}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {portfolio.type}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {portfolio.totalValue}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {portfolio.nav}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {portfolio.trend === 'up' ? (
                        <TrendingUp color="success" sx={{ mr: 0.5, fontSize: 16 }} />
                      ) : (
                        <TrendingDown color="error" sx={{ mr: 0.5, fontSize: 16 }} />
                      )}
                      <Typography
                        variant="body2"
                        color={portfolio.trend === 'up' ? 'success.main' : 'error.main'}
                        sx={{ fontWeight: 600 }}
                      >
                        {portfolio.performance}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {portfolio.assets}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={portfolio.status}
                      color={portfolio.status === 'Active' ? 'success' : 'warning'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <IconButton size="small" color="primary">
                        <Visibility fontSize="small" />
                      </IconButton>
                      <IconButton size="small">
                        <Edit fontSize="small" />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default Portfolios;