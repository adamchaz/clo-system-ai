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
        
        # Load ONLY the threshold configurations that are actually configured for this deal
        # This ensures we only run tests that have been explicitly set up for the deal
        configs = await self.threshold_service.get_deal_specific_thresholds(deal_id, analysis_date)
        self.threshold_configs = {config.test_id: config for config in configs}
        
        logger.info(f"Initialized concentration test engine for deal {deal_id} on {analysis_date}")
        logger.info(f"Loaded {len(self.threshold_configs)} deal-specific threshold configurations")
    
    async def get_deal_assets(self, deal_id: str) -> Dict[str, Asset]:
        """Get assets for a specific deal from deal_assets table"""
        try:
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import create_engine
            from ..core.config import settings
            from ..models.asset import Asset
            
            # Create database connection
            engine = create_engine(settings.database_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Load assets by blkrock_id list using proper SQLAlchemy ORM
            blkrock_ids_result = session.execute(
                "SELECT blkrock_id FROM deal_assets WHERE deal_id = :deal_id",
                {'deal_id': deal_id}
            ).fetchall()
            
            blkrock_ids = [row[0] for row in blkrock_ids_result]
            
            if blkrock_ids:
                # Use SQLAlchemy ORM to get proper Asset model instances
                assets = session.query(Asset).filter(Asset.blkrock_id.in_(blkrock_ids)).all()
            else:
                assets = []
            
            session.close()
            
            # Convert to dictionary with proper Asset objects
            assets_dict = {asset.blkrock_id: asset for asset in assets}
            logger.info(f"Loaded {len(assets_dict)} proper Asset objects for deal {deal_id}")
            
            return assets_dict
            
        except Exception as e:
            logger.error(f"Error loading assets for deal {deal_id}: {e}")
            return {}
    
    async def run_all_tests(self, assets_dict: Dict[str, Asset] = None) -> List[DatabaseTestResult]:
        """Run all concentration tests with database-driven thresholds"""
        if not self.deal_id or not self.analysis_date:
            raise ValueError("Test engine must be initialized with deal_id and analysis_date")
        
        self.test_results.clear()
        
        # If no assets_dict provided, load deal-specific assets
        if assets_dict is None:
            assets_dict = await self.get_deal_assets(self.deal_id)
            if not assets_dict:
                logger.error(f"No assets found for deal {self.deal_id}")
                return self.test_results
        
        # Calculate total portfolio value
        total_par = sum(asset.par_amount or 0 for asset in assets_dict.values())
        if total_par <= 0:
            logger.warning("Portfolio has zero total par amount")
            return self.test_results
        
        logger.info(f"Running concentration tests on {len(assets_dict)} assets for deal {self.deal_id} with ${total_par:,.2f} total par")
        
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
    
    async def _get_principal_proceeds(self, deal_id: str, analysis_date: date) -> Decimal:
        """Get principal proceeds from deal_accounts table (VBA clsPrinProceeds)"""
        try:
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import create_engine, text
            from ..core.config import settings
            
            # Create database connection
            engine = create_engine(settings.database_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Query total principal proceeds for the deal on the analysis date
            query = text("""
                SELECT COALESCE(SUM(principal_proceeds), 0) as total_principal_proceeds
                FROM deal_accounts 
                WHERE deal_id = :deal_id AND analysis_date = :analysis_date
            """)
            
            result = session.execute(query, {
                'deal_id': deal_id,
                'analysis_date': analysis_date
            }).fetchone()
            
            session.close()
            
            principal_proceeds = Decimal(str(result[0])) if result else Decimal('0')
            logger.info(f"Principal proceeds for {deal_id} on {analysis_date}: ${principal_proceeds:,.2f}")
            
            return principal_proceeds
            
        except Exception as e:
            logger.error(f"Error getting principal proceeds for {deal_id}: {e}")
            return Decimal('0')
    
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
        elif test_number == 2:  # Non Senior Secured Loans Maximum
            return await self._test_non_senior_secured_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 3:  # 6th Largest Obligor Maximum
            return await self._test_sixth_largest_obligor_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 4:  # Single Obligor Maximum
            return await self._test_single_obligor_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 5:  # DIP Obligor Maximum
            return await self._test_dip_obligor_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 6:  # Non-Senior Secured Obligor Maximum
            return await self._test_non_senior_secured_obligor_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 7:  # Caa-Rated Assets Maximum
            return await self._test_caa_rated_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 8:  # Assets Paying Less Frequently than Quarterly
            return await self._test_assets_paying_less_frequently_quarterly(config, assets_dict, total_par, threshold)
        elif test_number == 9:  # Fixed Rate Obligations Maximum
            return await self._test_fixed_rate_obligations_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 10:  # Current Pay Obligations Maximum
            return await self._test_current_pay_obligations_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 11:  # DIP Obligations Maximum
            return await self._test_dip_obligations_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 13:  # Participation Interest Maximum
            return await self._test_participation_interest_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 19:  # Limitation on Individual Group I Countries
            return await self._test_individual_group_i_countries(config, assets_dict, total_par, threshold)
        elif test_number == 20:  # Limitation on Group II Countries
            return await self._test_group_ii_countries(config, assets_dict, total_par, threshold)
        elif test_number == 21:  # Limitation on Individual Group II Countries
            return await self._test_individual_group_ii_countries(config, assets_dict, total_par, threshold)
        elif test_number == 22:  # Limitation on Group III Countries
            return await self._test_group_iii_countries(config, assets_dict, total_par, threshold)
        elif test_number == 23:  # Limitation on Individual Group III Countries
            return await self._test_individual_group_iii_countries(config, assets_dict, total_par, threshold)
        elif test_number == 24:  # Limitation on Tax Jurisdictions
            return await self._test_tax_jurisdictions(config, assets_dict, total_par, threshold)
        elif test_number == 27:  # Single Industry Maximum
            return await self._test_single_industry_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 28:  # Bridge Loans Maximum
            return await self._test_bridge_loans_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 29:  # Covenant-Lite Maximum
            return await self._test_covenant_lite_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 30:  # Deferrable Securities Maximum
            return await self._test_deferrable_securities_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 31:  # Facility Size Maximum
            return await self._test_facility_size_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 35:  # WAL Maximum
            return await self._test_wal_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 36:  # WARF Maximum
            return await self._test_warf_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 40:  # CCC-Rated Obligations Maximum
            return await self._test_ccc_rated_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 14:  # Countries Not US Maximum
            return await self._test_countries_not_us_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 16:  # Countries Not US Canada UK Maximum
            return await self._test_countries_not_us_canada_uk_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 17:  # Group Countries Maximum
            return await self._test_group_countries_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 18:  # Group I Countries Maximum
            return await self._test_group_i_countries_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 15:  # Countries Canada and Tax Jurisdictions Maximum
            return await self._test_countries_canada_tax_jurisdictions_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 25:  # 4th Largest SP Industry Classification Maximum
            return await self._test_fourth_largest_sp_industry_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 26:  # 2nd Largest SP Classification Maximum
            return await self._test_second_largest_sp_industry_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 41:  # Canada Maximum
            return await self._test_canada_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 42:  # Letter of Credit Maximum
            return await self._test_letter_of_credit_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 43:  # Long Dated Maximum
            return await self._test_long_dated_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 44:  # Unsecured Loans Maximum
            return await self._test_unsecured_loans_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 45:  # Swap Non Discount Maximum
            return await self._test_swap_non_discount_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 12:  # Unfunded Commitments Maximum
            return await self._test_unfunded_commitments_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 47:  # Non-Emerging Market Obligors Maximum
            return await self._test_non_emerging_market_obligors_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 48:  # SP Criteria Maximum
            return await self._test_sp_criteria_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 49:  # 1st Largest Moody Industry Maximum
            return await self._test_first_largest_moody_industry_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 50:  # 2nd Largest Moody Industry Maximum
            return await self._test_second_largest_moody_industry_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 51:  # 3rd Largest Moody Industry Maximum
            return await self._test_third_largest_moody_industry_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 52:  # 4th Largest Moody Industry Maximum
            return await self._test_fourth_largest_moody_industry_maximum(config, assets_dict, total_par, threshold)
        elif test_number == 53:  # Facility Size MAG08 Maximum
            return await self._test_facility_size_mag08_maximum(config, assets_dict, total_par, threshold)
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
                                         threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 1: Limitation on Senior Secured Loans - VBA Logic
        
        VBA Logic:
        1. Start with all LOANS (BondLoan = 'LOAN')
        2. SUBTRACT assets with MDYAssetCategory = 'MOODY'S NON-SENIOR SECURED LOAN'
        3. ADD principal proceeds (clsPrinProceeds)
        4. Calculate ratio against total collateral amount (including proceeds)
        """
        
        # Get principal proceeds for this deal
        principal_proceeds = await self._get_principal_proceeds(self.deal_id, self.analysis_date)
        
        # VBA Logic: Exact replication
        # Step 1: Start with lNumerator = 0
        numerator = Decimal('0')
        loans_par = Decimal('0')
        non_senior_secured_adjustment = Decimal('0')
        
        for asset in assets_dict.values():
            # VBA: If lAsset.DefaultAsset = False Then
            default_asset = getattr(asset, 'default_asset', False)
            
            if not default_asset:
                # VBA: If lAsset.BondLoan = "LOAN" Then
                #      lNumerator = lAsset.ParAmount + lNumerator
                if hasattr(asset, 'bond_loan') and asset.bond_loan and asset.bond_loan.upper() == 'LOAN':
                    numerator += asset.par_amount
                    loans_par += asset.par_amount
                
                # VBA: If lAsset.MDYAssetCategory = "MOODY'S NON-SENIOR SECURED LOAN" Then
                #      lNumerator = lNumerator - lAsset.ParAmount
                if (hasattr(asset, 'mdy_asset_category') and asset.mdy_asset_category and 
                    'NON-SENIOR SECURED LOAN' in asset.mdy_asset_category.upper()):
                    numerator -= asset.par_amount
                    non_senior_secured_adjustment += asset.par_amount
        
        # VBA: lNumerator = lNumerator + clsPrinProceeds
        numerator += principal_proceeds
        
        # Denominator: total collateral + principal proceeds (VBA: clsCollateralPrincipalAmount)
        denominator = total_par + principal_proceeds
        
        ratio = (numerator / denominator) if denominator > 0 else Decimal('0')
        percentage = ratio * 100
        # VBA Logic: If .Result > .Threshold Then .PassFail = True (Test 1 is a MINIMUM test)
        pass_fail = 'PASS' if ratio >= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), threshold - ratio)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=numerator,
            denominator=denominator,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Senior secured loans: ${numerator:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_single_obligor_maximum(self, 
                                         config: ThresholdConfiguration,
                                         assets_dict: Dict[str, Asset], 
                                         total_par: Decimal, 
                                         threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test single obligor concentration limit"""
        
        obligor_exposures = {}
        for asset in assets_dict.values():
            # Match VBA logic: exclude defaulted and DIP assets
            if not getattr(asset, 'default_asset', False) and not (asset.flags.get('dip', False) if asset.flags else False):
                # Use issuer_id as primary identifier, fallback to issuer_name
                obligor = getattr(asset, 'issuer_id', None) or asset.issuer_name or asset.obligor_name or "Unknown"
                obligor_exposures[obligor] = obligor_exposures.get(obligor, Decimal('0')) + asset.par_amount
        
        max_exposure = max(obligor_exposures.values()) if obligor_exposures else Decimal('0')
        max_obligor = max(obligor_exposures, key=obligor_exposures.get) if obligor_exposures else "None"
        ratio = (max_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=max_exposure,
            denominator=total_par + principal_proceeds,
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
                                    threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test Caa-rated assets concentration limit"""
        
        caa_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.mdy_rating and asset.mdy_rating.startswith('Caa'):
                caa_exposure += asset.par_amount
        
        ratio = (caa_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=caa_exposure,
            denominator=total_par + principal_proceeds,
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
                                        threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test covenant-lite assets concentration limit"""
        
        cov_lite_exposure = Decimal('0')
        for asset in assets_dict.values():
            # Check both flags JSON and sp_priority_category field for Cov-Lite designation
            is_cov_lite = False
            if asset.flags and asset.flags.get('cov_lite', False):
                is_cov_lite = True
            elif hasattr(asset, 'sp_priority_category') and asset.sp_priority_category:
                is_cov_lite = 'cov-lite' in asset.sp_priority_category.lower()
            
            if is_cov_lite:
                cov_lite_exposure += asset.par_amount
        
        ratio = (cov_lite_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=cov_lite_exposure,
            denominator=total_par + principal_proceeds,
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
                                    threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test CCC-rated assets concentration limit"""
        
        ccc_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.sp_rating and asset.sp_rating.startswith('CCC'):
                ccc_exposure += asset.par_amount
        
        ratio = (ccc_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=ccc_exposure,
            denominator=total_par + principal_proceeds,
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
                                          threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test single industry concentration limit"""
        
        industry_exposures = {}
        for asset in assets_dict.values():
            industry = asset.sp_industry or asset.industry or "Unknown"
            industry_exposures[industry] = industry_exposures.get(industry, Decimal('0')) + asset.par_amount
        
        max_exposure = max(industry_exposures.values()) if industry_exposures else Decimal('0')
        max_industry = max(industry_exposures, key=industry_exposures.get) if industry_exposures else "None"
        ratio = (max_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=max_exposure,
            denominator=total_par + principal_proceeds,
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
                               threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
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
                              threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
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
    # Geographic Concentration Tests
    # ========================================
    
    async def _test_individual_group_i_countries(self,
                                                config: ThresholdConfiguration,
                                                assets_dict: Dict[str, Asset],
                                                total_par: Decimal,
                                                threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 19: Limitation on Individual Group I Countries"""
        # Group I countries per VBA ConcentrationTest.cls:1568
        group_i_countries = ['NETHERLANDS', 'AUSTRALIA', 'NEW ZEALAND', 'UNITED KINGDOM']
        
        # Find the maximum exposure to any single Group I country
        country_exposures = {}
        for asset in assets_dict.values():
            # Use case-insensitive comparison
            if (asset.country or "").upper() in group_i_countries:
                if asset.country not in country_exposures:
                    country_exposures[asset.country] = Decimal('0')
                country_exposures[asset.country] += Decimal(str(asset.par_amount))
        
        # Find maximum single country exposure
        max_exposure = max(country_exposures.values()) if country_exposures else Decimal('0')
        result = max_exposure / total_par if total_par > 0 else Decimal('0')
        
        pass_fail = 'PASS' if result <= threshold else 'FAIL'
        excess = max_exposure - (threshold * total_par) if pass_fail == 'FAIL' else Decimal('0')
        
        max_country = max(country_exposures, key=country_exposures.get) if country_exposures else 'None'
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=result,
            numerator=max_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Maximum exposure: {max_country} ({result*100:.2f}%)"
        )
    
    async def _test_group_ii_countries(self,
                                      config: ThresholdConfiguration,
                                      assets_dict: Dict[str, Asset],
                                      total_par: Decimal,
                                      threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 20: Limitation on Group II Countries"""
        # Group II countries per VBA ConcentrationTest.cls:1635
        group_ii_countries = ['GERMANY', 'SWEDEN', 'SWITZERLAND']
        
        # Calculate total exposure to all Group II countries
        group_ii_exposure = Decimal('0')
        for asset in assets_dict.values():
            # Use case-insensitive comparison
            if (asset.country or "").upper() in group_ii_countries:
                group_ii_exposure += Decimal(str(asset.par_amount))
        
        result = group_ii_exposure / total_par if total_par > 0 else Decimal('0')
        
        pass_fail = 'PASS' if result <= threshold else 'FAIL'
        excess = group_ii_exposure - (threshold * total_par) if pass_fail == 'FAIL' else Decimal('0')
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=result,
            numerator=group_ii_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Total Group II exposure: {result*100:.2f}%"
        )
    
    async def _test_individual_group_ii_countries(self,
                                                 config: ThresholdConfiguration,
                                                 assets_dict: Dict[str, Asset],
                                                 total_par: Decimal,
                                                 threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 21: Limitation on Individual Group II Countries"""
        group_ii_countries = ['GERMANY', 'SWEDEN', 'SWITZERLAND']
        
        # Find the maximum exposure to any single Group II country
        country_exposures = {}
        for asset in assets_dict.values():
            # Use case-insensitive comparison
            if (asset.country or "").upper() in group_ii_countries:
                if asset.country not in country_exposures:
                    country_exposures[asset.country] = Decimal('0')
                country_exposures[asset.country] += Decimal(str(asset.par_amount))
        
        # Find maximum single country exposure
        max_exposure = max(country_exposures.values()) if country_exposures else Decimal('0')
        result = max_exposure / total_par if total_par > 0 else Decimal('0')
        
        pass_fail = 'PASS' if result <= threshold else 'FAIL'
        excess = max_exposure - (threshold * total_par) if pass_fail == 'FAIL' else Decimal('0')
        
        max_country = max(country_exposures, key=country_exposures.get) if country_exposures else 'None'
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=result,
            numerator=max_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Maximum exposure: {max_country} ({result*100:.2f}%)"
        )
    
    async def _test_group_iii_countries(self,
                                       config: ThresholdConfiguration,
                                       assets_dict: Dict[str, Asset],
                                       total_par: Decimal,
                                       threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 22: Limitation on Group III Countries"""
        # Group III countries per VBA ConcentrationTest.cls:1705
        group_iii_countries = ['AUSTRIA', 'BELGIUM', 'DENMARK', 'FINLAND', 'FRANCE', 
                              'ICELAND', 'LIECHTENSTEIN', 'LUXEMBOURG', 'NORWAY', 'SPAIN']
        
        # Calculate total exposure to all Group III countries
        group_iii_exposure = Decimal('0')
        for asset in assets_dict.values():
            # Use case-insensitive comparison
            if (asset.country or "").upper() in group_iii_countries:
                group_iii_exposure += Decimal(str(asset.par_amount))
        
        result = group_iii_exposure / total_par if total_par > 0 else Decimal('0')
        
        pass_fail = 'PASS' if result <= threshold else 'FAIL'
        excess = group_iii_exposure - (threshold * total_par) if pass_fail == 'FAIL' else Decimal('0')
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=result,
            numerator=group_iii_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Total Group III exposure: {result*100:.2f}%"
        )
    
    async def _test_individual_group_iii_countries(self,
                                                  config: ThresholdConfiguration,
                                                  assets_dict: Dict[str, Asset],
                                                  total_par: Decimal,
                                                  threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 23: Limitation on Individual Group III Countries"""
        group_iii_countries = ['AUSTRIA', 'BELGIUM', 'DENMARK', 'FINLAND', 'FRANCE', 
                              'ICELAND', 'LIECHTENSTEIN', 'LUXEMBOURG', 'NORWAY', 'SPAIN']
        
        # Find the maximum exposure to any single Group III country
        country_exposures = {}
        for asset in assets_dict.values():
            # Use case-insensitive comparison
            if (asset.country or "").upper() in group_iii_countries:
                if asset.country not in country_exposures:
                    country_exposures[asset.country] = Decimal('0')
                country_exposures[asset.country] += Decimal(str(asset.par_amount))
        
        # Find maximum single country exposure
        max_exposure = max(country_exposures.values()) if country_exposures else Decimal('0')
        result = max_exposure / total_par if total_par > 0 else Decimal('0')
        
        pass_fail = 'PASS' if result <= threshold else 'FAIL'
        excess = max_exposure - (threshold * total_par) if pass_fail == 'FAIL' else Decimal('0')
        
        max_country = max(country_exposures, key=country_exposures.get) if country_exposures else 'None'
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=result,
            numerator=max_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Maximum exposure: {max_country} ({result*100:.2f}%)"
        )
    
    async def _test_tax_jurisdictions(self,
                                     config: ThresholdConfiguration,
                                     assets_dict: Dict[str, Asset],
                                     total_par: Decimal,
                                     threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 24: Limitation on Tax Jurisdictions"""
        # Tax havens and special jurisdictions
        tax_jurisdictions = ['Cayman Islands', 'Bermuda', 'British Virgin Islands', 'Jersey', 
                           'Guernsey', 'Isle of Man', 'Luxembourg', 'Mauritius', 'Bahamas']
        
        # Calculate total exposure to tax jurisdictions
        tax_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.country in tax_jurisdictions:
                tax_exposure += Decimal(str(asset.par_amount))
        
        result = tax_exposure / total_par if total_par > 0 else Decimal('0')
        
        pass_fail = 'PASS' if result <= threshold else 'FAIL'
        excess = tax_exposure - (threshold * total_par) if pass_fail == 'FAIL' else Decimal('0')
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=result,
            numerator=tax_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Tax jurisdiction exposure: {result*100:.2f}%"
        )
    
    # ========================================
    # Asset Quality Tests - Additional Implementations
    # ========================================
    
    async def _test_non_senior_secured_maximum(self,
                                             config: ThresholdConfiguration,
                                             assets_dict: Dict[str, Asset],
                                             total_par: Decimal,
                                             threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 2: Limitation on Non Senior Secured Loans - VBA Logic
        
        VBA Logic:
        If Not (lAsset.Seniority = "SENIOR SECURED" And lAsset.BondLoan = "LOAN") Then
            lNumerator = lAsset.ParAmount + lNumerator
        ElseIf lAsset.SPPriorityCategory = "SENIOR UNSECURED LOAN/SECOND LIEN LOAN" Then
            lNumerator = lAsset.ParAmount + lNumerator
        """
        
        non_senior_exposure = Decimal('0')
        for asset in assets_dict.values():
            # VBA logic: exclude defaulted assets (implied in VBA loop)
            if not getattr(asset, 'default_asset', False):
                seniority_upper = (asset.seniority or "").upper()
                bond_loan_upper = (asset.bond_loan or "").upper()
                
                # Primary condition: NOT (SENIOR SECURED AND LOAN)
                if not (seniority_upper == 'SENIOR SECURED' and bond_loan_upper == 'LOAN'):
                    non_senior_exposure += asset.par_amount
                # ElseIf condition: Senior Secured Loans with specific S&P Priority Category  
                elif (seniority_upper == 'SENIOR SECURED' and bond_loan_upper == 'LOAN' and
                      asset.sp_priority_category and asset.sp_priority_category.upper() == 'SENIOR UNSECURED LOAN/SECOND LIEN LOAN'):
                    non_senior_exposure += asset.par_amount
        
        ratio = (non_senior_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=non_senior_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Non-senior secured exposure: ${non_senior_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_sixth_largest_obligor_maximum(self,
                                                config: ThresholdConfiguration,
                                                assets_dict: Dict[str, Asset],
                                                total_par: Decimal,
                                                threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 3: Limitation on 6th Largest Obligor"""
        
        obligor_exposures = {}
        for asset in assets_dict.values():
            # Match VBA logic exactly: exclude defaulted and DIP assets
            if not getattr(asset, 'default_asset', False) and not (asset.flags.get('dip', False) if asset.flags else False):
                # Use issuer_id as primary identifier, fallback to issuer_name
                obligor = getattr(asset, 'issuer_id', None) or asset.issuer_name or asset.obligor_name or "Unknown"
                obligor_exposures[obligor] = obligor_exposures.get(obligor, Decimal('0')) + asset.par_amount
        
        # Sort obligors by exposure descending
        sorted_exposures = sorted(obligor_exposures.items(), key=lambda x: x[1], reverse=True)
        
        # Get 6th largest exposure (index 5)
        sixth_exposure = sorted_exposures[5][1] if len(sorted_exposures) > 5 else Decimal('0')
        sixth_obligor = sorted_exposures[5][0] if len(sorted_exposures) > 5 else "None"
        
        ratio = (sixth_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=sixth_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"6th largest obligor '{sixth_obligor}': ${sixth_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_dip_obligor_maximum(self,
                                      config: ThresholdConfiguration,
                                      assets_dict: Dict[str, Asset],
                                      total_par: Decimal,
                                      threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 5: Limitation on DIP Obligor"""
        
        dip_obligor_exposures = {}
        for asset in assets_dict.values():
            # Match VBA logic: exclude defaulted assets, include only DIP assets
            if not getattr(asset, 'default_asset', False) and (asset.flags.get('dip', False) if asset.flags else False):
                # Use issuer_id as primary identifier, fallback to issuer_name
                obligor = getattr(asset, 'issuer_id', None) or asset.issuer_name or asset.obligor_name or "Unknown"
                dip_obligor_exposures[obligor] = dip_obligor_exposures.get(obligor, Decimal('0')) + asset.par_amount
        
        max_exposure = max(dip_obligor_exposures.values()) if dip_obligor_exposures else Decimal('0')
        max_obligor = max(dip_obligor_exposures, key=dip_obligor_exposures.get) if dip_obligor_exposures else "None"
        
        ratio = (max_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=max_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Largest DIP obligor '{max_obligor}': ${max_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_non_senior_secured_obligor_maximum(self,
                                                     config: ThresholdConfiguration,
                                                     assets_dict: Dict[str, Asset],
                                                     total_par: Decimal,
                                                     threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 6: Limitation on Non-Senior Secured Obligor"""
        
        non_senior_obligor_exposures = {}
        for asset in assets_dict.values():
            # Use SAME logic as Test 2 to identify non-senior secured assets
            if not getattr(asset, 'default_asset', False):
                seniority_upper = (asset.seniority or "").upper()
                bond_loan_upper = (asset.bond_loan or "").upper()
                
                # Include asset if it meets Test 2 non-senior secured criteria
                include_asset = False
                
                # Primary condition: NOT (SENIOR SECURED AND LOAN)
                if not (seniority_upper == 'SENIOR SECURED' and bond_loan_upper == 'LOAN'):
                    include_asset = True
                # ElseIf condition: Senior Secured Loans with specific S&P Priority Category  
                elif (seniority_upper == 'SENIOR SECURED' and bond_loan_upper == 'LOAN' and
                      asset.sp_priority_category and asset.sp_priority_category.upper() == 'SENIOR UNSECURED LOAN/SECOND LIEN LOAN'):
                    include_asset = True
                    
                if include_asset:
                    # Use issuer_id as primary identifier, fallback to issuer_name
                    obligor = getattr(asset, 'issuer_id', None) or asset.issuer_name or asset.obligor_name or "Unknown"
                    non_senior_obligor_exposures[obligor] = non_senior_obligor_exposures.get(obligor, Decimal('0')) + asset.par_amount
        
        max_exposure = max(non_senior_obligor_exposures.values()) if non_senior_obligor_exposures else Decimal('0')
        max_obligor = max(non_senior_obligor_exposures, key=non_senior_obligor_exposures.get) if non_senior_obligor_exposures else "None"
        
        ratio = (max_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=max_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Largest non-senior secured obligor '{max_obligor}': ${max_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_assets_paying_less_frequently_quarterly(self,
                                                          config: ThresholdConfiguration,
                                                          assets_dict: Dict[str, Asset],
                                                          total_par: Decimal,
                                                          threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 8: Limitation on Assets Paying Less Frequently than Quarterly"""
        
        less_frequent_exposure = Decimal('0')
        for asset in assets_dict.values():
            # Payment frequency < 4 means less frequent than quarterly
            if hasattr(asset, 'payment_frequency') and asset.payment_frequency and asset.payment_frequency < 4:
                less_frequent_exposure += asset.par_amount
        
        ratio = (less_frequent_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=less_frequent_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Assets paying less frequently than quarterly: ${less_frequent_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_fixed_rate_obligations_maximum(self,
                                                 config: ThresholdConfiguration,
                                                 assets_dict: Dict[str, Asset],
                                                 total_par: Decimal,
                                                 threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 9: Limitation on Fixed Rate Obligations"""
        
        fixed_rate_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.coupon_type == 'FIXED':
                fixed_rate_exposure += asset.par_amount
        
        ratio = (fixed_rate_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=fixed_rate_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Fixed rate obligations: ${fixed_rate_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_current_pay_obligations_maximum(self,
                                                  config: ThresholdConfiguration,
                                                  assets_dict: Dict[str, Asset],
                                                  total_par: Decimal,
                                                  threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 10: Limitation on Current Pay Obligations"""
        
        current_pay_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.flags.get('current_pay', False) if asset.flags else False:
                current_pay_exposure += asset.par_amount
        
        ratio = (current_pay_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=current_pay_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Current pay obligations: ${current_pay_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_dip_obligations_maximum(self,
                                          config: ThresholdConfiguration,
                                          assets_dict: Dict[str, Asset],
                                          total_par: Decimal,
                                          threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 11: Limitation on DIP Obligations"""
        
        dip_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.flags.get('dip', False) if asset.flags else False:
                dip_exposure += asset.par_amount
        
        ratio = (dip_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=dip_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"DIP obligations: ${dip_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_participation_interest_maximum(self,
                                                 config: ThresholdConfiguration,
                                                 assets_dict: Dict[str, Asset],
                                                 total_par: Decimal,
                                                 threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 13: Limitation on Participation Interest"""
        
        participation_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.flags.get('participation', False) if asset.flags else False:
                participation_exposure += asset.par_amount
        
        ratio = (participation_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=participation_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Participation interest: ${participation_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_bridge_loans_maximum(self,
                                       config: ThresholdConfiguration,
                                       assets_dict: Dict[str, Asset],
                                       total_par: Decimal,
                                       threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 28: Limitation on Bridge Loans"""
        
        bridge_loan_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.flags.get('bridge_loan', False) if asset.flags else False:
                bridge_loan_exposure += asset.par_amount
        
        ratio = (bridge_loan_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=bridge_loan_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Bridge loans: ${bridge_loan_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_deferrable_securities_maximum(self,
                                                config: ThresholdConfiguration,
                                                assets_dict: Dict[str, Asset],
                                                total_par: Decimal,
                                                threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 30: Limitation on Deferrable Securities"""
        
        deferrable_exposure = Decimal('0')
        for asset in assets_dict.values():
            if hasattr(asset, 'pik_asset') and asset.pik_asset:
                deferrable_exposure += asset.par_amount
        
        ratio = (deferrable_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=deferrable_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Deferrable securities: ${deferrable_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_facility_size_maximum(self,
                                        config: ThresholdConfiguration,
                                        assets_dict: Dict[str, Asset],
                                        total_par: Decimal,
                                        threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 31: Limitation on Facility Size"""
        
        small_facility_exposure = Decimal('0')
        for asset in assets_dict.values():
            facility_size = getattr(asset, 'facility_size', 0)
            if facility_size:
                # USA: < $150M, Other countries: < $250M
                if asset.country == 'USA' and facility_size < 150000000:
                    small_facility_exposure += asset.par_amount
                elif asset.country != 'USA' and facility_size < 250000000:
                    small_facility_exposure += asset.par_amount
        
        ratio = (small_facility_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=small_facility_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Small facility size assets: ${small_facility_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_countries_not_us_maximum(self,
                                           config: ThresholdConfiguration,
                                           assets_dict: Dict[str, Asset],
                                           total_par: Decimal,
                                           threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 14: Limitation on Countries Not US"""
        
        non_us_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.country and asset.country.upper() != 'USA':
                non_us_exposure += asset.par_amount
        
        ratio = (non_us_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=non_us_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Non-US country exposure: ${non_us_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_countries_not_us_canada_uk_maximum(self,
                                                     config: ThresholdConfiguration,
                                                     assets_dict: Dict[str, Asset],
                                                     total_par: Decimal,
                                                     threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 16: Limitation on Countries Not US Canada UK"""
        
        other_countries_exposure = Decimal('0')
        for asset in assets_dict.values():
            country = asset.country.upper() if asset.country else ''
            if country not in ['USA', 'CANADA', 'UNITED KINGDOM', 'UK']:
                other_countries_exposure += asset.par_amount
        
        ratio = (other_countries_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=other_countries_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Countries other than US/Canada/UK: ${other_countries_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_group_countries_maximum(self,
                                          config: ThresholdConfiguration,
                                          assets_dict: Dict[str, Asset],
                                          total_par: Decimal,
                                          threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 17: Limitation on Group Countries"""
        
        # Group countries are defined as Group I + Group II + Group III countries
        GROUP_I_COUNTRIES = ['NETHERLANDS', 'AUSTRALIA', 'NEW ZEALAND', 'UNITED KINGDOM']
        GROUP_II_COUNTRIES = ['GERMANY', 'SWEDEN', 'SWITZERLAND']
        GROUP_III_COUNTRIES = ['AUSTRIA', 'BELGIUM', 'DENMARK', 'FINLAND', 'FRANCE', 
                              'ICELAND', 'LIECHTENSTEIN', 'LUXEMBOURG', 'NORWAY', 'SPAIN']
        
        ALL_GROUP_COUNTRIES = GROUP_I_COUNTRIES + GROUP_II_COUNTRIES + GROUP_III_COUNTRIES
        
        group_countries_exposure = Decimal('0')
        for asset in assets_dict.values():
            country = asset.country.upper() if asset.country else ''
            if country in ALL_GROUP_COUNTRIES:
                group_countries_exposure += asset.par_amount
        
        ratio = (group_countries_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=group_countries_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Group countries exposure: ${group_countries_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_group_i_countries_maximum(self,
                                            config: ThresholdConfiguration,
                                            assets_dict: Dict[str, Asset],
                                            total_par: Decimal,
                                            threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 18: Limitation on Group I Countries"""
        
        # Group I countries per VBA specification
        GROUP_I_COUNTRIES = ['NETHERLANDS', 'AUSTRALIA', 'NEW ZEALAND', 'UNITED KINGDOM']
        
        group_i_exposure = Decimal('0')
        for asset in assets_dict.values():
            country = asset.country.upper() if asset.country else ''
            if country in GROUP_I_COUNTRIES:
                group_i_exposure += asset.par_amount
        
        ratio = (group_i_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=group_i_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Group I countries exposure: ${group_i_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_countries_canada_tax_jurisdictions_maximum(self,
                                                             config: ThresholdConfiguration,
                                                             assets_dict: Dict[str, Asset],
                                                             total_par: Decimal,
                                                             threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 15: Limitation on Countries Canada and Tax Jurisdictions"""
        
        # Canada and tax jurisdictions
        CANADA_TAX_JURISDICTIONS = ['CANADA']
        
        # Based on VBA analysis, tax jurisdictions typically include certain offshore locations
        # This may include countries that have specific tax treatment
        canada_tax_exposure = Decimal('0')
        
        for asset in assets_dict.values():
            country = asset.country.upper() if asset.country else ''
            if country in CANADA_TAX_JURISDICTIONS:
                canada_tax_exposure += asset.par_amount
        
        ratio = (canada_tax_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=canada_tax_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Canada and tax jurisdictions exposure: ${canada_tax_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_fourth_largest_sp_industry_maximum(self,
                                                     config: ThresholdConfiguration,
                                                     assets_dict: Dict[str, Asset],
                                                     total_par: Decimal,
                                                     threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 25: Limitation on 4th Largest SP Industry Classification"""
        
        # Calculate industry exposures
        industry_exposures = {}
        for asset in assets_dict.values():
            # Use S&P industry classification
            industry = getattr(asset, 'sp_industry', None) or 'Other'
            if industry and industry != 'Other':
                industry_exposures[industry] = industry_exposures.get(industry, Decimal('0')) + asset.par_amount
        
        # Sort industries by exposure descending
        sorted_industries = sorted(industry_exposures.items(), key=lambda x: x[1], reverse=True)
        
        # Get 4th largest industry exposure (index 3)
        fourth_exposure = sorted_industries[3][1] if len(sorted_industries) > 3 else Decimal('0')
        fourth_industry = sorted_industries[3][0] if len(sorted_industries) > 3 else "None"
        
        ratio = (fourth_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=fourth_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"4th largest S&P industry '{fourth_industry}': ${fourth_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_second_largest_sp_industry_maximum(self,
                                                     config: ThresholdConfiguration,
                                                     assets_dict: Dict[str, Asset],
                                                     total_par: Decimal,
                                                     threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 26: Limitation on 2nd Largest SP Classification"""
        
        # Calculate industry exposures
        industry_exposures = {}
        for asset in assets_dict.values():
            # Use S&P industry classification
            industry = getattr(asset, 'sp_industry', None) or 'Other'
            if industry and industry != 'Other':
                industry_exposures[industry] = industry_exposures.get(industry, Decimal('0')) + asset.par_amount
        
        # Sort industries by exposure descending
        sorted_industries = sorted(industry_exposures.items(), key=lambda x: x[1], reverse=True)
        
        # Get 2nd largest industry exposure (index 1)
        second_exposure = sorted_industries[1][1] if len(sorted_industries) > 1 else Decimal('0')
        second_industry = sorted_industries[1][0] if len(sorted_industries) > 1 else "None"
        
        ratio = (second_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=second_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"2nd largest S&P industry '{second_industry}': ${second_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_canada_maximum(self,
                                 config: ThresholdConfiguration,
                                 assets_dict: Dict[str, Asset],
                                 total_par: Decimal,
                                 threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 41: Limitation on Canada"""
        
        canada_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.country and asset.country.upper() == 'CANADA':
                canada_exposure += asset.par_amount
        
        ratio = (canada_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=canada_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Canada exposure: ${canada_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_letter_of_credit_maximum(self,
                                           config: ThresholdConfiguration,
                                           assets_dict: Dict[str, Asset],
                                           total_par: Decimal,
                                           threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 42: Limitation on Letter of Credit"""
        
        loc_exposure = Decimal('0')
        for asset in assets_dict.values():
            if getattr(asset, 'letter_of_credit', False):
                loc_exposure += asset.par_amount
        
        ratio = (loc_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=loc_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Letter of credit exposure: ${loc_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_long_dated_maximum(self,
                                     config: ThresholdConfiguration,
                                     assets_dict: Dict[str, Asset],
                                     total_par: Decimal,
                                     threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 43: Limitation on Long Dated"""
        
        long_dated_exposure = Decimal('0')
        for asset in assets_dict.values():
            # Long dated typically means maturity > 6 years
            if asset.maturity:
                from datetime import datetime, date
                try:
                    if isinstance(asset.maturity, str):
                        maturity_date = datetime.strptime(asset.maturity, '%Y-%m-%d').date()
                    else:
                        maturity_date = asset.maturity
                    
                    analysis_date = date(2016, 3, 23)  # Default analysis date
                    years_to_maturity = (maturity_date - analysis_date).days / 365.25
                    
                    if years_to_maturity > 6.0:
                        long_dated_exposure += asset.par_amount
                except:
                    pass  # Skip assets with invalid maturity data
        
        ratio = (long_dated_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=long_dated_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Long dated assets (>6 years): ${long_dated_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_unsecured_loans_maximum(self,
                                          config: ThresholdConfiguration,
                                          assets_dict: Dict[str, Asset],
                                          total_par: Decimal,
                                          threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 44: Limitation on Unsecured Loans"""
        
        unsecured_exposure = Decimal('0')
        for asset in assets_dict.values():
            if asset.seniority and 'unsecured' in asset.seniority.lower():
                unsecured_exposure += asset.par_amount
        
        ratio = (unsecured_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=unsecured_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Unsecured loans exposure: ${unsecured_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_swap_non_discount_maximum(self,
                                            config: ThresholdConfiguration,
                                            assets_dict: Dict[str, Asset],
                                            total_par: Decimal,
                                            threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 45: Limitation on Swap Non Discount"""
        
        swap_non_discount_exposure = Decimal('0')
        for asset in assets_dict.values():
            # Check for swap non discount attributes
            if getattr(asset, 'swap_non_discount', False):
                swap_non_discount_exposure += asset.par_amount
        
        ratio = (swap_non_discount_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=swap_non_discount_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Swap non discount exposure: ${swap_non_discount_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_unfunded_commitments_maximum(self,
                                               config: ThresholdConfiguration,
                                               assets_dict: Dict[str, Asset],
                                               total_par: Decimal,
                                               threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 12: Limitation on Unfunded Commitments"""
        
        unfunded_exposure = Decimal('0')
        for asset in assets_dict.values():
            unfunded_amount = getattr(asset, 'unfunded_amount', 0)
            if unfunded_amount and unfunded_amount > 0:
                unfunded_exposure += Decimal(str(unfunded_amount))
        
        ratio = (unfunded_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=unfunded_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Unfunded commitments: ${unfunded_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_non_emerging_market_obligors_maximum(self,
                                                       config: ThresholdConfiguration,
                                                       assets_dict: Dict[str, Asset],
                                                       total_par: Decimal,
                                                       threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 47: Limitation on Non-Emerging Market Obligors"""
        
        # Non-emerging market countries (developed markets)
        EMERGING_MARKETS = ['BRAZIL', 'CHINA', 'INDIA', 'RUSSIA', 'SOUTH AFRICA', 'MEXICO', 
                           'TURKEY', 'ARGENTINA', 'CHILE', 'COLOMBIA', 'PERU', 'THAILAND',
                           'MALAYSIA', 'INDONESIA', 'PHILIPPINES', 'TAIWAN', 'SOUTH KOREA']
        
        non_emerging_exposure = Decimal('0')
        for asset in assets_dict.values():
            country = asset.country.upper() if asset.country else ''
            if country and country not in EMERGING_MARKETS and country != 'USA':
                non_emerging_exposure += asset.par_amount
        
        ratio = (non_emerging_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=non_emerging_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Non-emerging market exposure: ${non_emerging_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_sp_criteria_maximum(self,
                                      config: ThresholdConfiguration,
                                      assets_dict: Dict[str, Asset],
                                      total_par: Decimal,
                                      threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 48: Limitation on SP Criteria"""
        
        sp_criteria_exposure = Decimal('0')
        for asset in assets_dict.values():
            # Check for S&P criteria attributes (structured products, etc.)
            if getattr(asset, 'sp_criteria', False) or getattr(asset, 'structured_finance', False):
                sp_criteria_exposure += asset.par_amount
        
        ratio = (sp_criteria_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=sp_criteria_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"S&P criteria assets: ${sp_criteria_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_first_largest_moody_industry_maximum(self,
                                                       config: ThresholdConfiguration,
                                                       assets_dict: Dict[str, Asset],
                                                       total_par: Decimal,
                                                       threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 49: Limitation on 1st Largest Moody Industry"""
        
        # Calculate Moody industry exposures
        industry_exposures = {}
        for asset in assets_dict.values():
            industry = getattr(asset, 'mdy_industry', None) or 'Other'
            if industry and industry != 'Other':
                industry_exposures[industry] = industry_exposures.get(industry, Decimal('0')) + asset.par_amount
        
        # Sort industries by exposure descending
        sorted_industries = sorted(industry_exposures.items(), key=lambda x: x[1], reverse=True)
        
        # Get 1st largest industry exposure
        first_exposure = sorted_industries[0][1] if sorted_industries else Decimal('0')
        first_industry = sorted_industries[0][0] if sorted_industries else "None"
        
        ratio = (first_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=first_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"1st largest Moody industry '{first_industry}': ${first_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_second_largest_moody_industry_maximum(self,
                                                        config: ThresholdConfiguration,
                                                        assets_dict: Dict[str, Asset],
                                                        total_par: Decimal,
                                                        threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 50: Limitation on 2nd Largest Moody Industry"""
        
        # Calculate Moody industry exposures
        industry_exposures = {}
        for asset in assets_dict.values():
            industry = getattr(asset, 'mdy_industry', None) or 'Other'
            if industry and industry != 'Other':
                industry_exposures[industry] = industry_exposures.get(industry, Decimal('0')) + asset.par_amount
        
        # Sort industries by exposure descending
        sorted_industries = sorted(industry_exposures.items(), key=lambda x: x[1], reverse=True)
        
        # Get 2nd largest industry exposure
        second_exposure = sorted_industries[1][1] if len(sorted_industries) > 1 else Decimal('0')
        second_industry = sorted_industries[1][0] if len(sorted_industries) > 1 else "None"
        
        ratio = (second_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=second_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"2nd largest Moody industry '{second_industry}': ${second_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_third_largest_moody_industry_maximum(self,
                                                       config: ThresholdConfiguration,
                                                       assets_dict: Dict[str, Asset],
                                                       total_par: Decimal,
                                                       threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 51: Limitation on 3rd Largest Moody Industry"""
        
        # Calculate Moody industry exposures
        industry_exposures = {}
        for asset in assets_dict.values():
            industry = getattr(asset, 'mdy_industry', None) or 'Other'
            if industry and industry != 'Other':
                industry_exposures[industry] = industry_exposures.get(industry, Decimal('0')) + asset.par_amount
        
        # Sort industries by exposure descending
        sorted_industries = sorted(industry_exposures.items(), key=lambda x: x[1], reverse=True)
        
        # Get 3rd largest industry exposure
        third_exposure = sorted_industries[2][1] if len(sorted_industries) > 2 else Decimal('0')
        third_industry = sorted_industries[2][0] if len(sorted_industries) > 2 else "None"
        
        ratio = (third_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=third_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"3rd largest Moody industry '{third_industry}': ${third_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_fourth_largest_moody_industry_maximum(self,
                                                        config: ThresholdConfiguration,
                                                        assets_dict: Dict[str, Asset],
                                                        total_par: Decimal,
                                                        threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 52: Limitation on 4th Largest Moody Industry"""
        
        # Calculate Moody industry exposures
        industry_exposures = {}
        for asset in assets_dict.values():
            industry = getattr(asset, 'mdy_industry', None) or 'Other'
            if industry and industry != 'Other':
                industry_exposures[industry] = industry_exposures.get(industry, Decimal('0')) + asset.par_amount
        
        # Sort industries by exposure descending
        sorted_industries = sorted(industry_exposures.items(), key=lambda x: x[1], reverse=True)
        
        # Get 4th largest industry exposure
        fourth_exposure = sorted_industries[3][1] if len(sorted_industries) > 3 else Decimal('0')
        fourth_industry = sorted_industries[3][0] if len(sorted_industries) > 3 else "None"
        
        ratio = (fourth_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=fourth_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"4th largest Moody industry '{fourth_industry}': ${fourth_exposure:,.2f} ({percentage:.2f}%)"
        )
    
    async def _test_facility_size_mag08_maximum(self,
                                              config: ThresholdConfiguration,
                                              assets_dict: Dict[str, Asset],
                                              total_par: Decimal,
                                              threshold: Decimal, principal_proceeds: Decimal = Decimal("0")) -> DatabaseTestResult:
        """Test 53: Limitation on Facility Size MAG08"""
        
        # Similar to regular facility size test but potentially with MAG08-specific thresholds
        small_facility_exposure = Decimal('0')
        for asset in assets_dict.values():
            facility_size = getattr(asset, 'facility_size', 0)
            if facility_size:
                # MAG08 specific: < $100M facilities
                if facility_size < 100000000:
                    small_facility_exposure += asset.par_amount
        
        ratio = (small_facility_exposure / total_par) if total_par > 0 else Decimal('0')
        percentage = ratio * 100
        pass_fail = 'PASS' if ratio <= threshold else 'FAIL'
        excess_amount = max(Decimal('0'), ratio - threshold)
        
        return DatabaseTestResult(
            test_id=config.test_id,
            test_number=config.test_number,
            test_name=config.test_name,
            threshold=threshold,
            result=ratio,
            numerator=small_facility_exposure,
            denominator=total_par + principal_proceeds,
            pass_fail=pass_fail,
            excess_amount=excess_amount,
            threshold_source=config.threshold_source,
            is_custom_override=config.is_custom_override,
            effective_date=config.effective_date,
            mag_version=config.mag_version,
            comments=f"Small facility size MAG08 (<$100M): ${small_facility_exposure:,.2f} ({percentage:.2f}%)"
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
