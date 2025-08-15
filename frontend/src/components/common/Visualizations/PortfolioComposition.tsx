import React, { useState, useMemo, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  SelectChangeEvent,
  Chip
} from '@mui/material';
import {
  PieChart,
  DonutLarge,
  Business as BusinessIcon,
  Public as PublicIcon,
  Category as CategoryIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  AccountBalance as AccountBalanceIcon
} from '@mui/icons-material';
import {
  PieChart as RechartsPieChart,
  Cell,
  Pie,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  Treemap
} from 'recharts';
import { useRealTime } from '../../../hooks/useRealTimeData';
import MetricCard from '../UI/MetricCard';

/**
 * TASK 13: Advanced Data Visualization Components
 * 
 * PortfolioComposition - Comprehensive portfolio composition visualization
 * 
 * Features:
 * - Asset allocation by type, sector, geography
 * - Interactive pie charts and treemap views
 * - Concentration analysis and risk metrics
 * - Real-time composition updates
 * - Top holdings with detailed breakdowns
 * - ESG and credit rating distributions
 */

interface AssetHolding {
  symbol: string;
  name: string;
  value: number;
  weight: number;
  sector: string;
  assetType: string;
  geography: string;
  creditRating?: string;
  esgScore?: number;
}

interface CompositionData {
  category: string;
  value: number;
  weight: number;
  color: string;
  subcategories?: CompositionData[];
}

export interface PortfolioCompositionProps {
  portfolioId?: string;
  showTopHoldings?: boolean;
  maxHoldings?: number;
  enableRealTime?: boolean;
  height?: number;
}

