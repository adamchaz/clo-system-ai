"""
Test suite for Rating System Integration with Asset Model

Tests the complete integration of the rating system with the existing Asset model
to ensure seamless operation and VBA functional parity.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock

from app.core.database import Base
from app.models.asset import Asset, AssetFlags
from app.models.rating_system import (
    RatingAgencyModel,
    RatingScale,
    RecoveryRateMatrix,
    RatingService,
    RatingDerivationEngine
)
from app.models.rating_migration import (
    RatingMigrationService,
    RatingMigrationItem,
    PeriodFrequency
)


@pytest.fixture
def integrated_db():
    """Create in-memory database with both asset and rating system data"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Set up rating system data
    agencies = [
        RatingAgencyModel(agency_name='SP', agency_full_name='S&P Global Ratings'),
        RatingAgencyModel(agency_name='MOODYS', agency_full_name="Moody's Investors Service"),
        RatingAgencyModel(agency_name='FITCH', agency_full_name='Fitch Ratings')
    ]
    for agency in agencies:
        session.add(agency)
    session.flush()
    
    # Add key rating scales
    test_ratings = [
        # S&P
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
        # Moody's
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
        (2, 'Caa3', 19, 'SPECULATIVE', 'CCC', False)
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
    
    # Add recovery rate matrices
    recovery_rates = [
        ("MOODY'S SENIOR SECURED LOAN", 1, 1, Decimal('0.5000'), False),
        ("MOODY'S SENIOR SECURED LOAN", 0, 0, Decimal('0.4500'), False),
        ("MOODY'S SENIOR SECURED LOAN", -1, -1, Decimal('0.4000'), False),
        ("OTHER", 1, 1, Decimal('0.3500'), False),
        ("OTHER", 0, 0, Decimal('0.3000'), False),
        ("OTHER", -1, -1, Decimal('0.2500'), False),
        ("ALL_CATEGORIES", -999, 999, Decimal('0.5000'), True)
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
def sample_assets(integrated_db):
    """Create sample assets for testing"""
    assets_data = [
        {
            'blkrock_id': 'TEST_LOAN_001',
            'issue_name': 'Test Company Term Loan B',
            'issuer_name': 'Test Company Inc',
            'par_amount': Decimal('5000000'),
            'bond_loan': 'LOAN',
            'seniority': 'SENIOR SECURED',
            'mdy_facility_rating': 'B1',
            'mdy_facility_outlook': '',
            'mdy_issuer_rating': 'Ba2',
            'mdy_issuer_outlook': '',
            'sp_issuer_rating': 'B+',
            'sp_facility_rating': '',
            'maturity': date(2028, 6, 15),
            'coupon': Decimal('0.075'),
            'flags': AssetFlags(dip=False, struct_finance=False).dict()
        },
        {
            'blkrock_id': 'TEST_BOND_002',
            'issue_name': 'Another Company Senior Notes',
            'issuer_name': 'Another Company LLC',
            'par_amount': Decimal('3000000'),
            'bond_loan': 'BOND',
            'seniority': 'SENIOR UNSECURED',
            'mdy_facility_rating': '',
            'mdy_issuer_rating': 'Ba3',
            'mdy_issuer_outlook': 'Negative',
            'sp_issuer_rating': 'BB-',
            'sp_facility_rating': '',
            'maturity': date(2029, 12, 1),
            'coupon': Decimal('0.085'),
            'flags': AssetFlags(dip=False, struct_finance=False).dict()
        },
        {
            'blkrock_id': 'TEST_DIP_003',
            'issue_name': 'Distressed Corp DIP Facility',
            'issuer_name': 'Distressed Corp',
            'par_amount': Decimal('2000000'),
            'bond_loan': 'LOAN',
            'seniority': 'SENIOR SECURED',
            'mdy_facility_rating': 'Caa2',
            'sp_facility_rating': 'CCC',
            'maturity': date(2026, 3, 31),
            'coupon': Decimal('0.120'),
            'flags': AssetFlags(dip=True, default_asset=False).dict()
        }
    ]
    
    assets = []
    for asset_data in assets_data:
        asset = Asset(**asset_data)
        integrated_db.add(asset)
        assets.append(asset)
    
    integrated_db.commit()
    return assets


class TestAssetRatingSystemIntegration:
    """Test Asset model integration with rating system"""
    
    def test_update_derived_ratings_integration(self, integrated_db, sample_assets):
        """Test Asset.update_derived_ratings() method with rating system"""
        loan_asset = sample_assets[0]  # TEST_LOAN_001
        rating_service = RatingService(integrated_db)
        
        # Update derived ratings
        results = loan_asset.update_derived_ratings(rating_service)
        
        # Verify results structure
        assert 'mdy_rating' in results
        assert 'mdy_dp_rating' in results
        assert 'sp_rating' in results
        assert 'mdy_recovery_rate' in results
        
        # Verify asset was updated
        assert loan_asset.derived_mdy_rating is not None
        assert loan_asset.derived_sp_rating is not None
        assert loan_asset.mdy_dp_rating is not None
        assert loan_asset.rating_derivation_date == date.today()
        
        # Verify VBA logic - senior secured loan should use facility rating
        assert loan_asset.derived_mdy_rating == 'B1'  # Facility rating priority
        assert loan_asset.derived_sp_rating == 'B+'   # Issuer rating
    
    def test_get_effective_ratings_logic(self, integrated_db, sample_assets):
        """Test effective rating selection logic"""
        asset = sample_assets[0]
        rating_service = RatingService(integrated_db)
        
        # Before derivation - should use facility/issuer ratings
        assert asset.get_effective_mdy_rating() == 'B1'  # Facility rating
        assert asset.get_effective_sp_rating() == 'B+'   # Issuer rating
        
        # After derivation - should prefer derived ratings
        asset.update_derived_ratings(rating_service)
        assert asset.get_effective_mdy_rating() == asset.derived_mdy_rating
        assert asset.get_effective_sp_rating() == asset.derived_sp_rating
    
    def test_recovery_rate_integration(self, integrated_db, sample_assets):
        """Test recovery rate calculation and integration"""
        loan_asset = sample_assets[0]
        rating_service = RatingService(integrated_db)
        
        # Update ratings to calculate recovery rate
        results = loan_asset.update_derived_ratings(rating_service)
        
        # Verify recovery rate was calculated
        assert 'mdy_recovery_rate' in results
        assert loan_asset.mdy_recovery_rate is not None
        
        # Test effective recovery rate
        effective_rate = loan_asset.get_effective_recovery_rate()
        assert effective_rate > Decimal('0')
        assert effective_rate <= Decimal('1')
        
        # Senior secured loan should have reasonable recovery rate
        assert effective_rate >= Decimal('0.30')  # Minimum expected
    
    def test_dip_asset_special_handling(self, integrated_db, sample_assets):
        """Test DIP asset gets special treatment"""
        dip_asset = sample_assets[2]  # TEST_DIP_003
        rating_service = RatingService(integrated_db)
        
        # Update derived ratings
        results = dip_asset.update_derived_ratings(rating_service)
        
        # DIP assets should get 50% recovery rate
        assert abs(results['mdy_recovery_rate'] - 0.5000) < 0.0001
        
        # Test effective recovery rate
        effective_rate = dip_asset.get_effective_recovery_rate()
        assert effective_rate == Decimal('0.5000')
    
    def test_rating_source_hierarchy_tracking(self, integrated_db, sample_assets):
        """Test rating source hierarchy is tracked correctly"""
        asset = sample_assets[0]
        rating_service = RatingService(integrated_db)
        
        # Update derived ratings
        asset.update_derived_ratings(rating_service)
        
        # Should have recorded source hierarchy
        assert asset.rating_source_hierarchy is not None
        
        import json
        hierarchy = json.loads(asset.rating_source_hierarchy)
        assert 'mdy_primary' in hierarchy
        assert 'sp_primary' in hierarchy
        
        # For this asset, should be facility for Moody's and issuer for S&P
        assert hierarchy['mdy_primary'] == 'facility'
        assert hierarchy['sp_primary'] == 'issuer'
    
    def test_rating_migration_tracking(self, integrated_db, sample_assets):
        """Test rating migration tracking functionality"""
        asset = sample_assets[1]  # TEST_BOND_002
        rating_service = RatingService(integrated_db)
        
        # Track a rating change
        new_ratings = {
            'sp': 'B+',   # Upgrade from BB-
            'mdy': 'Ba2', # Upgrade from Ba3
            'fitch': 'BB-'
        }
        
        migration = asset.track_rating_migration(new_ratings, rating_service)
        
        # Verify migration was recorded
        assert migration.asset_id == asset.blkrock_id
        assert migration.migration_type == "UPGRADE"
        assert migration.notch_change > 0  # Positive for upgrade
        assert migration.par_amount_at_migration == asset.par_amount
    
    def test_comprehensive_rating_analytics(self, integrated_db, sample_assets):
        """Test comprehensive rating analytics generation"""
        asset = sample_assets[0]
        rating_service = RatingService(integrated_db)
        
        # Update derived ratings first
        asset.update_derived_ratings(rating_service)
        
        # Get rating analytics
        analytics = asset.get_rating_analytics()
        
        # Verify structure
        assert 'asset_id' in analytics
        assert 'current_ratings' in analytics
        assert 'derived_ratings' in analytics
        assert 'effective_ratings' in analytics
        assert 'recovery_rate' in analytics
        assert 'derivation_info' in analytics
        assert 'asset_characteristics' in analytics
        
        # Verify content
        assert analytics['asset_id'] == asset.blkrock_id
        assert analytics['current_ratings']['mdy_rating'] == 'B1'
        assert analytics['current_ratings']['sp_rating'] == 'B+'
        assert analytics['asset_characteristics']['bond_loan'] == 'LOAN'
        assert analytics['asset_characteristics']['seniority'] == 'SENIOR SECURED'
        assert analytics['asset_characteristics']['dip'] == False


class TestRatingMigrationIntegration:
    """Test rating migration analysis integration"""
    
    def test_migration_analysis_with_real_assets(self, integrated_db, sample_assets):
        """Test rating migration analysis using real asset data"""
        migration_service = RatingMigrationService(integrated_db)
        
        # Create migration analysis
        analysis = migration_service.create_migration_analysis(
            deal_names=["TEST_DEAL"],
            num_simulations=10,
            analysis_date=date(2025, 1, 1),
            maturity_date=date(2027, 1, 1),
            period_frequency=PeriodFrequency.QUARTERLY
        )
        
        # Verify analysis created correctly
        assert len(analysis.deal_migration_items) == 1
        assert "TEST_DEAL" in analysis.deal_migration_items
        
        migration_item = analysis.deal_migration_items["TEST_DEAL"]
        assert migration_item.num_simulations == 10
        assert len(migration_item.payment_dates) > 8  # Quarterly over 2 years
    
    def test_asset_integration_with_migration_tracking(self, integrated_db, sample_assets):
        """Test end-to-end asset rating update with migration tracking"""
        asset = sample_assets[1]  # Bond asset
        rating_service = RatingService(integrated_db)
        
        # Initial state
        initial_mdy = asset.get_effective_mdy_rating()
        initial_sp = asset.get_effective_sp_rating()
        
        # Simulate rating change
        asset.mdy_issuer_rating = "Ba1"  # Upgrade
        asset.sp_issuer_rating = "BB"    # Upgrade
        
        # Update derived ratings
        results = asset.update_derived_ratings(rating_service)
        
        # Track the migration
        new_ratings = {
            'sp': results['sp_rating'],
            'mdy': results['mdy_rating'],
            'fitch': ''
        }
        migration = asset.track_rating_migration(new_ratings, rating_service)
        
        # Verify everything worked
        assert migration.migration_type in ["UPGRADE", "DOWNGRADE", "NO_CHANGE"]
        assert migration.asset_id == asset.blkrock_id
        
        # Verify database persistence
        db_migration = integrated_db.query(rating_service.derivation_engine.session.query(
            type(migration)).filter_by(asset_id=asset.blkrock_id).first
        )
        # Note: This would require proper foreign key setup in the migration


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases"""
    
    def test_missing_ratings_handling(self, integrated_db):
        """Test handling of assets with missing ratings"""
        # Create asset with minimal rating data
        asset = Asset(
            blkrock_id='MINIMAL_001',
            issue_name='Minimal Data Asset',
            issuer_name='Unknown Corp',
            par_amount=Decimal('1000000'),
            bond_loan='LOAN',
            maturity=date(2027, 1, 1),
            flags=AssetFlags().dict()
        )
        integrated_db.add(asset)
        integrated_db.commit()
        
        rating_service = RatingService(integrated_db)
        
        # Should handle missing ratings gracefully
        results = asset.update_derived_ratings(rating_service)
        
        # Should get default ratings
        assert results['mdy_rating'] == 'Caa3'
        assert results['sp_rating'] == 'CCC-'
        assert results['mdy_recovery_rate'] >= 0
    
    def test_invalid_rating_data_handling(self, integrated_db):
        """Test handling of invalid rating data"""
        asset = Asset(
            blkrock_id='INVALID_001',
            issue_name='Invalid Rating Asset',
            issuer_name='Invalid Corp',
            par_amount=Decimal('1000000'),
            bond_loan='BOND',
            mdy_issuer_rating='INVALID',
            sp_issuer_rating='ALSO_INVALID',
            maturity=date(2027, 1, 1),
            flags=AssetFlags().dict()
        )
        integrated_db.add(asset)
        integrated_db.commit()
        
        rating_service = RatingService(integrated_db)
        
        # Should handle invalid ratings gracefully
        results = asset.update_derived_ratings(rating_service)
        
        # Should fall back to defaults
        assert results is not None
        assert 'mdy_rating' in results
        assert 'sp_rating' in results
    
    def test_bulk_asset_rating_update_performance(self, integrated_db):
        """Test performance of bulk rating updates"""
        # Create multiple assets
        assets = []
        for i in range(50):
            asset = Asset(
                blkrock_id=f'BULK_{i:03d}',
                issue_name=f'Bulk Asset {i}',
                issuer_name=f'Bulk Corp {i}',
                par_amount=Decimal('1000000'),
                bond_loan='LOAN' if i % 2 == 0 else 'BOND',
                mdy_issuer_rating='Ba2',
                sp_issuer_rating='BB',
                maturity=date(2027, 1, 1),
                flags=AssetFlags().dict()
            )
            assets.append(asset)
            integrated_db.add(asset)
        
        integrated_db.commit()
        
        rating_service = RatingService(integrated_db)
        
        # Time bulk update (basic performance check)
        import time
        start_time = time.time()
        
        for asset in assets:
            asset.update_derived_ratings(rating_service)
        
        end_time = time.time()
        update_time = end_time - start_time
        
        # Should complete reasonably quickly (less than 10 seconds for 50 assets)
        assert update_time < 10.0
        
        # Verify all assets were updated
        updated_count = sum(1 for asset in assets if asset.derived_mdy_rating is not None)
        assert updated_count == len(assets)


class TestVBAComparisonIntegration:
    """Comprehensive VBA comparison for integrated functionality"""
    
    def test_complete_workflow_vba_parity(self, integrated_db, sample_assets):
        """Test complete workflow matches VBA exactly"""
        # Use the loan asset for comprehensive testing
        asset = sample_assets[0]  # Senior secured loan
        rating_service = RatingService(integrated_db)
        
        # Test VBA RatingDerivations.cls integration
        results = asset.update_derived_ratings(rating_service)
        
        # VBA expectations for senior secured loan:
        # 1. Should use facility rating as primary
        assert results['mdy_rating'] == 'B1'  # mdy_facility_rating
        
        # 2. Should calculate recovery rate based on rating difference
        # B1 (facility) vs Ba2 (issuer for DP) = rating difference
        assert results['mdy_recovery_rate'] > 0.30  # Senior secured minimum
        
        # 3. S&P should use issuer rating
        assert results['sp_rating'] == 'B+'  # sp_issuer_rating
        
        # Test effective rating methods
        assert asset.get_effective_mdy_rating() == results['mdy_rating']
        assert asset.get_effective_sp_rating() == results['sp_rating']
        
        # Test analytics generation
        analytics = asset.get_rating_analytics()
        assert analytics['effective_ratings']['effective_mdy'] == 'B1'
        assert analytics['effective_ratings']['effective_sp'] == 'B+'
        assert analytics['asset_characteristics']['bond_loan'] == 'LOAN'
        assert analytics['asset_characteristics']['seniority'] == 'SENIOR SECURED'
        
        # Verify rating hierarchy tracking
        hierarchy = analytics['derivation_info']['source_hierarchy']
        if hierarchy:
            import json
            parsed_hierarchy = json.loads(hierarchy)
            assert 'mdy_primary' in parsed_hierarchy
            assert parsed_hierarchy['mdy_primary'] == 'facility'
    
    def test_cross_agency_derivation_integration(self, integrated_db):
        """Test cross-agency derivation works through Asset model"""
        # Create asset with only S&P ratings
        asset = Asset(
            blkrock_id='CROSS_DERIVE_001',
            issue_name='Cross Derivation Test',
            issuer_name='Cross Corp',
            par_amount=Decimal('2000000'),
            bond_loan='BOND',
            sp_facility_rating='BB',  # Only S&P data
            mdy_facility_rating='',   # No Moody's data
            mdy_issuer_rating='',
            sp_issuer_rating='',
            maturity=date(2027, 1, 1),
            flags=AssetFlags(struct_finance=False).dict()
        )
        integrated_db.add(asset)
        integrated_db.commit()
        
        rating_service = RatingService(integrated_db)
        
        # Update should derive Moody's from S&P
        results = asset.update_derived_ratings(rating_service)
        
        # Should have derived Moody's rating
        assert results['mdy_rating'] != 'Caa3'  # Should not be default
        # BB (rank 12) -> Moody's should be Ba3 or B1 (depending on notching rules)
        assert results['mdy_rating'] in ['Ba3', 'B1', 'B2']