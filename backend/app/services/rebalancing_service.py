"""
Rebalancing Service

Service layer for portfolio rebalancing operations.
Provides high-level API for optimizing CLO portfolios through
intelligent asset selection and trading recommendations.

Author: Claude
Date: 2025-01-12
"""

from typing import List, Dict, Optional, Any, Callable
from datetime import date, datetime
import logging
from sqlalchemy.orm import Session
import pandas as pd

from ..models.rebalancing import (
    PortfolioRebalancer, 
    RebalanceInputs, 
    RebalanceResults,
    TransactionType,
    create_rebalance_inputs_from_config
)
from ..models.base import get_db_session
from ..models.portfolio import Portfolio
from ..models.asset import Asset
from ..core.exceptions import CLOBusinessError, CLOValidationError

logger = logging.getLogger(__name__)


class RebalancingService:
    """Service for portfolio rebalancing and optimization"""
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize rebalancing service"""
        self.db = db_session or get_db_session()
        self.rebalancer = PortfolioRebalancer()
        self.current_operation_id: Optional[str] = None
    
    def run_portfolio_rebalancing(
        self,
        portfolio_id: str,
        rebalance_config: Dict[str, Any],
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive portfolio rebalancing
        
        Args:
            portfolio_id: Portfolio identifier
            rebalance_config: Rebalancing configuration parameters
            progress_callback: Optional progress callback function
            
        Returns:
            Rebalancing results dictionary
        """
        try:
            logger.info(f"Starting portfolio rebalancing for portfolio {portfolio_id}")
            
            # Set progress callback
            if progress_callback:
                self.rebalancer.set_progress_callback(progress_callback)
            
            # Validate and parse configuration
            config = self._parse_rebalance_config(rebalance_config)
            
            # Get portfolio and collateral data
            portfolio = self._get_portfolio(portfolio_id)
            collateral_pool = self._create_collateral_pool(portfolio)
            all_collateral = self._get_all_collateral()
            
            # Validate rebalancing parameters
            self._validate_rebalancing_parameters(config, collateral_pool)
            
            # Get account balances if available
            accounts = self._get_account_balances(portfolio)
            
            # Execute rebalancing
            results = self.rebalancer.run_rebalancing(
                portfolio=collateral_pool,
                all_collateral=all_collateral,
                config=config,
                accounts=accounts
            )
            
            # Store results
            operation_id = self._store_rebalancing_results(portfolio_id, config, results)
            
            # Format response
            response = {
                "operation_id": operation_id,
                "portfolio_id": portfolio_id,
                "success": True,
                "results": self._format_rebalancing_results(results),
                "execution_summary": {
                    "objective_improvement": results.total_improvement,
                    "total_trades": len(results.sale_trades) + len(results.buy_trades),
                    "total_sale_amount": results.total_sale_amount,
                    "total_buy_amount": results.total_buy_amount,
                    "execution_time": results.execution_stats.get("duration_seconds", 0),
                    "warnings": results.warnings
                }
            }
            
            logger.info(f"Portfolio rebalancing completed for {portfolio_id}")
            return response
            
        except CLOValidationError as e:
            logger.error(f"Rebalancing validation error: {str(e)}")
            raise
        except CLOBusinessError as e:
            logger.error(f"Rebalancing business error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Rebalancing failed: {str(e)}")
            raise CLOBusinessError(f"Rebalancing failed: {str(e)}") from e
    
    def run_asset_ranking(
        self,
        portfolio_id: str,
        ranking_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run asset ranking analysis for buy/sell decisions
        
        Args:
            portfolio_id: Portfolio identifier
            ranking_config: Ranking configuration
            
        Returns:
            Asset ranking results
        """
        try:
            logger.info(f"Starting asset ranking for portfolio {portfolio_id}")
            
            # Parse configuration
            transaction_type = TransactionType.BUY
            if ranking_config.get('transaction_type', 'BUY').upper() == 'SELL':
                transaction_type = TransactionType.SELL
            
            filter_expression = ranking_config.get('filter_expression', '')
            max_assets = ranking_config.get('max_assets', 50)
            loan_size = ranking_config.get('incremental_loan_size', 1000000.0)
            
            # Get data
            portfolio = self._get_portfolio(portfolio_id)
            
            if transaction_type == TransactionType.SELL:
                # Rank assets in current portfolio
                asset_pool = self._create_collateral_pool(portfolio)
            else:
                # Rank assets from all available collateral
                asset_pool = self._get_all_collateral()
            
            # Create temporary config for ranking
            temp_config = RebalanceInputs(
                transaction_type=transaction_type,
                max_num_assets=max_assets,
                incremental_loan_size=loan_size,
                buy_filter=filter_expression if transaction_type == TransactionType.BUY else '',
                sale_filter=filter_expression if transaction_type == TransactionType.SELL else ''
            )
            
            # Get rankings
            ranked_assets = self.rebalancer._rank_assets_for_transaction(
                asset_pool=asset_pool,
                transaction_type=transaction_type,
                filter_expression=filter_expression,
                target_amount=loan_size,
                config=temp_config
            )
            
            # Format results
            rankings = []
            for i, asset_info in enumerate(ranked_assets[:max_assets], 1):
                asset = asset_info['asset']
                rankings.append({
                    "rank": i,
                    "asset_id": asset_info['asset_id'],
                    "asset_name": getattr(asset, 'issue_name', f"Asset {asset_info['asset_id']}"),
                    "objective_score": asset_info['objective_score'],
                    "par_amount": asset_info.get('par_amount', 0),
                    "current_price": getattr(asset, 'market_price', 100.0),
                    "spread": getattr(asset, 'spread', 0.0),
                    "rating": getattr(asset, 'sp_rating', 'NR'),
                    "maturity": getattr(asset, 'maturity_date', None),
                    "industry": getattr(asset, 'sp_industry', 'Unknown')
                })
            
            return {
                "portfolio_id": portfolio_id,
                "transaction_type": transaction_type.name,
                "filter_expression": filter_expression,
                "total_candidates": len(ranked_assets),
                "rankings": rankings,
                "summary": {
                    "top_score": rankings[0]["objective_score"] if rankings else 0,
                    "bottom_score": rankings[-1]["objective_score"] if rankings else 0,
                    "avg_score": sum(r["objective_score"] for r in rankings) / len(rankings) if rankings else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Asset ranking failed: {str(e)}")
            raise CLOBusinessError(f"Asset ranking failed: {str(e)}") from e
    
    def cancel_rebalancing(self, operation_id: str) -> Dict[str, Any]:
        """
        Cancel an ongoing rebalancing operation
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Cancellation status
        """
        try:
            if self.current_operation_id == operation_id:
                self.rebalancer.cancel_operation()
                logger.info(f"Rebalancing operation {operation_id} cancelled")
                return {
                    "operation_id": operation_id,
                    "cancelled": True,
                    "message": "Rebalancing operation cancelled successfully"
                }
            else:
                return {
                    "operation_id": operation_id,
                    "cancelled": False,
                    "message": "Operation not found or already completed"
                }
                
        except Exception as e:
            logger.error(f"Error cancelling operation {operation_id}: {str(e)}")
            raise CLOBusinessError(f"Cancellation failed: {str(e)}") from e
    
    def get_rebalancing_results(self, operation_id: str) -> Dict[str, Any]:
        """
        Retrieve stored rebalancing results
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Rebalancing results
        """
        try:
            # This would retrieve from database in real implementation
            logger.info(f"Retrieving rebalancing results for operation {operation_id}")
            
            # Mock response for now
            return {
                "operation_id": operation_id,
                "status": "completed",
                "message": "Results retrieval not implemented - would fetch from database"
            }
            
        except Exception as e:
            logger.error(f"Error retrieving results for {operation_id}: {str(e)}")
            raise CLOBusinessError(f"Results retrieval failed: {str(e)}") from e
    
    def export_rebalancing_results(
        self,
        operation_id: str,
        format_type: str = "excel"
    ) -> str:
        """
        Export rebalancing results to file
        
        Args:
            operation_id: Operation identifier
            format_type: Export format (excel, csv, json)
            
        Returns:
            File path or data
        """
        try:
            logger.info(f"Exporting rebalancing results for {operation_id} as {format_type}")
            
            # This would export actual results in real implementation
            filename = f"rebalancing_results_{operation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
            
            # Mock export
            if format_type.lower() == "excel":
                return self._create_mock_excel_export(operation_id, filename)
            elif format_type.lower() == "csv":
                return self._create_mock_csv_export(operation_id)
            else:
                return '{"message": "Export functionality not fully implemented"}'
                
        except Exception as e:
            logger.error(f"Export failed for {operation_id}: {str(e)}")
            raise CLOBusinessError(f"Export failed: {str(e)}") from e
    
    def _parse_rebalance_config(self, config_dict: Dict[str, Any]) -> RebalanceInputs:
        """Parse and validate rebalancing configuration"""
        try:
            return create_rebalance_inputs_from_config(config_dict)
        except Exception as e:
            raise CLOValidationError(f"Invalid rebalancing configuration: {str(e)}") from e
    
    def _get_portfolio(self, portfolio_id: str) -> Portfolio:
        """Get portfolio from database"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id
        ).first()
        
        if not portfolio:
            raise CLOValidationError(f"Portfolio not found: {portfolio_id}")
        
        return portfolio
    
    def _create_collateral_pool(self, portfolio: Portfolio) -> Any:
        """Create collateral pool from portfolio"""
        # Mock collateral pool for now
        class MockCollateralPool:
            def __init__(self, portfolio: Portfolio):
                self.portfolio = portfolio
                self.assets = {asset.id: asset for asset in portfolio.assets}
                self.total_par_amount = sum(asset.par_amount for asset in portfolio.assets)
                self.num_assets = len(self.assets)
            
            def get_objective_value(self) -> float:
                # Mock objective calculation
                return 45.0 + len(self.assets) * 0.1
            
            def get_test_results(self) -> Dict[str, Any]:
                return {
                    "oc_ratio": 1.15,
                    "ic_ratio": 1.20,
                    "diversity_score": 85.0
                }
            
            def get_collateral_par_amount(self, filter_expr: str) -> float:
                return self.total_par_amount * 0.5  # Mock 50% available
            
            def num_of_assets(self, filter_expr: str) -> int:
                return self.num_assets // 2  # Mock 50% available
            
            def apply_filter(self, filter_expr: str) -> Dict[str, Any]:
                # Simple mock filtering
                return {
                    asset_id: asset for asset_id, asset in self.assets.items()
                    if len(asset_id) > 5  # Simple mock filter
                }
            
            def sale_asset(self, asset: Any) -> None:
                # Mock sale operation
                if hasattr(asset, 'par_amount'):
                    self.total_par_amount -= asset.par_amount
                    self.num_assets -= 1
            
            def purchase_asset(self, asset: Any) -> None:
                # Mock purchase operation
                if hasattr(asset, 'par_amount'):
                    self.total_par_amount += asset.par_amount
                    self.num_assets += 1
        
        return MockCollateralPool(portfolio)
    
    def _get_all_collateral(self) -> Any:
        """Get universe of all available collateral"""
        # Mock all collateral pool
        class MockAllCollateral:
            def __init__(self):
                self.assets = {}
                # Create mock assets
                for i in range(1000):
                    asset_id = f"ASSET_{i:06d}"
                    self.assets[asset_id] = self._create_mock_asset(asset_id, i)
            
            def _create_mock_asset(self, asset_id: str, index: int):
                import random
                random.seed(hash(asset_id) % 2**32)  # Deterministic based on asset_id
                
                class MockAsset:
                    def __init__(self, asset_id: str, index: int):
                        self.id = asset_id
                        self.issue_name = f"Mock Asset {index}"
                        self.par_amount = random.uniform(1000000, 10000000)
                        self.market_price = random.uniform(95, 105)
                        self.spread = random.uniform(0.02, 0.08)
                        ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']
                        self.sp_rating = random.choice(ratings)
                        from datetime import timedelta
                        base_date = date.today()
                        self.maturity_date = base_date + timedelta(days=random.randint(365, 3650))
                        industries = ['Technology', 'Healthcare', 'Energy', 'Finance', 'Consumer']
                        self.sp_industry = random.choice(industries)
                
                return MockAsset(asset_id, index)
            
            def get_asset_ids(self) -> List[str]:
                return list(self.assets.keys())
            
            def get_asset(self, asset_id: str) -> Any:
                return self.assets.get(asset_id)
            
            def apply_filter(self, filter_expr: str) -> Dict[str, Any]:
                # Simple mock filtering
                return {
                    asset_id: asset for asset_id, asset in self.assets.items()
                    if hash(asset_id) % 3 == 0  # Return ~1/3 of assets
                }
        
        return MockAllCollateral()
    
    def _validate_rebalancing_parameters(
        self, 
        config: RebalanceInputs, 
        portfolio: Any
    ) -> None:
        """Validate rebalancing parameters against portfolio"""
        # Check sale amount availability
        if config.sale_par_amount > 0:
            available = portfolio.get_collateral_par_amount(config.sale_filter)
            if config.sale_par_amount > available:
                raise CLOValidationError(
                    f"Cannot sell ${config.sale_par_amount:,.0f}. "
                    f"Only ${available:,.0f} available under filter criteria."
                )
        
        # Validate filters
        if not config.buy_filter and config.buy_par_amount > 0:
            logger.warning("No buy filter specified for purchase operations")
        
        if not config.sale_filter and config.sale_par_amount > 0:
            logger.warning("No sale filter specified for sale operations")
    
    def _get_account_balances(self, portfolio: Portfolio) -> Dict:
        """Get account balances for portfolio"""
        # Mock account balances
        return {
            "Collection": 50000000.0,   # $50M available cash
            "Principal": 40000000.0,    # $40M for purchases
            "Interest": 5000000.0,      # $5M interest account
            "Reserve": 10000000.0       # $10M reserve
        }
    
    def _store_rebalancing_results(
        self, 
        portfolio_id: str, 
        config: RebalanceInputs, 
        results: RebalanceResults
    ) -> str:
        """Store rebalancing results in database"""
        # Generate operation ID
        operation_id = f"REBAL_{portfolio_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_operation_id = operation_id
        
        # In real implementation, this would store to database
        logger.info(f"Stored rebalancing results with operation ID: {operation_id}")
        
        return operation_id
    
    def _format_rebalancing_results(self, results: RebalanceResults) -> Dict[str, Any]:
        """Format rebalancing results for API response"""
        return {
            "objective_improvement": {
                "before": results.before_objective,
                "after_sale": results.after_sale_objective,
                "after_buy": results.after_buy_objective,
                "total_improvement": results.total_improvement
            },
            "trades": {
                "sales": [self._format_trade(trade) for trade in results.sale_trades],
                "purchases": [self._format_trade(trade) for trade in results.buy_trades]
            },
            "compliance_metrics": {
                "before": results.compliance_before,
                "after_sale": results.compliance_after_sale,
                "after_buy": results.compliance_after_buy
            },
            "execution_stats": results.execution_stats,
            "warnings": results.warnings
        }
    
    def _format_trade(self, trade) -> Dict[str, Any]:
        """Format individual trade for API response"""
        return {
            "asset_id": trade.asset_id,
            "asset_name": trade.asset_name,
            "transaction_type": trade.transaction_type.name,
            "par_amount": trade.par_amount,
            "price": trade.price,
            "objective_score": trade.objective_score,
            "rationale": trade.rationale
        }
    
    def _create_mock_excel_export(self, operation_id: str, filename: str) -> str:
        """Create mock Excel export"""
        # In real implementation, this would create actual Excel file
        logger.info(f"Created mock Excel export: {filename}")
        return filename
    
    def _create_mock_csv_export(self, operation_id: str) -> str:
        """Create mock CSV export"""
        csv_data = "asset_id,transaction_type,par_amount,price,objective_score\n"
        csv_data += "MOCK001,BUY,1000000,100.5,0.85\n"
        csv_data += "MOCK002,SELL,2000000,99.2,0.35\n"
        return csv_data