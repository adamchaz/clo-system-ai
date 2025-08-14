import { createListenerMiddleware } from '@reduxjs/toolkit';
import { cloApi } from '../api/cloApi';
import type { RootState } from '../index';

// Create listener middleware for optimistic updates
export const optimisticUpdatesMiddleware = createListenerMiddleware();

// Optimistic update for portfolio operations - simplified version to avoid complex typing issues
optimisticUpdatesMiddleware.startListening({
  matcher: cloApi.endpoints.calculateWaterfall.matchPending,
  effect: (action, listenerApi) => {
    try {
      const { deal_id } = action.meta.arg.originalArgs;
      
      // Optimistically update the portfolio with "calculating" status
      (listenerApi.dispatch as any)(
        cloApi.util.updateQueryData('getPortfolioSummary', deal_id, (draft: any) => {
          // Add calculation status to the draft
          draft.calculationStatus = 'calculating';
          draft.lastCalculationStart = new Date().toISOString();
        })
      );
    } catch (error) {
      console.warn('Optimistic update failed:', error);
    }
  },
});

optimisticUpdatesMiddleware.startListening({
  matcher: cloApi.endpoints.calculateWaterfall.matchFulfilled,
  effect: (action, listenerApi) => {
    try {
      const { deal_id } = action.meta.arg.originalArgs;
      const result = action.payload as any;
      
      // Update portfolio with calculation results
      (listenerApi.dispatch as any)(
        cloApi.util.updateQueryData('getPortfolioSummary', deal_id, (draft: any) => {
          if (draft.waterfall_summary) {
            Object.assign(draft.waterfall_summary, {
              mag_version: result.mag_version,
              payment_date: result.payment_date,
              total_cash_available: result.total_cash_available,
            });
          }
          
          draft.calculationStatus = 'completed';
          draft.lastCalculationComplete = result.calculation_timestamp;
        })
      );
    } catch (error) {
      console.warn('Optimistic update failed:', error);
    }
  },
});

optimisticUpdatesMiddleware.startListening({
  matcher: cloApi.endpoints.calculateWaterfall.matchRejected,
  effect: (action, listenerApi) => {
    try {
      const { deal_id } = action.meta.arg.originalArgs;
      
      // Revert optimistic updates on failure
      (listenerApi.dispatch as any)(
        cloApi.util.updateQueryData('getPortfolioSummary', deal_id, (draft: any) => {
          draft.calculationStatus = 'failed';
          draft.lastCalculationError = new Date().toISOString();
          delete draft.lastCalculationStart;
        })
      );
    } catch (error) {
      console.warn('Optimistic update failed:', error);
    }
  },
});

// Optimistic update for risk calculations
optimisticUpdatesMiddleware.startListening({
  matcher: cloApi.endpoints.calculateRisk.matchPending,
  effect: (action, listenerApi) => {
    try {
      const { deal_id, risk_type } = action.meta.arg.originalArgs;
      
      // Add to a temporary risk calculations state
      (listenerApi.dispatch as any)(
        cloApi.util.updateQueryData('getPortfolioSummary', deal_id, (draft: any) => {
          if (!draft.activeCalculations) {
            draft.activeCalculations = [];
          }
          draft.activeCalculations.push({
            type: 'risk',
            subtype: risk_type,
            status: 'calculating',
            startTime: new Date().toISOString(),
          });
        })
      );
    } catch (error) {
      console.warn('Optimistic update failed:', error);
    }
  },
});

