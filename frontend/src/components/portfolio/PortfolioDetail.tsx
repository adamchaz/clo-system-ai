import React, { useState, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  Chip,
  Alert,
  LinearProgress,
  Breadcrumbs,
  Link,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TableSortLabel,
  TablePagination,
  Avatar,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Edit,
  Delete,
  GetApp,
  Refresh,
  Security,
  AccountBalance,
  Search,
  FilterList,
  Warning,
  CheckCircle,
  Timeline,
  PieChart,
  BarChart,
  Home,
  BusinessCenter,
} from '@mui/icons-material';
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
} from 'recharts';
import { format, parseISO, formatDistanceToNow } from 'date-fns';
import {
  useGetPortfolioQuery,
  useGetPortfolioSummaryQuery,
  useGetAssetsQuery,
  Portfolio,
  Asset,
} from '../../store/api/cloApi';
// Utility functions for formatting
const formatCurrency = (amount: number | string | null | undefined) => {
  // Convert string to number if needed
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (!numAmount || typeof numAmount !== 'number' || isNaN(numAmount)) return '$0';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numAmount);
};

const formatPercentage = (value: number) => {
  if (!value || typeof value !== 'number') return '0%';
  return `${value.toFixed(1)}%`;
};

// Color palettes for charts
const RATING_COLORS = {
  'AAA': '#4CAF50',
  'AA': '#66BB6A',
  'A': '#81C784',
  'BBB': '#FFC107',
  'BB': '#FF9800',
  'B': '#FF5722',
  'CCC': '#F44336',
  'CC': '#D32F2F',
  'C': '#B71C1C',
  'D': '#424242',
  'NR': '#9E9E9E',
  'Other': '#9E9E9E',
};

// Function to get rating color with fallback logic
const getRatingColor = (rating: string): string => {
  if (!rating) return RATING_COLORS['NR'];
  
  // Normalize rating by removing modifiers like +, -, 1, 2, 3
  const normalizedRating = rating.replace(/[+\-123]/g, '');
  
  // Direct match first
  if (RATING_COLORS[normalizedRating as keyof typeof RATING_COLORS]) {
    return RATING_COLORS[normalizedRating as keyof typeof RATING_COLORS];
  }
  
  // Fallback based on first letter/pattern
  if (normalizedRating.startsWith('AAA')) return RATING_COLORS.AAA;
  if (normalizedRating.startsWith('AA')) return RATING_COLORS.AA;
  if (normalizedRating.startsWith('A')) return RATING_COLORS.A;
  if (normalizedRating.startsWith('BBB')) return RATING_COLORS.BBB;
  if (normalizedRating.startsWith('BB')) return RATING_COLORS.BB;
  if (normalizedRating.startsWith('B')) return RATING_COLORS.B;
  if (normalizedRating.startsWith('CCC')) return RATING_COLORS.CCC;
  if (normalizedRating.startsWith('CC')) return RATING_COLORS.CC;
  if (normalizedRating.startsWith('C')) return RATING_COLORS.C;
  if (normalizedRating.startsWith('D')) return RATING_COLORS.D;
  
  // Default fallback
  return RATING_COLORS.NR;
};

const TYPE_COLORS = {
  'Bond': '#2196F3',
  'Loan': '#FF9800',
  'Term Loan': '#9C27B0',
  'Other': '#607D8B',
};

const SECTOR_COLORS = [
  '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
  '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
];

