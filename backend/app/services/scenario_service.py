"""
Scenario Analysis Service
Handles scenario management, analysis, and custom scenario creation
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import logging
import json

from sqlalchemy.orm import Session
from ..core.database_config import db_config
from ..services.data_integration import DataIntegrationService

logger = logging.getLogger(__name__)

class ScenarioService:
    """Service for scenario analysis and management"""
    
    def __init__(self):
        self.integration_service = DataIntegrationService()
        
    def create_scenario(
        self,
        name: str,
        description: str,
        scenario_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new custom scenario
        
        Args:
            name: Scenario name
            description: Scenario description
            scenario_type: Type of scenario (custom, stress, etc.)
            parameters: Scenario parameters
            
        Returns:
            Created scenario data
        """
        logger.info(f"Creating scenario: {name}")
        
        try:
            # Validate parameters
            self._validate_scenario_parameters(parameters)
            
            # Create scenario record in operational database
            scenario_id = self._generate_scenario_id(name)
            
            scenario_data = {
                'id': scenario_id,
                'name': name,
                'description': description,
                'scenario_type': scenario_type,
                'created_date': datetime.now(),
                'is_active': True,
                'parameter_count': len(parameters),
                'parameters': parameters
            }
            
            # Store in operational database
            self._store_scenario(scenario_data)
            
            logger.info(f"Successfully created scenario {scenario_id}")
            return scenario_data
            
        except Exception as e:
            logger.error(f"Failed to create scenario {name}: {e}")
            raise
    
    def update_scenario(
        self,
        scenario_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing scenario
        
        Args:
            scenario_id: Scenario identifier
            updates: Fields to update
            
        Returns:
            Updated scenario data or None if not found
        """
        logger.info(f"Updating scenario: {scenario_id}")
        
        try:
            # Get existing scenario
            existing_scenario = self._get_custom_scenario(scenario_id)
            
            if not existing_scenario:
                return None
            
            # Apply updates
            for field, value in updates.items():
                if field in ['name', 'description', 'is_active', 'parameters']:
                    existing_scenario[field] = value
            
            existing_scenario['updated_date'] = datetime.now()
            
            # Update in database
            self._store_scenario(existing_scenario)
            
            logger.info(f"Successfully updated scenario {scenario_id}")
            return existing_scenario
            
        except Exception as e:
            logger.error(f"Failed to update scenario {scenario_id}: {e}")
            raise
    
    def delete_scenario(self, scenario_id: str) -> bool:
        """
        Delete a scenario (soft delete)
        
        Args:
            scenario_id: Scenario identifier
            
        Returns:
            True if deleted successfully
        """
        logger.info(f"Deleting scenario: {scenario_id}")
        
        try:
            # Check if scenario exists
            scenario = self._get_custom_scenario(scenario_id)
            
            if not scenario:
                return False
            
            # Soft delete - mark as inactive
            scenario['is_active'] = False
            scenario['deleted_date'] = datetime.now()
            
            # Update in database
            self._store_scenario(scenario)
            
            logger.info(f"Successfully deleted scenario {scenario_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete scenario {scenario_id}: {e}")
            raise
    
    def run_scenario_analysis(
        self,
        scenario_id: str,
        deal_ids: List[str],
        analysis_type: str = "comprehensive",
        time_horizon: int = 60,
        custom_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive scenario analysis
        
        Args:
            scenario_id: Scenario identifier
            deal_ids: List of deal identifiers
            analysis_type: Type of analysis to run
            time_horizon: Analysis time horizon in months
            custom_parameters: Additional analysis parameters
            
        Returns:
            Scenario analysis results
        """
        logger.info(f"Running {analysis_type} scenario analysis for scenario {scenario_id}")
        
        try:
            # Get scenario parameters
            scenario_params = self._get_scenario_parameters(scenario_id)
            
            if not scenario_params:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            # Analyze each deal
            portfolio_impacts = []
            
            for deal_id in deal_ids:
                impact = self._analyze_deal_under_scenario(
                    deal_id, 
                    scenario_params, 
                    time_horizon,
                    custom_parameters
                )
                portfolio_impacts.append(impact)
            
            # Calculate aggregated results
            total_impact = sum(impact['value_change'] for impact in portfolio_impacts)
            weighted_impact = total_impact / len(portfolio_impacts) if portfolio_impacts else 0
            
            # Calculate risk metrics under scenario
            risk_metrics = self._calculate_scenario_risk_metrics(portfolio_impacts)
            
            # Generate cash flow impacts if requested
            cash_flow_impacts = None
            if analysis_type in ["comprehensive", "cash_flow"]:
                cash_flow_impacts = self._analyze_cash_flow_impacts(deal_ids, scenario_params)
            
            # Generate waterfall impacts if requested
            waterfall_impacts = None
            if analysis_type in ["comprehensive", "waterfall"]:
                waterfall_impacts = self._analyze_waterfall_impacts(deal_ids, scenario_params)
            
            # Generate findings and recommendations
            findings = self._generate_key_findings(portfolio_impacts, risk_metrics)
            warnings = self._identify_risk_warnings(portfolio_impacts, risk_metrics)
            recommendations = self._generate_recommendations(portfolio_impacts, risk_metrics)
            
            return {
                'scenario_id': scenario_id,
                'analysis_date': datetime.now(),
                'deals_analyzed': deal_ids,
                'analysis_type': analysis_type,
                'portfolio_impacts': portfolio_impacts,
                'total_portfolio_impact': float(total_impact),
                'weighted_average_impact': float(weighted_impact),
                'risk_metrics': risk_metrics,
                'cash_flow_impacts': cash_flow_impacts,
                'waterfall_impacts': waterfall_impacts,
                'key_findings': findings,
                'risk_warnings': warnings,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Scenario analysis failed for scenario {scenario_id}: {e}")
            raise
    
    def compare_scenarios(
        self,
        scenario_ids: List[str],
        deal_id: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple scenarios for a deal
        
        Args:
            scenario_ids: List of scenario identifiers
            deal_id: Deal identifier
            metrics: Metrics to compare
            
        Returns:
            Scenario comparison results
        """
        logger.info(f"Comparing {len(scenario_ids)} scenarios for deal {deal_id}")
        
        try:
            # Run analysis for each scenario
            scenario_results = {}
            
            for scenario_id in scenario_ids:
                results = self.run_scenario_analysis(
                    scenario_id, 
                    [deal_id], 
                    "portfolio_impact"
                )
                scenario_results[scenario_id] = results
            
            # Compare metrics
            metric_comparisons = {}
            relative_performance = {}
            scenario_rankings = {}
            
            for metric in metrics:
                metric_values = {}
                
                for scenario_id in scenario_ids:
                    if metric == "portfolio_value":
                        value = scenario_results[scenario_id]['total_portfolio_impact']
                    elif metric == "risk_metrics":
                        value = scenario_results[scenario_id]['risk_metrics']['portfolio_volatility']
                    elif metric == "cash_flows":
                        # Simplified cash flow metric
                        value = abs(scenario_results[scenario_id]['total_portfolio_impact'])
                    else:
                        value = 0
                    
                    metric_values[scenario_id] = value
                
                metric_comparisons[metric] = metric_values
                
                # Calculate relative performance (normalized to 0-100)
                values = list(metric_values.values())
                min_val, max_val = min(values), max(values)
                
                if max_val > min_val:
                    relative_scores = {
                        scenario_id: ((value - min_val) / (max_val - min_val)) * 100
                        for scenario_id, value in metric_values.items()
                    }
                else:
                    relative_scores = {scenario_id: 50 for scenario_id in scenario_ids}
                
                relative_performance[metric] = relative_scores
                
                # Rank scenarios by metric (best to worst)
                ranked = sorted(metric_values.items(), key=lambda x: x[1], reverse=True)
                scenario_rankings[metric] = [scenario_id for scenario_id, _ in ranked]
            
            # Determine best/worst/recommended scenarios
            best_scenario = self._determine_best_scenario(metric_comparisons, metrics)
            worst_scenario = self._determine_worst_scenario(metric_comparisons, metrics)
            recommended_scenario = self._determine_recommended_scenario(scenario_results)
            
            return {
                'scenarios': scenario_ids,
                'deal_id': deal_id,
                'metrics_compared': metrics,
                'metric_comparisons': metric_comparisons,
                'relative_performance': relative_performance,
                'scenario_rankings': scenario_rankings,
                'best_performing_scenario': best_scenario,
                'worst_performing_scenario': worst_scenario,
                'recommended_scenario': recommended_scenario['scenario'],
                'recommendation_reason': recommended_scenario['reason']
            }
            
        except Exception as e:
            logger.error(f"Scenario comparison failed: {e}")
            raise
    
    def export_scenario_data(
        self,
        scenario_id: str,
        format: str = "json",
        include_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        Export scenario data in specified format
        
        Args:
            scenario_id: Scenario identifier
            format: Export format (json, excel, csv)
            include_analysis: Whether to include analysis results
            
        Returns:
            Export data
        """
        logger.info(f"Exporting scenario {scenario_id} in {format} format")
        
        try:
            # Get scenario data
            scenario_data = self._get_scenario_parameters(scenario_id)
            
            if not scenario_data:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            export_data = {
                'scenario_id': scenario_id,
                'export_timestamp': datetime.now().isoformat(),
                'format': format,
                'parameters': scenario_data
            }
            
            if include_analysis:
                # Add recent analysis results if available
                export_data['analysis_history'] = self._get_scenario_analysis_history(scenario_id)
            
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export scenario {scenario_id}: {e}")
            raise
    
    # Helper methods
    
    def _validate_scenario_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate scenario parameters"""
        required_categories = ['Economic', 'Market', 'Credit']
        
        for category in required_categories:
            if category not in parameters:
                logger.warning(f"Missing parameter category: {category}")
        
        # Additional validation logic here
    
    def _generate_scenario_id(self, name: str) -> str:
        """Generate unique scenario ID"""
        # Simple ID generation - in production would ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_name = "".join(c for c in name if c.isalnum())[:10]
        return f"SCEN_{safe_name}_{timestamp}"
    
    def _store_scenario(self, scenario_data: Dict[str, Any]) -> None:
        """Store scenario in operational database"""
        # Implementation would store in PostgreSQL scenarios table
        logger.info(f"Stored scenario {scenario_data['id']} in database")
    
    def _get_custom_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get custom scenario from database"""
        # Implementation would query PostgreSQL
        # For now, return None (scenario not found)
        return None
    
    def _get_scenario_parameters(self, scenario_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get scenario parameters (from MAG or custom scenarios)"""
        # Check if it's a MAG scenario first
        mag_scenarios = self.integration_service.get_available_scenarios()
        
        if scenario_id in mag_scenarios:
            return self.integration_service.get_scenario_parameters(scenario_id)
        
        # Otherwise check custom scenarios
        custom_scenario = self._get_custom_scenario(scenario_id)
        if custom_scenario:
            return custom_scenario.get('parameters', [])
        
        return None
    
    def _analyze_deal_under_scenario(
        self,
        deal_id: str,
        scenario_params: List[Dict[str, Any]],
        time_horizon: int,
        custom_parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze single deal under scenario"""
        # Mock analysis - in reality would run sophisticated modeling
        base_value = 450000000  # Mock portfolio value
        
        # Apply scenario shocks
        shock_factor = self._calculate_scenario_shock_factor(scenario_params)
        scenario_value = base_value * (1 - shock_factor)
        
        value_change = scenario_value - base_value
        value_change_percentage = (value_change / base_value) * 100
        
        return {
            'deal_id': deal_id,
            'base_portfolio_value': float(base_value),
            'scenario_portfolio_value': float(scenario_value),
            'value_change': float(value_change),
            'value_change_percentage': float(value_change_percentage),
            'asset_level_impacts': [],  # Mock empty for now
            'sector_impacts': {'Technology': -2.5, 'Healthcare': -1.2},
            'rating_impacts': {'BBB': -1.8, 'BB': -3.2}
        }
    
    def _calculate_scenario_shock_factor(self, scenario_params: List[Dict[str, Any]]) -> float:
        """Calculate aggregate shock factor from scenario parameters"""
        # Simplified shock calculation
        shock_factor = 0.0
        
        for param in scenario_params:
            param_name = param.get('parameter_name', '')
            param_value = param.get('value', 0)
            
            if 'default' in param_name.lower():
                # Default rate parameters contribute to shock
                try:
                    shock_factor += float(param_value) * 0.1
                except (ValueError, TypeError):
                    continue
            elif 'recovery' in param_name.lower():
                # Recovery rate parameters (inverse contribution)
                try:
                    shock_factor -= (1 - float(param_value)) * 0.05
                except (ValueError, TypeError):
                    continue
        
        return max(0, min(shock_factor, 0.5))  # Cap between 0 and 50%
    
    def _calculate_scenario_risk_metrics(self, portfolio_impacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate risk metrics under scenario"""
        if not portfolio_impacts:
            return {}
        
        # Calculate portfolio-level metrics
        value_changes = [impact['value_change_percentage'] for impact in portfolio_impacts]
        
        portfolio_volatility = float(np.std(value_changes) if len(value_changes) > 1 else 0)
        max_loss = float(min(value_changes))
        
        return {
            'portfolio_volatility': portfolio_volatility,
            'value_at_risk': abs(max_loss),
            'expected_shortfall': abs(max_loss) * 1.3,
            'maximum_drawdown': abs(max_loss)
        }
    
    def _analyze_cash_flow_impacts(
        self,
        deal_ids: List[str],
        scenario_params: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze cash flow impacts under scenario"""
        # Mock cash flow analysis
        return [
            {
                'deal_id': deal_id,
                'base_cash_flows': 8000000,
                'scenario_cash_flows': 7200000,
                'impact_percentage': -10.0
            }
            for deal_id in deal_ids
        ]
    
    def _analyze_waterfall_impacts(
        self,
        deal_ids: List[str],
        scenario_params: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze waterfall impacts under scenario"""
        # Mock waterfall analysis
        return [
            {
                'deal_id': deal_id,
                'senior_impact': 0,
                'mezzanine_impact': -5.2,
                'subordinate_impact': -15.8,
                'equity_impact': -35.0
            }
            for deal_id in deal_ids
        ]
    
    def _generate_key_findings(
        self,
        portfolio_impacts: List[Dict[str, Any]],
        risk_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate key findings from analysis"""
        findings = []
        
        avg_impact = sum(p['value_change_percentage'] for p in portfolio_impacts) / len(portfolio_impacts)
        
        if avg_impact < -5:
            findings.append("Scenario shows significant negative portfolio impact")
        elif avg_impact > 5:
            findings.append("Scenario shows positive portfolio impact")
        else:
            findings.append("Scenario shows moderate portfolio impact")
        
        if risk_metrics.get('portfolio_volatility', 0) > 20:
            findings.append("High volatility observed under scenario conditions")
        
        return findings
    
    def _identify_risk_warnings(
        self,
        portfolio_impacts: List[Dict[str, Any]],
        risk_metrics: Dict[str, Any]
    ) -> List[str]:
        """Identify risk warnings from analysis"""
        warnings = []
        
        max_loss = max((abs(p['value_change_percentage']) for p in portfolio_impacts), default=0)
        
        if max_loss > 10:
            warnings.append("Potential for significant portfolio losses under this scenario")
        
        if risk_metrics.get('value_at_risk', 0) > 15:
            warnings.append("Elevated Value at Risk under scenario conditions")
        
        return warnings
    
    def _generate_recommendations(
        self,
        portfolio_impacts: List[Dict[str, Any]],
        risk_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        avg_impact = sum(p['value_change_percentage'] for p in portfolio_impacts) / len(portfolio_impacts)
        
        if avg_impact < -5:
            recommendations.append("Consider hedging strategies to mitigate scenario risk")
            recommendations.append("Review portfolio diversification")
        
        if risk_metrics.get('portfolio_volatility', 0) > 20:
            recommendations.append("Implement volatility management measures")
        
        return recommendations
    
    def _determine_best_scenario(self, metric_comparisons: Dict[str, Dict], metrics: List[str]) -> str:
        """Determine best performing scenario"""
        # Simple implementation - choose scenario with least negative impact
        if 'portfolio_value' in metrics:
            portfolio_values = metric_comparisons['portfolio_value']
            return max(portfolio_values, key=portfolio_values.get)
        
        return list(metric_comparisons.values())[0].keys().__iter__().__next__()
    
    def _determine_worst_scenario(self, metric_comparisons: Dict[str, Dict], metrics: List[str]) -> str:
        """Determine worst performing scenario"""
        # Simple implementation - choose scenario with most negative impact
        if 'portfolio_value' in metrics:
            portfolio_values = metric_comparisons['portfolio_value']
            return min(portfolio_values, key=portfolio_values.get)
        
        return list(metric_comparisons.values())[0].keys().__iter__().__next__()
    
    def _determine_recommended_scenario(self, scenario_results: Dict[str, Any]) -> Dict[str, str]:
        """Determine recommended scenario"""
        # Simple recommendation logic
        scenarios = list(scenario_results.keys())
        
        if scenarios:
            return {
                'scenario': scenarios[0],
                'reason': 'Base case scenario recommended for planning purposes'
            }
        
        return {'scenario': 'None', 'reason': 'No scenarios available'}
    
    def _get_scenario_analysis_history(self, scenario_id: str) -> List[Dict[str, Any]]:
        """Get historical analysis results for scenario"""
        # Mock analysis history
        return [
            {
                'analysis_date': (datetime.now() - timedelta(days=30)).isoformat(),
                'deals_analyzed': 3,
                'total_impact': -2.5
            }
        ]