optimisticUpdatesMiddleware.startListening({
  matcher: cloApi.endpoints.calculateRisk.matchFulfilled,
  effect: (action, listenerApi) => {
    try {
      const { deal_id, risk_type } = action.meta.arg.originalArgs;
      const result = action.payload as any;
      
      // Update risk metrics in portfolio summary
      (listenerApi.dispatch as any)(
        cloApi.util.updateQueryData('getPortfolioSummary', deal_id, (draft: any) => {
          if (draft.risk_metrics) {
            draft.risk_metrics[`${risk_type}_var_95`] = result.var_95;
            draft.risk_metrics[`${risk_type}_var_99`] = result.var_99;
            draft.risk_metrics[`${risk_type}_expected_shortfall`] = result.expected_shortfall;
          }
          
          // Remove from active calculations
          if (draft.activeCalculations) {
            draft.activeCalculations = draft.activeCalculations.filter(
              (calc: any) => !(calc.type === 'risk' && calc.subtype === risk_type)
            );
          }
        })
      );
    } catch (error) {
      console.warn('Optimistic update failed:', error);
    }
  },
});

/**
 * Enhanced caching utilities - simplified to avoid complex typing issues
 */
export const cacheUtils = {
  // Prefetch related data when a portfolio is selected
  prefetchPortfolioData: (dispatch: any, portfolioId: string) => {
    try {
      const prefetchPromises = [
        (dispatch as any)(cloApi.util.prefetch('getPortfolioSummary', portfolioId, { force: false })),
        (dispatch as any)(cloApi.util.prefetch('getAssets', { skip: 0, limit: 50 }, { force: false })),
      ];
      
      return Promise.all(prefetchPromises);
    } catch (error) {
      console.warn('Prefetch failed:', error);
      return Promise.resolve([]);
    }
  },

  // Smart cache invalidation
  invalidateRelatedData: (dispatch: any, dataType: 'portfolio' | 'asset' | 'calculation', id?: string) => {
    try {
      switch (dataType) {
        case 'portfolio':
          if (id) {
            dispatch(cloApi.util.invalidateTags([{ type: 'Portfolio', id }]));
          } else {
            dispatch(cloApi.util.invalidateTags(['Portfolio']));
          }
          // Also invalidate related analytics
          dispatch(cloApi.util.invalidateTags(['Analytics']));
          break;
          
        case 'asset':
          dispatch(cloApi.util.invalidateTags(['Asset', 'Correlation']));
          // Asset changes affect portfolio analytics
          dispatch(cloApi.util.invalidateTags(['Analytics']));
          break;
          
        case 'calculation':
          dispatch(cloApi.util.invalidateTags(['Calculation', 'Risk', 'Analytics']));
          break;
      }
    } catch (error) {
      console.warn('Cache invalidation failed:', error);
    }
  },

  // Batch prefetch multiple resources
  batchPrefetch: (dispatch: any, resources: Array<{ endpoint: string; args: any }>) => {
    try {
      const promises = resources.map(({ endpoint, args }) => {
        const endpointSlice = (cloApi.endpoints as any)[endpoint];
        if (endpointSlice) {
          return (dispatch as any)(cloApi.util.prefetch(endpoint as any, args, { force: false }));
        }
        return Promise.resolve();
      });
      
      return Promise.all(promises);
    } catch (error) {
      console.warn('Batch prefetch failed:', error);
      return Promise.resolve([]);
    }
  },

  // Get cache statistics
  getCacheStats: (state: RootState) => {
    try {
      const queries = state.cloApi.queries;
      const queryCount = Object.keys(queries).length;
      const fulfilledQueries = Object.values(queries).filter(q => q?.status === 'fulfilled').length;
      const pendingQueries = Object.values(queries).filter(q => q?.status === 'pending').length;
      const errorQueries = Object.values(queries).filter(q => q?.status === 'rejected').length;
      
      return {
        total: queryCount,
        fulfilled: fulfilledQueries,
        pending: pendingQueries,
        errors: errorQueries,
        hitRate: queryCount > 0 ? fulfilledQueries / queryCount : 0,
      };
    } catch (error) {
      console.warn('Cache stats failed:', error);
      return {
        total: 0,
        fulfilled: 0,
        pending: 0,
        errors: 0,
        hitRate: 0,
      };
    }
  },
};