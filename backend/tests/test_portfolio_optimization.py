"""
Test Suite for Portfolio Optimization Engine
Comprehensive testing of Main.bas conversion functionality
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List

from ..app.models.portfolio_optimization import (
    PortfolioOptimizationEngine, PortfolioOptimizationService,
    OptimizationInputs, ObjectiveWeights, ComplianceTestResult,
    OptimizationType, ObjectiveWeightType
)
from ..app.models.clo_deal import CLODeal
from ..app.models.asset import Asset
from ..app.models.clo_deal_engine import CLODealEngine, AccountType, CashType


@pytest.fixture
def session():
    """Create test database session"""
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def test_clo_deal(session):
    """Create test CLO deal"""
    deal = CLODeal(
        deal_id="OPTIMIZE-TEST-001",
        deal_name="Portfolio Optimization Test Deal",
        manager_name="Test Manager",
        pricing_date=date(2023, 1, 15),
        closing_date=date(2023, 2, 15),
        effective_date=date(2023, 2, 15),
        first_payment_date=date(2023, 5, 15),
        maturity_date=date(2025, 5, 15),
        target_par_amount=Decimal('500000000')
    )
    return deal


@pytest.fixture
def test_current_assets(session, test_clo_deal):
    """Create test current portfolio assets"""
    assets = []
    
    # Create 5 current holdings
    for i in range(1, 6):
        asset = Asset(
            deal_id=test_clo_deal.deal_id,
            blk_rock_id=f"CURRENT-{i:03d}",
            issue_name=f"Current Asset {i}",
            issuer_name=f"Current Issuer {i}",
            par_amount=Decimal('10000000'),  # $10M each
            is_current_holding=True,
            is_potential_holding=False,
            coupon_spread=Decimal('0.035'),  # 350 bps
            maturity_date=date(2025, 12, 31)
        )
        assets.append(asset)
    
    return assets


@pytest.fixture
def test_potential_assets(session, test_clo_deal):
    """Create test potential assets"""
    assets = []
    
    # Create 20 potential assets
    for i in range(1, 21):
        asset = Asset(
            deal_id=test_clo_deal.deal_id,
            blk_rock_id=f"POTENTIAL-{i:03d}",
            issue_name=f"Potential Asset {i}",
            issuer_name=f"Potential Issuer {i}",
            par_amount=Decimal('0'),  # Not yet purchased
            is_current_holding=False,
            is_potential_holding=True,
            coupon_spread=Decimal('0.040' + str(i).zfill(3)),  # Varying spreads
            maturity_date=date(2025, 6, 30)
        )
        assets.append(asset)
    
    return assets


@pytest.fixture
def test_optimization_inputs():
    """Create test optimization inputs"""
    return OptimizationInputs(
        max_assets=50,
        max_loan_size=Decimal('50000000'),
        increase_current_loans=True,
        run_hypothesis_indicator=False,
        max_par_amount=Decimal('10000000'),
        include_current_assets=True,
        output_results=True
    )


@pytest.fixture
def test_objective_weights():
    """Create test objective weights"""
    return ObjectiveWeights(
        oc_test_32=Decimal('0.30'),
        oc_test_33=Decimal('0.25'),
        oc_test_37=Decimal('0.20'),
        ic_test_35=Decimal('0.15'),
        ic_test_36=Decimal('0.10')
    )


@pytest.fixture
def optimization_engine(session, test_clo_deal, test_optimization_inputs, test_objective_weights):
    """Create configured optimization engine"""
    engine = PortfolioOptimizationEngine(test_clo_deal, session)
    
    # Mock the asset loading methods
    with patch.object(engine, '_load_current_portfolio'), \
         patch.object(engine, '_load_potential_assets'), \
         patch.object(engine, '_load_hypothesis_portfolio'), \
         patch.object(engine, '_setup_accounts'):
        
        engine.setup_optimization(test_optimization_inputs, test_objective_weights)
    
    return engine


class TestPortfolioOptimizationEngine:
    """Test basic optimization engine functionality"""
    
    def test_engine_initialization(self, optimization_engine):
        """Test engine initialization"""
        assert optimization_engine.deal.deal_id == "OPTIMIZE-TEST-001"
        assert optimization_engine.deal_name == "Portfolio Optimization Test Deal"
        assert optimization_engine.optimization_inputs.max_assets == 50
        assert optimization_engine.objective_weights.oc_test_32 == Decimal('0.30')
    
    def test_objective_weights_get_weight(self, test_objective_weights):
        """Test objective weight retrieval"""
        assert test_objective_weights.get_weight(32) == Decimal('0.30')
        assert test_objective_weights.get_weight(33) == Decimal('0.25')
        assert test_objective_weights.get_weight(35) == Decimal('0.15')
        assert test_objective_weights.get_weight(99) == Decimal('0')  # Unknown test
    
    def test_optimization_inputs_defaults(self):
        """Test optimization input defaults"""
        inputs = OptimizationInputs()
        assert inputs.max_assets == 100
        assert inputs.max_loan_size == Decimal('50000000')
        assert inputs.increase_current_loans == True
        assert inputs.run_hypothesis_indicator == False


class TestObjectiveFunctionCalculation:
    """Test objective function calculation logic"""
    
    def test_calculate_objective_function_all_pass(self, optimization_engine):
        """Test objective function with all tests passing"""
        results = [
            ComplianceTestResult(
                test_number=32, test_name="OC Test 32", comments="",
                numerator=Decimal('120'), denominator=Decimal('100'),
                result=Decimal('1.20'), threshold=Decimal('1.10'),
                pass_fail=True, pass_fail_comment="PASS"
            ),
            ComplianceTestResult(
                test_number=33, test_name="OC Test 33", comments="",
                numerator=Decimal('115'), denominator=Decimal('100'),
                result=Decimal('1.15'), threshold=Decimal('1.05'),
                pass_fail=True, pass_fail_comment="PASS"
            ),
            ComplianceTestResult(
                test_number=35, test_name="IC Test 35", comments="",
                numerator=Decimal('110'), denominator=Decimal('100'),
                result=Decimal('1.10'), threshold=Decimal('1.05'),
                pass_fail=True, pass_fail_comment="PASS"
            )
        ]
        
        objective_value = optimization_engine._calculate_objective_function(results)
        
        # Should be positive since all tests pass
        assert objective_value > 0
        
        # Verify calculation
        expected = (
            (Decimal('1.20') / Decimal('1.10')) * Decimal('0.30') +  # OC Test 32
            (Decimal('1.15') / Decimal('1.05')) * Decimal('0.25') +  # OC Test 33  
            (Decimal('1.05') / Decimal('1.10')) * Decimal('0.15')    # IC Test 35
        ) * 100
        
        assert abs(objective_value - expected) < Decimal('0.01')
    
    def test_calculate_objective_function_critical_failure(self, optimization_engine):
        """Test objective function with critical test failure"""
        results = [
            ComplianceTestResult(
                test_number=32, test_name="OC Test 32", comments="",
                numerator=Decimal('100'), denominator=Decimal('100'),
                result=Decimal('1.00'), threshold=Decimal('1.10'),
                pass_fail=False, pass_fail_comment="FAIL"  # Critical failure
            ),
            ComplianceTestResult(
                test_number=33, test_name="OC Test 33", comments="",
                numerator=Decimal('115'), denominator=Decimal('100'),
                result=Decimal('1.15'), threshold=Decimal('1.05'),
                pass_fail=True, pass_fail_comment="PASS"
            )
        ]
        
        objective_value = optimization_engine._calculate_objective_function(results)
        
        # Should be 0 due to critical test failure
        assert objective_value == Decimal('0')
    
    def test_calculate_objective_function_test_31_exception(self, optimization_engine):
        """Test that test 31 failure doesn't zero objective"""
        results = [
            ComplianceTestResult(
                test_number=31, test_name="Test 31", comments="",
                numerator=Decimal('100'), denominator=Decimal('100'),
                result=Decimal('1.00'), threshold=Decimal('1.10'),
                pass_fail=False, pass_fail_comment="FAIL"  # Test 31 failure allowed
            ),
            ComplianceTestResult(
                test_number=32, test_name="OC Test 32", comments="",
                numerator=Decimal('120'), denominator=Decimal('100'),
                result=Decimal('1.20'), threshold=Decimal('1.10'),
                pass_fail=True, pass_fail_comment="PASS"
            )
        ]
        
        objective_value = optimization_engine._calculate_objective_function(results)
        
        # Should not be 0 despite test 31 failure
        assert objective_value > 0


