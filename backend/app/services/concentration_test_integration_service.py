"""
Concentration Test Integration Service
Integrates the enhanced concentration test engine with real portfolio data
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..models.asset import Asset
from ..models.database_driven_concentration_test import DatabaseDrivenConcentrationTest, DatabaseTestResult
from ..models.database.concentration_threshold_models import ConcentrationTestDefinition, DealConcentrationThreshold
from ..repositories.concentration_threshold_repository import ConcentrationThresholdRepository
from ..services.concentration_threshold_service import ConcentrationThresholdService
from ..core.database import get_db


class ConcentrationTestIntegrationService:
    """Service to run real concentration tests on portfolio data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.threshold_repository = ConcentrationThresholdRepository(db)
        self.threshold_service = ConcentrationThresholdService(self.threshold_repository)
        self.concentration_engine = DatabaseDrivenConcentrationTest(self.threshold_service)
    
    def run_portfolio_concentration_tests(
        self, 
        portfolio_id: str, 
        analysis_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Run actual concentration tests on a portfolio using real asset data
        """
        if not analysis_date:
            analysis_date = date(2016, 3, 23)  # Default CLO analysis date
        
        try:
            # Step 1: Load portfolio assets from database
            assets_dict = self._load_portfolio_assets(portfolio_id)
            if not assets_dict:
                return self._create_empty_result(portfolio_id, "No assets found for portfolio")
            
            # Step 2: Initialize concentration engine with database-driven thresholds  
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If called from sync context in async environment
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._run_async_tests(portfolio_id, analysis_date, assets_dict))
                    return future.result()
            else:
                return asyncio.run(self._run_async_tests(portfolio_id, analysis_date, assets_dict))
            
        except Exception as e:
            print(f"Error running concentration tests for {portfolio_id}: {e}")
            import traceback
            traceback.print_exc()
            return self._create_empty_result(portfolio_id, f"Error: {str(e)}")
    
    async def _run_async_tests(self, portfolio_id: str, analysis_date: date, assets_dict: Dict[str, Asset]) -> Dict[str, Any]:
        """Run the async concentration tests"""
        # Initialize concentration engine with database-driven thresholds
        await self.concentration_engine.initialize_for_deal(portfolio_id, analysis_date)
        
        # Run all concentration tests
        test_results = await self.concentration_engine.run_all_tests(assets_dict)
        
        # Save results to database
        await self.concentration_engine.save_results()
        
        # Format results for API response
        return self._format_database_test_results(portfolio_id, analysis_date, test_results)
    
    def _format_database_test_results(self, portfolio_id: str, analysis_date: date, test_results: List[DatabaseTestResult]) -> Dict[str, Any]:
        """Format database-driven concentration test results for API response"""
        formatted_tests = []
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0
        
        for result in test_results:
            status = result.pass_fail
            
            if status == 'PASS':
                passed_tests += 1
            elif status == 'FAIL':
                failed_tests += 1
            elif status == 'WARNING':
                warning_tests += 1
            
            formatted_test = {
                "test_id": result.test_id,
                "test_number": result.test_number,
                "test_name": result.test_name,
                "threshold": float(result.threshold),
                "result": float(result.result),
                "numerator": float(result.numerator),
                "denominator": float(result.denominator),
                "pass_fail": status,
                "excess_amount": float(result.excess_amount),
                "comments": result.comments,
                "threshold_source": result.threshold_source,
                "is_custom_override": result.is_custom_override,
                "effective_date": result.effective_date,
                "mag_version": result.mag_version
            }
            formatted_tests.append(formatted_test)
        
        return {
            "portfolio_id": portfolio_id,
            "analysis_date": analysis_date.isoformat(),
            "concentration_tests": formatted_tests,
            "summary": {
                "total_tests": len(formatted_tests),
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests,
                "compliance_score": f"{(passed_tests / len(formatted_tests) * 100):.1f}%" if formatted_tests else "0%",
                "custom_thresholds": sum(1 for r in test_results if r.is_custom_override)
            },
            "total_tests": len(formatted_tests),
            "passed_tests": passed_tests,
            "failed_tests": failed_tests
        }
    
    def _load_portfolio_assets(self, portfolio_id: str) -> Dict[str, Asset]:
        """Load all assets for a portfolio from database"""
        try:
            # Use the proper join with deal_assets table for all portfolios
            query = text("""
                    SELECT 
                        a.blkrock_id,
                        a.issue_name,
                        a.issuer_name,
                        a.par_amount,
                        a.market_value,
                        a.maturity,
                        a.mdy_industry as sector,
                        a.sp_industry as industry,
                        COALESCE(a.mdy_rating, a.sp_rating, a.derived_mdy_rating, a.derived_sp_rating) as rating,
                        a.mdy_rating,
                        a.sp_rating,
                        a.country,
                        a.currency,
                        a.seniority,
                        a.bond_loan,
                        a.coupon as coupon_rate,
                        a.coupon_type,
                        a.cpn_spread as spread_over_benchmark,
                        a.payment_freq as payment_frequency,
                        a.sp_priority_category,
                        CASE WHEN a.date_of_default IS NOT NULL THEN true ELSE false END as default_asset,
                        da.par_amount as position_par_amount,
                        false as cov_lite
                    FROM assets a
                    JOIN deal_assets da ON a.blkrock_id = da.blkrock_id
                    WHERE da.deal_id = :portfolio_id
                      AND (da.sale_date IS NULL OR da.sale_date > :analysis_date)
                    ORDER BY a.blkrock_id
                """)
            
            result = self.db.execute(query, {
                'portfolio_id': portfolio_id,
                'analysis_date': date(2016, 3, 23)
            })
            
            assets_dict = {}
            from decimal import Decimal
            for row in result:
                # Create a comprehensive asset dictionary for concentration tests
                # Include all attributes that concentration tests might need
                asset_data = {
                    'blkrock_id': row.blkrock_id,
                    'issue_name': row.issue_name or "",
                    'issuer_name': row.issuer_name or "",
                    'par_amount': Decimal(str(row.position_par_amount or row.par_amount or 0)),
                    'market_value': Decimal(str(row.market_value or 0)),
                    'maturity': row.maturity,
                    'maturity_date': row.maturity,  # Add maturity_date alias
                    'sector': row.sector or "",
                    'industry': row.industry or "",
                    'sp_industry': row.industry or "",  # Add sp_industry alias
                    'rating': row.rating or "",
                    'mdy_rating': getattr(row, 'mdy_rating', row.rating) or "",  # Use mdy_rating if available
                    'sp_rating': getattr(row, 'sp_rating', row.rating) or "",  # Use sp_rating if available
                    'country': row.country or "USA",
                    'currency': row.currency or "USD",
                    'seniority': row.seniority or "",
                    'asset_type': row.bond_loan or "",
                    'bond_loan': row.bond_loan or "",  # Add bond_loan directly
                    'coupon_rate': Decimal(str(row.coupon_rate or 0)),
                    'coupon_type': row.coupon_type or "",  # Add coupon_type for Test 9
                    'spread_over_benchmark': Decimal(str(row.spread_over_benchmark or 0)),
                    'payment_frequency': int(row.payment_frequency or 4),
                    'sp_priority_category': row.sp_priority_category or "",  # Add sp_priority_category
                    'dip': False,  # DIP (Debtor in Possession) - default to False since no column exists
                    'default_asset': bool(row.default_asset),
                    'cov_lite': getattr(row, 'cov_lite', False)  # Use cov_lite from DB or default to False
                }
                
                # Create a simple object that has the attributes concentration tests need
                from types import SimpleNamespace
                asset = SimpleNamespace(**asset_data)
                assets_dict[row.blkrock_id] = asset
            
            print(f"Loaded {len(assets_dict)} assets for portfolio {portfolio_id}")
            return assets_dict
            
        except Exception as e:
            print(f"Error loading assets for {portfolio_id}: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _create_empty_result(self, portfolio_id: str, message: str) -> Dict[str, Any]:
        """Create empty result when no data is available"""
        return {
            "portfolio_id": portfolio_id,
            "analysis_date": date.today().isoformat(),
            "concentration_tests": [],
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "warning_tests": 0,
                "compliance_score": "N/A"
            },
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "message": message
        }


def get_concentration_integration_service(db: Session = None) -> ConcentrationTestIntegrationService:
    """Factory function to get concentration test integration service"""
    if db is None:
        db = next(get_db())
    return ConcentrationTestIntegrationService(db)