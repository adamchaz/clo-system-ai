/**
 * useCloApi Hook - Central API Hook Management System
 * 
 * Provides centralized access to all CLO Management System APIs:
 * - Asset management operations (CRUD, analytics, risk metrics)
 * - Portfolio management and correlation analysis  
 * - Waterfall calculations and risk analytics
 * - System health monitoring and real-time updates
 * 
 * Part of CLO Management System - Task 9 Complete
 * Full RTK Query integration with optimistic updates and caching
 */
import { useEffect, useState, useCallback, useMemo } from 'react';
import { useAppDispatch } from './reduxHooks';
import {
  useGetPortfoliosQuery,
  useGetPortfolioQuery,
  useGetPortfolioSummaryQuery,
  useGetAssetsQuery,
  useGetAssetQuery,
  useGetAssetCorrelationsQuery,
  useGetAssetStatsQuery,
  useCreateAssetMutation,
  useUpdateAssetMutation,
  useDeleteAssetMutation,
  useGetAssetRiskMetricsQuery,
  useCalculateWaterfallMutation,
  useCalculateRiskMutation,
  useGetSystemHealthQuery,
  cloApi,
  type Portfolio,
  type WaterfallRequest,
  type RiskAnalyticsRequest,
} from '../store/api/cloApi';

// Export the main API object and all individual hooks for asset components
export { cloApi } from '../store/api/cloApi';

// Re-export all the hooks that asset components need
export {
  // Asset hooks
  useGetAssetsQuery,
  useGetAssetQuery,
  useGetAssetCorrelationsQuery,
  useGetAssetStatsQuery,
  useCreateAssetMutation,
  useUpdateAssetMutation,
  useDeleteAssetMutation,
  useGetAssetRiskMetricsQuery,
  
  // Portfolio hooks
  useGetPortfoliosQuery,
  useGetPortfolioQuery,
  useGetPortfolioSummaryQuery,
  
  // Waterfall and risk calculation hooks
  useCalculateWaterfallMutation,
  useCalculateRiskMutation,
  
  // System monitoring
  useGetSystemHealthQuery,
} from '../store/api/cloApi';

// Custom hook for CLO API access - provides easy access to all hooks
export const useCloApi = () => {
  return {
    // Asset hooks
    useGetAssetsQuery,
    useGetAssetQuery,
    useGetAssetCorrelationsQuery,
    useGetAssetStatsQuery,
    useCreateAssetMutation,
    useUpdateAssetMutation,
    useDeleteAssetMutation,
    useGetAssetRiskMetricsQuery,
    
    // Portfolio hooks
    useGetPortfoliosQuery,
    useGetPortfolioQuery,
    useGetPortfolioSummaryQuery,
    
    // Calculation hooks
    useCalculateWaterfallMutation,
    useCalculateRiskMutation,
    
    // System hooks
    useGetSystemHealthQuery,
  };
};

/**
 * Enhanced hook for portfolio management with caching and error handling
 */
export const usePortfolio = (dealId?: string) => {
  const dispatch = useAppDispatch();
  
  // Query hooks
  const portfoliosQuery = useGetPortfoliosQuery();
  const portfolioSummaryQuery = useGetPortfolioSummaryQuery(dealId!, { 
    skip: !dealId 
  });
  
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);

  // Memoized portfolio data
  const portfolioData = useMemo(() => {
    if (portfolioSummaryQuery.data) {
      return portfolioSummaryQuery.data;
    }
    return null;
  }, [portfolioSummaryQuery.data]);

  // Portfolio selection handler
  const selectPortfolio = useCallback((portfolio: Portfolio | null) => {
    setSelectedPortfolio(portfolio);
    if (portfolio) {
      // Prefetch portfolio details
      dispatch(
        cloApi.util.prefetch('getPortfolioSummary', portfolio.id, { force: false })
      );
    }
  }, [dispatch]);

  // Refresh portfolio data
  const refreshPortfolio = useCallback(() => {
    if (dealId) {
      dispatch(cloApi.util.invalidateTags([{ type: 'Portfolio', id: dealId }]));
    }
  }, [dispatch, dealId]);

  return {
    // Data
    portfolios: portfoliosQuery.data?.data || [],
    portfolioSummary: portfolioData,
    selectedPortfolio,
    
    // Loading states
    isLoadingPortfolios: portfoliosQuery.isLoading,
    isLoadingPortfolio: portfolioSummaryQuery.isLoading,
    
    // Error states
    portfoliosError: portfoliosQuery.error,
    portfolioError: portfolioSummaryQuery.error,
    
    // Actions
    selectPortfolio,
    refreshPortfolio,
    
    // Refetch functions
    refetchPortfolios: portfoliosQuery.refetch,
    refetchPortfolio: portfolioSummaryQuery.refetch,
  };
};