class TestAssetTesting:
    """Test asset addition testing logic"""
    
    @patch('backend.app.models.portfolio_optimization.PortfolioOptimizationEngine._calculate_compliance_tests')
    def test_test_asset_addition_new_asset(self, mock_compliance, optimization_engine):
        """Test adding a new asset"""
        # Mock compliance results
        mock_compliance.return_value = [
            ComplianceTestResult(
                test_number=32, test_name="OC Test 32", comments="",
                numerator=Decimal('125'), denominator=Decimal('100'),
                result=Decimal('1.25'), threshold=Decimal('1.10'),
                pass_fail=True, pass_fail_comment="PASS"
            )
        ]
        
        # Mock potential asset
        mock_asset = Mock(spec=Asset)
        mock_asset.blk_rock_id = "TEST-001"
        mock_asset.par_amount = Decimal('0')
        
        with patch.object(optimization_engine, '_get_potential_asset', return_value=mock_asset), \
             patch.object(optimization_engine, '_asset_exists_in_portfolio', return_value=False), \
             patch.object(optimization_engine, '_create_asset_copy', return_value=mock_asset), \
             patch.object(optimization_engine, '_add_asset_to_portfolio'), \
             patch.object(optimization_engine, '_remove_asset_from_portfolio'), \
             patch.object(optimization_engine, '_remove_cash_from_collection'), \
             patch.object(optimization_engine, '_add_cash_to_collection'):
            
            objective_value = optimization_engine._test_asset_addition("TEST-001", Decimal('10000000'))
            
            # Should return positive objective value
            assert objective_value > 0
    
    def test_test_asset_addition_existing_asset(self, optimization_engine):
        """Test increasing existing asset"""
        with patch.object(optimization_engine, '_get_potential_asset') as mock_get_asset, \
             patch.object(optimization_engine, '_asset_exists_in_portfolio', return_value=True), \
             patch.object(optimization_engine, '_get_asset_par_amount', return_value=Decimal('20000000')), \
             patch.object(optimization_engine, '_increase_asset_par'), \
             patch.object(optimization_engine, '_decrease_asset_par'), \
             patch.object(optimization_engine, '_remove_cash_from_collection'), \
             patch.object(optimization_engine, '_add_cash_to_collection'), \
             patch.object(optimization_engine, '_calculate_compliance_tests'), \
             patch.object(optimization_engine, '_calculate_objective_function', return_value=Decimal('85.5')):
            
            # Set max loan size to allow increase
            optimization_engine.optimization_inputs.max_loan_size = Decimal('50000000')
            
            objective_value = optimization_engine._test_asset_addition("EXISTING-001", Decimal('10000000'))
            
            assert objective_value == Decimal('85.5')
    
    def test_test_asset_addition_max_loan_exceeded(self, optimization_engine):
        """Test asset addition when max loan size would be exceeded"""
        with patch.object(optimization_engine, '_get_potential_asset') as mock_get_asset, \
             patch.object(optimization_engine, '_asset_exists_in_portfolio', return_value=True), \
             patch.object(optimization_engine, '_get_asset_par_amount', return_value=Decimal('45000000')):
            
            # Set max loan size  
            optimization_engine.optimization_inputs.max_loan_size = Decimal('50000000')
            
            objective_value = optimization_engine._test_asset_addition("EXISTING-001", Decimal('10000000'))
            
            # Should return 0 because increase would exceed max loan size
            assert objective_value == Decimal('0')


