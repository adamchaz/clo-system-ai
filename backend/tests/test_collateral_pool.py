"""
Test Suite for Collateral Pool System
Tests CollateralPool.cls and CollateralPoolForCLO.cls functionality
NOTE: Old VBA-based concentration test code removed - now using database-driven approach
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock, patch

from app.models.collateral_pool import (
    CollateralPool, CollateralPoolAsset, CollateralPoolAccount,
    CollateralPoolForCLO, AssetCashFlowForDeal,
    CollateralPoolCalculator, CollateralPoolForCLOCalculator,
    TransactionType, AnalysisType
)
from app.models.asset import Asset
from app.models.clo_deal_engine import Account, AccountType, CashType
from app.services.collateral_pool_service import CollateralPoolService, HypoInputs


class TestCollateralPoolModels:
    """Test SQLAlchemy model functionality"""
    
    def test_collateral_pool_creation(self):
        """Test basic collateral pool model creation"""
        pool = CollateralPool(
            deal_id="TEST_DEAL_001",
            pool_name="Main Pool",
            analysis_date=date(2023, 12, 15),
            analysis_type=AnalysisType.STATIC.value
        )
        
        assert pool.deal_id == "TEST_DEAL_001"
        assert pool.pool_name == "Main Pool"
        assert pool.analysis_date == date(2023, 12, 15)
        assert pool.analysis_type == AnalysisType.STATIC.value
        assert pool.use_rating_migration is False
        assert pool.current_period == 1
        assert pool.rerun_tests_required is True
        assert pool.total_par_amount == 0
        assert pool.total_assets == 0
    
    def test_collateral_pool_asset_creation(self):
        """Test pool asset position tracking"""
        pool_asset = CollateralPoolAsset(
            pool_id=1,
            asset_id=100,
            par_amount=Decimal('1000000'),
            original_par_amount=Decimal('1000000'),
            position_date=date.today()
        )
        
        assert pool_asset.pool_id == 1
        assert pool_asset.asset_id == 100
        assert pool_asset.par_amount == Decimal('1000000')
        assert pool_asset.original_par_amount == Decimal('1000000')
        assert pool_asset.is_defaulted is False
    
    def test_collateral_pool_account(self):
        """Test pool account cash tracking"""
        account = CollateralPoolAccount(
            pool_id=1,
            account_type=AccountType.COLLECTION.value,
            principal_proceeds=Decimal('50000000'),
            interest_proceeds=Decimal('2000000')
        )
        
        assert account.pool_id == 1
        assert account.account_type == AccountType.COLLECTION.value
        assert account.principal_proceeds == Decimal('50000000')
        assert account.interest_proceeds == Decimal('2000000')
        assert account.total_proceeds == Decimal('52000000')
    
    def test_collateral_pool_for_clo_creation(self):
        """Test deal-specific pool creation"""
        pool = CollateralPoolForCLO(
            deal_id="TEST_DEAL_001",
            parent_pool_id=1,
            analysis_date=date(2023, 12, 15),
            use_rating_migration=True
        )
        
        assert pool.deal_id == "TEST_DEAL_001"
        assert pool.parent_pool_id == 1
        assert pool.analysis_date == date(2023, 12, 15)
        assert pool.use_rating_migration is True
        assert pool.current_period == 1


class TestCollateralPoolCalculator:
    """Test portfolio calculation logic"""
    
    def setup_method(self):
        """Setup test data"""
        self.pool_config = CollateralPool(
            pool_id=1,
            deal_id="TEST_DEAL_001",
            pool_name="Test Pool",
            analysis_date=date(2023, 12, 15),
            analysis_type=AnalysisType.STATIC.value
        )
        
        self.calculator = CollateralPoolCalculator(self.pool_config)
        
        # Setup test assets
        self.asset1 = Mock(spec=Asset)
        self.asset1.blkrock_id = "ASSET001"
        self.asset1.par_amount = Decimal('1000000')
        self.asset1.market_value = Decimal('98.5')
        self.asset1.issuer_name = "Test Issuer 1"
        self.asset1.sp_rating = "B+"
        self.asset1.sp_industry = "Technology"
        self.asset1.default_asset = False
        self.asset1.maturity = date(2028, 6, 15)
        # Configure mock methods
        self.asset1.copy = Mock(return_value=self.asset1)
        self.asset1.add_par = Mock()
        self.asset1.apply_filter = Mock(return_value=True)
        self.asset1.add_moody_rating = Mock()
        self.asset1.add_sp_rating = Mock()
        self.asset1.mdy_rating = "B2"  # Add missing rating attribute
        self.asset1.cov_lite = False  # Add covenant lite attribute
        
        self.asset2 = Mock(spec=Asset)
        self.asset2.blkrock_id = "ASSET002"
        self.asset2.par_amount = Decimal('2000000')
        self.asset2.market_value = Decimal('102.25')
        self.asset2.issuer_name = "Test Issuer 2"
        self.asset2.sp_rating = "BB-"
        self.asset2.sp_industry = "Healthcare"
        self.asset2.default_asset = False
        self.asset2.maturity = date(2027, 12, 31)
        # Configure mock methods
        self.asset2.copy = Mock(return_value=self.asset2)
        self.asset2.add_par = Mock()
        self.asset2.apply_filter = Mock(return_value=True)
        self.asset2.add_moody_rating = Mock()
        self.asset2.add_sp_rating = Mock()
        self.asset2.mdy_rating = "Ba3"  # Add missing rating attribute
        self.asset2.cov_lite = False  # Add covenant lite attribute
        
        # Setup test accounts
        self.collection_account = Account(AccountType.COLLECTION)
        self.collection_account.principal_balance = Decimal('10000000')
        self.collection_account.interest_balance = Decimal('500000')
        
        self.calculator.accounts_dict[AccountType.COLLECTION] = self.collection_account
    
    def test_check_account_balance(self):
        """Test VBA CheckAccountBalance() conversion"""
        # Test principal balance
        principal_balance = self.calculator.check_account_balance(
            AccountType.COLLECTION, CashType.PRINCIPAL
        )
        assert principal_balance == Decimal('10000000')
        
        # Test interest balance
        interest_balance = self.calculator.check_account_balance(
            AccountType.COLLECTION, CashType.INTEREST
        )
        assert interest_balance == Decimal('500000')
        
        # Test total balance
        total_balance = self.calculator.check_account_balance(
            AccountType.COLLECTION, CashType.TOTAL
        )
        assert total_balance == Decimal('10500000')
        
        # Test non-existent account
        zero_balance = self.calculator.check_account_balance(
            AccountType.RAMP_UP, CashType.PRINCIPAL
        )
        assert zero_balance == Decimal('0')
    
    def test_add_asset(self):
        """Test VBA AddAsset() conversion"""
        # Add new asset
        self.calculator.add_asset(self.asset1)
        
        assert "ASSET001" in self.calculator.assets_dict
        assert self.calculator.assets_dict["ASSET001"] == self.asset1
        assert self.calculator.rerun_tests_required is True
        
        # Add existing asset (should increase position)
        additional_asset = Mock(spec=Asset)
        additional_asset.blkrock_id = "ASSET001"
        additional_asset.par_amount = Decimal('500000')
        
        self.calculator.add_asset(additional_asset)
        
        # Should call add_par on existing asset
        self.asset1.add_par.assert_called_with(Decimal('500000'))
    
    def test_remove_asset(self):
        """Test VBA RemoveAsset() conversion"""
        # Add then remove asset
        self.calculator.add_asset(self.asset1)
        assert "ASSET001" in self.calculator.assets_dict
        
        self.calculator.remove_asset("ASSET001")
        assert "ASSET001" not in self.calculator.assets_dict
        assert self.calculator.rerun_tests_required is True
    
    def test_get_asset(self):
        """Test VBA GetAsset() and GetAssetNonCopy() conversion"""
        self.calculator.add_asset(self.asset1)
        
        # Test copy version
        copied_asset = self.calculator.get_asset("ASSET001", copy=True)
        assert copied_asset == self.asset1
        self.asset1.copy.assert_called()
        
        # Test non-copy version
        direct_asset = self.calculator.get_asset("ASSET001", copy=False)
        assert direct_asset == self.asset1
        
        # Test non-existent asset
        none_asset = self.calculator.get_asset("NONEXISTENT")
        assert none_asset is None
    
    def test_get_asset_parameter(self):
        """Test VBA GetAssetParameter() conversion"""
        self.calculator.add_asset(self.asset1)
        
        # Test various parameter mappings
        assert self.calculator.get_asset_parameter("ASSET001", "PAR AMOUNT") == Decimal('1000000')
        assert self.calculator.get_asset_parameter("ASSET001", "MARKET VALUE") == Decimal('98.5')
        assert self.calculator.get_asset_parameter("ASSET001", "S & P RATING") == "B+"
        assert self.calculator.get_asset_parameter("ASSET001", "ISSUE NAME") == "Test Issuer 1"
        assert self.calculator.get_asset_parameter("ASSET001", "DEFAULTED") is False
        assert self.calculator.get_asset_parameter("ASSET001", "MATURITY") == date(2028, 6, 15)
        
        # Test non-existent asset
        assert self.calculator.get_asset_parameter("NONEXISTENT", "PAR AMOUNT") is None
    
    def test_get_collateral_par_amount(self):
        """Test VBA GetCollatParAmount() conversion"""
        self.calculator.add_asset(self.asset1)
        self.calculator.add_asset(self.asset2)
        
        # Test total par amount (no filter)
        total_par = self.calculator.get_collateral_par_amount()
        assert total_par == Decimal('3000000')
        
        # Test with filter
        filtered_par = self.calculator.get_collateral_par_amount("test_filter")
        # Both assets return True for apply_filter, so should be same
        assert filtered_par == Decimal('3000000')
        
        # Test with filter that excludes some assets
        self.asset2.apply_filter.return_value = False
        filtered_par = self.calculator.get_collateral_par_amount("exclusion_filter")
        assert filtered_par == Decimal('1000000')


# NOTE: Old VBA-based concentration test and rating derivation classes removed
# These have been replaced with database-driven concentration test approach
# See test_mag17_concentration_results.py for database-driven concentration test validation

if __name__ == "__main__":
    pytest.main([__file__, "-v"])