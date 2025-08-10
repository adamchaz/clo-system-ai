"""
CLO Concentration Test System
Placeholder implementation for ConcentrationTest.cls functionality
Handles 91 different compliance test types for CLO portfolios
"""

from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
from datetime import date
from enum import Enum

from .asset import Asset


class TestType(str, Enum):
    """Types of concentration tests"""
    OBLIGOR_CONCENTRATION = "OBLIGOR_CONCENTRATION"
    INDUSTRY_CONCENTRATION = "INDUSTRY_CONCENTRATION"
    GEOGRAPHIC_CONCENTRATION = "GEOGRAPHIC_CONCENTRATION"
    RATING_CONCENTRATION = "RATING_CONCENTRATION"
    COVENANT_LITE = "COVENANT_LITE"
    WEIGHTED_AVERAGE_LIFE = "WEIGHTED_AVERAGE_LIFE"
    WEIGHTED_AVERAGE_RATING_FACTOR = "WEIGHTED_AVERAGE_RATING_FACTOR"
    SECOND_LIEN = "SECOND_LIEN"
    CCC_ASSETS = "CCC_ASSETS"
    DEFAULTED_ASSETS = "DEFAULTED_ASSETS"


class TestResult:
    """Individual test result"""
    
    def __init__(self, test_number: int, test_name: str, threshold: Decimal, 
                 result: Decimal, pass_fail: str, comment: str = ""):
        self.test_number = test_number
        self.test_name = test_name
        self.threshold = threshold
        self.result = result
        self.pass_fail = pass_fail  # "PASS", "FAIL", "N/A"
        self.pass_fail_comment = comment