class TestPortfolioManagement:
    """Test portfolio management operations"""
    
    def test_asset_exists_in_portfolio(self, optimization_engine):
        """Test asset existence check"""
        # Setup mock current portfolio
        mock_asset = Mock(spec=Asset)
        mock_asset.blk_rock_id = "EXISTING-001"
        optimization_engine.current_portfolio = [mock_asset]
        
        assert optimization_engine._asset_exists_in_portfolio("EXISTING-001") == True
        assert optimization_engine._asset_exists_in_portfolio("NONEXISTENT-001") == False
    
    def test_get_asset_par_amount(self, optimization_engine):
        """Test getting asset par amount"""
        mock_asset = Mock(spec=Asset)
        mock_asset.blk_rock_id = "TEST-001"
        mock_asset.par_amount = Decimal('25000000')
        optimization_engine.current_portfolio = [mock_asset]
        
        par_amount = optimization_engine._get_asset_par_amount("TEST-001")
        assert par_amount == Decimal('25000000')
        
        # Test non-existent asset
        par_amount = optimization_engine._get_asset_par_amount("NONEXISTENT-001")
        assert par_amount == Decimal('0')
    
    def test_increase_decrease_asset_par(self, optimization_engine):
        """Test increasing and decreasing asset par amounts"""
        mock_asset = Mock(spec=Asset)
        mock_asset.blk_rock_id = "TEST-001"
        mock_asset.par_amount = Decimal('20000000')
        optimization_engine.current_portfolio = [mock_asset]
        
        # Test increase
        optimization_engine._increase_asset_par("TEST-001", Decimal('5000000'))
        assert mock_asset.par_amount == Decimal('25000000')
        
        # Test decrease
        optimization_engine._decrease_asset_par("TEST-001", Decimal('3000000'))
        assert mock_asset.par_amount == Decimal('22000000')
    
    def test_add_remove_asset_from_portfolio(self, optimization_engine):
        """Test adding and removing assets from portfolio"""
        mock_asset = Mock(spec=Asset)
        mock_asset.blk_rock_id = "TEST-001"
        
        # Test add
        optimization_engine._add_asset_to_portfolio(mock_asset)
        assert len(optimization_engine.current_portfolio) == 1
        assert optimization_engine.current_portfolio[0] == mock_asset
        
        # Test remove
        optimization_engine._remove_asset_from_portfolio("TEST-001")
        assert len(optimization_engine.current_portfolio) == 0


