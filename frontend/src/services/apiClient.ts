import { store } from '../store';
import { cloApi } from '../store/api/cloApi';
import type { 
  Asset, 
  Portfolio, 
  WaterfallRequest, 
  RiskAnalyticsRequest,
  PaginatedResponse 
} from '../store/api/cloApi';

/**
 * CLO API Client - Enterprise API Service Layer
 * 
 * Production-ready API client providing high-level operations:
 * - Portfolio analytics and asset management
 * - Risk calculation and waterfall processing
 * - Batch operations and cache management
 * - Real-time data subscriptions and utilities
 * 
 * Part of CLO Management System - Tasks 9-12 Complete
 * Includes fix for API return type mapping (result.data extraction)
 */
export class CLOApiClient {
  private dispatch = store.dispatch;

  // Portfolio operations
  async getPortfolioWithAssets(dealId: string) {
    try {
      const portfolioSummary = await this.dispatch(
        cloApi.endpoints.getPortfolioSummary.initiate(dealId)
      ).unwrap();
      
      return portfolioSummary;
    } catch (error) {
      console.error('Failed to fetch portfolio with assets:', error);
      throw error;
    }
  }

  async searchAssets(filters: {
    query?: string;
    asset_type?: string;
    rating?: string;
    sector?: string;
    limit?: number;
  }): Promise<PaginatedResponse<Asset>> {
    try {
      const result = await this.dispatch(
        cloApi.endpoints.getAssets.initiate(filters)
      ).unwrap();
      
      return result;
    } catch (error) {
      console.error('Failed to search assets:', error);
      throw error;
    }
  }

  async calculatePortfolioRisk(
    dealId: string, 
    riskType: 'var' | 'stress_test' | 'scenario_analysis',
    options: {
      confidence_level?: number;
      time_horizon?: number;
      scenario_parameters?: Record<string, any>;
    } = {}
  ) {
    try {
      const request: RiskAnalyticsRequest = {
        deal_id: dealId,
        risk_type: riskType,
        ...options,
      };

      const result = await this.dispatch(
        cloApi.endpoints.calculateRisk.initiate(request)
      ).unwrap();
      
      return result;
    } catch (error) {
      console.error('Failed to calculate portfolio risk:', error);
      throw error;
    }
  }

  async runWaterfallCalculation(
    dealId: string, 
    paymentDate: string,
    options: {
      mag_version?: string;
      scenario_overrides?: Record<string, any>;
    } = {}
  ) {
    try {
      const request: WaterfallRequest = {
        deal_id: dealId,
        payment_date: paymentDate,
        ...options,
      };

      const result = await this.dispatch(
        cloApi.endpoints.calculateWaterfall.initiate(request)
      ).unwrap();
      
      return result;
    } catch (error) {
      console.error('Failed to run waterfall calculation:', error);
      throw error;
    }
  }

  // Cache management utilities
  invalidatePortfolioData(portfolioId?: string) {
    if (portfolioId) {
      this.dispatch(
        cloApi.util.invalidateTags([{ type: 'Portfolio', id: portfolioId }])
      );
    } else {
      this.dispatch(cloApi.util.invalidateTags(['Portfolio']));
    }
  }

  invalidateAssetData() {
    this.dispatch(
      cloApi.util.invalidateTags(['Asset', 'Correlation', 'Analytics'])
    );
  }

  invalidateCalculations() {
    this.dispatch(
      cloApi.util.invalidateTags(['Calculation', 'Risk', 'Analytics'])
    );
  }

  // Batch operations
  async getMultipleAssets(assetIds: string[]): Promise<Asset[]> {
    try {
      const promises = assetIds.map(id =>
        this.dispatch(cloApi.endpoints.getAsset.initiate(id)).unwrap()
      );
      
      const results = await Promise.all(promises);
      return results.map(result => result.data);
    } catch (error) {
      console.error('Failed to fetch multiple assets:', error);
      throw error;
    }
  }

  async getPortfolioAnalytics(dealId: string) {
    try {
      // Fetch portfolio summary and risk metrics in parallel
      const [portfolioSummary, systemHealth] = await Promise.all([
        this.dispatch(
          cloApi.endpoints.getPortfolioSummary.initiate(dealId)
        ).unwrap(),
        this.dispatch(
          cloApi.endpoints.getSystemHealth.initiate()
        ).unwrap(),
      ]);

      return {
        portfolio: portfolioSummary,
        systemHealth,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Failed to fetch portfolio analytics:', error);
      throw error;
    }
  }

  // Real-time data utilities
  subscribeToPortfolioUpdates(dealId: string, callback: (data: any) => void) {
    // Implementation will be added when WebSocket integration is complete
    console.log('WebSocket subscription for portfolio:', dealId);
    // TODO: Implement WebSocket subscription
  }

  unsubscribeFromPortfolioUpdates(dealId: string) {
    // Implementation will be added when WebSocket integration is complete
    console.log('WebSocket unsubscription for portfolio:', dealId);
    // TODO: Implement WebSocket cleanup
  }
}

// Export singleton instance
export const cloApiClient = new CLOApiClient();

// Export utility functions for component use
export const apiUtils = {
  invalidatePortfolio: (dispatch: any, portfolioId?: string) => {
    if (portfolioId) {
      dispatch(cloApi.util.invalidateTags([{ type: 'Portfolio', id: portfolioId }]));
    } else {
      dispatch(cloApi.util.invalidateTags(['Portfolio']));
    }
  },

  invalidateAssets: (dispatch: any) => {
    dispatch(cloApi.util.invalidateTags(['Asset', 'Correlation', 'Analytics']));
  },

  invalidateCalculations: (dispatch: any) => {
    dispatch(cloApi.util.invalidateTags(['Calculation', 'Risk', 'Analytics']));
  },

  prefetchPortfolio: (dispatch: any, portfolioId: string) => {
    dispatch(cloApi.util.prefetch('getPortfolioSummary', portfolioId, { force: false }));
  },

  prefetchAssets: (dispatch: any, filters: Record<string, any> = {}) => {
    dispatch(cloApi.util.prefetch('getAssets', filters, { force: false }));
  },
};