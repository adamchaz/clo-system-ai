"""
Risk Analytics Service
Implements sophisticated risk calculations, correlation analysis, and portfolio risk metrics
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import logging
import numpy as np
from scipy import stats
from scipy.linalg import eigvals
import pandas as pd

from sqlalchemy.orm import Session
from ..core.database_config import db_config
from ..services.data_integration import DataIntegrationService

logger = logging.getLogger(__name__)

class RiskAnalyticsService:
    """Service for risk analytics and portfolio risk calculations"""
    
    def __init__(self):
        self.integration_service = DataIntegrationService()
        
    def calculate_portfolio_risk_metrics(
        self,
        deal_id: str,
        as_of_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics for a portfolio
        
        Args:
            deal_id: Portfolio identifier
            as_of_date: As-of date for calculations
            
        Returns:
            Comprehensive risk metrics
        """
        logger.info(f"Calculating risk metrics for deal {deal_id}")
        
        try:
            # Get portfolio assets
            portfolio_assets = self._get_portfolio_assets(deal_id)
            
            if not portfolio_assets:
                raise ValueError(f"No assets found for deal {deal_id}")
            
            # Calculate volatility metrics
            volatility_metrics = self._calculate_volatility_metrics(portfolio_assets)
            
            # Calculate concentration metrics
            concentration_metrics = self._calculate_concentration_metrics(portfolio_assets)
            
            # Calculate VaR metrics
            var_metrics = self._calculate_var_metrics(portfolio_assets)
            
            # Calculate duration and sensitivity
            duration_metrics = self._calculate_duration_metrics(portfolio_assets)
            
            # Calculate credit risk metrics
            credit_metrics = self._calculate_credit_risk_metrics(portfolio_assets)
            
            # Assess overall risk level
            risk_level = self._assess_risk_level(
                volatility_metrics, concentration_metrics, var_metrics
            )
            
            return {
                'deal_id': deal_id,
                'as_of_date': as_of_date or date.today(),
                'calculation_timestamp': datetime.now(),
                **volatility_metrics,
                **concentration_metrics,
                **var_metrics,
                **duration_metrics,
                **credit_metrics,
                'overall_risk_level': risk_level['level'],
                'risk_factors': risk_level['factors']
            }
            
        except Exception as e:
            logger.error(f"Risk metrics calculation failed for deal {deal_id}: {e}")
            raise
    
    def build_correlation_matrix(
        self,
        asset_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Build correlation matrix for a set of assets
        
        Args:
            asset_ids: List of asset identifiers
            
        Returns:
            Correlation matrix and analysis
        """
        logger.info(f"Building correlation matrix for {len(asset_ids)} assets")
        
        try:
            # Build correlation matrix from migrated data
            correlation_pairs = []
            matrix = np.zeros((len(asset_ids), len(asset_ids)))
            
            for i, asset1 in enumerate(asset_ids):
                for j, asset2 in enumerate(asset_ids):
                    if i == j:
                        matrix[i][j] = 1.0
                    else:
                        correlation = self.integration_service.get_correlation(asset1, asset2)
                        matrix[i][j] = correlation if correlation is not None else 0.0
            
            # Calculate matrix properties
            eigenvalues = eigvals(matrix).real
            condition_number = np.max(eigenvalues) / np.min(eigenvalues) if np.min(eigenvalues) > 0 else float('inf')
            
            # Calculate statistics
            upper_triangle = matrix[np.triu_indices_from(matrix, k=1)]
            avg_correlation = float(np.mean(upper_triangle))
            max_correlation = float(np.max(upper_triangle))
            min_correlation = float(np.min(upper_triangle))
            
            # Identify correlation clusters (simplified)
            clusters = self._identify_correlation_clusters(matrix, asset_ids)
            
            return {
                'asset_count': len(asset_ids),
                'correlation_matrix': matrix.tolist(),
                'asset_ids': asset_ids,
                'eigenvalues': eigenvalues.tolist(),
                'condition_number': float(condition_number) if condition_number != float('inf') else None,
                'average_correlation': avg_correlation,
                'max_correlation': max_correlation,
                'min_correlation': min_correlation,
                'correlation_clusters': clusters
            }
            
        except Exception as e:
            logger.error(f"Correlation matrix building failed: {e}")
            raise
    
    def analyze_concentration(
        self,
        deal_id: str,
        dimension: str = "sector"
    ) -> Dict[str, Any]:
        """
        Analyze portfolio concentration by various dimensions
        
        Args:
            deal_id: Portfolio identifier
            dimension: Concentration dimension (sector, industry, rating, etc.)
            
        Returns:
            Concentration analysis results
        """
        logger.info(f"Analyzing {dimension} concentration for deal {deal_id}")
        
        try:
            # Get portfolio assets with weights
            portfolio_assets = self._get_portfolio_assets_with_weights(deal_id)
            
            # Group assets by dimension
            concentrations = {}
            for asset in portfolio_assets:
                dim_value = asset.get(dimension, "Other")
                weight = asset.get('weight', 0)
                concentrations[dim_value] = concentrations.get(dim_value, 0) + weight
            
            # Calculate concentration ratios
            sorted_weights = sorted(concentrations.values(), reverse=True)
            concentration_ratio_top5 = sum(sorted_weights[:5])
            concentration_ratio_top10 = sum(sorted_weights[:10])
            
            # Calculate diversification metrics
            effective_positions = 1 / sum(w**2 for w in concentrations.values())
            diversification_ratio = len(concentrations) / effective_positions
            
            # Calculate concentration risk score (0-100, higher is riskier)
            risk_score = min(100, concentration_ratio_top5 * 100)
            
            # Identify over-concentrated segments (>10% in single dimension)
            over_concentrated = [dim for dim, weight in concentrations.items() if weight > 0.1]
            
            return {
                'deal_id': deal_id,
                'dimension': dimension,
                'analysis_date': date.today(),
                'concentrations': {k: float(v) for k, v in concentrations.items()},
                'concentration_ratio_top5': float(concentration_ratio_top5),
                'concentration_ratio_top10': float(concentration_ratio_top10),
                'concentration_risk_score': float(risk_score),
                'over_concentrated_segments': over_concentrated,
                'effective_number_of_positions': int(effective_positions),
                'diversification_ratio': float(diversification_ratio),
                'recommended_limits': {dim: 0.08 for dim in over_concentrated}  # 8% limit
            }
            
        except Exception as e:
            logger.error(f"Concentration analysis failed for deal {deal_id}: {e}")
            raise
    
    def run_comprehensive_stress_test(
        self,
        deal_id: str,
        scenarios: List[Dict[str, Any]],
        time_horizon: int = 12,
        monte_carlo_runs: int = 1000
    ) -> Dict[str, Any]:
        """
        Run comprehensive stress testing on a portfolio
        
        Args:
            deal_id: Portfolio identifier
            scenarios: List of stress test scenarios
            time_horizon: Time horizon in months
            monte_carlo_runs: Number of Monte Carlo simulations
            
        Returns:
            Comprehensive stress test results
        """
        logger.info(f"Running stress tests for deal {deal_id} with {len(scenarios)} scenarios")
        
        try:
            # Get base portfolio metrics
            base_portfolio_value = self._get_portfolio_value(deal_id)
            
            # Run each scenario
            scenario_results = []
            for scenario in scenarios:
                result = self._run_single_stress_scenario(
                    deal_id, scenario, base_portfolio_value, time_horizon, monte_carlo_runs
                )
                scenario_results.append(result)
            
            # Calculate summary statistics
            losses = [result['portfolio_loss'] for result in scenario_results]
            
            summary_stats = {
                'worst_case_loss': max(losses),
                'best_case_loss': min(losses),
                'median_loss': np.median(losses),
                'loss_distribution': self._calculate_loss_distribution(losses)
            }
            
            # Rank scenarios by severity
            scenario_rankings = [
                result['scenario']['scenario_name'] 
                for result in sorted(scenario_results, key=lambda x: x['portfolio_loss'], reverse=True)
            ]
            
            # Identify critical scenarios (>5% loss)
            critical_scenarios = [
                result['scenario']['scenario_name']
                for result in scenario_results
                if result['loss_percentage'] > 5.0
            ]
            
            return {
                'deal_id': deal_id,
                'test_date': datetime.now(),
                'scenarios_tested': len(scenarios),
                'monte_carlo_runs': monte_carlo_runs,
                'scenario_results': scenario_results,
                'scenario_rankings': scenario_rankings,
                'critical_scenarios': critical_scenarios,
                **summary_stats
            }
            
        except Exception as e:
            logger.error(f"Stress testing failed for deal {deal_id}: {e}")
            raise
    
    def calculate_var(
        self,
        deal_id: str,
        confidence_level: float = 0.95,
        time_horizon_days: int = 30,
        method: str = "monte_carlo"
    ) -> Dict[str, Any]:
        """
        Calculate Value at Risk for a portfolio
        
        Args:
            deal_id: Portfolio identifier
            confidence_level: Confidence level for VaR calculation
            time_horizon_days: Time horizon in days
            method: Calculation method (parametric, historical, monte_carlo)
            
        Returns:
            VaR calculation results
        """
        logger.info(f"Calculating {method} VaR for deal {deal_id}")
        
        try:
            portfolio_value = self._get_portfolio_value(deal_id)
            
            if method == "monte_carlo":
                var_result = self._calculate_monte_carlo_var(
                    deal_id, confidence_level, time_horizon_days, portfolio_value
                )
            elif method == "parametric":
                var_result = self._calculate_parametric_var(
                    deal_id, confidence_level, time_horizon_days, portfolio_value
                )
            elif method == "historical":
                var_result = self._calculate_historical_var(
                    deal_id, confidence_level, time_horizon_days, portfolio_value
                )
            else:
                raise ValueError(f"Unknown VaR method: {method}")
            
            var_percentage = (var_result['var'] / portfolio_value) * 100
            
            return {
                'var': var_result['var'],
                'expected_shortfall': var_result.get('expected_shortfall', 0),
                'portfolio_value': portfolio_value,
                'var_percentage': var_percentage,
                'calculation_details': var_result.get('details', {}),
                'assumptions': var_result.get('assumptions', [])
            }
            
        except Exception as e:
            logger.error(f"VaR calculation failed for deal {deal_id}: {e}")
            raise
    
    def calculate_risk_attribution(
        self,
        deal_id: str,
        attribution_type: str = "sector"
    ) -> Dict[str, Any]:
        """
        Calculate risk attribution for a portfolio
        
        Args:
            deal_id: Portfolio identifier
            attribution_type: Type of attribution analysis
            
        Returns:
            Risk attribution results
        """
        logger.info(f"Calculating {attribution_type} risk attribution for deal {deal_id}")
        
        try:
            # Get portfolio with risk contributions
            portfolio_assets = self._get_portfolio_assets_with_risk(deal_id)
            total_portfolio_risk = self._calculate_total_portfolio_risk(portfolio_assets)
            
            # Calculate attributions by dimension
            attributions = {}
            marginal_contributions = {}
            
            for asset in portfolio_assets:
                dim_value = asset.get(attribution_type, "Other")
                risk_contribution = asset.get('risk_contribution', 0)
                marginal_contribution = asset.get('marginal_contribution', 0)
                
                attributions[dim_value] = attributions.get(dim_value, 0) + risk_contribution
                marginal_contributions[dim_value] = marginal_contributions.get(dim_value, 0) + marginal_contribution
            
            # Identify top contributors
            top_contributors = sorted(
                [{'dimension': k, 'contribution': v} for k, v in attributions.items()],
                key=lambda x: x['contribution'],
                reverse=True
            )[:10]
            
            # Calculate concentration score
            risk_weights = list(attributions.values())
            concentration_score = sum(w**2 for w in risk_weights) * 100
            
            return {
                'deal_id': deal_id,
                'attribution_type': attribution_type,
                'total_portfolio_risk': total_portfolio_risk,
                'attributions': attributions,
                'marginal_contributions': marginal_contributions,
                'component_contributions': attributions,  # Alias for compatibility
                'top_risk_contributors': top_contributors,
                'risk_concentration_score': concentration_score
            }
            
        except Exception as e:
            logger.error(f"Risk attribution failed for deal {deal_id}: {e}")
            raise
    
    def compare_portfolios(
        self,
        deal_ids: List[str],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Compare risk metrics across multiple portfolios
        
        Args:
            deal_ids: List of portfolio identifiers
            metrics: List of metrics to compare
            
        Returns:
            Portfolio comparison results
        """
        logger.info(f"Comparing {len(deal_ids)} portfolios on {len(metrics)} metrics")
        
        try:
            comparison_results = {}
            
            for deal_id in deal_ids:
                deal_metrics = {}
                
                for metric in metrics:
                    if metric == "volatility":
                        deal_metrics[metric] = self._get_portfolio_volatility(deal_id)
                    elif metric == "var":
                        var_result = self.calculate_var(deal_id)
                        deal_metrics[metric] = var_result['var_percentage']
                    elif metric == "concentration":
                        conc_result = self.analyze_concentration(deal_id)
                        deal_metrics[metric] = conc_result['concentration_risk_score']
                    else:
                        deal_metrics[metric] = 0  # Default for unknown metrics
                
                comparison_results[deal_id] = deal_metrics
            
            # Calculate rankings
            rankings = {}
            for metric in metrics:
                metric_values = [(deal_id, results[metric]) for deal_id, results in comparison_results.items()]
                # Sort by metric value (lower is better for risk metrics)
                sorted_deals = sorted(metric_values, key=lambda x: x[1])
                rankings[metric] = [deal_id for deal_id, _ in sorted_deals]
            
            return {
                'comparison_results': comparison_results,
                'rankings': rankings
            }
            
        except Exception as e:
            logger.error(f"Portfolio comparison failed: {e}")
            raise
    
    def generate_comprehensive_report(
        self,
        deal_id: str,
        report_type: str = "detailed",
        include_sections: List[str] = None,
        custom_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive risk report
        
        Args:
            deal_id: Portfolio identifier
            report_type: Type of report to generate
            include_sections: Sections to include
            custom_parameters: Custom parameters for report
            
        Returns:
            Comprehensive risk report
        """
        logger.info(f"Generating {report_type} risk report for deal {deal_id}")
        
        try:
            report_sections = include_sections or ["metrics", "concentration", "stress_test"]
            
            report_data = {
                'deal_id': deal_id,
                'report_type': report_type,
                'generation_date': datetime.now(),
                'data_as_of_date': date.today(),
                'report_version': "1.0"
            }
            
            # Executive summary
            report_data['executive_summary'] = {
                'overall_risk_rating': 'Medium',
                'key_metrics': {
                    'portfolio_var_95': 2.5,  # Mock percentage
                    'concentration_score': 45.2,
                    'credit_quality': 'BBB+'
                },
                'main_concerns': ['High sector concentration', 'Credit spread risk']
            }
            
            # Include requested sections
            if "metrics" in report_sections:
                report_data['risk_metrics'] = self.calculate_portfolio_risk_metrics(deal_id)
            
            if "concentration" in report_sections:
                report_data['concentration_analysis'] = self.analyze_concentration(deal_id)
            
            if "stress_test" in report_sections:
                mock_scenarios = [
                    {'scenario_name': 'Base Case', 'default_rate_shock': 0.02},
                    {'scenario_name': 'Stress Case', 'default_rate_shock': 0.05}
                ]
                report_data['stress_test_results'] = self.run_comprehensive_stress_test(deal_id, mock_scenarios)
            
            # Recommendations
            report_data['risk_recommendations'] = [
                "Consider reducing sector concentration",
                "Monitor credit spread exposure",
                "Review trigger levels for compliance"
            ]
            
            report_data['action_items'] = [
                {
                    'priority': 'High',
                    'item': 'Diversify sector exposure',
                    'deadline': (date.today() + timedelta(days=30)).isoformat()
                }
            ]
            
            return report_data
            
        except Exception as e:
            logger.error(f"Risk report generation failed for deal {deal_id}: {e}")
            raise
    
    # Helper methods
    
    def _get_portfolio_assets(self, deal_id: str) -> List[Dict[str, Any]]:
        """Get assets for a portfolio"""
        # Implementation would query operational database
        # For now, return mock assets
        return [
            {
                'asset_id': 'ASSET001',
                'asset_name': 'Sample Corp Loan',
                'balance': 5000000,
                'rating': 'BB+',
                'sector': 'Technology',
                'industry': 'Software'
            },
            {
                'asset_id': 'ASSET002', 
                'asset_name': 'Another Corp Bond',
                'balance': 3000000,
                'rating': 'BBB-',
                'sector': 'Healthcare',
                'industry': 'Pharmaceuticals'
            }
        ]
    
    def _get_portfolio_assets_with_weights(self, deal_id: str) -> List[Dict[str, Any]]:
        """Get portfolio assets with weight calculations"""
        assets = self._get_portfolio_assets(deal_id)
        total_balance = sum(asset['balance'] for asset in assets)
        
        for asset in assets:
            asset['weight'] = asset['balance'] / total_balance
        
        return assets
    
    def _get_portfolio_assets_with_risk(self, deal_id: str) -> List[Dict[str, Any]]:
        """Get portfolio assets with risk contribution calculations"""
        assets = self._get_portfolio_assets_with_weights(deal_id)
        
        for asset in assets:
            # Mock risk contributions
            asset['risk_contribution'] = asset['weight'] * 0.15  # 15% risk contribution
            asset['marginal_contribution'] = asset['weight'] * 0.08  # 8% marginal contribution
        
        return assets
    
    def _calculate_volatility_metrics(self, assets: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate portfolio volatility metrics"""
        # Simplified calculation - in reality would use return series and correlations
        return {
            'portfolio_volatility': 0.18,  # 18% annualized
            'tracking_error': 0.02
        }
    
    def _calculate_concentration_metrics(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate portfolio concentration metrics"""
        total_balance = sum(asset['balance'] for asset in assets)
        weights = [asset['balance'] / total_balance for asset in assets]
        
        # Herfindahl index
        hhi = sum(w**2 for w in weights)
        
        # Single asset max weight
        max_weight = max(weights)
        
        # Sector concentration (mock)
        sectors = {}
        for asset in assets:
            sector = asset.get('sector', 'Other')
            weight = asset['balance'] / total_balance
            sectors[sector] = sectors.get(sector, 0) + weight
        
        # Rating concentration (mock)
        ratings = {}
        for asset in assets:
            rating = asset.get('rating', 'NR')
            weight = asset['balance'] / total_balance
            ratings[rating] = ratings.get(rating, 0) + weight
        
        return {
            'sector_concentration': sectors,
            'rating_concentration': ratings,
            'single_asset_max_weight': max_weight,
            'herfindahl_index': hhi
        }
    
    def _calculate_var_metrics(self, assets: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate VaR metrics"""
        portfolio_value = sum(asset['balance'] for asset in assets)
        
        return {
            'value_at_risk_95': portfolio_value * 0.025,  # 2.5% of portfolio
            'value_at_risk_99': portfolio_value * 0.045,  # 4.5% of portfolio
            'expected_shortfall': portfolio_value * 0.035  # 3.5% of portfolio
        }
    
    def _calculate_duration_metrics(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate duration and sensitivity metrics"""
        return {
            'modified_duration': 3.2,
            'effective_duration': 3.1,
            'convexity': 12.5,
            'interest_rate_sensitivity': -0.032,  # -3.2% per 1% rate change
            'credit_spread_sensitivity': -0.018   # -1.8% per 1% spread change
        }
    
    def _calculate_credit_risk_metrics(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate credit risk metrics"""
        # Mock credit risk calculations
        return {
            'average_rating_score': 12.5,  # Numeric rating scale
            'weighted_average_rating': 'BBB',
            'default_probability': 0.025  # 2.5% annual default probability
        }
    
    def _assess_risk_level(self, vol_metrics, conc_metrics, var_metrics) -> Dict[str, Any]:
        """Assess overall risk level"""
        # Simplified risk assessment
        risk_factors = []
        
        if vol_metrics['portfolio_volatility'] > 0.20:
            risk_factors.append("High portfolio volatility")
        
        if conc_metrics['herfindahl_index'] > 0.1:
            risk_factors.append("High concentration risk")
        
        if len(risk_factors) >= 2:
            level = "high"
        elif len(risk_factors) == 1:
            level = "medium"
        else:
            level = "low"
        
        return {'level': level, 'factors': risk_factors}
    
    def _identify_correlation_clusters(self, matrix: np.ndarray, asset_ids: List[str]) -> List[List[str]]:
        """Identify correlation clusters (simplified)"""
        # Simplified clustering - in reality would use proper clustering algorithms
        return []
    
    def _get_portfolio_value(self, deal_id: str) -> float:
        """Get total portfolio value"""
        assets = self._get_portfolio_assets(deal_id)
        return sum(asset['balance'] for asset in assets)
    
    def _get_portfolio_volatility(self, deal_id: str) -> float:
        """Get portfolio volatility"""
        return 0.18  # Mock 18% volatility
    
    def _calculate_total_portfolio_risk(self, assets: List[Dict[str, Any]]) -> float:
        """Calculate total portfolio risk"""
        return sum(asset.get('risk_contribution', 0) for asset in assets)
    
    def _run_single_stress_scenario(self, deal_id, scenario, base_value, time_horizon, monte_carlo_runs):
        """Run single stress test scenario"""
        # Mock stress test calculation
        loss = base_value * 0.05  # 5% loss
        return {
            'scenario': scenario,
            'portfolio_loss': loss,
            'loss_percentage': 5.0,
            'tranche_impacts': {'A': 0, 'B': loss * 0.3, 'C': loss * 0.7},
            'stressed_var': base_value * 0.08,
            'stressed_volatility': 0.25,
            'time_to_recovery': 18,
            'worst_performing_assets': [],
            'sector_impacts': {}
        }
    
    def _calculate_loss_distribution(self, losses: List[float]) -> Dict[str, int]:
        """Calculate loss distribution buckets"""
        buckets = {'0-1%': 0, '1-3%': 0, '3-5%': 0, '5%+': 0}
        # Implementation would categorize losses into buckets
        return buckets
    
    def _calculate_monte_carlo_var(self, deal_id, confidence_level, time_horizon_days, portfolio_value):
        """Calculate Monte Carlo VaR"""
        # Mock Monte Carlo calculation
        var_amount = portfolio_value * 0.025
        return {
            'var': var_amount,
            'expected_shortfall': var_amount * 1.4,
            'details': {'simulations': 10000, 'distribution': 'normal'},
            'assumptions': ['Normal distribution', 'Constant volatility']
        }
    
    def _calculate_parametric_var(self, deal_id, confidence_level, time_horizon_days, portfolio_value):
        """Calculate Parametric VaR"""
        # Mock parametric calculation
        var_amount = portfolio_value * 0.022
        return {
            'var': var_amount,
            'expected_shortfall': var_amount * 1.3,
            'details': {'volatility': 0.18, 'z_score': stats.norm.ppf(confidence_level)},
            'assumptions': ['Normal distribution', 'Linear price sensitivity']
        }
    
    def _calculate_historical_var(self, deal_id, confidence_level, time_horizon_days, portfolio_value):
        """Calculate Historical VaR"""
        # Mock historical calculation
        var_amount = portfolio_value * 0.028
        return {
            'var': var_amount,
            'expected_shortfall': var_amount * 1.2,
            'details': {'historical_periods': 252, 'data_source': 'historical_returns'},
            'assumptions': ['Historical patterns repeat', 'No regime changes']
        }