class TestCashManagement:
    """Test cash account management"""
    
    def test_get_available_cash(self, optimization_engine):
        """Test getting available cash"""
        # Mock deal engine with cash account
        mock_account = Mock()
        mock_account.principal_proceeds = Decimal('50000000')
        
        mock_deal_engine = Mock()
        mock_deal_engine.accounts = {AccountType.COLLECTION: mock_account}
        
        optimization_engine.deal_engine = mock_deal_engine
        
        available_cash = optimization_engine._get_available_cash()
        assert available_cash == Decimal('50000000')
    
    def test_get_available_cash_no_engine(self, optimization_engine):
        """Test getting available cash with no deal engine"""
        optimization_engine.deal_engine = None
        
        available_cash = optimization_engine._get_available_cash()
        assert available_cash == Decimal('0')
    
    def test_add_remove_cash_from_collection(self, optimization_engine):
        """Test adding and removing cash from collection account"""
        mock_account = Mock()
        mock_account.add = Mock()
        
        mock_deal_engine = Mock()
        mock_deal_engine.accounts = {AccountType.COLLECTION: mock_account}
        
        optimization_engine.deal_engine = mock_deal_engine
        
        # Test remove cash
        optimization_engine._remove_cash_from_collection(Decimal('10000000'))
        mock_account.add.assert_called_with(CashType.PRINCIPAL, -Decimal('10000000'))
        
        # Test add cash
        optimization_engine._add_cash_to_collection(Decimal('5000000'))
        mock_account.add.assert_called_with(CashType.PRINCIPAL, Decimal('5000000'))


