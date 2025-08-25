"""
Database-Driven Concentration Test System
Enhanced concentration test engine using database-driven thresholds
"""

from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
from datetime import date
from dataclasses import dataclass
import logging

from ..services.concentration_threshold_service import ConcentrationThresholdService, ThresholdConfiguration
from .concentration_test_enhanced import TestNum, EnhancedTestResult
from .asset import Asset


logger = logging.getLogger(__name__)


@dataclass
class DatabaseTestResult:
    """Test result with database-driven threshold information"""
    test_id: int
    test_number: int
    test_name: str
    threshold: Decimal
    result: Decimal
    numerator: Decimal
    denominator: Decimal
    pass_fail: str
    excess_amount: Decimal
    threshold_source: str
    is_custom_override: bool
    effective_date: str
    mag_version: Optional[str]
    comments: str


class DatabaseDrivenConcentrationTest:
    """
    Database-driven concentration test engine
    Uses ThresholdService for dynamic threshold resolution
    """
    
    def __init__(self, threshold_service: ConcentrationThresholdService):
        self.threshold_service = threshold_service
        self.test_results: List[DatabaseTestResult] = []
        self.deal_id: Optional[str] = None
        self.analysis_date: Optional[date] = None
        self.threshold_configs: Dict[int, ThresholdConfiguration] = {}
        
    async def initialize_for_deal(self, deal_id: str, analysis_date: date = date(2016, 3, 23)):
        """Initialize test engine for specific deal and analysis date"""
        self.deal_id = deal_id
        self.analysis_date = analysis_date
        
        # Load all threshold configurations for this deal
        configs = await self.threshold_service.get_deal_thresholds(deal_id, analysis_date)
        self.threshold_configs = {config.test_id: config for config in configs}
        
        logger.info(f"Initialized concentration test engine for deal {deal_id} on {analysis_date}")
        logger.info(f"Loaded {len(self.threshold_configs)} threshold configurations")
    
    async def run_all_tests(self, assets_dict: Dict[str, Asset]) -> List[DatabaseTestResult]:
        """Run all concentration tests with database-driven thresholds"""
        if not self.deal_id or not self.analysis_date:
            raise ValueError("Test engine must be initialized with deal_id and analysis_date")
        
        self.test_results.clear()
        
        # Calculate total portfolio value
        total_par = sum(asset.par_amount for asset in assets_dict.values())
        if total_par <= 0:
            logger.warning("Portfolio has zero total par amount")
            return self.test_results
        
        logger.info(f"Running concentration tests on portfolio with ${total_par:,.2f} total par")
        
        # Run each configured test
        for test_id, config in self.threshold_configs.items():
            try:
                result = await self._execute_test(config, assets_dict, total_par)
                if result:
                    self.test_results.append(result)
            except Exception as e:
                logger.error(f"Error executing test {config.test_name}: {e}")
                # Create failed result
                error_result = DatabaseTestResult(
                    test_id=test_id,
                    test_number=config.test_number,
                    test_name=config.test_name,
                    threshold=Decimal(str(config.threshold_value)),
                    result=Decimal('0'),
                    numerator=Decimal('0'),
                    denominator=Decimal('0'),
                    pass_fail='N/A',
                    excess_amount=Decimal('0'),
                    threshold_source=config.threshold_source,
                    is_custom_override=config.is_custom_override,
                    effective_date=config.effective_date,
                    mag_version=config.mag_version,
                    comments=f"Test execution error: {str(e)}"
                )
                self.test_results.append(error_result)
        
        logger.info(f"Completed {len(self.test_results)} concentration tests")
        return self.test_results
    
    async def _execute_test(self, 
                          config: ThresholdConfiguration, 
                          assets_dict: Dict[str, Asset], 
                          total_par: Decimal) -> Optional[DatabaseTestResult]:
        """Execute individual concentration test"""
        
        test_number = config.test_number
        threshold = Decimal(str(config.threshold_value))
        
        # Route to specific test implementation based on test number
        if test_number == 1:  # Senior Secured Loans Minimum
            return await self._test_senior_secured_minimum(config, assets_dict, total_par, threshold)
        elif test_number == 4:  # Single Obligor Maximum
            return await self._test_single_obligor_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 7:  # Caa-Rated Assets Maximum
            return await self._test_caa_rated_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 29:  # Covenant-Lite Maximum
            return await self._test_covenant_lite_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 40:  # CCC-Rated Obligations Maximum
            return await self._test_ccc_rated_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 27:  # Single Industry Maximum
            return await self._test_single_industry_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 36:  # WARF Maximum
            return await self._test_warf_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 35:  # WAL Maximum
            return await self._test_wal_maximum(config, assets_dict, total_par, threshold)
        else:
            # For unimplemented tests, create placeholder result
            return DatabaseTestResult(
                test_id=config.test_id,
                test_number=config.test_number,
                test_name=config.test_name,
                threshold=threshold,
                result=Decimal('0'),
                numerator=Decimal('0'),
                denominator=total_par,
                pass_fail='N/A',
                excess_amount=Decimal('0'),
                threshold_source=config.threshold_source,
                is_custom_override=config.is_custom_override,
                effective_date=config.effective_date,
                mag_version=config.mag_version,
                comments=f"Test implementation not yet available"
            )
    
    # ========================================
    # Individual Test Implementations
    # ========================================
    
    async def _test_senior_secured_minimum(self, 
                                         config: ThresholdConfiguration,
                                         assets_dict: Dict[str, Asset], 
                                         total_par: Decimal, 
                                         threshold: Decimal) -> DatabaseTestResult:
        """Test minimum senior secured loans percentage"""
        
        senior_secured_par = Decimal('0')
        for asset in assets_dict.values():
            if asset.seniority and asset.seniority.lower() in ['senior', 'senior secured']:
                senior_secured_par += asset.par_amount
        
        percentage = (senior_secured_par / total_par * 100) if total_par > 0 else Decimal('0')
        pass_fail = 'PASS' if percentage >= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), threshold - percentage)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=percentage,
            numerator=senior_secured_par,
            denominator=total_par,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Senior secured loans: ${senior_secured_par:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_single_obligor_maximum(self, 
                                         config: ThresholdConfiguration,
                                         assets_dict: Dict[str, Asset], 
                                         total_par: Decimal, 
                                         threshold: Decimal) -> DatabaseTestResult:
        """Test single obligor concentration limit"""
        
        obligor_exposures = {}
        for asset in assets_dict.values():
            obligor = asset.issuer_name or asset.obligor_name or "Unknown"
            obligor_exposures[obligor] = obligor_exposures.get(obligor, Decimal('0')) + asset.par_amount
        
        max_exposure = max(obligor_exposures.values()) if obligor_exposures else Decimal('0')
        max_obligor = max(obligor_exposures, key=obligor_exposures.get) if obligor_exposures else "None"
        percentage = (max_exposure / total_par * 100) if total_par > 0 else Decimal('0')
        
        pass_fail = 'PASS' if percentage <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), percentage - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=percentage,
            numerator=max_exposure,
            denominator=total_par,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Largest obligor '{max_obligor}': ${max_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_caa_rated_maximum(self, 
                                    config: ThresholdConfiguration,
                                    assets_dict: Dict[str, Asset], 
                                    total_par: Decimal, 
                                    threshold: Decimal) -> DatabaseTestResult:
        """Test Caa-rated assets concentration limit"""
        
        caa_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.mdy_rating and asset.mdy_rating.startswith('Caa'):
                caa_exposure += asset.par_amount
        
        percentage = (caa_exposure / total_par * 100) if total_par > 0 else Decimal('0')
        pass_fail = 'PASS' if percentage <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), percentage - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=percentage,
            numerator=caa_exposure,
            denominator=total_par,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Caa-rated assets: ${caa_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_covenant_lite_maximum(self, 
                                        config: ThresholdConfiguration,
                                        assets_dict: Dict[str, Asset], 
                                        total_par: Decimal, 
                                        threshold: Decimal) -> DatabaseTestResult:
        """Test covenant-lite assets concentration limit"""
        
        cov_lite_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.cov_lite:
                cov_lite_exposure += asset.par_amount
        
        percentage = (cov_lite_exposure / total_par * 100) if total_par > 0 else Decimal('0')
        pass_fail = 'PASS' if percentage <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), percentage - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=percentage,
            numerator=cov_lite_exposure,
            denominator=total_par,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Covenant-lite assets: ${cov_lite_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_ccc_rated_maximum(self, 
                                    config: ThresholdConfiguration,
                                    assets_dict: Dict[str, Asset], 
                                    total_par: Decimal, 
                                    threshold: Decimal) -> DatabaseTestResult:
        """Test CCC-rated assets concentration limit"""
        
        ccc_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.sp_rating and asset.sp_rating.startswith('CCC'):
                ccc_exposure += asset.par_amount
        
        percentage = (ccc_exposure / total_par * 100) if total_par > 0 else Decimal('0')
        pass_fail = 'PASS' if percentage <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), percentage - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=percentage,
            numerator=ccc_exposure,
            denominator=total_par,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"CCC-rated assets: ${ccc_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_single_industry_maximum(self, 
                                          config: ThresholdConfiguration,
                                          assets_dict: Dict[str, Asset], 
                                          total_par: Decimal, 
                                          threshold: Decimal) -> DatabaseTestResult:
        """Test single industry concentration limit"""
        
        industry_exposures = {}
        for asset in assets_dict.values():
            industry = asset.sp_industry or asset.industry or "Unknown"
            industry_exposures[industry] = industry_exposures.get(industry, Decimal('0')) + asset.par_amount
        
        max_exposure = max(industry_exposures.values()) if industry_exposures else Decimal('0')
        max_industry = max(industry_exposures, key=industry_exposures.get) if industry_exposures else "None"
        percentage = (max_exposure / total_par * 100) if total_par > 0 else Decimal('0')
        
        pass_fail = 'PASS' if percentage <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), percentage - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=percentage,
            numerator=max_exposure,
            denominator=total_par,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Largest industry '{max_industry}': ${max_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_warf_maximum(self, 
                               config: ThresholdConfiguration,
                               assets_dict: Dict[str, Asset], 
                               total_par: Decimal, 
                               threshold: Decimal) -> DatabaseTestResult:
        """Test Weighted Average Rating Factor maximum"""
        
        # Simplified WARF calculation (would need proper rating factors)
        total_weighted_rf = Decimal('0')
        total_weight = Decimal('0')
        
        rating_factors = {
            'AAA': 1, 'AA': 10, 'A': 40, 'BBB': 180, 'BB': 720,
            'B': 1350, 'CCC': 2720, 'CC': 5470, 'C': 10000
        }
        
        for asset in assets_dict.values():
            # Use S&P rating if available, fallback to Moody's
            rating = asset.sp_rating or asset.mdy_rating or 'B'
            
            # Map rating to base category
            base_rating = rating[:3] if len(rating) >= 3 else rating[:2] if len(rating) >= 2 else rating
            rating_factor = rating_factors.get(base_rating, 1350)  # Default to B
            
            weight = asset.par_amount
            total_weighted_rf += Decimal(rating_factor) * weight
            total_weight += weight
        
        warf = total_weighted_rf / total_weight if total_weight > 0 else Decimal('0')
        
        pass_fail = 'PASS' if warf <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), warf - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=warf,
            numerator=total_weighted_rf,
            denominator=total_weight,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Weighted Average Rating Factor: {warf:.0f}"
        )
    
    async def _test_wal_maximum(self, 
                              config: ThresholdConfiguration,
                              assets_dict: Dict[str, Asset], 
                              total_par: Decimal, 
                              threshold: Decimal) -> DatabaseTestResult:
        """Test Weighted Average Life maximum"""
        
        total_weighted_life = Decimal('0')
        total_weight = Decimal('0')
        
        analysis_date = self.analysis_date or date(2016, 3, 23)
        
        for asset in assets_dict.values():
            if asset.maturity_date:
                # Calculate years to maturity
                years_to_maturity = (asset.maturity_date - analysis_date).days / 365.25
                years_to_maturity = max(0, years_to_maturity)  # Ensure non-negative
                
                weight = asset.par_amount
                total_weighted_life += Decimal(str(years_to_maturity)) * weight
                total_weight += weight
        
        wal = total_weighted_life / total_weight if total_weight > 0 else Decimal('0')
        
        pass_fail = 'PASS' if wal <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), wal - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=wal,
            numerator=total_weighted_life,
            denominator=total_weight,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Weighted Average Life: {wal:.2f} years"
        )
    
    # ========================================
    # Result Management
    # ========================================
    
    async def save_results(self) -> None:
        """Save test results to database via threshold service"""
        if not self.test_results or not self.deal_id or not self.analysis_date:
            logger.warning("No results to save or missing deal context")
            return
        
        # Convert results to service format
        results_for_service = []
        for result in self.test_results:
            results_for_service.append({
                'test_id': result.test_id,
                'threshold': float(result.threshold),
                'result': float(result.result),
                'numerator': float(result.numerator),
                'denominator': float(result.denominator),
                'pass_fail_status': result.pass_fail,
                'excess_amount': float(result.excess_amount),
                'threshold_source': result.threshold_source,
                'comments': result.comments
            })
        
        await self.threshold_service.save_test_results(
            self.deal_id, self.analysis_date, results_for_service
        )
        
        logger.info(f"Saved {len(results_for_service)} test results to database")
    
    def get_results(self) -> List[DatabaseTestResult]:
        """Get current test results"""
        return self.test_results.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of test results"""
        if not self.test_results:
            return {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'na_tests': 0,
                'pass_rate': 0.0
            }
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.pass_fail == 'PASS')
        failed_tests = sum(1 for r in self.test_results if r.pass_fail == 'FAIL')
        na_tests = sum(1 for r in self.test_results if r.pass_fail == 'N/A')
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'na_tests': na_tests,
            'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0.0,
            'custom_thresholds': sum(1 for r in self.test_results if r.is_custom_override)
        }