"""
Comprehensive Test Suite for Collateral Pool System
Tests CollateralPool.cls and CollateralPoolForCLO.cls conversions
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
from app.models.concentration_test import ConcentrationTest, RatingDerivations, TestSettings
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
        self.asset1.copy.return_value = self.asset1
        self.asset1.add_par = Mock()
        self.asset1.apply_filter = Mock(return_value=True)
        
        self.asset2 = Mock(spec=Asset)
        self.asset2.blkrock_id = "ASSET002"
        self.asset2.par_amount = Decimal('2000000')
        self.asset2.market_value = Decimal('102.25')
        self.asset2.issuer_name = "Test Issuer 2"
        self.asset2.sp_rating = "BB-"
        self.asset2.sp_industry = "Healthcare"
        self.asset2.default_asset = False
        self.asset2.maturity = date(2027, 12, 31)
        self.asset2.copy.return_value = self.asset2
        self.asset2.add_par = Mock()
        self.asset2.apply_filter = Mock(return_value=True)
        
        # Setup test accounts
        self.collection_account = Account()
        self.collection_account.principal = Decimal('10000000')
        self.collection_account.interest = Decimal('500000')
        
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
    
    def test_purchase_asset(self):
        """Test VBA PurchaseAsset() conversion"""
        # Test full purchase within cash limits
        purchase_asset = Mock(spec=Asset)
        purchase_asset.blkrock_id = "PURCHASE001"
        purchase_asset.par_amount = Decimal('1000000')
        purchase_asset.market_value = Decimal('99.0')
        purchase_asset.copy.return_value = purchase_asset
        purchase_asset.add_par = Mock()
        
        self.calculator.purchase_asset(purchase_asset)
        
        # Should add asset to dictionary
        assert "PURCHASE001" in self.calculator.assets_dict
        
        # Should reduce cash by purchase amount (1,000,000 * 0.99 = 990,000)
        expected_remaining_cash = Decimal('10000000') - Decimal('990000')
        actual_remaining_cash = self.calculator.check_account_balance(
            AccountType.COLLECTION, CashType.PRINCIPAL
        )
        assert actual_remaining_cash == expected_remaining_cash
    
    def test_purchase_asset_insufficient_cash(self):
        """Test partial purchase when insufficient cash"""
        # Large asset that exceeds available cash
        large_asset = Mock(spec=Asset)
        large_asset.blkrock_id = "LARGE001"
        large_asset.par_amount = Decimal('20000000')  # $20M par
        large_asset.market_value = Decimal('100.0')   # At par
        large_asset.copy.return_value = large_asset
        large_asset.add_par = Mock()
        
        self.calculator.purchase_asset(large_asset)
        
        # Should reduce par amount to affordable level
        # Available: $10M, Price: 100% = $10M affordable par
        large_asset.add_par.assert_called()
        
        # Should use all available cash
        remaining_cash = self.calculator.check_account_balance(
            AccountType.COLLECTION, CashType.PRINCIPAL
        )
        assert remaining_cash == Decimal('0')
    
    def test_sell_asset(self):
        """Test VBA SaleAsset() conversion"""
        # Add asset first
        self.calculator.add_asset(self.asset1)
        
        # Sell partial position
        sell_asset = Mock(spec=Asset)
        sell_asset.blkrock_id = "ASSET001"
        sell_asset.par_amount = Decimal('500000')
        sell_asset.market_value = Decimal('98.5')
        
        self.calculator.sell_asset(sell_asset)
        
        # Should reduce position
        self.asset1.add_par.assert_called()
        
        # Should add cash proceeds (500,000 * 0.985 = 492,500)
        expected_cash = Decimal('10000000') + Decimal('492500')
        actual_cash = self.calculator.check_account_balance(
            AccountType.COLLECTION, CashType.PRINCIPAL
        )
        assert actual_cash == expected_cash
    
    def test_calculate_average_par_amount(self):
        """Test VBA CalcAverageParAmount() conversion"""
        # No assets
        avg = self.calculator.calculate_average_par_amount()
        assert avg == Decimal('0')
        
        # Add assets
        self.calculator.add_asset(self.asset1)  # $1M
        self.calculator.add_asset(self.asset2)  # $2M
        
        # Average should be $1.5M
        avg = self.calculator.calculate_average_par_amount()
        assert avg == Decimal('1500000')
    
    def test_get_last_maturity_date(self):
        """Test VBA LastMaturityDate() conversion"""
        # No assets
        assert self.calculator.get_last_maturity_date() is None
        
        # Add assets
        self.calculator.add_asset(self.asset1)  # 2028-06-15
        self.calculator.add_asset(self.asset2)  # 2027-12-31
        
        # Should return latest date
        latest = self.calculator.get_last_maturity_date()
        assert latest == date(2028, 6, 15)
    
    def test_get_num_assets(self):
        """Test VBA NumOfAssets() conversion"""
        # No assets
        assert self.calculator.get_num_assets() == 0
        
        # Add assets
        self.calculator.add_asset(self.asset1)
        self.calculator.add_asset(self.asset2)
        
        # Total count
        assert self.calculator.get_num_assets() == 2
        
        # Filtered count
        self.asset2.apply_filter.return_value = False
        assert self.calculator.get_num_assets("filter") == 1
    
    def test_apply_filter(self):
        """Test VBA ApplyFilter() conversion"""
        self.calculator.add_asset(self.asset1)
        self.calculator.add_asset(self.asset2)
        
        # All assets match filter
        matching = self.calculator.apply_filter("test_filter")
        assert matching == {"ASSET001": 1, "ASSET002": 1}
        
        # Only one asset matches
        self.asset2.apply_filter.return_value = False
        matching = self.calculator.apply_filter("exclusive_filter")
        assert matching == {"ASSET001": 1}
    
    def test_asset_exists(self):
        """Test VBA AssetExist() conversion"""
        assert self.calculator.asset_exists("ASSET001") is False
        
        self.calculator.add_asset(self.asset1)
        assert self.calculator.asset_exists("ASSET001") is True
    
    def test_add_par(self):
        """Test VBA AddPar() conversion"""
        self.calculator.add_asset(self.asset1)
        
        # Add par amount
        self.calculator.add_par("ASSET001", Decimal('500000'))
        self.asset1.add_par.assert_called_with(Decimal('500000'))
        
        # Test removal when par amount too small
        self.asset1.par_amount = Decimal('0.50')  # Very small amount
        self.calculator.add_par("ASSET001", Decimal('0'))
        # Asset should be removed from dictionary
        # (This would need more complex mocking to test fully)


class TestConcentrationTest:
    """Test concentration test functionality"""
    
    def setup_method(self):
        """Setup test concentration tests"""
        self.concentration_test = ConcentrationTest()
        
        # Create test assets
        self.assets_dict = {}
        
        # Asset 1: Large BB+ technology exposure
        asset1 = Mock(spec=Asset)
        asset1.par_amount = Decimal('5000000')
        asset1.issuer_name = "Large Tech Corp"
        asset1.sp_rating = "BB+"
        asset1.sp_industry = "Technology"
        asset1.default_asset = False
        asset1.cov_lite = False
        self.assets_dict["TECH001"] = asset1
        
        # Asset 2: Medium B healthcare exposure  
        asset2 = Mock(spec=Asset)
        asset2.par_amount = Decimal('3000000')
        asset2.issuer_name = "Healthcare Inc"
        asset2.sp_rating = "B"
        asset2.sp_industry = "Healthcare"
        asset2.default_asset = False
        asset2.cov_lite = True
        self.assets_dict["HEALTH001"] = asset2
        
        # Asset 3: Small CCC+ defaulted asset
        asset3 = Mock(spec=Asset)
        asset3.par_amount = Decimal('1000000')
        asset3.issuer_name = "Distressed Corp"
        asset3.sp_rating = "CCC+"
        asset3.sp_industry = "Energy"
        asset3.default_asset = True
        asset3.cov_lite = False
        self.assets_dict["ENERGY001"] = asset3
    
    def test_run_test_basic(self):
        """Test basic concentration test execution"""
        principal_proceeds = Decimal('10000000')
        
        self.concentration_test.run_test(self.assets_dict, principal_proceeds)
        
        # Should have test results
        results = self.concentration_test.get_results()
        assert len(results) > 0
        
        # Should have calculated objective function
        objective = self.concentration_test.calc_objective_function()
        assert isinstance(objective, Decimal)
    
    def test_obligor_concentration(self):
        """Test single obligor concentration test"""
        principal_proceeds = Decimal('10000000')
        self.concentration_test.run_test(self.assets_dict, principal_proceeds)
        
        results = self.concentration_test.get_results()
        obligor_test = next((r for r in results if r.test_number == 1), None)
        
        assert obligor_test is not None
        assert obligor_test.test_name == "Single Obligor Concentration"
        assert obligor_test.threshold == Decimal('2.0')
        
        # Largest exposure is 5M out of 9M total = 55.56%
        # Should fail the 2% threshold
        assert obligor_test.pass_fail == "FAIL"
    
    def test_industry_concentration(self):
        """Test industry concentration test"""
        principal_proceeds = Decimal('10000000')
        self.concentration_test.run_test(self.assets_dict, principal_proceeds)
        
        results = self.concentration_test.get_results()
        industry_test = next((r for r in results if r.test_number == 10), None)
        
        assert industry_test is not None
        assert industry_test.test_name == "Single Industry Concentration"
        assert industry_test.threshold == Decimal('12.0')
        
        # Technology has 5M out of 9M = 55.56%
        # Should fail the 12% threshold
        assert industry_test.pass_fail == "FAIL"
    
    def test_ccc_concentration(self):
        """Test CCC-rated assets concentration"""
        principal_proceeds = Decimal('10000000')
        self.concentration_test.run_test(self.assets_dict, principal_proceeds)
        
        results = self.concentration_test.get_results()
        ccc_test = next((r for r in results if r.test_number == 35), None)
        
        assert ccc_test is not None
        assert ccc_test.test_name == "CCC-Rated Assets"
        
        # CCC+ assets: 1M out of 9M = 11.11%
        # Should fail the 7.5% threshold
        assert ccc_test.pass_fail == "FAIL"
    
    def test_defaulted_assets(self):
        """Test defaulted assets concentration"""
        principal_proceeds = Decimal('10000000')
        self.concentration_test.run_test(self.assets_dict, principal_proceeds)
        
        results = self.concentration_test.get_results()
        default_test = next((r for r in results if r.test_number == 40), None)
        
        assert default_test is not None
        assert default_test.test_name == "Defaulted Assets"
        
        # Defaulted: 1M out of 9M = 11.11%  
        # Should fail the 5% threshold
        assert default_test.pass_fail == "FAIL"
    
    def test_covenant_lite_concentration(self):
        """Test covenant-lite assets concentration"""
        principal_proceeds = Decimal('10000000')
        self.concentration_test.run_test(self.assets_dict, principal_proceeds)
        
        results = self.concentration_test.get_results()
        covlite_test = next((r for r in results if r.test_number == 30), None)
        
        assert covlite_test is not None
        assert covlite_test.test_name == "Covenant-Lite Assets"
        
        # Cov-lite: 3M out of 9M = 33.33%
        # Should fail the 7.5% threshold
        assert covlite_test.pass_fail == "FAIL"
    
    def test_objective_function_calculation(self):
        """Test objective function includes all violations"""
        principal_proceeds = Decimal('10000000')
        self.concentration_test.run_test(self.assets_dict, principal_proceeds)
        
        objective = self.concentration_test.calc_objective_function()
        objective_dict = self.concentration_test.get_objective_dict()
        
        # Should have positive objective value (violations exist)
        assert objective > 0
        
        # Should have entries for failing tests
        assert len(objective_dict) > 0
        
        # Failed tests should contribute to objective
        failing_contributions = [v for v in objective_dict.values() if v > 0]
        assert len(failing_contributions) > 0


class TestRatingDerivations:
    """Test rating derivation functionality"""
    
    def setup_method(self):
        """Setup rating derivation tests"""
        self.rating_derivations = RatingDerivations()
        self.test_asset = Mock(spec=Asset)
    
    def test_get_moodys_rating_from_sp(self):
        """Test Moody's rating derivation from S&P"""
        self.test_asset.sp_rating = "BB+"
        self.test_asset.mdy_rating = None
        
        result = self.rating_derivations.get_moodys_rating(self.test_asset)
        
        # Should derive equivalent Moody's rating
        assert result in self.rating_derivations.moody_to_numeric.keys()
        assert self.test_asset.mdy_rating == result
    
    def test_get_snp_rating_from_moodys(self):
        """Test S&P rating derivation from Moody's"""
        self.test_asset.mdy_rating = "Ba1"
        self.test_asset.sp_rating = None
        
        result = self.rating_derivations.get_snp_ratings(self.test_asset)
        
        # Should derive equivalent S&P rating
        assert result in self.rating_derivations.sp_to_numeric.keys()
        assert self.test_asset.sp_rating == result
    
    def test_moody_recovery_rate(self):
        """Test recovery rate calculation"""
        self.test_asset.mdy_rating = "B2"
        self.test_asset.mdy_recovery_rate = None
        
        recovery_rate = self.rating_derivations.moody_recovery_rate(self.test_asset)
        
        assert isinstance(recovery_rate, Decimal)
        assert Decimal('0') <= recovery_rate <= Decimal('1')
        assert self.test_asset.mdy_recovery_rate == recovery_rate
    
    def test_return_ratings_rank(self):
        """Test numeric rating rank conversion"""
        # Test S&P rating
        sp_rank = self.rating_derivations.return_ratings_rank("BB+")
        assert sp_rank == 11
        
        # Test Moody's rating
        moody_rank = self.rating_derivations.return_ratings_rank("Ba1")
        assert moody_rank == 11
        
        # Test invalid rating
        invalid_rank = self.rating_derivations.return_ratings_rank("INVALID")
        assert invalid_rank == 15  # Default