/**
 * Enhanced hook for asset management with filtering and pagination
 */
export const useAssets = (filters: {
  asset_type?: string;
  rating?: string;
  sector?: string;
  limit?: number;
} = {}) => {
  const dispatch = useAppDispatch();
  
  // State for pagination and filtering
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(filters.limit || 50);
  const [activeFilters, setActiveFilters] = useState(filters);

  // Asset query with pagination
  const assetsQuery = useGetAssetsQuery({
    skip: currentPage * pageSize,
    limit: pageSize,
    ...activeFilters,
  });

  // Memoized asset data
  const assetData = useMemo(() => {
    return {
      assets: assetsQuery.data?.data || [],
      total: assetsQuery.data?.total || 0,
      hasMore: assetsQuery.data?.has_more || false,
      currentPage,
      pageSize,
    };
  }, [assetsQuery.data, currentPage, pageSize]);

  // Filter update handler
  const updateFilters = useCallback((newFilters: typeof filters) => {
    setActiveFilters(prev => ({ ...prev, ...newFilters }));
    setCurrentPage(0); // Reset to first page when filters change
  }, []);

  // Pagination handlers
  const nextPage = useCallback(() => {
    if (assetData.hasMore) {
      setCurrentPage(prev => prev + 1);
    }
  }, [assetData.hasMore]);

  const previousPage = useCallback(() => {
    if (currentPage > 0) {
      setCurrentPage(prev => prev - 1);
    }
  }, [currentPage]);

  const goToPage = useCallback((page: number) => {
    const maxPage = Math.floor(assetData.total / pageSize);
    if (page >= 0 && page <= maxPage) {
      setCurrentPage(page);
    }
  }, [assetData.total, pageSize]);

  // Refresh assets
  const refreshAssets = useCallback(() => {
    dispatch(cloApi.util.invalidateTags(['Asset', 'Analytics']));
  }, [dispatch]);

  return {
    // Data
    ...assetData,
    
    // Loading and error states
    isLoading: assetsQuery.isLoading,
    error: assetsQuery.error,
    
    // Filter state
    activeFilters,
    
    // Actions
    updateFilters,
    nextPage,
    previousPage,
    goToPage,
    refreshAssets,
    
    // Utilities
    refetch: assetsQuery.refetch,
  };
};

/**
 * Enhanced hook for waterfall calculations with history tracking
 */
export const useWaterfall = (dealId: string) => {
  const [calculateWaterfall, waterfallMutation] = useCalculateWaterfallMutation();
  const [calculationHistory, setCalculationHistory] = useState<any[]>([]);

  // Run waterfall calculation
  const runCalculation = useCallback(async (
    paymentDate: string, 
    options: Omit<WaterfallRequest, 'deal_id' | 'payment_date'> = {}
  ) => {
    try {
      const request: WaterfallRequest = {
        deal_id: dealId,
        payment_date: paymentDate,
        ...options,
      };

      const result = await calculateWaterfall(request).unwrap();
      
      // Add to history
      setCalculationHistory(prev => [result, ...prev].slice(0, 10)); // Keep last 10
      
      return result;
    } catch (error) {
      console.error('Waterfall calculation failed:', error);
      throw error;
    }
  }, [dealId, calculateWaterfall]);

  // Clear calculation history
  const clearHistory = useCallback(() => {
    setCalculationHistory([]);
  }, []);

  return {
    // State
    calculationHistory,
    isCalculating: waterfallMutation.isLoading,
    calculationError: waterfallMutation.error,
    
    // Actions
    runCalculation,
    clearHistory,
    
    // Last result
    lastResult: calculationHistory[0] || null,
  };
};