interface PortfolioDetailProps {
  portfolioId: string;
  onClose?: () => void;
  onEdit?: (portfolio: Portfolio) => void;
  onDelete?: (portfolio: Portfolio) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`portfolio-tabpanel-${index}`}
      aria-labelledby={`portfolio-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const PortfolioDetail: React.FC<PortfolioDetailProps> = ({
  portfolioId,
  onClose,
  onEdit,
  onDelete,
}) => {
  const [currentTab, setCurrentTab] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  
  // Asset list state
  const [assetSearch, setAssetSearch] = useState('');
  const [assetPage, setAssetPage] = useState(0);
  const [assetRowsPerPage, setAssetRowsPerPage] = useState(10);
  const [assetSortBy, setAssetSortBy] = useState<keyof Asset>('par_amount');
  const [assetSortOrder, setAssetSortOrder] = useState<'asc' | 'desc'>('desc');
  const [assetTypeFilter, setAssetTypeFilter] = useState('');
  const [ratingFilter, setRatingFilter] = useState('');

  // API queries
  const {
    data: portfolioData,
    isLoading: portfolioLoading,
    error: portfolioError,
    refetch: refetchPortfolio,
  } = useGetPortfolioQuery(portfolioId, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: portfolioSummary,
    isLoading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useGetPortfolioSummaryQuery(portfolioId, {
    refetchOnMountOrArgChange: true,
  });

  const {
    data: assetsData,
    isLoading: assetsLoading,
    error: assetsError,
    refetch: refetchAssets,
  } = useGetAssetsQuery({
    portfolio_id: portfolioId,
    skip: assetPage * assetRowsPerPage,
    limit: assetRowsPerPage,
    search: assetSearch || undefined,
    asset_type: assetTypeFilter || undefined,
    rating: ratingFilter || undefined,
  }, {
    skip: currentTab !== 1, // Only fetch when on assets tab
  });

  // Separate query for ALL assets (for composition analysis)
  const {
    data: allAssetsData,
    isLoading: allAssetsLoading,
    error: allAssetsError,
  } = useGetAssetsQuery({
    portfolio_id: portfolioId,
    skip: 0,
    limit: 1000, // Get all assets (max 1000)
  }, {
    skip: currentTab !== 1, // Only fetch when on assets tab
  });

  const portfolio = portfolioData;
  const summary = portfolioSummary;

  const handleTabChange = useCallback((event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  }, []);

  const handleRefresh = useCallback(() => {
    refetchPortfolio();
    refetchSummary();
    refetchAssets();
  }, [refetchPortfolio, refetchSummary, refetchAssets]);

  // Asset list handlers
  const handleAssetSort = useCallback((property: keyof Asset) => {
    const isAsc = assetSortBy === property && assetSortOrder === 'asc';
    setAssetSortOrder(isAsc ? 'desc' : 'asc');
    setAssetSortBy(property);
    setAssetPage(0);
  }, [assetSortBy, assetSortOrder]);

  const handleAssetSearchChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setAssetSearch(event.target.value);
    setAssetPage(0);
  }, []);

  const handleAssetPageChange = useCallback((event: unknown, newPage: number) => {
    setAssetPage(newPage);
  }, []);

  const handleAssetRowsPerPageChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setAssetRowsPerPage(parseInt(event.target.value, 10));
    setAssetPage(0);
  }, []);

  const handleAssetFilterChange = useCallback((filterType: 'type' | 'rating', value: string) => {
    if (filterType === 'type') {
      setAssetTypeFilter(value);
    } else {
      setRatingFilter(value);
    }
    setAssetPage(0);
  }, []);

  const clearAssetFilters = useCallback(() => {
    setAssetSearch('');
    setAssetTypeFilter('');
    setRatingFilter('');
    setAssetPage(0);
  }, []);

  // Asset composition calculation functions
  const getRatingDistribution = useCallback((assets: Asset[]) => {
    if (!assets || assets.length === 0) return [];
    
    const totalValue = assets.reduce((sum, asset) => {
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      return sum + amount;
    }, 0);
    const ratingMap = new Map<string, number>();
    
    assets.forEach(asset => {
      const rating = asset.mdy_rating || 'NR';
      const normalizedRating = rating.split(/[+-]/)[0]; // Remove + or - modifiers
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      ratingMap.set(normalizedRating, (ratingMap.get(normalizedRating) || 0) + amount);
    });
    
    return Array.from(ratingMap.entries())
      .map(([name, value]) => ({
        name,
        value: Number(value),
        percentage: totalValue > 0 ? (value / totalValue) * 100 : 0
      }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value);
  }, []);

  const getTypeDistribution = useCallback((assets: Asset[]) => {
    if (!assets || assets.length === 0) return [];
    
    const totalValue = assets.reduce((sum, asset) => {
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      return sum + amount;
    }, 0);
    const typeMap = new Map<string, number>();
    
    assets.forEach(asset => {
      const type = asset.bond_loan || 'Other';
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      typeMap.set(type, (typeMap.get(type) || 0) + amount);
    });
    
    return Array.from(typeMap.entries())
      .map(([name, value]) => ({
        name,
        value: Number(value),
        percentage: totalValue > 0 ? (value / totalValue) * 100 : 0
      }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value);
  }, []);

  const getTopHoldings = useCallback((assets: Asset[]) => {
    const totalValue = assets.reduce((sum, asset) => sum + (asset.par_amount || 0), 0);
    
    return [...assets]
      .sort((a, b) => (b.par_amount || 0) - (a.par_amount || 0))
      .slice(0, 10)
      .map(asset => ({
        name: asset.issue_name || asset.issuer_name || asset.blkrock_id,
        value: asset.par_amount || 0,
        percentage: totalValue > 0 ? ((asset.par_amount || 0) / totalValue) * 100 : 0
      }));
  }, []);

  const getPortfolioStats = useCallback((assets: Asset[]) => {
    const totalValue = assets.reduce((sum, asset) => sum + (asset.par_amount || 0), 0);
    const ratings = assets.map(a => a.mdy_rating).filter(Boolean);
    const types = assets.map(a => a.bond_loan).filter(Boolean);
    const coupons = assets.map(a => a.coupon).filter(c => c && c > 0);
    
    const avgCoupon = coupons.length > 0 ? 
      coupons.reduce((sum, c) => sum + c, 0) / coupons.length : 0;
      
    const ratingCounts = new Map<string, number>();
    ratings.forEach(r => {
      const normalized = r.split(/[+-]/)[0];
      ratingCounts.set(normalized, (ratingCounts.get(normalized) || 0) + 1);
    });
    
    const mostCommonRating = Array.from(ratingCounts.entries())
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A';
    
    const typeCounts = new Map<string, number>();
    types.forEach(t => typeCounts.set(t, (typeCounts.get(t) || 0) + 1));
    const mostCommonType = Array.from(typeCounts.entries())
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A';
    
    return [
      { label: 'Total Assets', value: assets.length.toString() },
      { label: 'Total Value', value: formatCurrency(totalValue) },
      { label: 'Avg Coupon', value: avgCoupon > 0 ? `${avgCoupon.toFixed(2)}%` : 'N/A' },
      { label: 'Top Rating', value: mostCommonRating },
      { label: 'Main Type', value: mostCommonType },
      { label: 'Rated Assets', value: `${ratings.length}/${assets.length}` },
    ];
  }, []);

  // Enhanced asset composition analysis functions
  const getSectorDistribution = useCallback((assets: Asset[]) => {
    console.log('getSectorDistribution called with:', assets.length, 'assets');
    
    if (!assets || assets.length === 0) {
      console.log('No assets provided to getSectorDistribution');
      return [];
    }
    
    const totalValue = assets.reduce((sum, asset) => {
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      return sum + amount;
    }, 0);
    const sectorMap = new Map<string, number>();
    
    console.log('Total value calculated:', totalValue);
    
    assets.forEach((asset, index) => {
      const sector = asset.mdy_industry || asset.sp_industry || 'Other';
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      
      if (index < 5) {
        console.log(`Asset ${index + 1}: sector="${sector}", amount=${amount} (type: ${typeof amount}), mdy_industry="${asset.mdy_industry}", sp_industry="${asset.sp_industry}"`);
      }
      sectorMap.set(sector, (sectorMap.get(sector) || 0) + amount);
    });
    
    const result = Array.from(sectorMap.entries())
      .map(([name, value]) => ({
        name: name.length > 25 ? name.substring(0, 25) + '...' : name,
        value: Number(value), // Ensure it's a number
        percentage: totalValue > 0 ? (value / totalValue) * 100 : 0
      }))
      .filter(item => item.value > 0) // Remove zero values
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);
    
    console.log('Sector distribution result:', result.length, 'sectors', result);
    return result;
  }, []);

  const getCountryDistribution = useCallback((assets: Asset[]) => {
    if (!assets || assets.length === 0) return [];
    
    const totalValue = assets.reduce((sum, asset) => {
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      return sum + amount;
    }, 0);
    const countryMap = new Map<string, number>();
    
    assets.forEach(asset => {
      const country = asset.country || 'Unknown';
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      countryMap.set(country, (countryMap.get(country) || 0) + amount);
    });
    
    return Array.from(countryMap.entries())
      .map(([name, value]) => ({
        name,
        value: Number(value),
        percentage: totalValue > 0 ? (value / totalValue) * 100 : 0
      }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value);
  }, []);

  const getMaturityProfile = useCallback((assets: Asset[]) => {
    const totalValue = assets.reduce((sum, asset) => sum + (asset.par_amount || 0), 0);
    const maturityBuckets = new Map<string, number>();
    
    const today = new Date();
    
    assets.forEach(asset => {
      if (asset.maturity) {
        const maturityDate = parseISO(asset.maturity);
        const yearsToMaturity = (maturityDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24 * 365);
        
        let bucket: string;
        if (yearsToMaturity < 1) bucket = '< 1 Year';
        else if (yearsToMaturity < 3) bucket = '1-3 Years';
        else if (yearsToMaturity < 5) bucket = '3-5 Years';
        else if (yearsToMaturity < 7) bucket = '5-7 Years';
        else bucket = '> 7 Years';
        
        const amount = asset.par_amount || 0;
        maturityBuckets.set(bucket, (maturityBuckets.get(bucket) || 0) + amount);
      }
    });
    
    return Array.from(maturityBuckets.entries())
      .map(([name, value]) => ({
        name,
        value,
        percentage: totalValue > 0 ? (value / totalValue) * 100 : 0
      }));
  }, []);

  const getCouponDistribution = useCallback((assets: Asset[]) => {
    if (!assets || assets.length === 0) return [];
    
    const assetsWithCoupons = assets.filter(a => a.coupon && a.coupon > 0);
    const totalValue = assetsWithCoupons.reduce((sum, asset) => {
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      return sum + amount;
    }, 0);
    const couponBuckets = new Map<string, number>();
    
    assetsWithCoupons.forEach(asset => {
      const coupon = asset.coupon || 0;
      let bucket: string;
      if (coupon < 5) bucket = '< 5%';
      else if (coupon < 7) bucket = '5-7%';
      else if (coupon < 9) bucket = '7-9%';
      else if (coupon < 12) bucket = '9-12%';
      else bucket = '> 12%';
      
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      couponBuckets.set(bucket, (couponBuckets.get(bucket) || 0) + amount);
    });
    
    return Array.from(couponBuckets.entries())
      .map(([name, value]) => ({
        name,
        value: Number(value),
        percentage: totalValue > 0 ? (value / totalValue) * 100 : 0
      }))
      .filter(item => item.value > 0);
  }, []);

  const getSeniorityDistribution = useCallback((assets: Asset[]) => {
    if (!assets || assets.length === 0) return [];
    
    const totalValue = assets.reduce((sum, asset) => {
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      return sum + amount;
    }, 0);
    const seniorityMap = new Map<string, number>();
    
    assets.forEach(asset => {
      const seniority = asset.seniority || 'Unknown';
      const amount = typeof asset.par_amount === 'string' ? parseFloat(asset.par_amount) : (asset.par_amount || 0);
      seniorityMap.set(seniority, (seniorityMap.get(seniority) || 0) + amount);
    });
    
    return Array.from(seniorityMap.entries())
      .map(([name, value]) => ({
        name,
        value: Number(value),
        percentage: totalValue > 0 ? (value / totalValue) * 100 : 0
      }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value);
  }, []);

  const getEnhancedPortfolioStats = useCallback((assets: Asset[]) => {
    const totalValue = assets.reduce((sum, asset) => sum + (asset.par_amount || 0), 0);
    const ratings = assets.map(a => a.mdy_rating).filter(Boolean);
    const types = assets.map(a => a.bond_loan).filter(Boolean);
    const coupons = assets.map(a => a.coupon).filter(c => c && c > 0);
    const countries = assets.map(a => a.country).filter(Boolean);
    const facilitySizes = assets.map(a => a.facility_size).filter(f => f && f > 0);
    
    const avgCoupon = coupons.length > 0 ? 
      coupons.reduce((sum, c) => sum + c, 0) / coupons.length : 0;
    
    const avgFacilitySize = facilitySizes.length > 0 ?
      facilitySizes.reduce((sum, f) => sum + f, 0) / facilitySizes.length : 0;
      
    const ratingCounts = new Map<string, number>();
    ratings.forEach(r => {
      const normalized = r.split(/[+-]/)[0];
      ratingCounts.set(normalized, (ratingCounts.get(normalized) || 0) + 1);
    });
    
    const mostCommonRating = Array.from(ratingCounts.entries())
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A';
    
    const typeCounts = new Map<string, number>();
    types.forEach(t => typeCounts.set(t, (typeCounts.get(t) || 0) + 1));
    const mostCommonType = Array.from(typeCounts.entries())
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A';
    
    const uniqueCountries = new Set(countries).size;
    
    return [
      { label: 'Total Assets', value: assets.length.toString() },
      { label: 'Total Value', value: formatCurrency(totalValue) },
      { label: 'Avg Coupon', value: avgCoupon > 0 ? `${avgCoupon.toFixed(2)}%` : 'N/A' },
      { label: 'Top Rating', value: mostCommonRating },
      { label: 'Main Type', value: mostCommonType },
      { label: 'Rated Assets', value: `${ratings.length}/${assets.length}` },
      { label: 'Countries', value: uniqueCountries.toString() },
      { label: 'Avg Facility Size', value: avgFacilitySize > 0 ? formatCurrency(avgFacilitySize) : 'N/A' },
    ];
  }, []);

  const handleEdit = useCallback(() => {
    if (portfolio) {
      onEdit?.(portfolio);
    }
  }, [portfolio, onEdit]);

  const handleDeleteConfirm = useCallback(() => {
    if (portfolio) {
      onDelete?.(portfolio);
      setDeleteDialogOpen(false);
    }
  }, [portfolio, onDelete]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'effective':
        return 'success';
      case 'pending':
        return 'warning';
      case 'inactive':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'effective':
        return 'Active';
      case 'pending':
        return 'Pending';
      case 'inactive':
        return 'Inactive';
      default:
        return status;
    }
  };

  const calculatePerformance = () => {
    if (!portfolio || !portfolio.current_portfolio_balance || !portfolio.deal_size) return 0;
    const result = ((portfolio.current_portfolio_balance / portfolio.deal_size) - 1) * 100;
    return isNaN(result) ? 0 : result;
  };

  if (portfolioError || summaryError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load portfolio data. Please check your connection and try again.
        </Alert>
      </Box>
    );
  }

  if (portfolioLoading && !portfolio) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography variant="body1" sx={{ mt: 2, textAlign: 'center' }}>
          Loading portfolio details...
        </Typography>
      </Box>
    );
  }

  if (!portfolio) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Alert severity="warning">
          Portfolio not found or you don't have access to view it.
        </Alert>
      </Box>
    );
  }

  const performance = calculatePerformance();
  const isPositivePerformance = performance >= 0;

  return (
    <Box>
      {/* Breadcrumbs */}
      <Box sx={{ mb: 3 }}>
        <Breadcrumbs aria-label="breadcrumb">
          <Link
            underline="hover"
            color="inherit"
            onClick={onClose}
            sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
          >
            <Home sx={{ mr: 0.5 }} fontSize="inherit" />
            Dashboard
          </Link>
          <Link
            underline="hover"
            color="inherit"
            onClick={onClose}
            sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
          >
            <BusinessCenter sx={{ mr: 0.5 }} fontSize="inherit" />
            Portfolios
          </Link>
          <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
            <AccountBalance sx={{ mr: 0.5 }} fontSize="inherit" />
            {portfolio.deal_name}
          </Typography>
        </Breadcrumbs>
      </Box>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
          <Avatar sx={{ bgcolor: 'primary.main', mr: 3, width: 64, height: 64 }}>
            <AccountBalance fontSize="large" />
          </Avatar>
          <Box>
            <Typography
              variant="h4"
              component="h1"
              sx={{ fontWeight: 700, color: 'text.primary', mb: 1 }}
            >
              {portfolio.deal_name}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Chip
                label={getStatusLabel(portfolio.status)}
                color={getStatusColor(portfolio.status)}
                variant="outlined"
              />
              <Typography variant="body2" color="text.secondary">
                Managed by {portfolio.manager}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Trustee: {portfolio.trustee}
              </Typography>
            </Box>
            <Typography variant="body1" color="text.secondary">
              Effective: {format(parseISO(portfolio.effective_date), 'PPP')} •
              Maturity: {format(parseISO(portfolio.stated_maturity), 'PPP')}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} disabled={portfolioLoading || summaryLoading}>
              <Refresh />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<GetApp />}
            size="small"
          >
            Export
          </Button>
          <Button
            variant="outlined"
            startIcon={<Edit />}
            onClick={handleEdit}
            size="small"
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={() => setDeleteDialogOpen(true)}
            size="small"
          >
            Delete
          </Button>
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalance color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Deal Size
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight={700}>
                ${typeof portfolio.deal_size === 'number' ? (portfolio.deal_size / 1000000).toFixed(1) : '0.0'}M
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {portfolio.currency}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PieChart color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Current NAV
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight={700}>
                ${typeof portfolio.current_portfolio_balance === 'number' ? (portfolio.current_portfolio_balance / 1000000).toFixed(1) : '0.0'}M
              </Typography>
              <Typography variant="caption" color={isPositivePerformance ? 'success.main' : 'error.main'}>
                {isPositivePerformance ? '+' : ''}{performance.toFixed(2)}% vs deal size
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <BarChart color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Assets
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight={700}>
                {portfolio.current_asset_count}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Securities
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Timeline color="warning" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Days to Maturity
                </Typography>
              </Box>
              <Typography variant="h5" fontWeight={700}>
                {portfolio.days_to_maturity}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatDistanceToNow(parseISO(portfolio.stated_maturity))}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="portfolio detail tabs">
          <Tab label="Overview" />
          <Tab label="Assets" />
          <Tab label="Tranches" />
          <Tab label="Risk Analysis" />
          <Tab label="Performance" />
          <Tab label="Compliance" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <TabPanel value={currentTab} index={0}>
        {/* Overview Tab */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Portfolio Information
                </Typography>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Deal Name</TableCell>
                      <TableCell sx={{ border: 0 }}>{portfolio.deal_name}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Manager</TableCell>
                      <TableCell sx={{ border: 0 }}>{portfolio.manager}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Trustee</TableCell>
                      <TableCell sx={{ border: 0 }}>{portfolio.trustee}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Currency</TableCell>
                      <TableCell sx={{ border: 0 }}>{portfolio.currency}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Effective Date</TableCell>
                      <TableCell sx={{ border: 0 }}>
                        {format(parseISO(portfolio.effective_date), 'PPP')}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600, border: 0 }}>Stated Maturity</TableCell>
                      <TableCell sx={{ border: 0 }}>
                        {format(parseISO(portfolio.stated_maturity), 'PPP')}
                      </TableCell>
                    </TableRow>
                    {portfolio.revolving_period_end && (
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600, border: 0 }}>Revolving Period End</TableCell>
                        <TableCell sx={{ border: 0 }}>
                          {format(parseISO(portfolio.revolving_period_end), 'PPP')}
                        </TableCell>
                      </TableRow>
                    )}
                    {portfolio.reinvestment_period_end && (
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600, border: 0 }}>Reinvestment Period End</TableCell>
                        <TableCell sx={{ border: 0 }}>
                          {format(parseISO(portfolio.reinvestment_period_end), 'PPP')}
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent Activity
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Portfolio created"
                      secondary={`${formatDistanceToNow(parseISO(portfolio.created_at))} ago`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Last updated"
                      secondary={`${formatDistanceToNow(parseISO(portfolio.updated_at))} ago`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Current asset count"
                      secondary={`${portfolio.current_asset_count} securities`}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {/* Assets Tab */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Portfolio Assets
                {assetsData && (
                  <Chip 
                    label={`${assetsData.total} total`} 
                    size="small" 
                    sx={{ ml: 2 }} 
                  />
                )}
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<FilterList />}
                  onClick={clearAssetFilters}
                  disabled={!assetSearch && !assetTypeFilter && !ratingFilter}
                >
                  Clear Filters
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<GetApp />}
                >
                  Export
                </Button>
              </Box>
            </Box>

            {/* Filters and Search */}
            <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
              <TextField
                size="small"
                placeholder="Search assets..."
                value={assetSearch}
                onChange={handleAssetSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
                sx={{ minWidth: 250 }}
              />
              
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Type</InputLabel>
                <Select
                  value={assetTypeFilter}
                  onChange={(e) => handleAssetFilterChange('type', e.target.value)}
                  label="Type"
                >
                  <MenuItem value="">All Types</MenuItem>
                  <MenuItem value="Bond">Bond</MenuItem>
                  <MenuItem value="Loan">Loan</MenuItem>
                  <MenuItem value="Term Loan">Term Loan</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Rating</InputLabel>
                <Select
                  value={ratingFilter}
                  onChange={(e) => handleAssetFilterChange('rating', e.target.value)}
                  label="Rating"
                >
                  <MenuItem value="">All Ratings</MenuItem>
                  <MenuItem value="AAA">AAA</MenuItem>
                  <MenuItem value="AA">AA</MenuItem>
                  <MenuItem value="A">A</MenuItem>
                  <MenuItem value="BBB">BBB</MenuItem>
                  <MenuItem value="BB">BB</MenuItem>
                  <MenuItem value="B">B</MenuItem>
                  <MenuItem value="CCC">CCC</MenuItem>
                </Select>
              </FormControl>
            </Box>

            {/* Asset Composition Charts */}
            {allAssetsData?.data && allAssetsData.data.length > 0 ? (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Asset Composition Breakdown ({allAssetsData.data.length} assets)
                </Typography>

                
                <Grid container spacing={3}>
                  {/* Rating Distribution */}
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          By Credit Rating
                        </Typography>
                        <Box sx={{ height: 250 }}>
                          <ResponsiveContainer>
                            <RechartsPieChart>
                              <Pie
                                data={getRatingDistribution(allAssetsData.data)}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                innerRadius={40}
                              >
                                {getRatingDistribution(allAssetsData.data).map((entry, index) => (
                                  <Cell key={`rating-${index}`} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
                                ))}
                              </Pie>
                              <RechartsTooltip 
                                formatter={(value: number) => [formatCurrency(value), 'Amount']}
                              />
                              <Legend 
                                formatter={(value) => {
                                  const item = getRatingDistribution(allAssetsData.data).find(d => d.name === value);
                                  return `${value} (${formatPercentage(item?.percentage || 0)})`;
                                }}
                              />
                            </RechartsPieChart>
                          </ResponsiveContainer>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Asset Type Distribution */}
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          By Asset Type
                        </Typography>
                        <Box sx={{ height: 250 }}>
                          <ResponsiveContainer>
                            <RechartsPieChart>
                              <Pie
                                data={getTypeDistribution(allAssetsData.data)}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                innerRadius={40}
                              >
                                {getTypeDistribution(allAssetsData.data).map((entry, index) => (
                                  <Cell key={`type-${index}`} fill={TYPE_COLORS[entry.name as keyof typeof TYPE_COLORS] || '#607D8B'} />
                                ))}
                              </Pie>
                              <RechartsTooltip 
                                formatter={(value: number) => [formatCurrency(value), 'Amount']}
                              />
                              <Legend 
                                formatter={(value) => {
                                  const item = getTypeDistribution(allAssetsData.data).find(d => d.name === value);
                                  return `${value} (${formatPercentage(item?.percentage || 0)})`;
                                }}
                              />
                            </RechartsPieChart>
                          </ResponsiveContainer>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Top Holdings */}
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          Top Holdings
                        </Typography>
                        <Box sx={{ height: 250, overflow: 'auto' }}>
                          {getTopHoldings(allAssetsData.data).map((holding, index) => (
                            <Box key={holding.name} sx={{ mb: 1 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                <Typography variant="body2" noWrap sx={{ fontSize: '0.75rem' }}>
                                  {index + 1}. {holding.name}
                                </Typography>
                                <Typography variant="body2" fontWeight={600} sx={{ fontSize: '0.75rem' }}>
                                  {formatPercentage(holding.percentage)}
                                </Typography>
                              </Box>
                              <LinearProgress 
                                variant="determinate" 
                                value={holding.percentage} 
                                sx={{ height: 4, borderRadius: 2 }}
                              />
                            </Box>
                          ))}
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Enhanced Composition Analysis */}
                <Grid container spacing={3} sx={{ mt: 2 }}>
                  {/* Sector/Industry Distribution */}
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          By Sector/Industry
                        </Typography>
                        <Box sx={{ height: 250 }}>
                          <ResponsiveContainer>
                            <RechartsPieChart>
                              <Pie
                                data={getSectorDistribution(allAssetsData.data)}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                innerRadius={40}
                              >
                                {getSectorDistribution(allAssetsData.data).map((entry, index) => (
                                  <Cell key={`sector-${index}`} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
                                ))}
                              </Pie>
                              <RechartsTooltip 
                                formatter={(value: number) => [formatCurrency(value), 'Amount']}
                              />
                              <Legend 
                                formatter={(value) => {
                                  const item = getSectorDistribution(allAssetsData.data).find(d => d.name === value);
                                  return `${value} (${formatPercentage(item?.percentage || 0)})`;
                                }}
                              />
                            </RechartsPieChart>
                          </ResponsiveContainer>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Country Distribution */}
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          By Geography
                        </Typography>
                        <Box sx={{ height: 250 }}>
                          <ResponsiveContainer>
                            <RechartsPieChart>
                              <Pie
                                data={getCountryDistribution(allAssetsData.data)}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                innerRadius={40}
                              >
                                {getCountryDistribution(allAssetsData.data).map((entry, index) => (
                                  <Cell key={`country-${index}`} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
                                ))}
                              </Pie>
                              <RechartsTooltip 
                                formatter={(value: number) => [formatCurrency(value), 'Amount']}
                              />
                              <Legend 
                                formatter={(value) => {
                                  const item = getCountryDistribution(allAssetsData.data).find(d => d.name === value);
                                  return `${value} (${formatPercentage(item?.percentage || 0)})`;
                                }}
                              />
                            </RechartsPieChart>
                          </ResponsiveContainer>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Maturity Profile */}
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          By Maturity Profile
                        </Typography>
                        <Box sx={{ height: 250 }}>
                          <ResponsiveContainer>
                            <RechartsPieChart>
                              <Pie
                                data={getMaturityProfile(allAssetsData.data)}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                innerRadius={40}
                              >
                                {getMaturityProfile(allAssetsData.data).map((entry, index) => (
                                  <Cell key={`maturity-${index}`} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
                                ))}
                              </Pie>
                              <RechartsTooltip 
                                formatter={(value: number) => [formatCurrency(value), 'Amount']}
                              />
                              <Legend 
                                formatter={(value) => {
                                  const item = getMaturityProfile(allAssetsData.data).find(d => d.name === value);
                                  return `${value} (${formatPercentage(item?.percentage || 0)})`;
                                }}
                              />
                            </RechartsPieChart>
                          </ResponsiveContainer>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Coupon Distribution */}
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          By Coupon Range
                        </Typography>
                        <Box sx={{ height: 250 }}>
                          <ResponsiveContainer>
                            <RechartsPieChart>
                              <Pie
                                data={getCouponDistribution(allAssetsData.data)}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                innerRadius={40}
                              >
                                {getCouponDistribution(allAssetsData.data).map((entry, index) => (
                                  <Cell key={`coupon-${index}`} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
                                ))}
                              </Pie>
                              <RechartsTooltip 
                                formatter={(value: number) => [formatCurrency(value), 'Amount']}
                              />
                              <Legend 
                                formatter={(value) => {
                                  const item = getCouponDistribution(allAssetsData.data).find(d => d.name === value);
                                  return `${value} (${formatPercentage(item?.percentage || 0)})`;
                                }}
                              />
                            </RechartsPieChart>
                          </ResponsiveContainer>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Seniority Distribution */}
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          By Seniority
                        </Typography>
                        <Box sx={{ height: 250 }}>
                          <ResponsiveContainer>
                            <RechartsPieChart>
                              <Pie
                                data={getSeniorityDistribution(allAssetsData.data)}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={80}
                                innerRadius={40}
                              >
                                {getSeniorityDistribution(allAssetsData.data).map((entry, index) => (
                                  <Cell key={`seniority-${index}`} fill={SECTOR_COLORS[index % SECTOR_COLORS.length]} />
                                ))}
                              </Pie>
                              <RechartsTooltip 
                                formatter={(value: number) => [formatCurrency(value), 'Amount']}
                              />
                              <Legend 
                                formatter={(value) => {
                                  const item = getSeniorityDistribution(allAssetsData.data).find(d => d.name === value);
                                  return `${value} (${formatPercentage(item?.percentage || 0)})`;
                                }}
                              />
                            </RechartsPieChart>
                          </ResponsiveContainer>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Enhanced Portfolio Statistics */}
                <Grid container spacing={3} sx={{ mt: 2 }}>
                  <Grid size={{ xs: 12 }}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          Enhanced Portfolio Statistics
                        </Typography>
                        <Grid container spacing={2}>
                          {getEnhancedPortfolioStats(allAssetsData.data).map((stat, index) => (
                            <Grid key={index} size={{ xs: 6, sm: 4, md: 3 }}>
                              <Box sx={{ textAlign: 'center', p: 1 }}>
                                <Typography variant="h6" fontWeight={600}>
                                  {stat.value}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {stat.label}
                                </Typography>
                              </Box>
                            </Grid>
                          ))}
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Box>
            ) : (
              <Box sx={{ mb: 4 }}>
                <Alert severity="info">
                  Asset Composition Debug: {
                    allAssetsLoading ? " Loading..." : 
                    allAssetsError ? " Error loading assets" :
                    !allAssetsData ? " No data available" :
                    !allAssetsData.data ? " Data structure missing" :
                    allAssetsData.data.length === 0 ? " No assets found" : " Unknown issue"
                  }
                  {allAssetsData?.data && ` (${allAssetsData.data.length} assets loaded)`}
                </Alert>
              </Box>
            )}

            {/* Asset Table */}
            {assetsError ? (
              <Alert severity="error" sx={{ mb: 3 }}>
                Failed to load portfolio assets. Please try again.
              </Alert>
            ) : assetsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <LinearProgress sx={{ width: '50%' }} />
              </Box>
            ) : assetsData?.data && assetsData.data.length > 0 ? (
              <>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>
                          <TableSortLabel
                            active={assetSortBy === 'issue_name'}
                            direction={assetSortBy === 'issue_name' ? assetSortOrder : 'asc'}
                            onClick={() => handleAssetSort('issue_name')}
                          >
                            Asset Name
                          </TableSortLabel>
                        </TableCell>
                        <TableCell>
                          <TableSortLabel
                            active={assetSortBy === 'issuer_name'}
                            direction={assetSortBy === 'issuer_name' ? assetSortOrder : 'asc'}
                            onClick={() => handleAssetSort('issuer_name')}
                          >
                            Issuer
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="right">
                          <TableSortLabel
                            active={assetSortBy === 'par_amount'}
                            direction={assetSortBy === 'par_amount' ? assetSortOrder : 'asc'}
                            onClick={() => handleAssetSort('par_amount')}
                          >
                            Par Amount
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="center">
                          <TableSortLabel
                            active={assetSortBy === 'mdy_rating'}
                            direction={assetSortBy === 'mdy_rating' ? assetSortOrder : 'asc'}
                            onClick={() => handleAssetSort('mdy_rating')}
                          >
                            Rating
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="center">Type</TableCell>
                        <TableCell align="right">
                          <TableSortLabel
                            active={assetSortBy === 'coupon'}
                            direction={assetSortBy === 'coupon' ? assetSortOrder : 'asc'}
                            onClick={() => handleAssetSort('coupon')}
                          >
                            Coupon
                          </TableSortLabel>
                        </TableCell>
                        <TableCell align="center">
                          <TableSortLabel
                            active={assetSortBy === 'maturity'}
                            direction={assetSortBy === 'maturity' ? assetSortOrder : 'asc'}
                            onClick={() => handleAssetSort('maturity')}
                          >
                            Maturity
                          </TableSortLabel>
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {assetsData.data.map((asset) => (
                        <TableRow 
                          key={asset.blkrock_id}
                          hover
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight={600}>
                                {asset.issue_name || asset.blkrock_id}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {asset.blkrock_id}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {asset.issuer_name || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" fontWeight={600}>
                              {formatCurrency(asset.par_amount)}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={asset.mdy_rating || 'NR'}
                              size="small"
                              variant="outlined"
                              color={
                                asset.mdy_rating?.startsWith('A') ? 'success' :
                                asset.mdy_rating?.startsWith('B') ? 'warning' :
                                'default'
                              }
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Typography variant="body2">
                              {asset.bond_loan || 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {asset.coupon ? `${asset.coupon}%` : 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Typography variant="body2">
                              {asset.maturity ? format(parseISO(asset.maturity), 'MMM yyyy') : 'N/A'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <TablePagination
                  component="div"
                  count={assetsData.total}
                  page={assetPage}
                  onPageChange={handleAssetPageChange}
                  rowsPerPage={assetRowsPerPage}
                  onRowsPerPageChange={handleAssetRowsPerPageChange}
                  rowsPerPageOptions={[5, 10, 25, 50]}
                />
              </>
            ) : (
              <Paper
                sx={{
                  p: 4,
                  textAlign: 'center',
                  backgroundColor: 'background.paper',
                  border: 1,
                  borderColor: 'divider',
                  borderStyle: 'dashed',
                }}
              >
                <BarChart sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                <Typography variant="body1" color="text.secondary">
                  {assetSearch || assetTypeFilter || ratingFilter
                    ? 'No assets match the current filters'
                    : 'No assets found in this portfolio'
                  }
                </Typography>
                {(assetSearch || assetTypeFilter || ratingFilter) && (
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={clearAssetFilters}
                    sx={{ mt: 2 }}
                  >
                    Clear Filters
                  </Button>
                )}
              </Paper>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        {/* Tranches Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              MAG17 Tranches Structure
            </Typography>
            
            {/* Tranches Overview */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      Senior Tranches (AAA)
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="h4" fontWeight={700}>
                        85.5%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        of total deal size
                      </Typography>
                    </Box>
                    <List dense>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemText 
                          primary="Class A-1" 
                          secondary="$342M • L+115 bps • AAA/Aaa"
                        />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemText 
                          primary="Class A-2" 
                          secondary="$171M • L+135 bps • AAA/Aaa"
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle2" color="warning.main" gutterBottom>
                      Mezzanine Tranches
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="h4" fontWeight={700}>
                        10.5%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        of total deal size
                      </Typography>
                    </Box>
                    <List dense>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemText 
                          primary="Class B" 
                          secondary="$42M • L+250 bps • AA/Aa2"
                        />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemText 
                          primary="Class C" 
                          secondary="$21M • L+400 bps • A/A2"
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle2" color="error.main" gutterBottom>
                      Subordinate Tranches
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="h4" fontWeight={700}>
                        4.0%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        of total deal size
                      </Typography>
                    </Box>
                    <List dense>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemText 
                          primary="Class D" 
                          secondary="$16M • L+650 bps • BBB/Baa2"
                        />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemText 
                          primary="Class E" 
                          secondary="$8M • L+900 bps • BB/Ba2"
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle2" color="success.main" gutterBottom>
                      Equity Tranche
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="h4" fontWeight={700}>
                        Equity
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Residual cash flows
                      </Typography>
                    </Box>
                    <List dense>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemText 
                          primary="Income Notes" 
                          secondary="$25M • Residual • Unrated"
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Detailed Tranches Table */}
            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
              Detailed Tranche Information
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Tranche</TableCell>
                    <TableCell align="right">Principal Amount</TableCell>
                    <TableCell align="center">Coupon</TableCell>
                    <TableCell align="center">Moody's Rating</TableCell>
                    <TableCell align="center">S&P Rating</TableCell>
                    <TableCell align="right">% of Deal</TableCell>
                    <TableCell align="center">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>Class A-1 Notes</Typography>
                        <Typography variant="caption" color="text.secondary">Senior Secured</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={600}>$342,000,000</Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="L+115 bps" size="small" color="primary" variant="outlined" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Aaa" size="small" color="success" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="AAA" size="small" color="success" />
                    </TableCell>
                    <TableCell align="right">57.0%</TableCell>
                    <TableCell align="center">
                      <Chip label="Outstanding" size="small" color="success" variant="outlined" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>Class A-2 Notes</Typography>
                        <Typography variant="caption" color="text.secondary">Senior Secured</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={600}>$171,000,000</Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="L+135 bps" size="small" color="primary" variant="outlined" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Aaa" size="small" color="success" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="AAA" size="small" color="success" />
                    </TableCell>
                    <TableCell align="right">28.5%</TableCell>
                    <TableCell align="center">
                      <Chip label="Outstanding" size="small" color="success" variant="outlined" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>Class B Notes</Typography>
                        <Typography variant="caption" color="text.secondary">Mezzanine</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={600}>$42,000,000</Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="L+250 bps" size="small" color="warning" variant="outlined" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Aa2" size="small" color="success" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="AA" size="small" color="success" />
                    </TableCell>
                    <TableCell align="right">7.0%</TableCell>
                    <TableCell align="center">
                      <Chip label="Outstanding" size="small" color="success" variant="outlined" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>Class C Notes</Typography>
                        <Typography variant="caption" color="text.secondary">Mezzanine</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={600}>$21,000,000</Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="L+400 bps" size="small" color="warning" variant="outlined" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="A2" size="small" color="info" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="A" size="small" color="info" />
                    </TableCell>
                    <TableCell align="right">3.5%</TableCell>
                    <TableCell align="center">
                      <Chip label="Outstanding" size="small" color="success" variant="outlined" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>Class D Notes</Typography>
                        <Typography variant="caption" color="text.secondary">Subordinate</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={600}>$16,000,000</Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="L+650 bps" size="small" color="warning" variant="outlined" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Baa2" size="small" color="warning" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="BBB" size="small" color="warning" />
                    </TableCell>
                    <TableCell align="right">2.7%</TableCell>
                    <TableCell align="center">
                      <Chip label="Outstanding" size="small" color="success" variant="outlined" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>Class E Notes</Typography>
                        <Typography variant="caption" color="text.secondary">Subordinate</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={600}>$8,000,000</Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="L+900 bps" size="small" color="error" variant="outlined" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Ba2" size="small" color="error" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="BB" size="small" color="error" />
                    </TableCell>
                    <TableCell align="right">1.3%</TableCell>
                    <TableCell align="center">
                      <Chip label="Outstanding" size="small" color="success" variant="outlined" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight={600}>Income Notes</Typography>
                        <Typography variant="caption" color="text.secondary">Equity</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight={600}>$25,000,000</Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="Residual" size="small" color="default" variant="outlined" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="NR" size="small" color="default" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip label="NR" size="small" color="default" />
                    </TableCell>
                    <TableCell align="right">-</TableCell>
                    <TableCell align="center">
                      <Chip label="Outstanding" size="small" color="success" variant="outlined" />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            {/* Payment Waterfall Summary */}
            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
              Payment Waterfall Priority
            </Typography>
            <Card variant="outlined">
              <CardContent>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Interest Payment Priority
                    </Typography>
                    <List dense>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>1</Avatar>
                        <ListItemText primary="Senior Management Fees" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>2</Avatar>
                        <ListItemText primary="Class A-1 & A-2 Interest" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>3</Avatar>
                        <ListItemText primary="Class B Interest" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>4</Avatar>
                        <ListItemText primary="Class C Interest" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>5</Avatar>
                        <ListItemText primary="Class D Interest" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>6</Avatar>
                        <ListItemText primary="Class E Interest" />
                      </ListItem>
                    </List>
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Principal Payment Priority
                    </Typography>
                    <List dense>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>1</Avatar>
                        <ListItemText primary="Class A-1 Principal" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>2</Avatar>
                        <ListItemText primary="Class A-2 Principal" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>3</Avatar>
                        <ListItemText primary="Class B Principal" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>4</Avatar>
                        <ListItemText primary="Class C Principal" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>5</Avatar>
                        <ListItemText primary="Class D Principal" />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <Avatar sx={{ width: 24, height: 24, mr: 1, fontSize: 12 }}>6</Avatar>
                        <ListItemText primary="Class E Principal" />
                      </ListItem>
                    </List>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        {/* Risk Analysis Tab */}
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Metrics
                </Typography>
                {summary?.risk_metrics ? (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Metric</TableCell>
                          <TableCell align="right">Value</TableCell>
                          <TableCell align="right">Status</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        <TableRow>
                          <TableCell>Weighted Average Life</TableCell>
                          <TableCell align="right">
                            {typeof summary.risk_metrics.weighted_average_life === 'number' 
                              ? `${summary.risk_metrics.weighted_average_life.toFixed(2)} years`
                              : summary.risk_metrics.weighted_average_life || 'N/A'}
                          </TableCell>
                          <TableCell align="right">
                            <CheckCircle color="success" fontSize="small" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Average Rating</TableCell>
                          <TableCell align="right">
                            {summary.risk_metrics.average_rating}
                          </TableCell>
                          <TableCell align="right">
                            <CheckCircle color="success" fontSize="small" />
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Portfolio Value</TableCell>
                          <TableCell align="right">
                            {typeof summary.risk_metrics.portfolio_value === 'number' 
                              ? `$${(summary.risk_metrics.portfolio_value / 1000000).toFixed(1)}M`
                              : summary.risk_metrics.portfolio_value || 'N/A'}
                          </TableCell>
                          <TableCell align="right">
                            <CheckCircle color="success" fontSize="small" />
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Paper
                    sx={{
                      p: 4,
                      textAlign: 'center',
                      backgroundColor: 'background.paper',
                      border: 1,
                      borderColor: 'divider',
                      borderStyle: 'dashed',
                    }}
                  >
                    <Security sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary">
                      Risk analysis data loading...
                    </Typography>
                  </Paper>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Compliance Status
                </Typography>
                {summary?.compliance_status ? (
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="OC Tests"
                        secondary={summary.compliance_status.oc_tests_passing ? 'Passing' : 'Failed'}
                      />
                      {summary.compliance_status.oc_tests_passing ? (
                        <CheckCircle color="success" />
                      ) : (
                        <Warning color="error" />
                      )}
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="IC Tests"
                        secondary={summary.compliance_status.ic_tests_passing ? 'Passing' : 'Failed'}
                      />
                      {summary.compliance_status.ic_tests_passing ? (
                        <CheckCircle color="success" />
                      ) : (
                        <Warning color="error" />
                      )}
                    </ListItem>
                    <ListItem>
                      <ListItemText
                        primary="Concentration Tests"
                        secondary={summary.compliance_status.concentration_tests_passing ? 'Passing' : 'Failed'}
                      />
                      {summary.compliance_status.concentration_tests_passing ? (
                        <CheckCircle color="success" />
                      ) : (
                        <Warning color="error" />
                      )}
                    </ListItem>
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Loading compliance data...
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={currentTab} index={4}>
        {/* Performance Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance Analysis
            </Typography>
            <Paper
              sx={{
                p: 4,
                textAlign: 'center',
                backgroundColor: 'background.paper',
                border: 1,
                borderColor: 'divider',
                borderStyle: 'dashed',
              }}
            >
              <Timeline sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
              <Typography variant="body1" color="text.secondary">
                Performance charts and analysis coming soon
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Historical performance, benchmarks, and risk-adjusted returns
              </Typography>
            </Paper>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={currentTab} index={5}>
        {/* Compliance Tab */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Compliance Details
            </Typography>
            {summary?.compliance_status ? (
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Failed Tests
                  </Typography>
                  {summary.compliance_status.failed_tests.length > 0 ? (
                    <List>
                      {summary.compliance_status.failed_tests.map((test, index) => (
                        <ListItem key={index}>
                          <Warning color="error" sx={{ mr: 1 }} />
                          <ListItemText primary={test} />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="success.main">
                      All compliance tests are passing
                    </Typography>
                  )}
                </Grid>

                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Warnings
                  </Typography>
                  {summary.compliance_status.warnings.length > 0 ? (
                    <List>
                      {summary.compliance_status.warnings.map((warning, index) => (
                        <ListItem key={index}>
                          <Warning color="warning" sx={{ mr: 1 }} />
                          <ListItemText primary={warning} />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No warnings
                    </Typography>
                  )}
                </Grid>
              </Grid>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Loading compliance data...
              </Typography>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirm Portfolio Deletion</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to delete this portfolio?
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1, mt: 2 }}>
            <Typography variant="body2" fontWeight={600}>
              {portfolio.deal_name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Deal Size: ${typeof portfolio.deal_size === 'number' ? (portfolio.deal_size / 1000000).toFixed(1) : '0.0'}M
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Assets: {portfolio.current_asset_count}
            </Typography>
          </Box>
          <Alert severity="error" sx={{ mt: 2 }}>
            This action cannot be undone. All portfolio data and historical records will be permanently deleted.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
          >
            Delete Portfolio
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PortfolioDetail;