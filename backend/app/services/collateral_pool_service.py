"""
Collateral Pool Service Layer
Business logic coordination for portfolio management and optimization
"""

from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session

from ..models.collateral_pool import (
    CollateralPool, CollateralPoolAsset, CollateralPoolAccount, ConcentrationTestResult,
    CollateralPoolForCLO, AssetCashFlowForDeal,
    CollateralPoolCalculator, CollateralPoolForCLOCalculator,
    TransactionType, AnalysisType
)
# NOTE: Old VBA-based concentration test imports removed - now using database-driven approach
# from ..models.concentration_test import ConcentrationTest, RatingDerivations, TestSettings
from ..models.asset import Asset
from ..models.clo_deal_engine import Account, AccountType, CashType


class HypoInputs:
    """Hypothesis testing inputs - VBA HypoInputs structure"""
    
    def __init__(self, asset: Asset, transaction: str, price: Decimal):
        self.asset = asset
        self.transaction = transaction.upper()  # BUY, SELL, SALE
        self.price = price


class CollateralPoolService:
    """
    Service layer for collateral pool operations
    Coordinates between models, calculations, and database operations
    """
    
    def __init__(self, db_session: Session):
        """Initialize service with database session"""
        self.db_session = db_session
    
    def create_collateral_pool(self, deal_id: str, pool_name: str, 
                              analysis_date: date, 
                              analysis_type: AnalysisType = AnalysisType.STATIC) -> CollateralPool:
        """Create new collateral pool"""
        pool = CollateralPool(
            deal_id=deal_id,
            pool_name=pool_name,
            analysis_date=analysis_date,
            analysis_type=analysis_type.value,
            use_rating_migration=(analysis_type == AnalysisType.RATING_MIGRATION)
        )
        
        self.db_session.add(pool)
        self.db_session.flush()  # Get ID
        
        return pool
    
    def create_pool_for_clo(self, deal_id: str, parent_pool_id: Optional[int],
                           analysis_date: date) -> CollateralPoolForCLO:
        """Create deal-specific collateral pool"""
        pool = CollateralPoolForCLO(
            deal_id=deal_id,
            parent_pool_id=parent_pool_id,
            analysis_date=analysis_date
        )
        
        self.db_session.add(pool)
        self.db_session.flush()
        
        return pool
    
    def get_pool_calculator(self, pool_id: int) -> CollateralPoolCalculator:
        """Get calculator instance for pool"""
        pool = self.db_session.query(CollateralPool).filter_by(pool_id=pool_id).first()
        if not pool:
            raise ValueError(f"Pool {pool_id} not found")
        
        calculator = CollateralPoolCalculator(pool)
        
        # Load assets
        pool_assets = self.db_session.query(CollateralPoolAsset).filter_by(pool_id=pool_id).all()
        for pool_asset in pool_assets:
            asset = pool_asset.asset
            # Override par amount from pool position
            asset.par_amount = pool_asset.par_amount
            calculator.assets_dict[asset.blkrock_id] = asset
        
        # Load accounts
        pool_accounts = self.db_session.query(CollateralPoolAccount).filter_by(pool_id=pool_id).all()
        for pool_account in pool_accounts:
            account = Account()
            account.principal = Decimal(str(pool_account.principal_proceeds))
            account.interest = Decimal(str(pool_account.interest_proceeds))
            
            account_type = AccountType(pool_account.account_type)
            calculator.accounts_dict[account_type] = account
        
        # Initialize supporting components
        # NOTE: Old VBA-based concentration test initialization removed
        # Now using database-driven concentration test approach
        # calculator.concentration_test = ConcentrationTest()
        # calculator.ratings_derivation = RatingDerivations()
        # calculator.test_settings = TestSettings()
        
        return calculator
    
    def get_pool_for_clo_calculator(self, pool_id: int) -> CollateralPoolForCLOCalculator:
        """Get deal-specific calculator instance"""
        pool = self.db_session.query(CollateralPoolForCLO).filter_by(pool_id=pool_id).first()
        if not pool:
            raise ValueError(f"CLO Pool {pool_id} not found")
        
        calculator = CollateralPoolForCLOCalculator(pool)
        
        # Load assets from parent pool if available
        if pool.parent_pool_id:
            parent_assets = self.db_session.query(CollateralPoolAsset)\
                .filter_by(pool_id=pool.parent_pool_id).all()
            for pool_asset in parent_assets:
                asset = pool_asset.asset
                asset.par_amount = pool_asset.par_amount
                calculator.assets_dict[asset.blkrock_id] = asset
        
        # Initialize supporting components
        # NOTE: Old VBA-based rating derivation removed - now using database-driven approach
        # calculator.ratings_derivation = RatingDerivations()
        
        return calculator
    
    def add_asset_to_pool(self, pool_id: int, asset: Asset, 
                         reduce_cash: bool = False,
                         account_type: Optional[AccountType] = None) -> CollateralPoolAsset:
        """Add asset to collateral pool"""
        # Check if asset already exists
        existing = self.db_session.query(CollateralPoolAsset)\
            .filter_by(pool_id=pool_id, asset_id=asset.asset_id).first()
        
        if existing:
            # Update existing position
            existing.par_amount += asset.par_amount
            existing.updated_at = datetime.now()
            pool_asset = existing
        else:
            # Create new position
            pool_asset = CollateralPoolAsset(
                pool_id=pool_id,
                asset_id=asset.asset_id,
                par_amount=asset.par_amount,
                original_par_amount=asset.par_amount,
                position_date=date.today(),
                is_defaulted=asset.default_asset or False
            )
            self.db_session.add(pool_asset)
        
        # Update pool metrics
        self._update_pool_metrics(pool_id)
        
        # Handle cash reduction if requested
        if reduce_cash and account_type:
            self._reduce_cash_for_purchase(pool_id, asset, account_type)
        
        return pool_asset
    
    def remove_asset_from_pool(self, pool_id: int, blkrock_id: str) -> bool:
        """Remove asset from pool"""
        pool_asset = self.db_session.query(CollateralPoolAsset)\
            .join(Asset).filter(
                CollateralPoolAsset.pool_id == pool_id,
                Asset.blkrock_id == blkrock_id
            ).first()
        
        if pool_asset:
            self.db_session.delete(pool_asset)
            self._update_pool_metrics(pool_id)
            return True
        
        return False
    
    def purchase_asset(self, pool_id: int, asset: Asset, 
                      price: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Purchase asset using available cash
        Returns transaction details including cash impact
        """
        calculator = self.get_pool_calculator(pool_id)
        
        # Calculate purchase details
        purchase_price = price if price else asset.market_value / 100
        if purchase_price > 1:
            purchase_price = purchase_price / 100
        
        purchase_amount = purchase_price * asset.par_amount
        available_cash = calculator.check_account_balance(AccountType.COLLECTION, CashType.PRINCIPAL)
        
        # Check if we can afford full purchase
        affordable_par = asset.par_amount
        if purchase_amount > available_cash:
            affordable_par = available_cash / purchase_price
            purchase_amount = available_cash
        
        # Execute purchase
        purchased_asset = Asset()
        purchased_asset.copy_from(asset)
        purchased_asset.par_amount = affordable_par
        
        # Add to pool
        pool_asset = self.add_asset_to_pool(pool_id, purchased_asset)
        
        # Reduce cash
        self._update_account_cash(pool_id, AccountType.COLLECTION, 
                                CashType.PRINCIPAL, -purchase_amount)
        
        return {
            "asset_id": asset.blkrock_id,
            "par_purchased": float(affordable_par),
            "purchase_price": float(purchase_price),
            "cash_used": float(purchase_amount),
            "remaining_cash": float(available_cash - purchase_amount)
        }
    
    def sell_asset(self, pool_id: int, blkrock_id: str, par_amount: Decimal,
                  price: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Sell asset and add cash proceeds
        Returns transaction details including cash impact
        """
        calculator = self.get_pool_calculator(pool_id)
        
        if blkrock_id not in calculator.assets_dict:
            raise ValueError(f"Asset {blkrock_id} not found in pool")
        
        asset = calculator.assets_dict[blkrock_id]
        
        # Calculate sale details
        sale_price = price if price else asset.market_value / 100
        if sale_price > 1:
            sale_price = sale_price / 100
        
        # Limit sale amount to available position
        actual_sale_amount = min(par_amount, asset.par_amount)
        sale_proceeds = actual_sale_amount * sale_price
        
        # Reduce position
        self._update_asset_position(pool_id, blkrock_id, -actual_sale_amount)
        
        # Add cash proceeds
        self._update_account_cash(pool_id, AccountType.COLLECTION,
                                CashType.PRINCIPAL, sale_proceeds)
        
        return {
            "asset_id": blkrock_id,
            "par_sold": float(actual_sale_amount),
            "sale_price": float(sale_price),
            "cash_received": float(sale_proceeds)
        }
    
    def run_concentration_tests(self, pool_id: int, 
                               save_results: bool = True) -> List[Dict[str, Any]]:
        """Run concentration tests on pool"""
        calculator = self.get_pool_calculator(pool_id)
        
        # Get principal proceeds for testing
        principal_proceeds = calculator.check_account_balance(
            AccountType.COLLECTION, CashType.PRINCIPAL
        )
        
        # Run tests
        calculator.concentration_test.run_test(calculator.assets_dict, principal_proceeds)
        
        # Get results
        test_results = calculator.concentration_test.get_results()
        
        # Save to database if requested
        if save_results:
            self._save_concentration_results(pool_id, test_results)
        
        # Format results
        formatted_results = []
        for result in test_results:
            formatted_results.append({
                "test_number": result.test_number,
                "test_name": result.test_name,
                "threshold": float(result.threshold),
                "result": float(result.result),
                "pass_fail": result.pass_fail,
                "comment": result.pass_fail_comment
            })
        
        return formatted_results
    
    def get_portfolio_rankings(self, pool_id: int, 
                              hypo_inputs: List[HypoInputs]) -> Dict[str, float]:
        """
        Calculate asset rankings for portfolio optimization
        VBA GetRankings() conversion
        """
        calculator = self.get_pool_calculator(pool_id)
        
        # Get baseline objective value
        if calculator.rerun_tests_required:
            principal_proceeds = calculator.check_account_balance(
                AccountType.COLLECTION, CashType.PRINCIPAL
            )
            calculator.concentration_test.run_test(calculator.assets_dict, principal_proceeds)
        
        baseline_objective = calculator.concentration_test.calc_objective_function()
        
        rankings = {}
        
        # Test each hypothesis
        for hypo_input in hypo_inputs:
            asset = hypo_input.asset
            transaction = hypo_input.transaction
            price = hypo_input.price
            
            # Apply transaction
            if transaction == "BUY":
                calculator.purchase_asset(asset, price)
            elif transaction in ["SELL", "SALE"]:
                calculator.sell_asset(asset, price)
            
            # Recalculate objective
            calculator.concentration_test.run_test(calculator.assets_dict, 
                calculator.check_account_balance(AccountType.COLLECTION, CashType.PRINCIPAL))
            new_objective = calculator.concentration_test.calc_objective_function()
            
            # Store ranking (improvement in objective function)
            rankings[asset.blkrock_id] = float(new_objective - baseline_objective)
            
            # Reverse transaction for next test
            if transaction == "BUY":
                calculator.sell_asset(asset, price)
            elif transaction in ["SELL", "SALE"]:
                calculator.purchase_asset(asset, price)
        
        return rankings
    
    def get_hypothesis_outputs(self, pool_id: int, 
                             hypo_inputs: List[HypoInputs]) -> List[List[Any]]:
        """
        Get detailed hypothesis testing outputs
        VBA GetHypoOutputs() conversion
        """
        calculator = self.get_pool_calculator(pool_id)
        
        # Get baseline results
        principal_proceeds = calculator.check_account_balance(
            AccountType.COLLECTION, CashType.PRINCIPAL
        )
        calculator.concentration_test.run_test(calculator.assets_dict, principal_proceeds)
        baseline_results = calculator.concentration_test.get_results()
        baseline_objective = calculator.concentration_test.calc_objective_function()
        
        # Apply all hypotheses
        for hypo_input in hypo_inputs:
            if hypo_input.transaction == "BUY":
                calculator.purchase_asset(hypo_input.asset, hypo_input.price)
            elif hypo_input.transaction in ["SELL", "SALE"]:
                calculator.sell_asset(hypo_input.asset, hypo_input.price)
        
        # Get hypothesis results
        calculator.concentration_test.run_test(calculator.assets_dict, 
            calculator.check_account_balance(AccountType.COLLECTION, CashType.PRINCIPAL))
        hypo_results = calculator.concentration_test.get_results()
        hypo_objective = calculator.concentration_test.calc_objective_function()
        
        # Format output (similar to VBA structure)
        output = []
        
        # Headers
        headers = [
            "Test Num", "Test Name", "Threshold", "Results", "Pass/Fail", "",
            "Hypo Result", "Hypo Pass/Fail", "Differences", "Hypo Comments"
        ]
        output.append(headers)
        
        # Test comparisons
        for i, (baseline, hypo) in enumerate(zip(baseline_results, hypo_results)):
            difference = hypo.result - baseline.result
            
            row = [
                baseline.test_number,
                baseline.test_name,
                float(baseline.threshold),
                float(baseline.result),
                baseline.pass_fail,
                "",
                float(hypo.result),
                hypo.pass_fail,
                float(difference),
                hypo.pass_fail_comment
            ]
            output.append(row)
        
        # Objective function comparison
        objective_row = [
            "", "Objective Function", "", float(baseline_objective), "",
            "", float(hypo_objective), "", float(hypo_objective - baseline_objective), ""
        ]
        output.append(objective_row)
        
        return output
    
    def get_pool_summary(self, pool_id: int) -> Dict[str, Any]:
        """Get comprehensive pool summary"""
        pool = self.db_session.query(CollateralPool).filter_by(pool_id=pool_id).first()
        if not pool:
            raise ValueError(f"Pool {pool_id} not found")
        
        calculator = self.get_pool_calculator(pool_id)
        
        # Asset summary
        total_par = sum(asset.par_amount for asset in calculator.assets_dict.values())
        total_market_value = sum(asset.market_value * asset.par_amount / 100 
                               for asset in calculator.assets_dict.values())
        
        # Account summary
        cash_summary = {}
        for account_type, account in calculator.accounts_dict.items():
            cash_summary[account_type.value] = {
                "principal": float(account.principal),
                "interest": float(account.interest),
                "total": float(account.total_proceeds)
            }
        
        return {
            "pool_id": pool_id,
            "pool_name": pool.pool_name,
            "analysis_date": pool.analysis_date.isoformat(),
            "total_assets": len(calculator.assets_dict),
            "total_par_amount": float(total_par),
            "total_market_value": float(total_market_value),
            "average_par_amount": float(calculator.calculate_average_par_amount()),
            "last_maturity_date": calculator.get_last_maturity_date().isoformat() if calculator.get_last_maturity_date() else None,
            "accounts": cash_summary
        }
    
    def _update_pool_metrics(self, pool_id: int) -> None:
        """Update cached pool metrics"""
        pool_assets = self.db_session.query(CollateralPoolAsset)\
            .filter_by(pool_id=pool_id).all()
        
        total_par = sum(Decimal(str(asset.par_amount)) for asset in pool_assets)
        total_assets = len(pool_assets)
        avg_par = total_par / total_assets if total_assets > 0 else Decimal('0')
        
        pool = self.db_session.query(CollateralPool).filter_by(pool_id=pool_id).first()
        if pool:
            pool.total_par_amount = total_par
            pool.total_assets = total_assets
            pool.average_par_amount = avg_par
            pool.updated_at = datetime.now()
    
    def _update_account_cash(self, pool_id: int, account_type: AccountType,
                           cash_type: CashType, amount: Decimal) -> None:
        """Update account cash balance"""
        account = self.db_session.query(CollateralPoolAccount)\
            .filter_by(pool_id=pool_id, account_type=account_type.value).first()
        
        if not account:
            account = CollateralPoolAccount(
                pool_id=pool_id,
                account_type=account_type.value,
                principal_proceeds=Decimal('0'),
                interest_proceeds=Decimal('0')
            )
            self.db_session.add(account)
        
        if cash_type == CashType.PRINCIPAL:
            account.principal_proceeds += amount
        elif cash_type == CashType.INTEREST:
            account.interest_proceeds += amount
        
        account.updated_at = datetime.now()
    
    def _update_asset_position(self, pool_id: int, blkrock_id: str, 
                             par_change: Decimal) -> None:
        """Update asset position size"""
        pool_asset = self.db_session.query(CollateralPoolAsset)\
            .join(Asset).filter(
                CollateralPoolAsset.pool_id == pool_id,
                Asset.blkrock_id == blkrock_id
            ).first()
        
        if pool_asset:
            pool_asset.par_amount += par_change
            pool_asset.updated_at = datetime.now()
            
            # Remove if position too small
            if pool_asset.par_amount <= Decimal('1'):
                self.db_session.delete(pool_asset)
            
            self._update_pool_metrics(pool_id)
    
    def _reduce_cash_for_purchase(self, pool_id: int, asset: Asset, 
                                account_type: AccountType) -> None:
        """Reduce cash for asset purchase"""
        purchase_amount = asset.market_value * asset.par_amount / 100
        self._update_account_cash(pool_id, account_type, CashType.PRINCIPAL, 
                                -Decimal(str(purchase_amount)))
    
    def _save_concentration_results(self, pool_id: int, test_results) -> None:
        """Save concentration test results to database - now uses database-driven approach"""
        # NOTE: This method has been updated to work with database-driven concentration tests
        # Clear previous results
        self.db_session.query(ConcentrationTestResult)\
            .filter_by(pool_id=pool_id).delete()
        
        # Save new results from database-driven concentration tests
        for result in test_results:
            db_result = ConcentrationTestResult(
                pool_id=pool_id,
                test_date=date.today(),
                test_number=result.test_number,
                test_name=result.test_name,
                threshold_value=result.threshold,
                result_value=result.result,
                pass_fail=result.pass_fail,
                pass_fail_comment=result.comments  # Updated field name
            )
            self.db_session.add(db_result)