class TestCollateralPoolService:
    """Test service layer functionality"""
    
    def setup_method(self):
        """Setup service tests"""
        self.mock_db_session = Mock()
        self.service = CollateralPoolService(self.mock_db_session)
    
    def test_create_collateral_pool(self):
        """Test collateral pool creation"""
        pool = self.service.create_collateral_pool(
            deal_id="TEST_DEAL_001",
            pool_name="Main Pool",
            analysis_date=date(2023, 12, 15),
            analysis_type=AnalysisType.RATING_MIGRATION
        )
        
        assert pool.deal_id == "TEST_DEAL_001"
        assert pool.pool_name == "Main Pool"
        assert pool.analysis_type == AnalysisType.RATING_MIGRATION.value
        assert pool.use_rating_migration is True
        
        self.mock_db_session.add.assert_called_once_with(pool)
        self.mock_db_session.flush.assert_called_once()
    
    def test_create_pool_for_clo(self):
        """Test CLO-specific pool creation"""
        pool = self.service.create_pool_for_clo(
            deal_id="TEST_DEAL_001",
            parent_pool_id=1,
            analysis_date=date(2023, 12, 15)
        )
        
        assert pool.deal_id == "TEST_DEAL_001"
        assert pool.parent_pool_id == 1
        assert pool.analysis_date == date(2023, 12, 15)
        
        self.mock_db_session.add.assert_called_once_with(pool)
        self.mock_db_session.flush.assert_called_once()
    
    @patch('backend.app.services.collateral_pool_service.CollateralPoolCalculator')
    def test_get_pool_calculator_setup(self, mock_calculator_class):
        """Test calculator initialization with database data"""
        # Mock database queries
        mock_pool = Mock()
        mock_pool.pool_id = 1
        mock_pool.deal_id = "TEST_DEAL_001"
        
        mock_pool_asset = Mock()
        mock_pool_asset.asset = Mock()
        mock_pool_asset.asset.blkrock_id = "ASSET001"
        mock_pool_asset.par_amount = Decimal('1000000')
        
        mock_pool_account = Mock()
        mock_pool_account.account_type = AccountType.COLLECTION.value
        mock_pool_account.principal_proceeds = Decimal('5000000')
        mock_pool_account.interest_proceeds = Decimal('100000')
        
        self.mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_pool
        self.mock_db_session.query.return_value.filter_by.return_value.all.side_effect = [
            [mock_pool_asset],  # Assets query
            [mock_pool_account]  # Accounts query
        ]
        
        # Mock calculator instance
        mock_calculator = Mock()
        mock_calculator.assets_dict = {}
        mock_calculator.accounts_dict = {}
        mock_calculator_class.return_value = mock_calculator
        
        calculator = self.service.get_pool_calculator(1)
        
        # Should initialize calculator with pool data
        mock_calculator_class.assert_called_once_with(mock_pool)
        
        # Should load assets and accounts
        assert calculator == mock_calculator
    
    def test_hypo_inputs_creation(self):
        """Test hypothesis inputs structure"""
        mock_asset = Mock()
        mock_asset.blkrock_id = "TEST001"
        
        hypo = HypoInputs(
            asset=mock_asset,
            transaction="BUY",
            price=Decimal('99.5')
        )
        
        assert hypo.asset == mock_asset
        assert hypo.transaction == "BUY"
        assert hypo.price == Decimal('99.5')