/**
 * Enhanced hook for risk analytics with caching
 */
export const useRiskAnalytics = (dealId: string) => {
  const [calculateRisk, riskMutation] = useCalculateRiskMutation();
  const [riskCache, setRiskCache] = useState<Map<string, any>>(new Map());

  // Run risk calculation with caching
  const runRiskAnalysis = useCallback(async (
    riskType: 'var' | 'stress_test' | 'scenario_analysis',
    options: Omit<RiskAnalyticsRequest, 'deal_id' | 'risk_type'> = {}
  ) => {
    const cacheKey = `${dealId}-${riskType}-${JSON.stringify(options)}`;
    
    // Check cache first (valid for 5 minutes)
    const cached = riskCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
      return cached.data;
    }

    try {
      const request: RiskAnalyticsRequest = {
        deal_id: dealId,
        risk_type: riskType,
        ...options,
      };

      const result = await calculateRisk(request).unwrap();
      
      // Cache the result
      setRiskCache(prev => new Map(prev).set(cacheKey, {
        data: result,
        timestamp: Date.now(),
      }));
      
      return result;
    } catch (error) {
      console.error('Risk calculation failed:', error);
      throw error;
    }
  }, [dealId, calculateRisk, riskCache]);

  // Clear risk cache
  const clearCache = useCallback(() => {
    setRiskCache(new Map());
  }, []);

  return {
    // State
    isCalculating: riskMutation.isLoading,
    calculationError: riskMutation.error,
    cacheSize: riskCache.size,
    
    // Actions
    runRiskAnalysis,
    clearCache,
  };
};

/**
 * System monitoring hook with real-time updates
 */
export const useSystemMonitoring = (refreshInterval: number = 30000) => {
  const systemHealthQuery = useGetSystemHealthQuery(undefined, {
    pollingInterval: refreshInterval,
  });

  const [alerts, setAlerts] = useState<string[]>([]);

  // Monitor system alerts
  useEffect(() => {
    if (systemHealthQuery.data && systemHealthQuery.data.system_alerts > 0) {
      // In a real implementation, you'd fetch detailed alert information
      setAlerts(prev => [...prev, `System alert detected at ${new Date().toLocaleTimeString()}`]);
    }
  }, [systemHealthQuery.data?.system_alerts]);

  // Clear alerts
  const clearAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  return {
    // System health data
    systemHealth: systemHealthQuery.data,
    
    // Loading and error states
    isLoading: systemHealthQuery.isLoading,
    error: systemHealthQuery.error,
    
    // Alerts
    alerts,
    clearAlerts,
    
    // Manual refresh
    refresh: systemHealthQuery.refetch,
  };
};

/**
 * Combined hook for dashboard data
 */
export const useDashboardData = (dealId?: string) => {
  const portfolio = usePortfolio(dealId);
  const assets = useAssets({ limit: 20 }); // Top 20 assets
  const systemMonitoring = useSystemMonitoring();

  const isLoading = portfolio.isLoadingPortfolio || assets.isLoading || systemMonitoring.isLoading;
  const hasError = !!(portfolio.portfolioError || assets.error || systemMonitoring.error);

  return {
    portfolio,
    assets,
    systemMonitoring,
    
    // Combined states
    isLoading,
    hasError,
    
    // Combined refresh
    refreshAll: () => {
      portfolio.refreshPortfolio();
      assets.refreshAssets();
      systemMonitoring.refresh();
    },
  };
};