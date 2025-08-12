"""
Tests for Credit Migration Module

Comprehensive test suite for credit migration modeling functionality
converted from VBA CreditMigration.bas.

Author: Claude
Date: 2025-01-12
"""

import pytest
import numpy as np
from datetime import date, timedelta
from unittest.mock import Mock, MagicMock

from app.models.credit_migration import (
    CreditMigration,
    SPRating,
    RatingHist,
    RatingHistBal,
    SimHistory
)


class MockCollateralPool:
    """Mock collateral pool for testing"""
    
    def __init__(self):
        self.assets = {
            "ASSET_1": {
                "sp_rating": "BBB",
                "maturity": date(2028, 12, 31),
                "defaulted": False,
                "issuer_id": "ISSUER_1",
                "sp_industry": "TECHNOLOGY",
                "balance": 1000000.0
            },
            "ASSET_2": {
                "sp_rating": "A",
                "maturity": date(2027, 12, 31),
                "defaulted": False,
                "issuer_id": "ISSUER_2",
                "sp_industry": "HEALTHCARE",
                "balance": 2000000.0
            },
            "ASSET_3": {
                "sp_rating": "CCC+",
                "maturity": date(2026, 12, 31),
                "defaulted": False,
                "issuer_id": "ISSUER_3",
                "sp_industry": "ENERGY",
                "balance": 500000.0
            }
        }
    
    def get_asset_ids(self):
        return list(self.assets.keys())
    
    def get_asset(self, asset_id):
        asset_data = self.assets[asset_id]
        mock_asset = Mock()
        mock_asset.sp_rating = asset_data["sp_rating"]
        mock_asset.issuer_id = asset_data["issuer_id"]
        mock_asset.sp_industry = asset_data["sp_industry"]
        return mock_asset
    
    def get_sp_rating(self, asset_id, date_val=None):
        return self.assets[asset_id]["sp_rating"]
    
    def get_asset_maturity(self, asset_id):
        return self.assets[asset_id]["maturity"]
    
    def is_defaulted(self, asset_id):
        return self.assets[asset_id]["defaulted"]
    
    def get_last_maturity_date(self):
        return max(asset["maturity"] for asset in self.assets.values())
    
    def get_beginning_balance(self, asset_id, date_val):
        return self.assets[asset_id]["balance"]
    
    def get_scheduled_principal(self, asset_id, start_date, end_date):
        # Simple mock - return 0 unless maturity
        maturity = self.assets[asset_id]["maturity"]
        if start_date <= maturity <= end_date:
            return self.assets[asset_id]["balance"]
        return 0.0
    
    def add_sp_rating(self, asset_id, date_val, rating):
        # Mock method to track rating changes
        pass


class TestSPRating:
    """Test SPRating enumeration"""
    
    def test_rating_enum_values(self):
        """Test that rating enum has correct values"""
        assert SPRating.AAA == 1
        assert SPRating.AA_PLUS == 2
        assert SPRating.AA == 3
        assert SPRating.DEFAULT == 18
    
    def test_rating_enum_completeness(self):
        """Test that all major ratings are included"""
        assert len(SPRating) == 18
        assert SPRating.BBB in SPRating
        assert SPRating.CCC in SPRating


class TestRatingStructures:
    """Test rating history data structures"""
    
    def test_rating_hist_initialization(self):
        """Test RatingHist initialization with defaults"""
        hist = RatingHist()
        
        assert hist.upgrades == 0
        assert hist.downgrades == 0
        assert hist.num_aaa == 0
        assert hist.num_defaults == 0
        assert hist.num_period_defaults == 0
    
    def test_rating_hist_bal_initialization(self):
        """Test RatingHistBal initialization with defaults"""
        hist_bal = RatingHistBal()
        
        assert hist_bal.bal_aaa == 0.0
        assert hist_bal.bal_defaults == 0.0
        assert hist_bal.cdr == 0.0
    
    def test_sim_history_initialization(self):
        """Test SimHistory initialization"""
        sim_hist = SimHistory()
        
        assert isinstance(sim_hist.rating_hist, list)
        assert isinstance(sim_hist.rating_hist_bal, list)
        assert len(sim_hist.rating_hist) == 0