class TestCollateralPoolIntegration:
    """Integration tests for complete collateral pool functionality"""
    
    def setup_method(self):
        """Setup integration test environment"""
        # This would typically use a test database
        # For now, we'll use mocks to test the integration patterns
        pass
    
    def test_complete_portfolio_workflow(self):
        """Test complete portfolio management workflow"""
        # This test would demonstrate:
        # 1. Creating a collateral pool
        # 2. Adding multiple assets
        # 3. Running concentration tests  
        # 4. Executing buy/sell transactions
        # 5. Rebalancing portfolio
        # 6. Generating optimization rankings
        # 7. Producing hypothesis testing outputs
        
        # Due to the complexity of setting up a full database environment,
        # this integration test is left as a framework for future implementation
        pass
    
    def test_waterfall_integration(self):
        """Test integration with waterfall calculation system"""
        # This would test how collateral pools feed into:
        # 1. Cash flow generation
        # 2. Trigger calculations (OC/IC tests)
        # 3. Waterfall execution
        # 4. Fee calculations
        pass
    
    def test_optimization_integration(self):
        """Test integration with portfolio optimization engine"""
        # This would test how collateral pools integrate with:
        # 1. Main.bas optimization logic
        # 2. Objective function calculations
        # 3. Constraint satisfaction
        # 4. Ranking algorithms
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])