class ConcentrationTest:
    """
    Concentration test engine - placeholder for VBA ConcentrationTest.cls
    This is a simplified implementation focusing on core structure
    """
    
    def __init__(self):
        """Initialize concentration test engine"""
        self.test_results: List[TestResult] = []
        self.objective_dict: Dict[str, Decimal] = {}
        self.previous_objective_value = Decimal('0')
        self.current_objective_value = Decimal('0')
    
    def run_test(self, assets_dict: Dict[str, Asset], principal_proceeds: Decimal) -> None:
        """
        Run all concentration tests - placeholder for VBA RunTest()
        
        Args:
            assets_dict: Dictionary of assets by BLKRockID
            principal_proceeds: Available principal cash
        """
        # Clear previous results
        self.test_results.clear()
        
        # Calculate portfolio metrics
        total_par = sum(asset.par_amount for asset in assets_dict.values())
        
        if total_par <= 0:
            return
        
        # Example test implementations (simplified)
        self._test_obligor_concentration(assets_dict, total_par)
        self._test_industry_concentration(assets_dict, total_par)
        self._test_rating_concentration(assets_dict, total_par)
        self._test_covenant_lite(assets_dict, total_par)
        self._test_ccc_assets(assets_dict, total_par)
        self._test_defaulted_assets(assets_dict, total_par)
        
        # Calculate objective function
        self._calculate_objective_function()
    
    def _test_obligor_concentration(self, assets_dict: Dict[str, Asset], total_par: Decimal) -> None:
        """Test obligor concentration limits"""
        obligor_exposures = {}
        
        # Aggregate by obligor
        for asset in assets_dict.values():
            obligor = asset.issuer_name or "Unknown"
            if obligor not in obligor_exposures:
                obligor_exposures[obligor] = Decimal('0')
            obligor_exposures[obligor] += asset.par_amount
        
        # Find largest exposure
        max_exposure = max(obligor_exposures.values()) if obligor_exposures else Decimal('0')
        max_concentration = (max_exposure / total_par) * 100 if total_par > 0 else Decimal('0')
        
        # Test against 2% threshold
        threshold = Decimal('2.0')
        pass_fail = "PASS" if max_concentration <= threshold else "FAIL"
        
        result = TestResult(
            test_number=1,
            test_name="Single Obligor Concentration",
            threshold=threshold,
            result=max_concentration,
            pass_fail=pass_fail,
            comment=f"Max exposure: {max_concentration:.3f}%"
        )
        self.test_results.append(result)
    
    def _test_industry_concentration(self, assets_dict: Dict[str, Asset], total_par: Decimal) -> None:
        """Test industry concentration limits"""
        industry_exposures = {}
        
        # Aggregate by industry
        for asset in assets_dict.values():
            industry = asset.sp_industry or "Unknown"
            if industry not in industry_exposures:
                industry_exposures[industry] = Decimal('0')
            industry_exposures[industry] += asset.par_amount
        
        # Find largest exposure
        max_exposure = max(industry_exposures.values()) if industry_exposures else Decimal('0')
        max_concentration = (max_exposure / total_par) * 100 if total_par > 0 else Decimal('0')
        
        # Test against 12% threshold
        threshold = Decimal('12.0')
        pass_fail = "PASS" if max_concentration <= threshold else "FAIL"
        
        result = TestResult(
            test_number=10,
            test_name="Single Industry Concentration",
            threshold=threshold,
            result=max_concentration,
            pass_fail=pass_fail,
            comment=f"Max industry exposure: {max_concentration:.3f}%"
        )
        self.test_results.append(result)
    
    def _test_rating_concentration(self, assets_dict: Dict[str, Asset], total_par: Decimal) -> None:
        """Test rating concentration"""
        rating_exposures = {}
        
        # Aggregate by S&P rating
        for asset in assets_dict.values():
            rating = asset.sp_rating or "NR"
            if rating not in rating_exposures:
                rating_exposures[rating] = Decimal('0')
            rating_exposures[rating] += asset.par_amount
        
        # Calculate B-rated concentration
        b_ratings = ['B+', 'B', 'B-']
        b_exposure = sum(rating_exposures.get(rating, Decimal('0')) for rating in b_ratings)
        b_concentration = (b_exposure / total_par) * 100 if total_par > 0 else Decimal('0')
        
        # Test against 70% threshold
        threshold = Decimal('70.0')
        pass_fail = "PASS" if b_concentration <= threshold else "FAIL"
        
        result = TestResult(
            test_number=20,
            test_name="B-Rated Assets",
            threshold=threshold,
            result=b_concentration,
            pass_fail=pass_fail,
            comment=f"B-rated concentration: {b_concentration:.3f}%"
        )
        self.test_results.append(result)
    
    def _test_covenant_lite(self, assets_dict: Dict[str, Asset], total_par: Decimal) -> None:
        """Test covenant-lite concentration"""
        cov_lite_exposure = Decimal('0')
        
        for asset in assets_dict.values():
            if asset.cov_lite:
                cov_lite_exposure += asset.par_amount
        
        cov_lite_concentration = (cov_lite_exposure / total_par) * 100 if total_par > 0 else Decimal('0')
        
        # Test against 7.5% threshold
        threshold = Decimal('7.5')
        pass_fail = "PASS" if cov_lite_concentration <= threshold else "FAIL"
        
        result = TestResult(
            test_number=30,
            test_name="Covenant-Lite Assets",
            threshold=threshold,
            result=cov_lite_concentration,
            pass_fail=pass_fail,
            comment=f"Cov-Lite concentration: {cov_lite_concentration:.3f}%"
        )
        self.test_results.append(result)
    
    def _test_ccc_assets(self, assets_dict: Dict[str, Asset], total_par: Decimal) -> None:
        """Test CCC-rated assets concentration"""
        ccc_exposure = Decimal('0')
        
        for asset in assets_dict.values():
            if asset.sp_rating and asset.sp_rating.startswith('CCC'):
                ccc_exposure += asset.par_amount
        
        ccc_concentration = (ccc_exposure / total_par) * 100 if total_par > 0 else Decimal('0')
        
        # Test against 7.5% threshold
        threshold = Decimal('7.5')
        pass_fail = "PASS" if ccc_concentration <= threshold else "FAIL"
        
        result = TestResult(
            test_number=35,
            test_name="CCC-Rated Assets",
            threshold=threshold,
            result=ccc_concentration,
            pass_fail=pass_fail,
            comment=f"CCC concentration: {ccc_concentration:.3f}%"
        )
        self.test_results.append(result)
    
    def _test_defaulted_assets(self, assets_dict: Dict[str, Asset], total_par: Decimal) -> None:
        """Test defaulted assets concentration"""
        defaulted_exposure = Decimal('0')
        
        for asset in assets_dict.values():
            if asset.default_asset:
                defaulted_exposure += asset.par_amount
        
        defaulted_concentration = (defaulted_exposure / total_par) * 100 if total_par > 0 else Decimal('0')
        
        # Test against 5% threshold
        threshold = Decimal('5.0')
        pass_fail = "PASS" if defaulted_concentration <= threshold else "FAIL"
        
        result = TestResult(
            test_number=40,
            test_name="Defaulted Assets",
            threshold=threshold,
            result=defaulted_concentration,
            pass_fail=pass_fail,
            comment=f"Defaulted concentration: {defaulted_concentration:.3f}%"
        )
        self.test_results.append(result)
    
    def _calculate_objective_function(self) -> None:
        """Calculate objective function based on test results"""
        # Simple objective function: sum of violations weighted by severity
        objective_value = Decimal('0')
        
        for result in self.test_results:
            if result.pass_fail == "FAIL":
                # Weight by excess over threshold
                excess = result.result - result.threshold
                objective_value += excess
        
        self.current_objective_value = objective_value
        
        # Update objective dictionary for optimization
        self.objective_dict.clear()
        for i, result in enumerate(self.test_results):
            test_key = f"Test_{result.test_number}"
            if result.pass_fail == "FAIL":
                self.objective_dict[test_key] = result.result - result.threshold
            else:
                self.objective_dict[test_key] = Decimal('0')
    
    def get_results(self) -> List[TestResult]:
        """Get all test results"""
        return self.test_results.copy()
    
    def get_objective_dict(self) -> Dict[str, Decimal]:
        """Get objective function components dictionary"""
        return self.objective_dict.copy()
    
    def calc_objective_function(self) -> Decimal:
        """Calculate and return objective function value"""
        return self.current_objective_value
    
    def calc_asset_objective(self, asset_dict: Dict[str, Asset], 
                           transaction_type: str) -> Dict[str, Decimal]:
        """
        Calculate asset-specific objective function impact
        Placeholder for complex VBA CalcAssetObject2() logic
        """
        # Simplified implementation
        asset_objectives = {}
        
        for blkrock_id, asset in asset_dict.items():
            # Calculate impact of adding/removing this asset
            impact = Decimal('0')
            
            # Example: penalize high concentrations
            if asset.sp_rating and asset.sp_rating.startswith('CCC'):
                impact += asset.par_amount * Decimal('0.1')  # CCC penalty
            
            if asset.default_asset:
                impact += asset.par_amount * Decimal('0.2')  # Default penalty
            
            asset_objectives[blkrock_id] = impact
        
        return asset_objectives
    
    def update_previous_values(self) -> None:
        """Update previous values for next iteration"""
        self.previous_objective_value = self.current_objective_value
    
    def get_result_output(self) -> List[List[Any]]:
        """
        Get formatted results output - VBA GetResultOutput() conversion
        """
        if not self.test_results:
            return []
        
        # Create output array with headers
        output = []
        headers = ["Test Num", "Test Name", "Threshold", "Results", "Pass/Fail"]
        output.append(headers)
        
        # Add test results
        for result in self.test_results:
            row = [
                result.test_number,
                result.test_name,
                float(result.threshold),
                float(result.result),
                result.pass_fail
            ]
            output.append(row)
        
        # Add objective function
        objective_row = ["", "Objective Function", "", float(self.current_objective_value), ""]
        output.append(objective_row)
        
        return output