class TestCreditMigration:
    """Test CreditMigration class"""
    
    @pytest.fixture
    def credit_migration(self):
        """Create CreditMigration instance for testing"""
        return CreditMigration()
    
    @pytest.fixture
    def mock_pool(self):
        """Create mock collateral pool"""
        return MockCollateralPool()
    
    def test_initialization(self, credit_migration):
        """Test CreditMigration initialization"""
        assert credit_migration.tran_matrix is None
        assert credit_migration.corr_matrix is None
        assert credit_migration.num_assets == 0
        assert credit_migration.sim_count == 0
        assert credit_migration.period_type == "QUARTERLY"
    
    def test_cleanup(self, credit_migration):
        """Test cleanup method"""
        credit_migration.num_assets = 5
        credit_migration.asset_order = ["A", "B", "C"]
        credit_migration.sim_count = 10
        
        credit_migration.cleanup()
        
        assert credit_migration.tran_matrix is None
        assert credit_migration.corr_matrix is None
        assert len(credit_migration.asset_order) == 0
        assert credit_migration.sim_count == 0
    
    def test_setup_default_matrix(self, credit_migration):
        """Test setup with default correlation matrix"""
        credit_migration.setup(num_sims=10, debug_mode=True)
        
        assert credit_migration.tran_matrix is not None
        assert credit_migration.corr_matrix is not None
        assert len(credit_migration.sim_hist) == 10
        assert credit_migration.tran_matrix.shape == (18, 18)
    
    def test_setup_with_collateral_pool(self, credit_migration, mock_pool):
        """Test setup with collateral pool"""
        credit_migration.setup(
            num_sims=5, 
            debug_mode=True, 
            collateral_pool=mock_pool,
            period="QUARTERLY"
        )
        
        assert credit_migration.num_assets == 3  # Number of assets in mock pool
        assert len(credit_migration.asset_order) == 3
        assert credit_migration.period_type == "QUARTERLY"
    
    def test_transition_matrix_setup_quarterly(self, credit_migration):
        """Test transition matrix setup for quarterly periods"""
        credit_migration._setup_transition_matrix("QUARTERLY")
        
        assert credit_migration.tran_matrix is not None
        assert credit_migration.tran_matrix.shape == (18, 18)
        
        # Check that it's a cumulative matrix (values should be non-decreasing across rows)
        for i in range(18):
            for j in range(17):
                assert credit_migration.tran_matrix[i, j] <= credit_migration.tran_matrix[i, j + 1]
    
    def test_transition_matrix_setup_annually(self, credit_migration):
        """Test transition matrix setup for annual periods"""
        credit_migration._setup_transition_matrix("ANNUALLY")
        
        assert credit_migration.tran_matrix is not None
        # Should still be 18x18 for all rating categories
        assert credit_migration.tran_matrix.shape == (18, 18)
    
    def test_default_correlation_matrix(self, credit_migration):
        """Test default correlation matrix creation"""
        corr_matrix = credit_migration._create_default_correlation_matrix()
        
        assert isinstance(corr_matrix, np.ndarray)
        assert corr_matrix.shape[0] == corr_matrix.shape[1]  # Square matrix
        
        # Check that diagonal elements are 1.0
        np.testing.assert_array_equal(np.diag(corr_matrix), np.ones(corr_matrix.shape[0]))
        
        # Check symmetry
        np.testing.assert_array_equal(corr_matrix, corr_matrix.T)
    
    def test_correlation_matrix_from_pool(self, credit_migration, mock_pool):
        """Test correlation matrix creation from collateral pool"""
        corr_matrix = credit_migration._create_correlation_matrix_from_pool(mock_pool)
        
        assert isinstance(corr_matrix, np.ndarray)
        assert corr_matrix.shape == (3, 3)  # 3 assets in mock pool
        
        # Check diagonal elements
        np.testing.assert_array_equal(np.diag(corr_matrix), np.ones(3))
        
        # Check symmetry
        np.testing.assert_array_equal(corr_matrix, corr_matrix.T)
        
        # Check that all values are between 0 and 1
        assert np.all(corr_matrix >= 0.0)
        assert np.all(corr_matrix <= 1.0)
    
    def test_rating_conversions(self, credit_migration):
        """Test rating string to enum conversions"""
        # Test rating to enum
        assert credit_migration._convert_rating_to_enum("AAA") == SPRating.AAA
        assert credit_migration._convert_rating_to_enum("BBB") == SPRating.BBB
        assert credit_migration._convert_rating_to_enum("D") == SPRating.DEFAULT
        assert credit_migration._convert_rating_to_enum("INVALID") == SPRating.DEFAULT
        
        # Test enum to rating string
        assert credit_migration._convert_rating_enum_to_str(SPRating.AAA) == "AAA"
        assert credit_migration._convert_rating_enum_to_str(SPRating.BBB) == "BBB"
        assert credit_migration._convert_rating_enum_to_str(SPRating.DEFAULT) == "D"
    
    def test_rating_rank(self, credit_migration):
        """Test rating ranking system"""
        assert credit_migration._get_rating_rank("AAA") < credit_migration._get_rating_rank("BBB")
        assert credit_migration._get_rating_rank("BBB") < credit_migration._get_rating_rank("CCC")
        assert credit_migration._get_rating_rank("CCC") < credit_migration._get_rating_rank("D")
        
        # Test invalid rating
        assert credit_migration._get_rating_rank("INVALID") == 18
    
    def test_correlated_random_generation(self, credit_migration, mock_pool):
        """Test correlated random number generation"""
        credit_migration.setup(num_sims=1, collateral_pool=mock_pool)
        
        # Generate correlated random numbers
        random_numbers = credit_migration._get_correlated_random()
        
        assert isinstance(random_numbers, np.ndarray)
        assert len(random_numbers) == credit_migration.num_assets
        
        # All values should be between 0 and 1 (uniform distribution)
        assert np.all(random_numbers >= 0.0)
        assert np.all(random_numbers <= 1.0)
    
    def test_should_include_asset(self, credit_migration):
        """Test asset inclusion logic"""
        # Test with no deal collateral (should include all)
        assert credit_migration._should_include_asset("ASSET_1", None) is True
        
        # Test with deal collateral
        deal_collateral = {"ASSET_1": 1000000.0, "ASSET_2": 2000000.0}
        assert credit_migration._should_include_asset("ASSET_1", deal_collateral) is True
        assert credit_migration._should_include_asset("ASSET_3", deal_collateral) is False
    
    def test_update_rating_hist(self, credit_migration):
        """Test rating history updates"""
        credit_migration.rating_hist = [RatingHist()]
        
        credit_migration._update_rating_hist(0, "AAA")
        credit_migration._update_rating_hist(0, "BBB")
        credit_migration._update_rating_hist(0, "D")
        
        hist = credit_migration.rating_hist[0]
        assert hist.num_aaa == 1
        assert hist.num_bbb == 1
        assert hist.num_defaults == 1
    
    def test_update_rating_hist_bal(self, credit_migration):
        """Test rating balance history updates"""
        credit_migration.rating_hist_bal = [RatingHistBal()]
        
        credit_migration._update_rating_hist_bal(0, "AAA", 1000000.0)
        credit_migration._update_rating_hist_bal(0, "AAA", 500000.0)
        credit_migration._update_rating_hist_bal(0, "D", 2000000.0)
        
        hist_bal = credit_migration.rating_hist_bal[0]
        assert hist_bal.bal_aaa == 1500000.0
        assert hist_bal.bal_defaults == 2000000.0
    
    def test_calculate_num_periods(self, credit_migration):
        """Test period calculation"""
        start_date = date(2024, 1, 1)
        end_date = date(2025, 1, 1)
        
        # Quarterly periods
        periods = credit_migration._calculate_num_periods(start_date, end_date, 3)
        assert periods == 4  # 4 quarters
    
    def test_run_rating_history_basic(self, credit_migration, mock_pool):
        """Test basic rating history simulation run"""
        credit_migration.setup(num_sims=1, collateral_pool=mock_pool, debug_mode=True)
        
        analysis_date = date(2024, 1, 1)
        credit_migration.run_rating_history(analysis_date, mock_pool, period="QUARTERLY")
        
        assert credit_migration.analysis_date == analysis_date
        assert credit_migration.num_periods > 0
        assert len(credit_migration.rating_hist) == credit_migration.num_periods + 1
        assert len(credit_migration.rating_hist_bal) == credit_migration.num_periods + 1
    
    def test_run_rating_history_with_deal_collateral(self, credit_migration, mock_pool):
        """Test rating history with specific deal collateral"""
        credit_migration.setup(num_sims=1, collateral_pool=mock_pool, debug_mode=True)
        
        deal_collateral = {"ASSET_1": 1000000.0, "ASSET_2": 2000000.0}
        analysis_date = date(2024, 1, 1)
        
        credit_migration.run_rating_history(
            analysis_date, mock_pool, deal_collateral, "QUARTERLY"
        )
        
        # Should only process assets in deal_collateral
        initial_hist = credit_migration.rating_hist[0]
        total_initial_assets = (
            initial_hist.num_aaa + initial_hist.num_aa_plus + initial_hist.num_aa +
            initial_hist.num_aa_minus + initial_hist.num_a_plus + initial_hist.num_a +
            initial_hist.num_a_minus + initial_hist.num_bbb_plus + initial_hist.num_bbb +
            initial_hist.num_bbb_minus + initial_hist.num_bb_plus + initial_hist.num_bb +
            initial_hist.num_bb_minus + initial_hist.num_b_plus + initial_hist.num_b +
            initial_hist.num_b_minus + initial_hist.num_ccc_assets
        )
        
        assert total_initial_assets == 2  # Only 2 assets in deal collateral
    
    def test_get_simulation_results_empty(self, credit_migration):
        """Test simulation results with no data"""
        results = credit_migration.get_simulation_results()
        assert results == {}
    
    def test_get_simulation_results_with_data(self, credit_migration, mock_pool):
        """Test simulation results generation"""
        credit_migration.setup(num_sims=2, collateral_pool=mock_pool, debug_mode=True)
        
        # Run a couple of simulations
        analysis_date = date(2024, 1, 1)
        for _ in range(2):
            credit_migration.run_rating_history(analysis_date, mock_pool, period="QUARTERLY")
        
        results = credit_migration.get_simulation_results()
        
        assert results["num_simulations"] == 2
        assert results["num_periods"] > 0
        assert results["period_type"] == "QUARTERLY"
        assert results["analysis_date"] == analysis_date
        assert "statistics" in results
    
    def test_export_to_dataframe_empty(self, credit_migration):
        """Test DataFrame export with no data"""
        df = credit_migration.export_to_dataframe()
        assert len(df) == 0
    
    def test_export_to_dataframe_with_data(self, credit_migration, mock_pool):
        """Test DataFrame export with simulation data"""
        credit_migration.setup(num_sims=1, collateral_pool=mock_pool, debug_mode=True)
        
        analysis_date = date(2024, 1, 1)
        credit_migration.run_rating_history(analysis_date, mock_pool, period="QUARTERLY")
        
        df = credit_migration.export_to_dataframe()
        
        assert len(df) > 0
        assert "simulation" in df.columns
        assert "period" in df.columns
        assert "upgrades" in df.columns
        assert "downgrades" in df.columns
        assert "num_defaults" in df.columns
    
    def test_get_next_rating_deterministic(self, credit_migration):
        """Test next rating generation with deterministic input"""
        credit_migration._setup_transition_matrix("QUARTERLY")
        
        # Test with very low z-value (should upgrade or stay same)
        next_rating = credit_migration._get_next_rating("BBB", 0.01)
        assert next_rating in ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB"]
        
        # Test with very high z-value (should downgrade or default)
        next_rating = credit_migration._get_next_rating("BBB", 0.99)
        assert next_rating in ["BBB-", "BB+", "BB", "BB-", "B+", "B", "B-", "CCC", "D"]


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_invalid_period_setup(self):
        """Test setup with invalid period"""
        cm = CreditMigration()
        # Should not raise error, should default to some behavior
        cm.setup(num_sims=1, period="INVALID_PERIOD")
        assert cm.period_type == "INVALID_PERIOD"
    
    def test_zero_simulations(self):
        """Test setup with zero simulations"""
        cm = CreditMigration()
        cm.setup(num_sims=0)
        assert len(cm.sim_hist) == 0
    
    def test_empty_asset_list(self):
        """Test with empty asset list"""
        cm = CreditMigration()
        mock_pool = MockCollateralPool()
        mock_pool.assets = {}  # Empty assets
        
        cm.setup(num_sims=1, collateral_pool=mock_pool)
        assert cm.num_assets == 0
    
    def test_rating_conversion_edge_cases(self):
        """Test rating conversion with edge cases"""
        cm = CreditMigration()
        
        # Test CCC variants
        assert cm._convert_rating_to_enum("CCC+") == SPRating.CCC
        assert cm._convert_rating_to_enum("CCC-") == SPRating.CCC
        assert cm._convert_rating_to_enum("CC") == SPRating.CCC
        
        # Test unknown ratings
        assert cm._convert_rating_to_enum("") == SPRating.DEFAULT
        assert cm._convert_rating_to_enum("UNKNOWN") == SPRating.DEFAULT


class TestIntegration:
    """Integration tests for complete workflow"""
    
    def test_full_simulation_workflow(self):
        """Test complete simulation from setup to results"""
        cm = CreditMigration()
        mock_pool = MockCollateralPool()
        
        # Setup
        cm.setup(num_sims=3, collateral_pool=mock_pool, debug_mode=True, period="QUARTERLY")
        
        # Run multiple simulations
        analysis_date = date(2024, 1, 1)
        deal_collateral = {"ASSET_1": 1000000.0, "ASSET_2": 2000000.0}
        
        for _ in range(3):
            cm.run_rating_history(analysis_date, mock_pool, deal_collateral, "QUARTERLY")
        
        # Get results
        results = cm.get_simulation_results()
        df = cm.export_to_dataframe()
        
        # Validate results
        assert results["num_simulations"] == 3
        assert len(df) > 0
        assert df["simulation"].nunique() == 3
        
        # Cleanup
        cm.cleanup()
        assert cm.tran_matrix is None
        assert len(cm.asset_order) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])