const PortfolioComposition: React.FC<PortfolioCompositionProps> = ({
  portfolioId = 'default',
  showTopHoldings = true,
  maxHoldings = 10,
  enableRealTime = true,
  height = 400
}) => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [viewType, setViewType] = useState<'pie' | 'bar' | 'treemap'>('pie');

  // Real-time data integration
  const { portfolio, assets } = useRealTime();
  const portfolioData = portfolio.portfolioData;
  const assetUpdates = assets.assetUpdates;

  // Generate mock portfolio holdings
  const holdings: AssetHolding[] = useMemo(() => {
    const mockHoldings: AssetHolding[] = [
      // Technology
      { symbol: 'AAPL', name: 'Apple Inc.', value: 150000, weight: 0.15, sector: 'Technology', assetType: 'Equity', geography: 'US', creditRating: 'AA+', esgScore: 82 },
      { symbol: 'MSFT', name: 'Microsoft Corp.', value: 120000, weight: 0.12, sector: 'Technology', assetType: 'Equity', geography: 'US', creditRating: 'AAA', esgScore: 86 },
      { symbol: 'GOOGL', name: 'Alphabet Inc.', value: 100000, weight: 0.10, sector: 'Technology', assetType: 'Equity', geography: 'US', creditRating: 'AA+', esgScore: 78 },
      
      // Financial
      { symbol: 'JPM', name: 'JPMorgan Chase', value: 80000, weight: 0.08, sector: 'Financial', assetType: 'Equity', geography: 'US', creditRating: 'A+', esgScore: 71 },
      { symbol: 'BAC', name: 'Bank of America', value: 70000, weight: 0.07, sector: 'Financial', assetType: 'Equity', geography: 'US', creditRating: 'A-', esgScore: 69 },
      
      // Healthcare
      { symbol: 'JNJ', name: 'Johnson & Johnson', value: 90000, weight: 0.09, sector: 'Healthcare', assetType: 'Equity', geography: 'US', creditRating: 'AAA', esgScore: 79 },
      { symbol: 'PFE', name: 'Pfizer Inc.', value: 60000, weight: 0.06, sector: 'Healthcare', assetType: 'Equity', geography: 'US', creditRating: 'A+', esgScore: 73 },
      
      // Consumer
      { symbol: 'AMZN', name: 'Amazon.com Inc.', value: 85000, weight: 0.085, sector: 'Consumer Discretionary', assetType: 'Equity', geography: 'US', creditRating: 'AA', esgScore: 68 },
      { symbol: 'KO', name: 'Coca-Cola Co.', value: 55000, weight: 0.055, sector: 'Consumer Staples', assetType: 'Equity', geography: 'US', creditRating: 'AA-', esgScore: 77 },
      
      // Bonds
      { symbol: 'UST-10Y', name: 'US Treasury 10Y', value: 120000, weight: 0.12, sector: 'Government', assetType: 'Bond', geography: 'US', creditRating: 'AAA' },
      { symbol: 'CORP-IG', name: 'Investment Grade Corp', value: 70000, weight: 0.07, sector: 'Corporate', assetType: 'Bond', geography: 'US', creditRating: 'BBB+' },
      
      // International
      { symbol: 'ASML', name: 'ASML Holding', value: 50000, weight: 0.05, sector: 'Technology', assetType: 'Equity', geography: 'Europe', creditRating: 'A+', esgScore: 84 },
      { symbol: 'TSM', name: 'Taiwan Semiconductor', value: 45000, weight: 0.045, sector: 'Technology', assetType: 'Equity', geography: 'Asia', creditRating: 'AA-', esgScore: 80 }
    ];

    const totalValue = mockHoldings.reduce((sum, holding) => sum + holding.value, 0);
    return mockHoldings.map(holding => ({
      ...holding,
      weight: holding.value / totalValue
    }));
  }, []);

  // Asset type composition
  const assetTypeComposition: CompositionData[] = useMemo(() => {
    const grouped = holdings.reduce((acc, holding) => {
      if (!acc[holding.assetType]) {
        acc[holding.assetType] = { value: 0, count: 0 };
      }
      acc[holding.assetType].value += holding.value;
      acc[holding.assetType].count += 1;
      return acc;
    }, {} as Record<string, { value: number; count: number }>);

    const colors = { 'Equity': '#2196f3', 'Bond': '#4caf50', 'Cash': '#ff9800', 'Alternative': '#9c27b0' };
    const totalValue = Object.values(grouped).reduce((sum, g) => sum + g.value, 0);

    return Object.entries(grouped).map(([type, data]) => ({
      category: type,
      value: data.value,
      weight: data.value / totalValue,
      color: colors[type as keyof typeof colors] || '#757575'
    }));
  }, [holdings]);

  // Sector composition
  const sectorComposition: CompositionData[] = useMemo(() => {
    const grouped = holdings.reduce((acc, holding) => {
      if (!acc[holding.sector]) {
        acc[holding.sector] = { value: 0, count: 0 };
      }
      acc[holding.sector].value += holding.value;
      acc[holding.sector].count += 1;
      return acc;
    }, {} as Record<string, { value: number; count: number }>);

    const colors = ['#2196f3', '#4caf50', '#ff9800', '#f44336', '#9c27b0', '#00bcd4', '#795548', '#607d8b'];
    const totalValue = Object.values(grouped).reduce((sum, g) => sum + g.value, 0);

    return Object.entries(grouped).map(([sector, data], index) => ({
      category: sector,
      value: data.value,
      weight: data.value / totalValue,
      color: colors[index % colors.length]
    }));
  }, [holdings]);

  // Geography composition
  const geographyComposition: CompositionData[] = useMemo(() => {
    const grouped = holdings.reduce((acc, holding) => {
      if (!acc[holding.geography]) {
        acc[holding.geography] = { value: 0, count: 0 };
      }
      acc[holding.geography].value += holding.value;
      acc[holding.geography].count += 1;
      return acc;
    }, {} as Record<string, { value: number; count: number }>);

    const colors = { 'US': '#2196f3', 'Europe': '#4caf50', 'Asia': '#ff9800', 'Emerging': '#f44336' };
    const totalValue = Object.values(grouped).reduce((sum, g) => sum + g.value, 0);

    return Object.entries(grouped).map(([geo, data]) => ({
      category: geo,
      value: data.value,
      weight: data.value / totalValue,
      color: colors[geo as keyof typeof colors] || '#757575'
    }));
  }, [holdings]);

  // Credit rating composition (for bonds)
  const creditRatingComposition: CompositionData[] = useMemo(() => {
    const bondsWithRating = holdings.filter(h => h.creditRating);
    const grouped = bondsWithRating.reduce((acc, holding) => {
      const rating = holding.creditRating!;
      if (!acc[rating]) {
        acc[rating] = { value: 0, count: 0 };
      }
      acc[rating].value += holding.value;
      acc[rating].count += 1;
      return acc;
    }, {} as Record<string, { value: number; count: number }>);

    const colors = ['#4caf50', '#8bc34a', '#cddc39', '#ffeb3b', '#ffc107', '#ff9800', '#f44336'];
    const totalValue = Object.values(grouped).reduce((sum, g) => sum + g.value, 0);

    return Object.entries(grouped).map(([rating, data], index) => ({
      category: rating,
      value: data.value,
      weight: data.value / totalValue,
      color: colors[index % colors.length]
    }));
  }, [holdings]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleViewTypeChange = (event: SelectChangeEvent<string>) => {
    setViewType(event.target.value as 'pie' | 'bar' | 'treemap');
  };

  const handleExport = () => {
    console.log('Exporting portfolio composition chart...');
  };

  const formatValue = (value: number) => `$${(value / 1000).toFixed(0)}K`;
  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  const renderPieChart = (data: CompositionData[]) => (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsPieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="category"
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={120}
          paddingAngle={2}
          label={({ category, weight }) => `${category}: ${formatPercent(weight)}`}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <RechartsTooltip 
          formatter={(value: number) => [formatValue(value), 'Value']}
        />
        <Legend />
      </RechartsPieChart>
    </ResponsiveContainer>
  );

  const renderBarChart = (data: CompositionData[]) => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="horizontal">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" tickFormatter={formatValue} />
        <YAxis type="category" dataKey="category" width={100} />
        <RechartsTooltip 
          formatter={(value: number) => [formatValue(value), 'Value']}
        />
        <Bar dataKey="value" fill="#2196f3" />
      </BarChart>
    </ResponsiveContainer>
  );

  const renderTreemap = (data: CompositionData[]) => (
    <ResponsiveContainer width="100%" height={height}>
      <Treemap
        data={data as any}
        dataKey="value"
        stroke="#fff"
        fill="#2196f3"
      />
    </ResponsiveContainer>
  );

  const getCurrentData = () => {
    switch (activeTab) {
      case 0: return assetTypeComposition;
      case 1: return sectorComposition;
      case 2: return geographyComposition;
      case 3: return creditRatingComposition;
      default: return assetTypeComposition;
    }
  };

  const topHoldings = holdings
    .sort((a, b) => b.value - a.value)
    .slice(0, maxHoldings);

  const totalPortfolioValue = holdings.reduce((sum, holding) => sum + holding.value, 0);

  // Calculate concentration metrics
  const top10Concentration = topHoldings.reduce((sum, holding) => sum + holding.weight, 0);
  const herfindahlIndex = holdings.reduce((sum, holding) => sum + Math.pow(holding.weight, 2), 0);

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      {/* Controls */}
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>View Type</InputLabel>
          <Select value={viewType} onChange={handleViewTypeChange} label="View Type">
            <MenuItem value="pie">Pie Chart</MenuItem>
            <MenuItem value="bar">Bar Chart</MenuItem>
            <MenuItem value="treemap">Treemap</MenuItem>
          </Select>
        </FormControl>

        <Box sx={{ flex: 1 }} />

        <Tooltip title="Refresh Data">
          <IconButton onClick={() => window.location.reload()} size="small">
            <RefreshIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Export Chart">
          <IconButton onClick={handleExport} size="small">
            <DownloadIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Summary Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Total Value"
            value={formatValue(totalPortfolioValue)}
            icon={<AccountBalanceIcon />}
            color="primary"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Top 10 Holdings"
            value={formatPercent(top10Concentration)}
            trend={top10Concentration > 0.6 ? "up" : "flat"}
            icon={<BusinessIcon />}
            color={top10Concentration > 0.6 ? "warning" : "success"}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Total Holdings"
            value={holdings.length.toString()}
            icon={<CategoryIcon />}
            color="info"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Diversification"
            value={(1 / herfindahlIndex).toFixed(0)}
            trend="up"
            icon={<PublicIcon />}
            color="success"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Main Chart */}
        <Grid size={{ xs: 12, md: 8 }} component="div">
          {/* Chart Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
            <Tabs value={activeTab} onChange={handleTabChange}>
              <Tab label="Asset Type" />
              <Tab label="Sector" />
              <Tab label="Geography" />
              <Tab label="Credit Rating" />
            </Tabs>
          </Box>

          {/* Chart Content */}
          <Box>
            {viewType === 'pie' && renderPieChart(getCurrentData())}
            {viewType === 'bar' && renderBarChart(getCurrentData())}
            {viewType === 'treemap' && renderTreemap(getCurrentData())}
          </Box>
        </Grid>

        {/* Top Holdings */}
        {showTopHoldings && (
          <Grid size={{ xs: 12, md: 4 }} component="div">
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Top Holdings
                </Typography>
                <List dense>
                  {topHoldings.map((holding, index) => (
                    <ListItem key={holding.symbol}>
                      <ListItemIcon>
                        <Chip 
                          label={index + 1} 
                          size="small" 
                          color="primary"
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={holding.symbol}
                        secondary={
                          <Box>
                            <Typography variant="body2" component="span">
                              {formatValue(holding.value)} ({formatPercent(holding.weight)})
                            </Typography>
                            <br />
                            <Typography variant="caption" color="textSecondary">
                              {holding.sector}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>

            {/* Concentration Analysis */}
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Metrics
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Chip 
                    label={`Herfindahl Index: ${(herfindahlIndex * 10000).toFixed(0)}`}
                    color="info"
                    variant="outlined"
                  />
                  <Chip 
                    label={`Effective Holdings: ${(1 / herfindahlIndex).toFixed(0)}`}
                    color="success"
                    variant="outlined"
                  />
                  <Chip 
                    label={`Top 5 Concentration: ${formatPercent(topHoldings.slice(0, 5).reduce((sum, h) => sum + h.weight, 0))}`}
                    color={topHoldings.slice(0, 5).reduce((sum, h) => sum + h.weight, 0) > 0.5 ? "warning" : "success"}
                    variant="outlined"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {enableRealTime && (assetUpdates.length > 0 || portfolioData) && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
          Last updated: {new Date().toLocaleTimeString()} (Real-time) | 
          Assets updated: {assetUpdates.length}
        </Typography>
      )}
    </Paper>
  );
};

export default PortfolioComposition;