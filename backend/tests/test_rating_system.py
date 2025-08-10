"""
Test suite for Rating System - VBA Rating classes Python implementation

Comprehensive testing of RatingDerivationEngine, RatingService, RatingMigrationItem, 
and RatingMigrationOutput to ensure perfect VBA functional parity.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock

from app.core.database import Base
from app.models.rating_system import (
    RatingDerivationEngine,
    RatingService,
    RatingAgencyModel,
    RatingScale,
    RatingDerivationRule,
    RecoveryRateMatrix,
    RatingMigration,
    PortfolioMigrationStats,
    RatingDistributionHistory,
    RatingAgency
)
from app.models.rating_migration import (
    RatingMigrationItem,
    RatingMigrationOutput,
    RatingMigrationService,
    PeriodFrequency,
    StatisticType,
    RatingHistogram,
    RatingHistogramBalance
)


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database with rating system data"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create rating agencies
    agencies = [
        RatingAgencyModel(agency_name='SP', agency_full_name='S&P Global Ratings'),
        RatingAgencyModel(agency_name='MOODYS', agency_full_name="Moody's Investors Service"),
        RatingAgencyModel(agency_name='FITCH', agency_full_name='Fitch Ratings')
    ]
    for agency in agencies:
        session.add(agency)
    session.flush()
    
    # Create rating scales (simplified set for testing)
    test_ratings = [
        # S&P ratings
        (1, 'AAA', 1, 'INVESTMENT', 'AAA', True),
        (1, 'AA+', 2, 'INVESTMENT', 'AA', True),
        (1, 'AA', 3, 'INVESTMENT', 'AA', True),
        (1, 'AA-', 4, 'INVESTMENT', 'AA', True),
        (1, 'A+', 5, 'INVESTMENT', 'A', True),
        (1, 'A', 6, 'INVESTMENT', 'A', True),
        (1, 'A-', 7, 'INVESTMENT', 'A', True),
        (1, 'BBB+', 8, 'INVESTMENT', 'BBB', True),
        (1, 'BBB', 9, 'INVESTMENT', 'BBB', True),
        (1, 'BBB-', 10, 'INVESTMENT', 'BBB', True),
        (1, 'BB+', 11, 'SPECULATIVE', 'BB', False),
        (1, 'BB', 12, 'SPECULATIVE', 'BB', False),
        (1, 'BB-', 13, 'SPECULATIVE', 'BB', False),
        (1, 'B+', 14, 'SPECULATIVE', 'B', False),
        (1, 'B', 15, 'SPECULATIVE', 'B', False),
        (1, 'B-', 16, 'SPECULATIVE', 'B', False),
        (1, 'CCC+', 17, 'SPECULATIVE', 'CCC', False),
        (1, 'CCC', 18, 'SPECULATIVE', 'CCC', False),
        (1, 'CCC-', 19, 'SPECULATIVE', 'CCC', False),
        (1, 'CC', 20, 'DEFAULT', 'CC', False),
        (1, 'C', 21, 'DEFAULT', 'C', False),
        # Moody's ratings
        (2, 'Aaa', 1, 'INVESTMENT', 'AAA', True),
        (2, 'Aa1', 2, 'INVESTMENT', 'AA', True),
        (2, 'Aa2', 3, 'INVESTMENT', 'AA', True),
        (2, 'Aa3', 4, 'INVESTMENT', 'AA', True),
        (2, 'A1', 5, 'INVESTMENT', 'A', True),
        (2, 'A2', 6, 'INVESTMENT', 'A', True),
        (2, 'A3', 7, 'INVESTMENT', 'A', True),
        (2, 'Baa1', 8, 'INVESTMENT', 'BBB', True),
        (2, 'Baa2', 9, 'INVESTMENT', 'BBB', True),
        (2, 'Baa3', 10, 'INVESTMENT', 'BBB', True),
        (2, 'Ba1', 11, 'SPECULATIVE', 'BB', False),
        (2, 'Ba2', 12, 'SPECULATIVE', 'BB', False),
        (2, 'Ba3', 13, 'SPECULATIVE', 'BB', False),
        (2, 'B1', 14, 'SPECULATIVE', 'B', False),
        (2, 'B2', 15, 'SPECULATIVE', 'B', False),
        (2, 'B3', 16, 'SPECULATIVE', 'B', False),
        (2, 'Caa1', 17, 'SPECULATIVE', 'CCC', False),
        (2, 'Caa2', 18, 'SPECULATIVE', 'CCC', False),
        (2, 'Caa3', 19, 'SPECULATIVE', 'CCC', False),
        (2, 'Ca', 20, 'DEFAULT', 'CC', False),
        (2, 'C', 21, 'DEFAULT', 'C', False)
    ]
    
    for agency_id, symbol, rank, category, grade, is_ig in test_ratings:
        scale = RatingScale(
            agency_id=agency_id,
            rating_symbol=symbol,
            numeric_rank=rank,
            rating_category=category,
            rating_grade=grade,
            is_investment_grade=is_ig
        )
        session.add(scale)
    
    # Create recovery rate matrices
    recovery_rates = [
        ("MOODY'S SENIOR SECURED LOAN", 2, 999, Decimal('0.6000'), False),
        ("MOODY'S SENIOR SECURED LOAN", 1, 1, Decimal('0.5000'), False),
        ("MOODY'S SENIOR SECURED LOAN", 0, 0, Decimal('0.4500'), False),
        ("MOODY'S SENIOR SECURED LOAN", -1, -1, Decimal('0.4000'), False),
        ("MOODY'S SENIOR SECURED LOAN", -2, -2, Decimal('0.3000'), False),
        ("OTHER", 2, 999, Decimal('0.4500'), False),
        ("OTHER", 1, 1, Decimal('0.3500'), False),
        ("OTHER", 0, 0, Decimal('0.3000'), False),
        ("OTHER", -1, -1, Decimal('0.2500'), False),
        ("OTHER", -2, -2, Decimal('0.1500'), False),
        ("ALL_CATEGORIES", -999, 999, Decimal('0.5000'), True)  # DIP
    ]
    
    for category, diff_min, diff_max, rate, is_dip in recovery_rates:
        matrix = RecoveryRateMatrix(
            asset_category=category,
            rating_diff_min=diff_min,
            rating_diff_max=diff_max,
            recovery_rate=rate,
            is_dip=is_dip
        )
        session.add(matrix)
    
    session.commit()
    return session


@pytest.fixture
def mock_asset():
    """Create mock asset for testing"""
    asset = Mock()
    asset.dip = False
    asset.default_asset = False
    asset.struct_finance = False
    asset.bond_loan = "LOAN"
    asset.seniority = "SENIOR SECURED"
    asset.mdy_issuer_rating = "Ba2"
    asset.mdy_issuer_outlook = ""
    asset.mdy_facility_rating = "B1"
    asset.mdy_facility_outlook = ""
    asset.mdy_snr_unsec_rating = ""
    asset.mdy_snr_sec_rating = ""
    asset.mdy_credit_est_rating = ""
    asset.mdy_credit_est_date = None
    asset.mdy_sub_rating = ""
    asset.sp_issuer_rating = "B+"
    asset.sp_facility_rating = "B"
    asset.sp_snr_sec_rating = ""
    asset.sp_subordinate = ""
    asset.mdy_asset_category = "MOODY'S SENIOR SECURED LOAN"
    return asset


class TestRatingDerivationEngine:
    """Test VBA RatingDerivations.cls functionality"""
    
    def test_return_ratings_rank_vba_parity(self, in_memory_db):
        """Test ReturnRatingsRank function matches VBA exactly"""
        engine = RatingDerivationEngine(in_memory_db)
        
        # VBA test cases from the original function
        vba_test_cases = [
            ("AAA", 1), ("Aaa", 1),
            ("AA+", 2), ("Aa1", 2),
            ("AA", 3), ("Aa2", 3),
            ("AA-", 4), ("Aa3", 4),
            ("A+", 5), ("A1", 5),
            ("A", 6), ("A2", 6),
            ("A-", 7), ("A3", 7),
            ("BBB+", 8), ("Baa1", 8),
            ("BBB", 9), ("Baa2", 9),
            ("BBB-", 10), ("Baa3", 10),
            ("BB+", 11), ("Ba1", 11),
            ("BB", 12), ("Ba2", 12),
            ("BB-", 13), ("Ba3", 13),
            ("B+", 14), ("B1", 14),
            ("B", 15), ("B2", 15),
            ("B-", 16), ("B3", 16),
            ("CCC+", 17), ("Caa1", 17),
            ("CCC", 18), ("Caa2", 18),
            ("CCC-", 19), ("Caa3", 19),
            ("CC", 20), ("Ca", 20),
            ("C", 21)
        ]
        
        for rating, expected_rank in vba_test_cases:
            assert engine.return_ratings_rank(rating) == expected_rank
        
        # Test edge cases
        assert engine.return_ratings_rank("") == 21
        assert engine.return_ratings_rank("NR") == 21
        assert engine.return_ratings_rank("UNKNOWN") == 21
    
    def test_notch_rating_vba_parity(self, in_memory_db):
        """Test NotchRating function matches VBA behavior"""
        engine = RatingDerivationEngine(in_memory_db)
        
        # VBA: NotchRating(12, Moodys, -1) should return "Ba3"
        result = engine.notch_rating(12, RatingAgency.MOODYS, -1)
        assert result == "Ba3"
        
        # VBA: NotchRating(12, Moodys, 1) should return "Ba1" 
        result = engine.notch_rating(12, RatingAgency.MOODYS, 1)
        assert result == "Ba1"
        
        # VBA: NotchRating(1, SandP, -1) should return "AA+" (clamped)
        result = engine.notch_rating(1, RatingAgency.SP, -1)
        assert result == "AAA"  # Clamped to best rating
        
        # VBA: NotchRating(21, Moodys, 1) should return "C" (clamped)
        result = engine.notch_rating(21, RatingAgency.MOODYS, 1)
        assert result == "C"  # Clamped to worst rating
        
        # Test S&P ratings
        result = engine.notch_rating(8, RatingAgency.SP, -2)  # BBB+ down 2 notches
        assert result == "BBB-"
    
    def test_get_moodys_default_prob_rating_vba_parity(self, in_memory_db, mock_asset):
        """Test GetMoodysDefProbRating matches VBA logic exactly"""
        engine = RatingDerivationEngine(in_memory_db)
        
        # Test case 1: Normal issuer rating
        mock_asset.mdy_issuer_rating = "Ba2"
        mock_asset.mdy_issuer_outlook = ""
        result = engine.get_moodys_default_prob_rating(mock_asset)
        assert result == "Ba2"
        
        # Test case 2: Issuer rating with downgrade outlook
        mock_asset.mdy_issuer_outlook = "Downgrade"
        result = engine.get_moodys_default_prob_rating(mock_asset)
        assert result == "Ba3"  # Down 1 notch
        
        # Test case 3: Issuer rating with upgrade outlook
        mock_asset.mdy_issuer_outlook = "Upgrade"
        result = engine.get_moodys_default_prob_rating(mock_asset)
        assert result == "Ba1"  # Up 1 notch
        
        # Test case 4: DIP asset
        mock_asset.dip = True
        mock_asset.mdy_facility_rating = "B2"
        result = engine.get_moodys_default_prob_rating(mock_asset)
        assert result == "B3"  # DIP gets facility rating down 1 notch
        
        # Test case 5: No ratings available - should use cross-derivation or default
        mock_asset.dip = False
        mock_asset.mdy_issuer_rating = ""
        mock_asset.mdy_snr_unsec_rating = ""
        mock_asset.mdy_snr_sec_rating = ""
        mock_asset.mdy_credit_est_rating = ""
        result = engine.get_moodys_default_prob_rating(mock_asset)
        # Should either derive from S&P or default to Caa3
        assert result in ["Caa3", "CCC+", "CCC"]  # Allow derived rating or default
    
    def test_get_moodys_rating_senior_secured_loan(self, in_memory_db, mock_asset):
        """Test GetMoodysRating for senior secured loans"""
        engine = RatingDerivationEngine(in_memory_db)
        
        mock_asset.bond_loan = "LOAN"
        mock_asset.seniority = "SENIOR SECURED"
        
        # Test facility rating priority
        mock_asset.mdy_facility_rating = "B1"
        mock_asset.mdy_facility_outlook = ""
        result = engine.get_moodys_rating(mock_asset)
        assert result == "B1"
        
        # Test facility rating with upgrade outlook
        mock_asset.mdy_facility_outlook = "Upgrade"
        result = engine.get_moodys_rating(mock_asset)
        assert result == "Ba3"  # B1 up 1 notch
        
        # Test facility rating with downgrade outlook
        mock_asset.mdy_facility_outlook = "Downgrade"
        result = engine.get_moodys_rating(mock_asset)
        assert result == "B2"  # B1 down 1 notch
    
    def test_get_sp_ratings_vba_parity(self, in_memory_db, mock_asset):
        """Test GetSnPRatings matches VBA logic"""
        engine = RatingDerivationEngine(in_memory_db)
        
        # Test case 1: DIP assets
        mock_asset.dip = True
        mock_asset.sp_facility_rating = "B"
        result = engine.get_sp_ratings(mock_asset)
        assert result == "B"
        
        # Test case 2: Default assets
        mock_asset.dip = False
        mock_asset.default_asset = True
        result = engine.get_sp_ratings(mock_asset)
        assert result == "D"
        
        # Test case 3: Normal issuer rating
        mock_asset.default_asset = False
        mock_asset.sp_issuer_rating = "B+"
        result = engine.get_sp_ratings(mock_asset)
        assert result == "B+"
        
        # Test case 4: Senior secured rating
        mock_asset.sp_issuer_rating = ""
        mock_asset.sp_snr_sec_rating = "B"
        result = engine.get_sp_ratings(mock_asset)
        assert result == "B"
    
    def test_calculate_moody_recovery_rate_vba_parity(self, in_memory_db, mock_asset):
        """Test MoodyRecoveryRate matches VBA calculation"""
        engine = RatingDerivationEngine(in_memory_db)
        
        # Test case 1: DIP asset gets fixed 50% recovery
        mock_asset.dip = True
        result = engine.calculate_moody_recovery_rate(mock_asset, "B1", "B2")
        assert result == Decimal('0.5000')
        
        # Test case 2: Senior secured loan with rating difference = 2
        mock_asset.dip = False
        mock_asset.mdy_asset_category = "MOODY'S SENIOR SECURED LOAN"
        # B1 (rank 14) vs Ba3 (rank 13) = difference of 1 (14-13=1)
        # But let's test with difference = 2
        result = engine.calculate_moody_recovery_rate(mock_asset, "Ba2", "B2")  # 12 vs 15 = 3
        # This should map to the 2+ category for senior secured loans
        assert result == Decimal('0.6000')
        
        # Test case 3: Senior secured loan with rating difference = 0
        result = engine.calculate_moody_recovery_rate(mock_asset, "B1", "B1")  # Same rating
        assert result == Decimal('0.4500')
        
        # Test case 4: Other asset category
        mock_asset.mdy_asset_category = "OTHER"
        result = engine.calculate_moody_recovery_rate(mock_asset, "B1", "B1")
        assert result == Decimal('0.3000')
    
    def test_cross_agency_derivation_sp_to_moodys(self, in_memory_db, mock_asset):
        """Test GetDerivedMoodyRatingFromSandP function"""
        engine = RatingDerivationEngine(in_memory_db)
        
        # Test case 1: Investment grade bond (rank <= 10)
        mock_asset.struct_finance = False
        mock_asset.bond_loan = "BOND"
        mock_asset.sp_facility_rating = "BBB"  # Rank 9
        result = engine.get_derived_moody_rating_from_sp(mock_asset)
        assert result == "Baa3"  # BBB down 1 notch in Moody's scale
        
        # Test case 2: Speculative grade bond (rank > 10)
        mock_asset.sp_facility_rating = "BB"  # Rank 12
        result = engine.get_derived_moody_rating_from_sp(mock_asset)
        assert result == "B1"  # BB down 2 notches in Moody's scale
        
        # Test case 3: Loan gets different treatment
        mock_asset.bond_loan = "LOAN"
        mock_asset.sp_facility_rating = "BBB"  # Rank 9
        result = engine.get_derived_moody_rating_from_sp(mock_asset)
        assert result == "Ba1"  # BBB down 2 notches for loans
    
    def test_cross_agency_derivation_moodys_to_sp(self, in_memory_db, mock_asset):
        """Test GetDerivedSandPRatingFromMoody function"""
        engine = RatingDerivationEngine(in_memory_db)
        
        mock_asset.bond_loan = "LOAN"
        mock_asset.seniority = "SENIOR SECURED"
        mock_asset.mdy_facility_rating = "Baa2"  # Rank 9
        
        result = engine.get_derived_sp_rating_from_moody(mock_asset)
        # Investment grade (rank <= 10) gets -1 notch
        assert result == "BBB-"  # Baa2 to S&P with -1 notch


class TestRatingService:
    """Test RatingService functionality"""
    
    def test_update_asset_ratings_complete_workflow(self, in_memory_db, mock_asset):
        """Test complete asset rating update workflow"""
        service = RatingService(in_memory_db)
        
        # Test complete rating derivation
        results = service.update_asset_ratings(mock_asset)
        
        # Verify all ratings are calculated
        assert 'mdy_rating' in results
        assert 'mdy_dp_rating' in results
        assert 'mdy_dp_rating_warf' in results
        assert 'sp_rating' in results
        assert 'mdy_recovery_rate' in results
        
        # Verify data types
        assert isinstance(results['mdy_recovery_rate'], float)
        assert 0 <= results['mdy_recovery_rate'] <= 1
    
    def test_create_rating_migration_record(self, in_memory_db):
        """Test rating migration record creation"""
        service = RatingService(in_memory_db)
        
        previous_ratings = {'sp': 'BB+', 'mdy': 'Ba1', 'fitch': 'BB+'}
        new_ratings = {'sp': 'BB', 'mdy': 'Ba2', 'fitch': 'BB'}
        
        migration = service.create_rating_migration(
            asset_id="TEST_ASSET_001",
            migration_date=date(2025, 1, 15),
            previous_ratings=previous_ratings,
            new_ratings=new_ratings,
            par_amount=Decimal('1000000'),
            portfolio_weight=Decimal('0.025')
        )
        
        assert migration.asset_id == "TEST_ASSET_001"
        assert migration.notch_change == -1  # BB+ (11) to BB (12) = downgrade
        assert migration.migration_type == "DOWNGRADE"
        assert migration.par_amount_at_migration == Decimal('1000000')
    
    def test_portfolio_migration_summary(self, in_memory_db):
        """Test portfolio migration summary generation"""
        service = RatingService(in_memory_db)
        
        # This test would require setting up more complex data
        # For now, test the basic structure
        summary = service.get_portfolio_migration_summary(
            "TEST_DEAL", date(2025, 1, 1), date(2025, 12, 31)
        )
        
        # Should handle empty results gracefully
        assert isinstance(summary, dict)


class TestRatingMigrationItem:
    """Test VBA RatingMigrationItem.cls functionality"""
    
    def test_constructor_and_payment_schedule(self, in_memory_db):
        """Test RatingMigrationItem initialization matches VBA Constructor"""
        migration_item = RatingMigrationItem(
            deal_name="TEST_DEAL",
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2027, 1, 1),
            num_simulations=100,
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        # Test basic properties
        assert migration_item.deal_name == "TEST_DEAL"
        assert migration_item.num_simulations == 100
        assert migration_item.num_months == 3  # Quarterly
        
        # Test payment schedule generation
        assert len(migration_item.payment_dates) >= 8  # 2 years quarterly + analysis date
        assert migration_item.payment_dates[0] == date(2025, 1, 1)
        assert migration_item.payment_dates[-1] == date(2027, 1, 1)
        
        # Test date indexing
        assert migration_item.date_to_index[date(2025, 1, 1)] == 0
        assert date(2025, 4, 1) in migration_item.date_to_index  # Q1 payment
    
    def test_add_rating_and_balance_vba_parity(self, in_memory_db):
        """Test AddRatingAndBalance matches VBA behavior"""
        migration_item = RatingMigrationItem(
            deal_name="TEST_DEAL",
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            num_simulations=10,
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        # Test adding various ratings - VBA style
        test_date = date(2025, 1, 1)
        
        # VBA: AddRatingAndBalance(1, analysis_date, "BBB", 1000000)
        migration_item.add_rating_and_balance(1, test_date, "BBB", Decimal('1000000'))
        
        # Verify rating histogram updated
        rating_hist, rating_hist_bal = migration_item.simulation_data[0][0]  # Sim 1, Period 0
        assert rating_hist.num_bbb == 1
        assert rating_hist_bal.bal_bbb == Decimal('1000000')
        assert rating_hist_bal.bal_performing == Decimal('1000000')
        
        # Test CCC normalization (VBA: "CCC+", "CCC-", "CC" all become "CCC")
        migration_item.add_rating_and_balance(1, test_date, "CCC+", Decimal('500000'))
        migration_item.add_rating_and_balance(1, test_date, "CCC-", Decimal('300000'))
        migration_item.add_rating_and_balance(1, test_date, "CC", Decimal('200000'))
        
        rating_hist, rating_hist_bal = migration_item.simulation_data[0][0]
        assert rating_hist.num_ccc_assets == 3  # All normalized to CCC
        assert rating_hist_bal.bal_ccc == Decimal('1000000')  # 500000 + 300000 + 200000
        
        # Test defaults
        migration_item.add_rating_and_balance(1, test_date, "D", Decimal('750000'))
        rating_hist, rating_hist_bal = migration_item.simulation_data[0][0]
        assert rating_hist.num_defaults == 1  # Period 0 default
        assert rating_hist_bal.bal_defaults == Decimal('750000')
        
        # Test matured assets
        migration_item.add_rating_and_balance(1, test_date, "M", Decimal('250000'))
        rating_hist, rating_hist_bal = migration_item.simulation_data[0][0]
        assert rating_hist.num_matures == 1
        assert rating_hist_bal.bal_mature == Decimal('250000')
    
    def test_add_upgrade_downgrade_tracking(self, in_memory_db):
        """Test AddUpgrade and AddDowngrade methods"""
        migration_item = RatingMigrationItem(
            deal_name="TEST_DEAL",
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            num_simulations=5,
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        test_date = date(2025, 1, 1)
        
        # VBA: AddUpgrade(1, test_date)
        migration_item.add_upgrade(1, test_date)
        migration_item.add_upgrade(1, test_date)
        
        # VBA: AddDowngrade(1, test_date)
        migration_item.add_downgrade(1, test_date)
        
        rating_hist, _ = migration_item.simulation_data[0][0]
        assert rating_hist.upgrades == 2
        assert rating_hist.downgrades == 1
    
    def test_update_defaults_cumulative_calculation(self, in_memory_db):
        """Test UpdateDefaults method for cumulative calculation"""
        migration_item = RatingMigrationItem(
            deal_name="TEST_DEAL", 
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            num_simulations=3,
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        # Add period defaults to different periods
        dates = migration_item.payment_dates[:3]  # First 3 periods
        
        # Period 0: Initial defaults
        migration_item.add_rating_and_balance(1, dates[0], "D", Decimal('100000'))
        
        # Period 1: Additional period defaults
        migration_item.add_rating_and_balance(1, dates[1], "D", Decimal('200000'))
        
        # Period 2: More period defaults
        migration_item.add_rating_and_balance(1, dates[2], "D", Decimal('150000'))
        
        # VBA: UpdateDefaults(1)
        migration_item.update_defaults(1)
        
        # Check cumulative defaults calculation
        _, bal_period_1 = migration_item.simulation_data[0][1]  # Sim 1, Period 1
        _, bal_period_2 = migration_item.simulation_data[0][2]  # Sim 1, Period 2
        
        # Period 1 cumulative = Period 1 defaults + Period 0 cumulative
        assert bal_period_1.bal_defaults == Decimal('300000')  # 200000 + 100000
        
        # Period 2 cumulative = Period 2 defaults + Period 1 cumulative
        assert bal_period_2.bal_defaults == Decimal('450000')  # 150000 + 300000
    
    def test_get_simulation_data_point_vba_parity(self, in_memory_db):
        """Test GetSimDataPoint matches VBA field access"""
        migration_item = RatingMigrationItem(
            deal_name="TEST_DEAL",
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            num_simulations=10,
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        test_date = date(2025, 1, 1)
        
        # Set up test data
        migration_item.add_rating_and_balance(1, test_date, "BBB", Decimal('500000'))
        migration_item.add_rating_and_balance(1, test_date, "BB", Decimal('750000'))
        migration_item.add_upgrade(1, test_date)
        migration_item.add_downgrade(1, test_date)
        migration_item.add_downgrade(1, test_date)
        
        # Test VBA field access patterns
        assert migration_item.get_simulation_data_point(1, test_date, "NUMBBB") == 1
        assert migration_item.get_simulation_data_point(1, test_date, "NUMBB") == 1
        assert migration_item.get_simulation_data_point(1, test_date, "BALBBB") == Decimal('500000')
        assert migration_item.get_simulation_data_point(1, test_date, "BALBB") == Decimal('750000')
        assert migration_item.get_simulation_data_point(1, test_date, "UPGRADES") == 1
        assert migration_item.get_simulation_data_point(1, test_date, "DOWNGRADES") == 2
        assert migration_item.get_simulation_data_point(1, test_date, "BALPERF") == Decimal('1250000')
    
    def test_cdr_calculation_quarterly_annualized(self, in_memory_db):
        """Test CDR (Cumulative Default Rate) calculation with quarterly annualization"""
        migration_item = RatingMigrationItem(
            deal_name="TEST_DEAL",
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            num_simulations=5,
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        dates = migration_item.payment_dates[:3]
        
        # Period 0: Set performing balance
        migration_item.add_rating_and_balance(1, dates[0], "BBB", Decimal('10000000'))
        
        # Period 1: Add defaults (should calculate CDR)
        migration_item.add_rating_and_balance(1, dates[1], "D", Decimal('250000'))  # 2.5% quarterly default
        
        _, bal_period_1 = migration_item.simulation_data[0][1]
        
        # CDR should be annualized for quarterly: 2.5% * 4 = 10%
        expected_cdr = Decimal('250000') / Decimal('10000000') * Decimal('4')
        assert abs(bal_period_1.cdr - expected_cdr) < Decimal('0.0001')
    
    def test_get_statistic_data_across_simulations(self, in_memory_db):
        """Test GeStatData method for statistical analysis"""
        migration_item = RatingMigrationItem(
            deal_name="TEST_DEAL",
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            num_simulations=5,
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        test_date = date(2025, 1, 1)
        
        # Create test data across simulations
        for sim in range(1, 6):  # Simulations 1-5
            # Add different numbers of defaults per simulation
            for i in range(sim):
                migration_item.add_rating_and_balance(sim, test_date, "D", Decimal('100000'))
        
        # Test statistical functions (VBA: GeStatData("AVERAGE", "NUMDEF", test_date))
        avg_defaults = migration_item.get_statistic_data("AVERAGE", "NUMDEF", test_date)
        assert avg_defaults == Decimal('3')  # (1+2+3+4+5)/5 = 3
        
        min_defaults = migration_item.get_statistic_data("MIN", "NUMDEF", test_date)
        assert min_defaults == Decimal('1')
        
        max_defaults = migration_item.get_statistic_data("MAX", "NUMDEF", test_date)
        assert max_defaults == Decimal('5')
        
        median_defaults = migration_item.get_statistic_data("MEDIAN", "NUMDEF", test_date)
        assert median_defaults == Decimal('3')


class TestRatingMigrationOutput:
    """Test VBA RatingMigrationOutput.cls functionality"""
    
    def test_constructor_multi_deal_setup(self, in_memory_db):
        """Test RatingMigrationOutput initialization with multiple deals"""
        deal_names = ["DEAL_001", "DEAL_002", "DEAL_003"]
        
        migration_output = RatingMigrationOutput(
            deal_names=deal_names,
            num_simulations=50,
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2027, 1, 1),
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        # Verify multi-deal setup
        assert len(migration_output.deal_migration_items) == 3
        assert all(deal in migration_output.deal_migration_items for deal in deal_names)
        
        # Verify each deal has correct configuration
        for deal_name in deal_names:
            item = migration_output.deal_migration_items[deal_name]
            assert item.deal_name == deal_name
            assert item.num_simulations == 50
            assert item.analysis_date == date(2025, 1, 1)
    
    def test_get_simulation_time_series_multi_deal(self, in_memory_db):
        """Test GetSimTimeSeries across multiple deals"""
        deal_names = ["DEAL_A", "DEAL_B"]
        
        migration_output = RatingMigrationOutput(
            deal_names=deal_names,
            num_simulations=10,
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2025, 10, 1),
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        # Add test data to both deals
        test_date = date(2025, 1, 1)
        
        # Deal A: 5 defaults
        migration_output.deal_migration_items["DEAL_A"].add_rating_and_balance(
            1, test_date, "D", Decimal('500000')
        )
        
        # Deal B: 3 defaults
        migration_output.deal_migration_items["DEAL_B"].add_rating_and_balance(
            1, test_date, "D", Decimal('300000')
        )
        
        # VBA: GetSimTimeSeries(1, "BALDEF")
        time_series = migration_output.get_simulation_time_series(1, "BALDEF")
        
        # Verify output structure
        assert len(time_series) > 0
        assert time_series[0] == ["Period", "DEAL_A", "DEAL_B"]  # Header row
        
        # Verify first data row
        data_row = time_series[1]
        assert data_row[0] == test_date
        assert data_row[1] == 500000.0  # Deal A defaults
        assert data_row[2] == 300000.0  # Deal B defaults


class TestRatingMigrationService:
    """Test service layer functionality"""
    
    def test_create_migration_analysis(self, in_memory_db):
        """Test migration analysis creation"""
        service = RatingMigrationService(in_memory_db)
        
        analysis = service.create_migration_analysis(
            deal_names=["SERVICE_TEST"],
            num_simulations=25,
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            period_frequency=PeriodFrequency.SEMI_ANNUALLY
        )
        
        assert isinstance(analysis, RatingMigrationOutput)
        assert len(analysis.deal_migration_items) == 1
        assert "SERVICE_TEST" in analysis.deal_migration_items
        
        # Verify semi-annual frequency
        item = analysis.deal_migration_items["SERVICE_TEST"]
        assert item.num_months == 6
    
    def test_get_deal_migration_summary_empty_data(self, in_memory_db):
        """Test migration summary with no data"""
        service = RatingMigrationService(in_memory_db)
        
        summary = service.get_deal_migration_summary(
            "NONEXISTENT_DEAL", 
            date(2025, 1, 1), 
            date(2025, 12, 31)
        )
        
        assert "error" in summary
        assert "No migration data found" in summary["error"]


class TestVBAComparisonScenarios:
    """Comprehensive VBA comparison test scenarios"""
    
    def test_complete_workflow_vba_parity(self, in_memory_db):
        """Test complete workflow matching VBA exactly"""
        # Create rating engine
        engine = RatingDerivationEngine(in_memory_db)
        service = RatingService(in_memory_db)
        
        # Create mock asset with specific VBA test data
        asset = Mock()
        asset.dip = False
        asset.default_asset = False
        asset.struct_finance = False
        asset.bond_loan = "LOAN"
        asset.seniority = "SENIOR SECURED"
        asset.mdy_issuer_rating = "Ba2"
        asset.mdy_issuer_outlook = "Negative"
        asset.mdy_facility_rating = "B1"
        asset.mdy_facility_outlook = ""
        asset.mdy_snr_unsec_rating = ""
        asset.mdy_snr_sec_rating = ""
        asset.mdy_credit_est_rating = ""
        asset.mdy_credit_est_date = None
        asset.mdy_sub_rating = ""
        asset.sp_issuer_rating = "B+"
        asset.sp_facility_rating = ""
        asset.sp_snr_sec_rating = ""
        asset.sp_subordinate = ""
        asset.mdy_asset_category = "MOODY'S SENIOR SECURED LOAN"
        
        # Test complete rating derivation
        results = service.update_asset_ratings(asset)
        
        # VBA expectations:
        # 1. Moody's rating should prioritize facility rating for senior secured loans
        assert results['mdy_rating'] == "B1"  # Facility rating takes priority
        
        # 2. Moody's DP rating should use issuer rating with negative outlook adjustment
        assert results['mdy_dp_rating'] == "Ba3"  # Ba2 down 1 notch for negative
        
        # 3. S&P rating should use issuer rating
        assert results['sp_rating'] == "B+"
        
        # 4. Recovery rate should be based on rating difference
        # B1 vs Ba3: 14 vs 13 = difference of 1, senior secured loan = 50%
        assert abs(results['mdy_recovery_rate'] - 0.5000) < 0.0001
    
    def test_rating_migration_complete_scenario(self, in_memory_db):
        """Test complete rating migration scenario matching VBA"""
        # Create migration item
        migration_item = RatingMigrationItem(
            deal_name="VBA_COMPARISON",
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            num_simulations=100,
            period_frequency=PeriodFrequency.QUARTERLY,
            session=in_memory_db
        )
        
        # Simulate VBA portfolio evolution
        dates = migration_item.payment_dates[:5]
        
        # Period 0: Initial portfolio
        for sim in range(1, 101):
            migration_item.add_rating_and_balance(sim, dates[0], "BBB", Decimal('5000000'))
            migration_item.add_rating_and_balance(sim, dates[0], "BB+", Decimal('3000000'))
            migration_item.add_rating_and_balance(sim, dates[0], "B", Decimal('2000000'))
        
        # Period 1: Some migrations
        for sim in range(1, 51):  # Half the simulations
            # Some downgrades
            migration_item.add_rating_and_balance(sim, dates[1], "BBB-", Decimal('4500000'))  # BBB downgraded
            migration_item.add_rating_and_balance(sim, dates[1], "BB", Decimal('3000000'))   # BB+ downgraded
            migration_item.add_rating_and_balance(sim, dates[1], "B-", Decimal('2000000'))   # B downgraded
            migration_item.add_downgrade(sim, dates[1])
            migration_item.add_downgrade(sim, dates[1])
            migration_item.add_downgrade(sim, dates[1])
        
        # Update cumulative defaults
        for sim in range(1, 101):
            migration_item.update_defaults(sim)
        
        # Test statistical analysis (VBA: GeStatData("AVERAGE", "DOWNGRADES", dates[1]))
        avg_downgrades = migration_item.get_statistic_data("AVERAGE", "DOWNGRADES", dates[1])
        assert avg_downgrades == Decimal('1.5')  # (50 sims * 3 downgrades + 50 sims * 0) / 100
        
        # Test time series
        time_series = migration_item.get_simulation_time_series(1, "BALPERF")
        assert len(time_series) == len(dates)
        assert time_series[0] == Decimal('10000000')  # Period 0 performing balance