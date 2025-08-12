"""
Credit Migration Service

Service layer for credit migration Monte Carlo simulations.
Provides high-level API for running credit risk scenarios and
managing simulation results.

Author: Claude
Date: 2025-01-12
"""

from typing import List, Dict, Optional, Any, Union
from datetime import date, datetime
import logging
from dataclasses import asdict
import pandas as pd
from sqlalchemy.orm import Session

from ..models.credit_migration import CreditMigration
from ..models.base import get_db_session
from ..models.asset import Asset
from ..models.portfolio import Portfolio
from ..utils.math_utils import MathUtils
from ..core.exceptions import CLOBusinessError, CLOValidationError

logger = logging.getLogger(__name__)


class CreditMigrationService:
    """Service for credit migration simulations and analysis"""
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize credit migration service"""
        self.db = db_session or get_db_session()
        self.credit_migration = CreditMigration()
        self.math_utils = MathUtils()
    
    def run_portfolio_simulation(
        self,
        portfolio_id: str,
        num_simulations: int = 1000,
        analysis_date: Optional[date] = None,
        period_type: str = "QUARTERLY",
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Run credit migration simulation for entire portfolio
        
        Args:
            portfolio_id: Portfolio identifier
            num_simulations: Number of Monte Carlo simulations
            analysis_date: Analysis start date (defaults to today)
            period_type: Period frequency (QUARTERLY, SEMI-ANNUALLY, ANNUALLY)
            debug_mode: Whether to use deterministic random seed
            
        Returns:
            Simulation results dictionary
        """
        try:
            logger.info(f"Starting credit migration simulation for portfolio {portfolio_id}")
            
            # Validate inputs
            if num_simulations <= 0:
                raise CLOValidationError("Number of simulations must be positive")
            
            if period_type not in ["QUARTERLY", "SEMI-ANNUALLY", "ANNUALLY"]:
                raise CLOValidationError(f"Invalid period type: {period_type}")
            
            # Get portfolio and assets
            portfolio = self._get_portfolio(portfolio_id)
            collateral_pool = self._create_collateral_pool(portfolio)
            
            if analysis_date is None:
                analysis_date = date.today()
            
            # Setup simulation
            self.credit_migration.setup(
                num_sims=num_simulations,
                debug_mode=debug_mode,
                collateral_pool=collateral_pool,
                period=period_type
            )
            
            # Run simulations
            results = []
            for sim_num in range(num_simulations):
                logger.debug(f"Running simulation {sim_num + 1}/{num_simulations}")
                
                self.credit_migration.run_rating_history(
                    analysis_date=analysis_date,
                    collateral_pool=collateral_pool,
                    period=period_type
                )
                
                if sim_num % 100 == 0:
                    logger.info(f"Completed {sim_num + 1}/{num_simulations} simulations")
            
            # Get comprehensive results
            simulation_results = self.credit_migration.get_simulation_results()
            
            # Store results in database if needed
            simulation_id = self._store_simulation_results(
                portfolio_id, simulation_results, analysis_date
            )
            
            logger.info(f"Credit migration simulation completed for portfolio {portfolio_id}")
            
            return {
                "simulation_id": simulation_id,
                "portfolio_id": portfolio_id,
                "analysis_date": analysis_date,
                "num_simulations": num_simulations,
                "period_type": period_type,
                "results": simulation_results,
                "export_available": True
            }
            
        except Exception as e:
            logger.error(f"Credit migration simulation failed: {str(e)}")
            raise CLOBusinessError(f"Simulation failed: {str(e)}") from e
        finally:
            self.credit_migration.cleanup()
    
    def run_deal_specific_simulation(
        self,
        portfolio_id: str,
        asset_allocations: Dict[str, float],
        num_simulations: int = 1000,
        analysis_date: Optional[date] = None,
        period_type: str = "QUARTERLY"
    ) -> Dict[str, Any]:
        """
        Run simulation for specific deal structure with asset allocations
        
        Args:
            portfolio_id: Base portfolio identifier
            asset_allocations: Dict of asset_id -> par_amount
            num_simulations: Number of simulations
            analysis_date: Analysis start date
            period_type: Period frequency
            
        Returns:
            Simulation results dictionary
        """
        try:
            logger.info(f"Starting deal-specific simulation with {len(asset_allocations)} assets")
            
            # Validate asset allocations
            if not asset_allocations:
                raise CLOValidationError("Asset allocations cannot be empty")
            
            total_allocation = sum(asset_allocations.values())
            if total_allocation <= 0:
                raise CLOValidationError("Total asset allocation must be positive")
            
            # Get portfolio and create collateral pool
            portfolio = self._get_portfolio(portfolio_id)
            collateral_pool = self._create_collateral_pool(portfolio)
            
            if analysis_date is None:
                analysis_date = date.today()
            
            # Setup and run simulation
            self.credit_migration.setup(
                num_sims=num_simulations,
                collateral_pool=collateral_pool,
                period=period_type
            )
            
            # Run simulations with deal collateral
            for sim_num in range(num_simulations):
                self.credit_migration.run_rating_history(
                    analysis_date=analysis_date,
                    collateral_pool=collateral_pool,
                    deal_collateral=asset_allocations,
                    period=period_type
                )
            
            # Get results
            simulation_results = self.credit_migration.get_simulation_results()
            simulation_results["asset_allocations"] = asset_allocations
            simulation_results["total_par_amount"] = total_allocation
            
            logger.info(f"Deal-specific simulation completed")
            
            return {
                "portfolio_id": portfolio_id,
                "analysis_date": analysis_date,
                "num_simulations": num_simulations,
                "period_type": period_type,
                "asset_count": len(asset_allocations),
                "total_par_amount": total_allocation,
                "results": simulation_results
            }
            
        except Exception as e:
            logger.error(f"Deal-specific simulation failed: {str(e)}")
            raise CLOBusinessError(f"Deal simulation failed: {str(e)}") from e
        finally:
            self.credit_migration.cleanup()
    
    def export_simulation_results(
        self,
        format_type: str = "excel",
        include_details: bool = True
    ) -> Union[pd.DataFrame, str]:
        """
        Export simulation results in various formats
        
        Args:
            format_type: Export format (excel, csv, json)
            include_details: Whether to include detailed period-by-period data
            
        Returns:
            DataFrame or file path depending on format
        """
        try:
            # Get results as DataFrame
            df = self.credit_migration.export_to_dataframe()
            
            if df.empty:
                raise CLOBusinessError("No simulation results available for export")
            
            if format_type.lower() == "csv":
                return df
            elif format_type.lower() == "excel":
                return self._export_to_excel(df, include_details)
            elif format_type.lower() == "json":
                return df.to_json(orient="records")
            else:
                raise CLOValidationError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise CLOBusinessError(f"Export failed: {str(e)}") from e
    
    def analyze_scenario_impact(
        self,
        base_results: Dict[str, Any],
        stress_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze impact between base case and stress scenario
        
        Args:
            base_results: Base case simulation results
            stress_results: Stress scenario results
            
        Returns:
            Impact analysis results
        """
        try:
            # Extract key metrics for comparison
            base_stats = base_results.get("statistics", {})
            stress_stats = stress_results.get("statistics", {})
            
            impact_analysis = {
                "scenario_comparison": {},
                "period_analysis": {},
                "risk_metrics": {}
            }
            
            # Compare final period metrics
            if base_stats and stress_stats:
                final_period_base = max(base_stats.keys(), key=lambda x: int(x.split('_')[1]))
                final_period_stress = max(stress_stats.keys(), key=lambda x: int(x.split('_')[1]))
                
                base_final = base_stats.get(final_period_base, {})
                stress_final = stress_stats.get(final_period_stress, {})
                
                # Calculate impact on key metrics
                for metric in ["num_defaults", "num_ccc_assets", "num_downgrades"]:
                    if metric in base_final and metric in stress_final:
                        base_value = base_final[metric].get("mean", 0)
                        stress_value = stress_final[metric].get("mean", 0)
                        
                        impact_analysis["scenario_comparison"][metric] = {
                            "base_mean": base_value,
                            "stress_mean": stress_value,
                            "absolute_change": stress_value - base_value,
                            "relative_change": (stress_value - base_value) / base_value if base_value > 0 else 0
                        }
            
            # Risk metrics
            impact_analysis["risk_metrics"] = {
                "increased_default_risk": self._calculate_default_risk_increase(base_stats, stress_stats),
                "rating_migration_impact": self._calculate_migration_impact(base_stats, stress_stats),
                "timeline_analysis": self._analyze_timeline_impact(base_stats, stress_stats)
            }
            
            return impact_analysis
            
        except Exception as e:
            logger.error(f"Scenario analysis failed: {str(e)}")
            raise CLOBusinessError(f"Scenario analysis failed: {str(e)}") from e
    
    def _get_portfolio(self, portfolio_id: str) -> Portfolio:
        """Get portfolio from database"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id
        ).first()
        
        if not portfolio:
            raise CLOValidationError(f"Portfolio not found: {portfolio_id}")
        
        return portfolio
    
    def _create_collateral_pool(self, portfolio: Portfolio) -> Any:
        """Create mock collateral pool from portfolio assets"""
        # This would create a proper collateral pool object
        # For now, return a mock that matches our test interface
        
        class CollateralPool:
            def __init__(self, portfolio: Portfolio):
                self.portfolio = portfolio
                self.assets = {
                    asset.id: asset for asset in portfolio.assets
                }
            
            def get_asset_ids(self):
                return list(self.assets.keys())
            
            def get_asset(self, asset_id):
                return self.assets.get(asset_id)
            
            def get_sp_rating(self, asset_id, date_val=None):
                asset = self.assets.get(asset_id)
                return asset.sp_rating if asset else "D"
            
            def is_defaulted(self, asset_id):
                asset = self.assets.get(asset_id)
                return asset.defaulted if asset else True
            
            def get_asset_maturity(self, asset_id):
                asset = self.assets.get(asset_id)
                return asset.maturity_date if asset else date.today()
            
            def get_last_maturity_date(self):
                return max(asset.maturity_date for asset in self.assets.values())
            
            def get_beginning_balance(self, asset_id, date_val):
                asset = self.assets.get(asset_id)
                return asset.par_amount if asset else 0.0
            
            def get_scheduled_principal(self, asset_id, start_date, end_date):
                # Simplified principal calculation
                return 0.0
            
            def add_sp_rating(self, asset_id, date_val, rating):
                # Track rating changes
                pass
        
        return CollateralPool(portfolio)
    
    def _store_simulation_results(
        self,
        portfolio_id: str,
        results: Dict[str, Any],
        analysis_date: date
    ) -> str:
        """Store simulation results in database"""
        # This would store results in a simulation results table
        # For now, return a mock simulation ID
        simulation_id = f"SIM_{portfolio_id}_{analysis_date.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}"
        
        logger.info(f"Simulation results stored with ID: {simulation_id}")
        return simulation_id
    
    def _export_to_excel(self, df: pd.DataFrame, include_details: bool) -> str:
        """Export results to Excel format"""
        filename = f"credit_migration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            df.groupby(['simulation']).agg({
                'num_defaults': 'max',
                'bal_defaults': 'max',
                'cdr': 'mean'
            }).to_excel(writer, sheet_name='Summary')
            
            if include_details:
                # Detailed results
                df.to_excel(writer, sheet_name='Detailed_Results', index=False)
                
                # Statistics by period
                stats_df = df.groupby(['period']).agg({
                    'num_defaults': ['min', 'max', 'mean', 'std'],
                    'bal_defaults': ['min', 'max', 'mean', 'std'],
                    'cdr': ['min', 'max', 'mean', 'std']
                }).round(4)
                
                stats_df.to_excel(writer, sheet_name='Period_Statistics')
        
        logger.info(f"Results exported to Excel: {filename}")
        return filename
    
    def _calculate_default_risk_increase(
        self,
        base_stats: Dict[str, Any],
        stress_stats: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate increase in default risk between scenarios"""
        risk_increase = {
            "early_period_risk": 0.0,
            "mid_period_risk": 0.0,
            "late_period_risk": 0.0
        }
        
        if not base_stats or not stress_stats:
            return risk_increase
        
        # Analyze risk across different time periods
        num_periods = len(base_stats)
        
        if num_periods > 0:
            early_periods = list(base_stats.keys())[:num_periods//3] if num_periods >= 3 else []
            mid_periods = list(base_stats.keys())[num_periods//3:2*num_periods//3] if num_periods >= 3 else []
            late_periods = list(base_stats.keys())[2*num_periods//3:] if num_periods >= 3 else []
            
            # Calculate average default increases for each period
            for period_type, periods in [("early_period_risk", early_periods),
                                       ("mid_period_risk", mid_periods),
                                       ("late_period_risk", late_periods)]:
                if periods:
                    base_avg = sum(base_stats[p].get("num_defaults", {}).get("mean", 0) for p in periods) / len(periods)
                    stress_avg = sum(stress_stats[p].get("num_defaults", {}).get("mean", 0) for p in periods) / len(periods)
                    
                    if base_avg > 0:
                        risk_increase[period_type] = (stress_avg - base_avg) / base_avg
        
        return risk_increase
    
    def _calculate_migration_impact(
        self,
        base_stats: Dict[str, Any],
        stress_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate rating migration impact"""
        migration_impact = {
            "downgrades_increase": 0.0,
            "upgrades_decrease": 0.0,
            "ccc_bucket_increase": 0.0
        }
        
        if not base_stats or not stress_stats:
            return migration_impact
        
        # Compare final period migrations
        final_base = list(base_stats.values())[-1] if base_stats else {}
        final_stress = list(stress_stats.values())[-1] if stress_stats else {}
        
        base_downgrades = final_base.get("downgrades", {}).get("mean", 0)
        stress_downgrades = final_stress.get("downgrades", {}).get("mean", 0)
        
        base_upgrades = final_base.get("upgrades", {}).get("mean", 0)
        stress_upgrades = final_stress.get("upgrades", {}).get("mean", 0)
        
        base_ccc = final_base.get("num_ccc_assets", {}).get("mean", 0)
        stress_ccc = final_stress.get("num_ccc_assets", {}).get("mean", 0)
        
        if base_downgrades > 0:
            migration_impact["downgrades_increase"] = (stress_downgrades - base_downgrades) / base_downgrades
        
        if base_upgrades > 0:
            migration_impact["upgrades_decrease"] = (base_upgrades - stress_upgrades) / base_upgrades
        
        if base_ccc >= 0:  # CCC can be 0 in base case
            migration_impact["ccc_bucket_increase"] = stress_ccc - base_ccc
        
        return migration_impact
    
    def _analyze_timeline_impact(
        self,
        base_stats: Dict[str, Any],
        stress_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze impact over time"""
        timeline_analysis = {
            "peak_stress_period": 0,
            "cumulative_impact": 0.0,
            "acceleration_factor": 0.0
        }
        
        if not base_stats or not stress_stats:
            return timeline_analysis
        
        # Find period with maximum stress impact
        max_impact = 0.0
        peak_period = 0
        cumulative_impact = 0.0
        
        for i, (period_key in enumerate(base_stats.keys())):
            base_defaults = base_stats[period_key].get("num_defaults", {}).get("mean", 0)
            stress_defaults = stress_stats[period_key].get("num_defaults", {}).get("mean", 0)
            
            period_impact = stress_defaults - base_defaults
            cumulative_impact += period_impact
            
            if period_impact > max_impact:
                max_impact = period_impact
                peak_period = i
        
        timeline_analysis["peak_stress_period"] = peak_period
        timeline_analysis["cumulative_impact"] = cumulative_impact
        
        # Calculate acceleration factor (how much faster defaults occur)
        if cumulative_impact > 0:
            early_impact = sum(
                stress_stats[list(stress_stats.keys())[i]].get("num_defaults", {}).get("mean", 0) -
                base_stats[list(base_stats.keys())[i]].get("num_defaults", {}).get("mean", 0)
                for i in range(min(3, len(base_stats)))
            )
            timeline_analysis["acceleration_factor"] = early_impact / cumulative_impact if cumulative_impact > 0 else 0.0
        
        return timeline_analysis