class TestOptimizationAlgorithms:
    """Test optimization algorithm implementations"""
    
    @patch('backend.app.models.portfolio_optimization.PortfolioOptimizationEngine._calculate_compliance_tests')
    @patch('backend.app.models.portfolio_optimization.PortfolioOptimizationEngine._get_available_cash')
    def test_run_generic_optimization(self, mock_cash, mock_compliance, optimization_engine):
        """Test generic optimization algorithm"""
        # Mock initial compliance
        mock_compliance.return_value = [
            ComplianceTestResult(
                test_number=32, test_name="OC Test 32", comments="",
                numerator=Decimal('110'), denominator=Decimal('100'),
                result=Decimal('1.10'), threshold=Decimal('1.10'),
                pass_fail=True, pass_fail_comment="PASS"
            )
        ]
        
        # Mock available cash - decreases each iteration
        mock_cash.side_effect = [Decimal('30000000'), Decimal('20000000'), Decimal('10000000'), Decimal('0')]
        
        with patch.object(optimization_engine, '_generic_optimization_rankings') as mock_rankings, \
             patch.object(optimization_engine, '_add_best_asset', return_value=True), \
             patch.object(optimization_engine, '_load_potential_assets'):
            
            # Mock rankings to show improvement then decline
            mock_rankings.side_effect = [
                {"ASSET-001": Decimal('92.5')},  # Improvement
                {"ASSET-002": Decimal('95.0')},  # More improvement
                {"ASSET-003": Decimal('90.0')}   # Decline
            ]
            
            final_objective = optimization_engine.run_generic_optimization()
            
            # Should have positive final objective
            assert final_objective > 0
            
            # Should have called rankings multiple times
            assert mock_rankings.call_count >= 2
    
    def test_generic_optimization_rankings(self, optimization_engine):
        """Test generic optimization rankings algorithm"""
        with patch.object(optimization_engine, '_get_random_asset') as mock_random, \
             patch.object(optimization_engine, '_test_asset_addition') as mock_test:
            
            # Mock random asset selection
            mock_random.side_effect = ["ASSET-001", "ASSET-002", "ASSET-003", None]
            
            # Mock asset testing results
            mock_test.side_effect = [Decimal('85.5'), Decimal('92.3'), Decimal('78.1')]
            
            rankings = optimization_engine._generic_optimization_rankings(
                max_assets=3,
                include_current_assets=True,
                max_par_amount=Decimal('10000000'),
                output_results=False
            )
            
            # Should have 3 rankings
            assert len(rankings) == 3
            assert rankings["ASSET-001"] == Decimal('85.5')
            assert rankings["ASSET-002"] == Decimal('92.3')
            assert rankings["ASSET-003"] == Decimal('78.1')
    
    def test_get_random_asset_potential_only(self, optimization_engine):
        """Test random asset selection from potential assets"""
        # Mock potential assets
        mock_assets = []
        for i in range(3):
            mock_asset = Mock(spec=Asset)
            mock_asset.blk_rock_id = f"POTENTIAL-{i:03d}"
            mock_assets.append(mock_asset)
        
        optimization_engine.potential_assets = mock_assets
        optimization_engine.current_portfolio = []
        
        with patch.object(optimization_engine, '_asset_exists_in_portfolio', return_value=False):
            asset_id = optimization_engine._get_random_asset(Decimal('10000000'), False)
            
            # Should return one of the potential asset IDs
            assert asset_id in ["POTENTIAL-000", "POTENTIAL-001", "POTENTIAL-002"]