class RatingDerivations:
    """
    Rating derivation system - placeholder for VBA RatingDerivations.cls
    Handles Moody's and S&P rating conversions and calculations
    """
    
    def __init__(self):
        """Initialize rating derivations"""
        # Rating mapping tables (simplified)
        self.sp_to_numeric = {
            'AAA': 1, 'AA+': 2, 'AA': 3, 'AA-': 4,
            'A+': 5, 'A': 6, 'A-': 7,
            'BBB+': 8, 'BBB': 9, 'BBB-': 10,
            'BB+': 11, 'BB': 12, 'BB-': 13,
            'B+': 14, 'B': 15, 'B-': 16,
            'CCC+': 17, 'CCC': 18, 'CCC-': 19,
            'CC': 20, 'C': 21, 'D': 22
        }
        
        self.moody_to_numeric = {
            'Aaa': 1, 'Aa1': 2, 'Aa2': 3, 'Aa3': 4,
            'A1': 5, 'A2': 6, 'A3': 7,
            'Baa1': 8, 'Baa2': 9, 'Baa3': 10,
            'Ba1': 11, 'Ba2': 12, 'Ba3': 13,
            'B1': 14, 'B2': 15, 'B3': 16,
            'Caa1': 17, 'Caa2': 18, 'Caa3': 19,
            'Ca': 20, 'C': 21
        }
    
    def get_moodys_rating(self, asset: Asset) -> str:
        """Derive Moody's rating - placeholder for VBA GetMoodysRating()"""
        # Simplified: use S&P rating to estimate Moody's
        if asset.sp_rating:
            sp_numeric = self.sp_to_numeric.get(asset.sp_rating, 15)
            # Simple mapping (in reality this would be more complex)
            moody_ratings = list(self.moody_to_numeric.keys())
            if sp_numeric <= len(moody_ratings):
                derived_rating = moody_ratings[sp_numeric - 1]
                asset.mdy_rating = derived_rating
                return derived_rating
        
        return asset.mdy_rating or "B2"  # Default
    
    def get_moodys_def_prob_rating(self, asset: Asset) -> str:
        """Get Moody's default probability rating - placeholder"""
        # Simplified implementation
        rating = asset.mdy_rating or self.get_moodys_rating(asset)
        asset.mdy_dp_rating = rating
        return rating
    
    def get_moodys_def_prob_rating_warf(self, asset: Asset) -> str:
        """Get Moody's WARF rating - placeholder"""
        # Simplified implementation
        rating = asset.mdy_dp_rating or self.get_moodys_def_prob_rating(asset)
        asset.mdy_dp_rating_warf = rating
        return rating
    
    def get_snp_ratings(self, asset: Asset) -> str:
        """Get S&P rating - placeholder for VBA GetSnPRatings()"""
        # If already has S&P rating, return it
        if asset.sp_rating:
            return asset.sp_rating
        
        # Otherwise derive from Moody's
        if asset.mdy_rating:
            moody_numeric = self.moody_to_numeric.get(asset.mdy_rating, 15)
            sp_ratings = list(self.sp_to_numeric.keys())
            if moody_numeric <= len(sp_ratings):
                derived_rating = sp_ratings[moody_numeric - 1]
                asset.sp_rating = derived_rating
                return derived_rating
        
        return asset.sp_rating or "B"  # Default
    
    def moody_recovery_rate(self, asset: Asset) -> Decimal:
        """Calculate Moody's recovery rate - placeholder"""
        # Simplified recovery rate calculation
        rating = asset.mdy_rating or "B2"
        
        recovery_rates = {
            'Aaa': Decimal('0.70'), 'Aa1': Decimal('0.70'), 'Aa2': Decimal('0.70'),
            'A1': Decimal('0.65'), 'A2': Decimal('0.65'), 'A3': Decimal('0.65'),
            'Baa1': Decimal('0.60'), 'Baa2': Decimal('0.60'), 'Baa3': Decimal('0.60'),
            'Ba1': Decimal('0.50'), 'Ba2': Decimal('0.50'), 'Ba3': Decimal('0.50'),
            'B1': Decimal('0.40'), 'B2': Decimal('0.40'), 'B3': Decimal('0.40'),
            'Caa1': Decimal('0.30'), 'Caa2': Decimal('0.25'), 'Caa3': Decimal('0.20')
        }
        
        recovery_rate = recovery_rates.get(rating, Decimal('0.35'))  # Default 35%
        asset.mdy_recovery_rate = recovery_rate
        return recovery_rate
    
    def return_ratings_rank(self, rating: str) -> int:
        """Return numeric rating rank - placeholder"""
        if not rating:
            return 15  # Default to B equivalent
        
        # Try S&P first
        if rating in self.sp_to_numeric:
            return self.sp_to_numeric[rating]
        
        # Try Moody's
        if rating in self.moody_to_numeric:
            return self.moody_to_numeric[rating]
        
        return 15  # Default


class TestSettings:
    """
    Test configuration settings - placeholder for VBA TestSettings.cls
    """
    
    def __init__(self):
        """Initialize test settings"""
        self.obligor_limit = Decimal('2.0')  # 2% single obligor limit
        self.industry_limit = Decimal('12.0')  # 12% single industry limit
        self.ccc_limit = Decimal('7.5')  # 7.5% CCC limit
        self.cov_lite_limit = Decimal('7.5')  # 7.5% covenant-lite limit
        self.defaulted_limit = Decimal('5.0')  # 5% defaulted assets limit
        
        # Objective function weights
        self.test_weights: Dict[int, Decimal] = {
            1: Decimal('1.0'),   # Obligor concentration
            10: Decimal('0.8'),  # Industry concentration
            20: Decimal('0.6'),  # Rating concentration
            30: Decimal('0.7'),  # Covenant-lite
            35: Decimal('0.9'),  # CCC assets
            40: Decimal('1.0')   # Defaulted assets
        }