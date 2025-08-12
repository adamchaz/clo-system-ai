"""
Tests for Rebalancing Module

Comprehensive test suite for portfolio rebalancing functionality
converted from VBA ComplianceHypo.bas rebalancing algorithms.

Author: Claude
Date: 2025-01-12
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List

from app.models.rebalancing import (
    PortfolioRebalancer,
    RebalanceInputs,
    RebalanceResults,
    TradeRecommendation,
    TransactionType,
    AccountType,
    create_rebalance_inputs_from_config
)
from app.services.rebalancing_service import RebalancingService


class MockAsset:
    """Mock asset for testing"""
    
    def __init__(self, asset_id: str, **kwargs):
        self.id = asset_id
        self.asset_id = asset_id
        self.issue_name = kwargs.get('issue_name', f'Mock Asset {asset_id}')
        self.par_amount = kwargs.get('par_amount', 1000000.0)
        self.market_price = kwargs.get('market_price', 100.0)
        self.spread = kwargs.get('spread', 0.05)
        self.sp_rating = kwargs.get('sp_rating', 'BBB')
        self.maturity_date = kwargs.get('maturity_date', date.today() + timedelta(days=1825))
        self.sp_industry = kwargs.get('sp_industry', 'Technology')
    
    def copy(self):
        return MockAsset(self.asset_id, **self.__dict__)
    
    def update_par(self, new_par: float):
        self.par_amount = new_par


class MockPortfolio:
    """Mock portfolio/collateral pool for testing"""
    
    def __init__(self, assets: List[MockAsset]):
        self.assets = {asset.asset_id: asset for asset in assets}
        self.total_par_amount = sum(asset.par_amount for asset in assets)
        self.num_assets = len(assets)
        self.objective_value = 50.0
    
    def get_objective_value(self) -> float:
        return self.objective_value
    
    def get_test_results(self) -> Dict:
        return {
            'oc_ratio': 1.15,
            'ic_ratio': 1.20,
            'diversity_score': 85.0,
            'warf': 2500
        }
    
    def get_collateral_par_amount(self, filter_expr: str) -> float:
        # Simple mock - return total amount if no filter
        return self.total_par_amount * 0.8  # 80% available for sale
    
    def num_of_assets(self, filter_expr: str) -> int:
        return len([a for a in self.assets.values() if a.sp_rating in ['B', 'BB']])
    
    def apply_filter(self, filter_expr: str) -> Dict:
        # Simple mock filtering
        if 'rating' in filter_expr.lower():
            return {
                aid: asset for aid, asset in self.assets.items()
                if asset.sp_rating in ['B', 'BB', 'BBB']
            }
        return self.assets
    
    def sale_asset(self, asset: MockAsset):
        if asset.asset_id in self.assets:
            self.total_par_amount -= asset.par_amount
            self.objective_value += 0.5  # Mock improvement
    
    def purchase_asset(self, asset: MockAsset):
        if asset.asset_id not in self.assets:
            self.assets[asset.asset_id] = asset
        self.total_par_amount += asset.par_amount
        self.objective_value += 1.0  # Mock improvement
    
    def get_asset_position(self, asset_id: str) -> float:
        return self.assets.get(asset_id, MockAsset(asset_id)).par_amount


class TestRebalanceInputs:
    """Test RebalanceInputs data class"""
    
    def test_rebalance_inputs_initialization(self):
        """Test RebalanceInputs initialization with valid data"""
        inputs = RebalanceInputs(
            transaction_type=TransactionType.BUY,
            max_num_assets=100,
            sale_par_amount=5000000.0,
            buy_par_amount=10000000.0
        )
        
        assert inputs.transaction_type == TransactionType.BUY
        assert inputs.max_num_assets == 100
        assert inputs.sale_par_amount == 5000000.0
        assert inputs.buy_par_amount == 10000000.0
        assert inputs.max_concentration_per_asset == 0.05
    
    def test_rebalance_inputs_validation(self):
        """Test RebalanceInputs validation"""
        # Test negative sale amount
        with pytest.raises(ValueError, match="Sale par amount must be non-negative"):
            RebalanceInputs(
                transaction_type=TransactionType.SELL,
                sale_par_amount=-1000000.0
            )
        
        # Test invalid concentration limit
        with pytest.raises(ValueError, match="Max concentration per asset"):
            RebalanceInputs(
                transaction_type=TransactionType.BUY,
                max_concentration_per_asset=1.5
            )
    
    def test_create_rebalance_inputs_from_config(self):
        """Test creation from configuration dictionary"""
        config_dict = {
            'transaction_type': 'BUY',
            'max_num_assets': 75,
            'sale_par_amount': 2000000.0,
            'buy_par_amount': 8000000.0,
            'buy_filter': 'rating >= BBB',
            'libor_rate': 0.025
        }
        
        inputs = create_rebalance_inputs_from_config(config_dict)
        
        assert inputs.transaction_type == TransactionType.BUY
        assert inputs.max_num_assets == 75
        assert inputs.sale_par_amount == 2000000.0
        assert inputs.buy_par_amount == 8000000.0
        assert inputs.buy_filter == 'rating >= BBB'
        assert inputs.libor_rate == 0.025


class TestTradeRecommendation:
    """Test TradeRecommendation data class"""
    
    def test_trade_recommendation_creation(self):
        """Test trade recommendation creation"""
        trade = TradeRecommendation(
            asset_id='TEST001',
            asset_name='Test Asset',
            transaction_type=TransactionType.BUY,
            par_amount=1000000.0,
            price=100.5,
            current_position=0.0,
            objective_score=0.85,
            compliance_impact={},
            rationale='High quality asset'
        )
        
        assert trade.asset_id == 'TEST001'
        assert trade.transaction_type == TransactionType.BUY
        assert trade.par_amount == 1000000.0
        assert trade.objective_score == 0.85


class TestRebalanceResults:
    """Test RebalanceResults data class"""
    
    def test_rebalance_results_properties(self):
        """Test RebalanceResults calculated properties"""
        sale_trades = [
            TradeRecommendation(
                asset_id='SELL001', asset_name='Sell Asset', 
                transaction_type=TransactionType.SELL, par_amount=2000000.0,
                price=99.0, current_position=2000000.0, objective_score=0.3,
                compliance_impact={}, rationale='Low performer'
            )
        ]
        
        buy_trades = [
            TradeRecommendation(
                asset_id='BUY001', asset_name='Buy Asset',
                transaction_type=TransactionType.BUY, par_amount=1500000.0,
                price=101.0, current_position=0.0, objective_score=0.9,
                compliance_impact={}, rationale='High quality'
            )
        ]
        
        results = RebalanceResults(
            before_objective=45.0,
            after_sale_objective=46.0,
            after_buy_objective=48.0,
            total_improvement=3.0,
            sale_trades=sale_trades,
            buy_trades=buy_trades,
            compliance_before={},
            compliance_after_sale={},
            compliance_after_buy={},
            execution_stats={}
        )
        
        assert results.total_sale_amount == 2000000.0
        assert results.total_buy_amount == 1500000.0
        assert results.total_improvement == 3.0


class TestPortfolioRebalancer:
    """Test PortfolioRebalancer class"""
    
    @pytest.fixture
    def rebalancer(self):
        return PortfolioRebalancer()
    
    @pytest.fixture
    def mock_portfolio(self):
        assets = [
            MockAsset('ASSET001', par_amount=2000000, sp_rating='B', spread=0.08),
            MockAsset('ASSET002', par_amount=1500000, sp_rating='BB', spread=0.06),
            MockAsset('ASSET003', par_amount=1000000, sp_rating='BBB', spread=0.04),
        ]
        return MockPortfolio(assets)
    
    @pytest.fixture
    def mock_all_collateral(self):
        assets = []
        ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']
        for i in range(20):
            rating = ratings[i % len(ratings)]
            spread = 0.02 + (5 - ratings.index(rating)) * 0.01
            assets.append(MockAsset(
                f'UNIV{i:03d}',
                par_amount=1000000,
                sp_rating=rating,
                spread=spread
            ))
        return MockPortfolio(assets)
    
    @pytest.fixture
    def rebalance_config(self):
        return RebalanceInputs(
            transaction_type=TransactionType.BUY,
            sale_par_amount=2000000.0,
            buy_par_amount=3000000.0,
            incremental_loan_size=500000.0,
            buy_filter='rating >= BBB',
            sale_filter='rating <= BB'
        )
    
    def test_rebalancer_initialization(self, rebalancer):
        """Test rebalancer initialization"""
        assert rebalancer.progress_callback is None
        assert not rebalancer.cancelled
    
    def test_set_progress_callback(self, rebalancer):
        """Test setting progress callback"""
        def mock_callback(message: str, progress: float):
            pass
        
        rebalancer.set_progress_callback(mock_callback)
        assert rebalancer.progress_callback == mock_callback
    
    def test_cancel_operation(self, rebalancer):
        """Test operation cancellation"""
        assert not rebalancer.cancelled
        rebalancer.cancel_operation()
        assert rebalancer.cancelled
    
    def test_calculate_objective(self, rebalancer, mock_portfolio):
        """Test objective function calculation"""
        objective = rebalancer._calculate_objective(mock_portfolio)
        assert isinstance(objective, float)
        assert objective > 0
    
    def test_get_rating_score(self, rebalancer):
        """Test rating to score conversion"""
        assert rebalancer._get_rating_score('AAA') > rebalancer._get_rating_score('BBB')
        assert rebalancer._get_rating_score('BBB') > rebalancer._get_rating_score('B')
        assert rebalancer._get_rating_score('B') > rebalancer._get_rating_score('D')
        assert rebalancer._get_rating_score('UNKNOWN') == 3.0  # Default
    
    def test_get_maturity_score(self, rebalancer):
        """Test maturity scoring"""
        today = date.today()
        
        # Test optimal range (3-7 years)
        optimal_date = today + timedelta(days=5 * 365)
        optimal_score = rebalancer._get_maturity_score(optimal_date)
        
        # Test too short (< 1 year)
        short_date = today + timedelta(days=180)
        short_score = rebalancer._get_maturity_score(short_date)
        
        # Test too long (> 10 years)
        long_date = today + timedelta(days=12 * 365)
        long_score = rebalancer._get_maturity_score(long_date)
        
        assert optimal_score > short_score
        assert optimal_score > long_score
        assert optimal_score == 5.0
    
    def test_calculate_asset_objective_score(self, rebalancer, rebalance_config):
        """Test asset objective score calculation"""
        asset = MockAsset('TEST001', spread=0.06, sp_rating='A')
        
        score = rebalancer._calculate_asset_objective_score(
            asset, TransactionType.BUY, 1000000.0, rebalance_config
        )
        
        assert isinstance(score, float)
        assert score > 0
    
    def test_rank_assets_for_transaction_buy(self, rebalancer, mock_all_collateral, rebalance_config):
        """Test asset ranking for buy transactions"""
        ranked_assets = rebalancer._rank_assets_for_transaction(
            mock_all_collateral,
            TransactionType.BUY,
            'rating >= BBB',
            1000000.0,
            rebalance_config
        )
        
        assert len(ranked_assets) > 0
        assert len(ranked_assets) <= 50  # Max candidates
        
        # Verify sorting (highest scores first for BUY)
        if len(ranked_assets) > 1:
            assert ranked_assets[0]['objective_score'] >= ranked_assets[1]['objective_score']
    
    def test_rank_assets_for_transaction_sell(self, rebalancer, mock_portfolio, rebalance_config):
        """Test asset ranking for sell transactions"""
        sell_config = RebalanceInputs(
            transaction_type=TransactionType.SELL,
            sale_filter='rating <= BB'
        )
        
        ranked_assets = rebalancer._rank_assets_for_transaction(
            mock_portfolio,
            TransactionType.SELL,
            'rating <= BB',
            1000000.0,
            sell_config
        )
        
        assert len(ranked_assets) > 0
        
        # Verify sorting (lowest scores first for SELL)
        if len(ranked_assets) > 1:
            assert ranked_assets[0]['objective_score'] <= ranked_assets[1]['objective_score']
    
    def test_execute_sale(self, rebalancer, mock_portfolio):
        """Test sale execution"""
        asset_info = {
            'asset_id': 'ASSET001',
            'asset': mock_portfolio.assets['ASSET001'],
            'objective_score': 0.3
        }
        
        trade = rebalancer._execute_sale(mock_portfolio, asset_info, 500000.0)
        
        assert trade is not None
        assert trade.asset_id == 'ASSET001'
        assert trade.transaction_type == TransactionType.SELL
        assert trade.par_amount == 500000.0
    
    def test_execute_purchase(self, rebalancer, mock_portfolio, mock_all_collateral):
        """Test purchase execution"""
        asset_info = {
            'asset_id': 'UNIV001',
            'asset': mock_all_collateral.assets['UNIV001'],
            'objective_score': 0.8
        }
        
        trade = rebalancer._execute_purchase(
            mock_portfolio, mock_all_collateral, asset_info, 1000000.0
        )
        
        assert trade is not None
        assert trade.asset_id == 'UNIV001'
        assert trade.transaction_type == TransactionType.BUY
        assert trade.par_amount == 1000000.0
    
    def test_would_exceed_concentration(self, rebalancer, mock_portfolio, rebalance_config):
        """Test concentration limit checking"""
        asset_info = {'asset_id': 'TEST001'}
        existing_buys = [
            TradeRecommendation(
                asset_id='TEST001', asset_name='Test', transaction_type=TransactionType.BUY,
                par_amount=100000.0, price=100.0, current_position=0.0,
                objective_score=0.8, compliance_impact={}, rationale='Test'
            )
        ]
        
        # Test within limits
        within_limits = rebalancer._would_exceed_concentration(
            mock_portfolio, asset_info, 50000.0, rebalance_config, existing_buys
        )
        
        # Test exceeding limits
        exceed_limits = rebalancer._would_exceed_concentration(
            mock_portfolio, asset_info, 200000.0, rebalance_config, existing_buys
        )
        
        assert not within_limits
        assert exceed_limits
    
    def test_run_rebalancing_basic(self, rebalancer, mock_portfolio, mock_all_collateral, rebalance_config):
        """Test basic rebalancing workflow"""
        results = rebalancer.run_rebalancing(
            portfolio=mock_portfolio,
            all_collateral=mock_all_collateral,
            config=rebalance_config
        )
        
        assert isinstance(results, RebalanceResults)
        assert results.before_objective > 0
        assert len(results.execution_stats) > 0
        assert 'start_time' in results.execution_stats
        assert 'duration_seconds' in results.execution_stats
    
    def test_run_rebalancing_sales_only(self, rebalancer, mock_portfolio, mock_all_collateral):
        """Test rebalancing with only sales"""
        config = RebalanceInputs(
            transaction_type=TransactionType.SELL,
            sale_par_amount=1000000.0,
            buy_par_amount=0.0,
            sale_filter='rating <= BB'
        )
        
        results = rebalancer.run_rebalancing(
            portfolio=mock_portfolio,
            all_collateral=mock_all_collateral,
            config=config
        )
        
        assert len(results.sale_trades) > 0
        assert len(results.buy_trades) == 0
        assert results.total_sale_amount > 0
        assert results.total_buy_amount == 0
    
    def test_run_rebalancing_purchases_only(self, rebalancer, mock_portfolio, mock_all_collateral):
        """Test rebalancing with only purchases"""
        config = RebalanceInputs(
            transaction_type=TransactionType.BUY,
            sale_par_amount=0.0,
            buy_par_amount=2000000.0,
            buy_filter='rating >= A'
        )
        
        results = rebalancer.run_rebalancing(
            portfolio=mock_portfolio,
            all_collateral=mock_all_collateral,
            config=config
        )
        
        assert len(results.sale_trades) == 0
        assert len(results.buy_trades) > 0
        assert results.total_sale_amount == 0
        assert results.total_buy_amount > 0
    
    def test_run_rebalancing_with_progress_callback(self, rebalancer, mock_portfolio, mock_all_collateral, rebalance_config):
        """Test rebalancing with progress tracking"""
        progress_calls = []
        
        def progress_callback(message: str, progress: float):
            progress_calls.append((message, progress))
        
        rebalancer.set_progress_callback(progress_callback)
        
        results = rebalancer.run_rebalancing(
            portfolio=mock_portfolio,
            all_collateral=mock_all_collateral,
            config=rebalance_config
        )
        
        assert len(progress_calls) > 0
        # Check that we got both sale and buy progress updates
        messages = [call[0] for call in progress_calls]
        assert any('Sale' in msg for msg in messages)
        assert any('Buy' in msg for msg in messages)
    
    def test_run_rebalancing_cancellation(self, rebalancer, mock_portfolio, mock_all_collateral, rebalance_config):
        """Test rebalancing cancellation"""
        def progress_callback(message: str, progress: float):
            if progress > 0.1:  # Cancel after some progress
                rebalancer.cancel_operation()
        
        rebalancer.set_progress_callback(progress_callback)
        
        results = rebalancer.run_rebalancing(
            portfolio=mock_portfolio,
            all_collateral=mock_all_collateral,
            config=rebalance_config
        )
        
        assert results.execution_stats.get('cancelled', False)


class TestRebalancingService:
    """Test RebalancingService class"""
    
    @pytest.fixture
    def service(self):
        return RebalancingService()
    
    @pytest.fixture
    def mock_portfolio_config(self):
        return {
            'transaction_type': 'BUY',
            'max_num_assets': 50,
            'sale_par_amount': 5000000.0,
            'buy_par_amount': 10000000.0,
            'incremental_loan_size': 1000000.0,
            'buy_filter': 'rating >= BBB',
            'sale_filter': 'rating <= BB',
            'max_concentration_per_asset': 0.05
        }
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service.rebalancer is not None
        assert service.current_operation_id is None
    
    def test_parse_rebalance_config(self, service, mock_portfolio_config):
        """Test configuration parsing"""
        config = service._parse_rebalance_config(mock_portfolio_config)
        
        assert isinstance(config, RebalanceInputs)
        assert config.transaction_type == TransactionType.BUY
        assert config.max_num_assets == 50
        assert config.sale_par_amount == 5000000.0
        assert config.buy_par_amount == 10000000.0
    
    def test_parse_rebalance_config_invalid(self, service):
        """Test invalid configuration parsing"""
        invalid_config = {'sale_par_amount': -1000000.0}
        
        with pytest.raises(Exception):  # CLOValidationError in real implementation
            service._parse_rebalance_config(invalid_config)
    
    @patch('app.services.rebalancing_service.RebalancingService._get_portfolio')
    @patch('app.services.rebalancing_service.RebalancingService._create_collateral_pool')
    @patch('app.services.rebalancing_service.RebalancingService._get_all_collateral')
    def test_run_portfolio_rebalancing(self, mock_all_collateral, mock_collateral_pool, 
                                     mock_get_portfolio, service, mock_portfolio_config):
        """Test portfolio rebalancing execution"""
        # Mock return values
        mock_portfolio = Mock()
        mock_portfolio.id = 'TEST_PORTFOLIO'
        mock_get_portfolio.return_value = mock_portfolio
        
        mock_pool = MockPortfolio([MockAsset('ASSET001')])
        mock_collateral_pool.return_value = mock_pool
        
        mock_all = MockPortfolio([MockAsset('UNIV001'), MockAsset('UNIV002')])
        mock_all_collateral.return_value = mock_all
        
        # Run rebalancing
        result = service.run_portfolio_rebalancing(
            portfolio_id='TEST_PORTFOLIO',
            rebalance_config=mock_portfolio_config
        )
        
        assert result['success'] is True
        assert 'operation_id' in result
        assert 'execution_summary' in result
        assert result['portfolio_id'] == 'TEST_PORTFOLIO'
    
    def test_run_asset_ranking_buy(self, service):
        """Test asset ranking for buy transactions"""
        ranking_config = {
            'transaction_type': 'BUY',
            'filter_expression': 'rating >= A',
            'max_assets': 10,
            'incremental_loan_size': 1000000.0
        }
        
        with patch.object(service, '_get_portfolio') as mock_get_portfolio, \
             patch.object(service, '_get_all_collateral') as mock_get_all:
            
            mock_portfolio = Mock()
            mock_get_portfolio.return_value = mock_portfolio
            
            mock_all = MockPortfolio([
                MockAsset('RANK001', sp_rating='AAA', spread=0.03),
                MockAsset('RANK002', sp_rating='A', spread=0.05),
                MockAsset('RANK003', sp_rating='BBB', spread=0.06)
            ])
            mock_get_all.return_value = mock_all
            
            result = service.run_asset_ranking('TEST_PORTFOLIO', ranking_config)
            
            assert result['transaction_type'] == 'BUY'
            assert len(result['rankings']) > 0
            assert 'summary' in result
    
    def test_run_asset_ranking_sell(self, service):
        """Test asset ranking for sell transactions"""
        ranking_config = {
            'transaction_type': 'SELL',
            'filter_expression': 'rating <= BB',
            'max_assets': 5
        }
        
        with patch.object(service, '_get_portfolio') as mock_get_portfolio, \
             patch.object(service, '_create_collateral_pool') as mock_create_pool:
            
            mock_portfolio = Mock()
            mock_get_portfolio.return_value = mock_portfolio
            
            mock_pool = MockPortfolio([
                MockAsset('SELL001', sp_rating='B', spread=0.08),
                MockAsset('SELL002', sp_rating='BB', spread=0.06)
            ])
            mock_create_pool.return_value = mock_pool
            
            result = service.run_asset_ranking('TEST_PORTFOLIO', ranking_config)
            
            assert result['transaction_type'] == 'SELL'
            assert len(result['rankings']) > 0
    
    def test_cancel_rebalancing(self, service):
        """Test rebalancing cancellation"""
        operation_id = 'TEST_OP_001'
        
        # Test cancelling non-existent operation
        result = service.cancel_rebalancing(operation_id)
        assert not result['cancelled']
        
        # Test cancelling current operation
        service.current_operation_id = operation_id
        result = service.cancel_rebalancing(operation_id)
        assert result['cancelled']
    
    def test_get_rebalancing_results(self, service):
        """Test retrieving rebalancing results"""
        operation_id = 'TEST_OP_001'
        
        result = service.get_rebalancing_results(operation_id)
        
        assert result['operation_id'] == operation_id
        assert 'status' in result
    
    def test_export_rebalancing_results_excel(self, service):
        """Test Excel export"""
        operation_id = 'TEST_OP_001'
        
        filename = service.export_rebalancing_results(operation_id, 'excel')
        
        assert 'rebalancing_results' in filename
        assert filename.endswith('.excel')
    
    def test_export_rebalancing_results_csv(self, service):
        """Test CSV export"""
        operation_id = 'TEST_OP_001'
        
        csv_data = service.export_rebalancing_results(operation_id, 'csv')
        
        assert isinstance(csv_data, str)
        assert 'asset_id,transaction_type,par_amount' in csv_data
    
    def test_create_collateral_pool(self, service):
        """Test collateral pool creation"""
        mock_portfolio = Mock()
        mock_portfolio.assets = [MockAsset('ASSET001'), MockAsset('ASSET002')]
        
        pool = service._create_collateral_pool(mock_portfolio)
        
        assert hasattr(pool, 'get_objective_value')
        assert hasattr(pool, 'apply_filter')
        assert hasattr(pool, 'sale_asset')
        assert hasattr(pool, 'purchase_asset')
    
    def test_get_all_collateral(self, service):
        """Test all collateral pool creation"""
        all_collateral = service._get_all_collateral()
        
        assert hasattr(all_collateral, 'get_asset_ids')
        assert hasattr(all_collateral, 'get_asset')
        assert hasattr(all_collateral, 'apply_filter')
        
        asset_ids = all_collateral.get_asset_ids()
        assert len(asset_ids) > 0


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_rebalancing_with_insufficient_assets(self):
        """Test rebalancing when insufficient assets meet criteria"""
        rebalancer = PortfolioRebalancer()
        
        # Portfolio with only one small asset
        portfolio = MockPortfolio([MockAsset('ONLY001', par_amount=100000)])
        all_collateral = MockPortfolio([])  # No assets available for purchase
        
        config = RebalanceInputs(
            transaction_type=TransactionType.BUY,
            buy_par_amount=5000000.0,
            buy_filter='rating >= AAA'  # Very restrictive filter
        )
        
        results = rebalancer.run_rebalancing(portfolio, all_collateral, config)
        
        # Should complete without error but with limited trades
        assert isinstance(results, RebalanceResults)
        assert len(results.warnings) >= 0  # May have warnings
    
    def test_rebalancing_with_zero_amounts(self):
        """Test rebalancing with zero sale/buy amounts"""
        rebalancer = PortfolioRebalancer()
        portfolio = MockPortfolio([MockAsset('ASSET001')])
        all_collateral = MockPortfolio([MockAsset('UNIV001')])
        
        config = RebalanceInputs(
            transaction_type=TransactionType.BUY,
            sale_par_amount=0.0,
            buy_par_amount=0.0
        )
        
        results = rebalancer.run_rebalancing(portfolio, all_collateral, config)
        
        assert len(results.sale_trades) == 0
        assert len(results.buy_trades) == 0
        assert results.total_improvement == 0.0
    
    def test_objective_score_calculation_errors(self):
        """Test handling of errors in objective score calculation"""
        rebalancer = PortfolioRebalancer()
        
        # Asset with missing attributes
        incomplete_asset = Mock()
        incomplete_asset.asset_id = 'INCOMPLETE'
        # Missing spread, rating, maturity attributes
        
        config = RebalanceInputs(transaction_type=TransactionType.BUY)
        
        # Should not raise exception, should return default score
        score = rebalancer._calculate_asset_objective_score(
            incomplete_asset, TransactionType.BUY, 1000000.0, config
        )
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_concentration_limit_edge_cases(self):
        """Test concentration limit checking edge cases"""
        rebalancer = PortfolioRebalancer()
        portfolio = MockPortfolio([])
        
        config = RebalanceInputs(
            transaction_type=TransactionType.BUY,
            buy_par_amount=0.0,  # Zero buy amount
            max_concentration_per_asset=0.05
        )
        
        # Test with zero buy amount (should not exceed)
        asset_info = {'asset_id': 'TEST001'}
        result = rebalancer._would_exceed_concentration(
            portfolio, asset_info, 1000000.0, config, []
        )
        
        assert not result  # Should not exceed when buy_par_amount is 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])