class TestPortfolioOptimizationService:
    """Test optimization service layer"""
    
    @pytest.fixture
    def optimization_service(self, session):
        """Create optimization service"""
        return PortfolioOptimizationService(session)
    
    @patch('backend.app.models.portfolio_optimization.PortfolioOptimizationEngine')
    async def test_run_portfolio_optimization(self, mock_engine_class, optimization_service, test_clo_deal):
        """Test service-level portfolio optimization"""
        # Mock engine
        mock_engine = Mock()
        mock_engine.initial_objective_value = Decimal('75.5')
        mock_engine.current_portfolio = []
        mock_engine._get_available_cash.return_value = Decimal('5000000')
        
        mock_compliance = [
            ComplianceTestResult(
                test_number=32, test_name="OC Test 32", comments="",
                numerator=Decimal('120'), denominator=Decimal('100'),
                result=Decimal('1.20'), threshold=Decimal('1.10'),
                pass_fail=True, pass_fail_comment="PASS"
            )
        ]
        
        mock_engine.run_compliance_tests.return_value = mock_compliance
        mock_engine.run_generic_optimization.return_value = Decimal('92.8')
        mock_engine_class.return_value = mock_engine
        
        # Mock session query
        with patch.object(optimization_service.session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = test_clo_deal
            
            result = await optimization_service.run_portfolio_optimization(
                deal_id="OPTIMIZE-TEST-001",
                optimization_inputs=OptimizationInputs(),
                objective_weights=ObjectiveWeights()
            )
        
        # Verify results
        assert result['deal_id'] == "OPTIMIZE-TEST-001"
        assert result['optimization_type'] == 'generic_optimization'
        assert result['initial_objective_value'] == 75.5
        assert result['final_objective_value'] == 92.8
        assert result['improvement'] == 17.3
    
    async def test_run_portfolio_optimization_deal_not_found(self, optimization_service):
        """Test service with non-existent deal"""
        with patch.object(optimization_service.session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            
            with pytest.raises(ValueError, match="Deal NONEXISTENT not found"):
                await optimization_service.run_portfolio_optimization(
                    deal_id="NONEXISTENT",
                    optimization_inputs=OptimizationInputs(),
                    objective_weights=ObjectiveWeights()
                )
    
    @patch('backend.app.models.portfolio_optimization.PortfolioOptimizationEngine')
    async def test_run_scenario_analysis(self, mock_engine_class, optimization_service, test_clo_deal):
        """Test service-level scenario analysis"""
        # Mock engine
        mock_engine = Mock()
        mock_scenarios = [
            {'inputs': {'max_assets': 25}, 'weights': {'oc_test_32': 0.4}},
            {'inputs': {'max_assets': 50}, 'weights': {'oc_test_32': 0.2}}
        ]
        
        mock_engine.run_scenario_analysis.return_value = {
            'scenario_1': {
                'inputs': mock_scenarios[0],
                'final_objective_value': 85.5,
                'initial_objective_value': 75.0,
                'improvement': 10.5,
                'assets_in_portfolio': 8
            },
            'scenario_2': {
                'inputs': mock_scenarios[1],
                'final_objective_value': 92.3,
                'initial_objective_value': 75.0,
                'improvement': 17.3,
                'assets_in_portfolio': 12
            }
        }
        
        mock_engine_class.return_value = mock_engine
        
        # Mock session query
        with patch.object(optimization_service.session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = test_clo_deal
            
            result = await optimization_service.run_scenario_analysis(
                deal_id="OPTIMIZE-TEST-001",
                scenarios=mock_scenarios
            )
        
        # Verify results
        assert result['deal_id'] == "OPTIMIZE-TEST-001"
        assert result['analysis_type'] == 'scenario_analysis'
        assert result['scenarios_count'] == 2
        assert 'scenario_1' in result['results']
        assert 'scenario_2' in result['results']


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_potential_assets(self, optimization_engine):
        """Test optimization with no potential assets"""
        optimization_engine.potential_assets = []
        optimization_engine.current_portfolio = []
        
        asset_id = optimization_engine._get_random_asset(Decimal('10000000'), False)
        assert asset_id is None
    
    def test_reset_portfolio_state(self, optimization_engine):
        """Test portfolio state reset"""
        # Add some state
        optimization_engine.current_portfolio = [Mock()]
        optimization_engine.potential_assets = [Mock()]
        optimization_engine.optimization_rankings = {"TEST": Decimal('85.5')}
        optimization_engine.current_objective_value = Decimal('90.0')
        
        # Reset
        optimization_engine._reset_portfolio_state()
        
        # Verify reset
        assert len(optimization_engine.current_portfolio) == 0
        assert len(optimization_engine.potential_assets) == 0
        assert len(optimization_engine.optimization_rankings) == 0
        assert optimization_engine.current_objective_value == Decimal('0')
    
    def test_compliance_result_to_dict_conversion(self):
        """Test compliance result dictionary conversion"""
        service = PortfolioOptimizationService(Mock())
        
        result = ComplianceTestResult(
            test_number=32,
            test_name="OC Test 32",
            comments="Test comment",
            numerator=Decimal('120.50'),
            denominator=Decimal('100.00'),
            result=Decimal('1.205'),
            threshold=Decimal('1.100'),
            pass_fail=True,
            pass_fail_comment="PASS"
        )
        
        result_dict = service._compliance_result_to_dict(result)
        
        assert result_dict['test_number'] == 32
        assert result_dict['test_name'] == "OC Test 32"
        assert result_dict['result'] == 1.205
        assert result_dict['threshold'] == 1.100
        assert result_dict['pass_fail'] == True
        assert result_dict['numerator'] == 120.50
        assert result_dict['denominator'] == 100.00


if __name__ == "__main__":
    pytest.main([__file__, "-v"])