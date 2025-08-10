"""
Rating System Models - VBA Rating classes Python implementation

This module implements the VBA RatingDerivations.cls, Ratings.cls, RatingMigrationItem.cls
and RatingMigrationOutput.cls functionality with database persistence.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
import logging

from ..core.database import Base


logger = logging.getLogger(__name__)


class RatingAgency(str, Enum):
    """Rating agencies enumeration - matches VBA RatingAgencies enum"""
    MOODYS = "MOODYS"
    SP = "SP" 
    FITCH = "FITCH"


class MigrationType(str, Enum):
    """Migration type enumeration"""
    UPGRADE = "UPGRADE"
    DOWNGRADE = "DOWNGRADE"
    DEFAULT = "DEFAULT"
    RECOVERY = "RECOVERY"
    NO_CHANGE = "NO_CHANGE"


class RatingAgencyModel(Base):
    """Rating agency definitions"""
    __tablename__ = 'rating_agencies'
    
    agency_id = Column(Integer, primary_key=True, autoincrement=True)
    agency_name = Column(String(20), nullable=False, unique=True)
    agency_full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    rating_scales = relationship("RatingScale", back_populates="agency")
    derivation_rules_source = relationship("RatingDerivationRule", 
                                         foreign_keys="RatingDerivationRule.source_agency_id",
                                         back_populates="source_agency")
    derivation_rules_target = relationship("RatingDerivationRule",
                                         foreign_keys="RatingDerivationRule.target_agency_id", 
                                         back_populates="target_agency")


class RatingScale(Base):
    """Standardized rating scales for all agencies"""
    __tablename__ = 'rating_scales'
    
    scale_id = Column(Integer, primary_key=True, autoincrement=True)
    agency_id = Column(Integer, ForeignKey('rating_agencies.agency_id'), nullable=False)
    rating_symbol = Column(String(10), nullable=False)
    numeric_rank = Column(Integer, nullable=False)
    rating_category = Column(String(20))  # INVESTMENT, SPECULATIVE, DEFAULT
    rating_grade = Column(String(5))      # AAA, AA, A, BBB, etc.
    is_investment_grade = Column(Boolean, default=False)
    is_watch = Column(Boolean, default=False)
    outlook = Column(String(10))          # POSITIVE, NEGATIVE, STABLE
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    agency = relationship("RatingAgencyModel", back_populates="rating_scales")


class RatingDerivationRule(Base):
    """Cross-agency rating derivation rules"""
    __tablename__ = 'rating_derivation_rules'
    
    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    source_agency_id = Column(Integer, ForeignKey('rating_agencies.agency_id'), nullable=False)
    target_agency_id = Column(Integer, ForeignKey('rating_agencies.agency_id'), nullable=False)
    source_rating = Column(String(10), nullable=False)
    target_rating = Column(String(10), nullable=False)
    adjustment_notches = Column(Integer, default=0)
    bond_loan_type = Column(String(10))       # BOND, LOAN
    seniority_level = Column(String(30))      # SENIOR SECURED, etc.
    is_structured_finance = Column(Boolean, default=False)
    rating_threshold = Column(Integer)        # Rank threshold for rule application
    effective_date = Column(Date)
    expiration_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    source_agency = relationship("RatingAgencyModel", 
                               foreign_keys=[source_agency_id],
                               back_populates="derivation_rules_source")
    target_agency = relationship("RatingAgencyModel",
                               foreign_keys=[target_agency_id], 
                               back_populates="derivation_rules_target")


class RecoveryRateMatrix(Base):
    """Recovery rate matrices by asset category and rating difference"""
    __tablename__ = 'recovery_rate_matrices'
    
    matrix_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_category = Column(String(50), nullable=False)
    rating_diff_min = Column(Integer, nullable=False)
    rating_diff_max = Column(Integer, nullable=False) 
    recovery_rate = Column(DECIMAL(6,4), nullable=False)
    confidence_interval = Column(DECIMAL(6,4))
    data_vintage = Column(Date)
    is_dip = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class RatingMigration(Base):
    """Rating migration tracking for individual assets"""
    __tablename__ = 'rating_migrations'
    
    migration_id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String(50), ForeignKey('assets.blkrock_id'), nullable=False)
    migration_date = Column(Date, nullable=False)
    previous_sp_rating = Column(String(10))
    previous_mdy_rating = Column(String(10))
    previous_fitch_rating = Column(String(10))
    new_sp_rating = Column(String(10))
    new_mdy_rating = Column(String(10))
    new_fitch_rating = Column(String(10))
    notch_change = Column(Integer, default=0)
    migration_type = Column(String(20))
    is_default_event = Column(Boolean, default=False)
    recovery_amount = Column(DECIMAL(18,2))
    portfolio_weight_at_migration = Column(DECIMAL(8,6))
    par_amount_at_migration = Column(DECIMAL(18,2))
    created_at = Column(DateTime, server_default=func.now())


class PortfolioMigrationStats(Base):
    """Portfolio-level migration statistics"""
    __tablename__ = 'portfolio_migration_stats'
    
    stat_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    calculation_date = Column(Date, nullable=False)
    period_start_date = Column(Date)
    period_end_date = Column(Date)
    simulation_number = Column(Integer, default=1)
    total_upgrades = Column(Integer, default=0)
    total_downgrades = Column(Integer, default=0)
    total_defaults = Column(Integer, default=0)
    period_defaults = Column(Integer, default=0)
    upgrade_dollar_volume = Column(DECIMAL(18,2), default=Decimal('0.00'))
    downgrade_dollar_volume = Column(DECIMAL(18,2), default=Decimal('0.00'))
    default_dollar_volume = Column(DECIMAL(18,2), default=Decimal('0.00'))
    period_default_dollar_volume = Column(DECIMAL(18,2), default=Decimal('0.00'))
    performing_balance = Column(DECIMAL(18,2), default=Decimal('0.00'))
    cumulative_default_rate = Column(DECIMAL(8,6), default=Decimal('0.000000'))
    weighted_average_rating_change = Column(DECIMAL(6,4))
    portfolio_quality_trend = Column(String(20))  # IMPROVING, DETERIORATING, STABLE
    created_at = Column(DateTime, server_default=func.now())


class RatingDistributionHistory(Base):
    """Detailed rating distribution tracking by simulation"""
    __tablename__ = 'rating_distribution_history'
    
    distribution_id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    calculation_date = Column(Date, nullable=False)
    simulation_number = Column(Integer, nullable=False)
    rating_bucket = Column(String(10), nullable=False)
    asset_count = Column(Integer, default=0)
    balance_amount = Column(DECIMAL(18,2), default=Decimal('0.00'))
    created_at = Column(DateTime, server_default=func.now())


class RatingDerivationEngine:
    """
    Python implementation of VBA RatingDerivations.cls
    Provides cross-agency rating derivation and recovery rate calculation
    """
    
    def __init__(self, session: Session):
        self.session = session
        self._rating_lookup_cache: Dict[str, Dict[str, int]] = {}
        self._agencies_cache: Dict[str, int] = {}
        self._rating_scales_cache: Dict[int, List[RatingScale]] = {}
        self._recovery_matrices_cache: List[RecoveryRateMatrix] = []
        
        # Initialize caches
        self._build_caches()
    
    def _build_caches(self):
        """Build lookup caches for performance"""
        # Cache agencies
        agencies = self.session.query(RatingAgencyModel).all()
        for agency in agencies:
            self._agencies_cache[agency.agency_name] = agency.agency_id
        
        # Cache rating scales
        scales = self.session.query(RatingScale).all()
        for scale in scales:
            if scale.agency_id not in self._rating_scales_cache:
                self._rating_scales_cache[scale.agency_id] = []
            self._rating_scales_cache[scale.agency_id].append(scale)
        
        # Build rating lookup cache
        for agency_id, scales in self._rating_scales_cache.items():
            agency_name = next(name for name, id in self._agencies_cache.items() if id == agency_id)
            self._rating_lookup_cache[agency_name] = {}
            for scale in scales:
                self._rating_lookup_cache[agency_name][scale.rating_symbol] = scale.numeric_rank
        
        # Cache recovery rate matrices
        self._recovery_matrices_cache = self.session.query(RecoveryRateMatrix).all()
    
    def return_ratings_rank(self, rating_string: str) -> int:
        """
        VBA: ReturnRatingsRank function
        Convert rating string to numeric rank (1-21)
        """
        if not rating_string or rating_string in ["NR", ""]:
            return 21  # Default to worst rating
        
        # Check all agencies for this rating
        for agency_ratings in self._rating_lookup_cache.values():
            if rating_string in agency_ratings:
                return agency_ratings[rating_string]
        
        logger.warning(f"Unknown rating: {rating_string}, defaulting to rank 21")
        return 21
    
    def notch_rating(self, rating_rank: int, agency: RatingAgency, notch_adjustment: int) -> str:
        """
        VBA: NotchRating function
        Adjust rating by specified number of notches
        """
        agency_id = self._agencies_cache.get(agency.value)
        if not agency_id or agency_id not in self._rating_scales_cache:
            return "CCC-"
        
        # Calculate new rank
        new_rank = rating_rank - notch_adjustment
        
        # Clamp to valid range
        scales = self._rating_scales_cache[agency_id]
        min_rank = min(scale.numeric_rank for scale in scales)
        max_rank = max(scale.numeric_rank for scale in scales)
        
        if new_rank < min_rank:
            new_rank = min_rank
        elif new_rank > max_rank:
            new_rank = max_rank
        
        # Find rating for this rank
        for scale in scales:
            if scale.numeric_rank == new_rank:
                return scale.rating_symbol
        
        # Fallback
        return "CCC-"
    
    def get_moodys_default_prob_rating(self, asset: Any) -> str:
        """
        VBA: GetMoodysDefProbRating method
        Calculate Moody's default probability rating based on asset characteristics
        """
        try:
            # DIP assets
            if getattr(asset, 'dip', False):
                facility_rating = getattr(asset, 'mdy_facility_rating', '')
                if facility_rating and facility_rating != "NR":
                    return self.notch_rating(
                        self.return_ratings_rank(facility_rating), 
                        RatingAgency.MOODYS, 
                        -1
                    )
            
            # Standard hierarchy for non-DIP assets
            if not getattr(asset, 'dip', False):
                # 1. Issuer rating with outlook adjustments
                issuer_rating = getattr(asset, 'mdy_issuer_rating', '')
                if issuer_rating and issuer_rating != "NR":
                    issuer_outlook = getattr(asset, 'mdy_issuer_outlook', '')
                    facility_outlook = getattr(asset, 'mdy_facility_outlook', '')
                    
                    if issuer_outlook == "Downgrade" or facility_outlook == "Downgrade":
                        return self.notch_rating(
                            self.return_ratings_rank(issuer_rating),
                            RatingAgency.MOODYS,
                            -1
                        )
                    elif issuer_outlook == "Upgrade" or facility_outlook == "Upgrade":
                        return self.notch_rating(
                            self.return_ratings_rank(issuer_rating),
                            RatingAgency.MOODYS,
                            1
                        )
                    else:
                        return issuer_rating
                
                # 2. Senior unsecured rating
                snr_unsec_rating = getattr(asset, 'mdy_snr_unsec_rating', '')
                if snr_unsec_rating and snr_unsec_rating != "NR":
                    return snr_unsec_rating
                
                # 3. Senior secured rating (notched down)
                snr_sec_rating = getattr(asset, 'mdy_snr_sec_rating', '')
                if snr_sec_rating and snr_sec_rating != "NR":
                    return self.notch_rating(
                        self.return_ratings_rank(snr_sec_rating),
                        RatingAgency.MOODYS,
                        -1
                    )
                
                # 4. Credit estimate (if recent)
                credit_est_rating = getattr(asset, 'mdy_credit_est_rating', '')
                credit_est_date = getattr(asset, 'mdy_credit_est_date', None)
                if (credit_est_rating and credit_est_rating != "NR" and 
                    credit_est_date and self._is_recent_date(credit_est_date, 15)):
                    return credit_est_rating
            
            # 5. Try cross-agency derivation from S&P
            derived_from_sp = self.get_derived_moody_rating_from_sp(asset)
            if derived_from_sp:
                return derived_from_sp
            
            # Default fallback
            return "Caa3"
            
        except Exception as e:
            logger.error(f"Error calculating Moody's DP rating: {e}")
            return "Caa3"
    
    def get_moodys_default_prob_rating_warf(self, asset: Any) -> str:
        """
        VBA: GetMoodysDefProbRatingWARF method
        WARF version includes negative outlook adjustment
        """
        try:
            # Similar to regular DP rating but with negative outlook handling
            if not getattr(asset, 'dip', False):
                issuer_rating = getattr(asset, 'mdy_issuer_rating', '')
                if issuer_rating and issuer_rating != "NR":
                    issuer_outlook = getattr(asset, 'mdy_issuer_outlook', '')
                    facility_outlook = getattr(asset, 'mdy_facility_outlook', '')
                    
                    # WARF-specific: Negative outlook gets -2 notches
                    if issuer_outlook == "Negative":
                        return self.notch_rating(
                            self.return_ratings_rank(issuer_rating),
                            RatingAgency.MOODYS,
                            -2
                        )
                    elif issuer_outlook == "Downgrade" or facility_outlook == "Downgrade":
                        return self.notch_rating(
                            self.return_ratings_rank(issuer_rating),
                            RatingAgency.MOODYS,
                            -1
                        )
                    elif issuer_outlook == "Upgrade" or facility_outlook == "Upgrade":
                        return self.notch_rating(
                            self.return_ratings_rank(issuer_rating),
                            RatingAgency.MOODYS,
                            1
                        )
                    else:
                        return issuer_rating
            
            # Fall through to regular DP rating logic
            return self.get_moodys_default_prob_rating(asset)
            
        except Exception as e:
            logger.error(f"Error calculating Moody's DP rating WARF: {e}")
            return "Caa3"
    
    def get_moodys_rating(self, asset: Any) -> str:
        """
        VBA: GetMoodysRating method
        Get final Moody's rating based on asset type and seniority
        """
        try:
            bond_loan = getattr(asset, 'bond_loan', '')
            seniority = getattr(asset, 'seniority', '')
            
            if bond_loan == "LOAN" and seniority == "SENIOR SECURED":
                return self._get_moodys_rating_senior_secured_loan(asset)
            else:
                return self._get_moodys_rating_other(asset)
                
        except Exception as e:
            logger.error(f"Error calculating Moody's rating: {e}")
            return "Caa3"
    
    def get_sp_ratings(self, asset: Any) -> str:
        """
        VBA: GetSnPRatings method
        Calculate S&P rating with cross-agency derivation
        """
        try:
            # DIP assets
            if getattr(asset, 'dip', False):
                return getattr(asset, 'sp_facility_rating', 'CCC-')
            
            # Default assets
            if getattr(asset, 'default_asset', False):
                return "D"
            
            # Standard hierarchy
            issuer_rating = getattr(asset, 'sp_issuer_rating', '')
            if issuer_rating and issuer_rating != "NR":
                return issuer_rating
            
            snr_sec_rating = getattr(asset, 'sp_snr_sec_rating', '')
            if snr_sec_rating and snr_sec_rating != "NR":
                return snr_sec_rating
            
            subordinate_rating = getattr(asset, 'sp_subordinate', '')
            if subordinate_rating and subordinate_rating != "NR":
                rank = self.return_ratings_rank(subordinate_rating)
                if rank < 11:  # Investment grade
                    return self.notch_rating(rank, RatingAgency.SP, 1)
                else:  # Speculative grade
                    return self.notch_rating(rank, RatingAgency.SP, 2)
            
            # Try derivation from Moody's
            derived_from_mdy = self.get_derived_sp_rating_from_moody(asset)
            if derived_from_mdy:
                return derived_from_mdy
            
            return "CCC-"
            
        except Exception as e:
            logger.error(f"Error calculating S&P rating: {e}")
            return "CCC-"
    
    def get_derived_moody_rating_from_sp(self, asset: Any) -> Optional[str]:
        """
        VBA: GetDerivedMoodyRatingFromSandP function
        Cross-agency rating derivation from S&P to Moody's
        """
        try:
            struct_finance = getattr(asset, 'struct_finance', False)
            bond_loan = getattr(asset, 'bond_loan', '')
            sp_facility_rating = getattr(asset, 'sp_facility_rating', '')
            sp_snr_sec_rating = getattr(asset, 'sp_snr_sec_rating', '')
            sp_subordinate = getattr(asset, 'sp_subordinate', '')
            
            if not struct_finance and sp_facility_rating and sp_facility_rating != "NR":
                rank = self.return_ratings_rank(sp_facility_rating)
                if bond_loan != "LOAN":
                    if rank <= 10:  # Investment grade
                        return self.notch_rating(rank, RatingAgency.MOODYS, -1)
                    else:
                        return self.notch_rating(rank, RatingAgency.MOODYS, -2)
                else:
                    return self.notch_rating(rank, RatingAgency.MOODYS, -2)
            else:
                if sp_snr_sec_rating and sp_snr_sec_rating != "NR":
                    rank = self.return_ratings_rank(sp_snr_sec_rating)
                    if rank <= 15:
                        return self.notch_rating(rank, RatingAgency.MOODYS, -1)
                    else:
                        return self.notch_rating(rank, RatingAgency.MOODYS, -2)
                elif sp_subordinate and sp_subordinate != "NR":
                    rank = self.return_ratings_rank(sp_subordinate)
                    if rank <= 16:
                        return self.notch_rating(rank, RatingAgency.MOODYS, 1)
                    else:
                        return self.notch_rating(rank, RatingAgency.MOODYS, 0)
            
            return None
            
        except Exception as e:
            logger.error(f"Error deriving Moody's rating from S&P: {e}")
            return None
    
    def get_derived_sp_rating_from_moody(self, asset: Any) -> Optional[str]:
        """
        VBA: GetDerivedSandPRatingFromMoody function
        Cross-agency rating derivation from Moody's to S&P
        """
        try:
            # Get the Moody's rating to convert
            mdy_rating = self._get_base_moodys_rating_for_conversion(asset)
            if not mdy_rating:
                return None
            
            rank = self.return_ratings_rank(mdy_rating)
            if rank <= 10:  # Investment grade
                return self.notch_rating(rank, RatingAgency.SP, -1)
            else:  # Speculative grade
                return self.notch_rating(rank, RatingAgency.SP, -2)
                
        except Exception as e:
            logger.error(f"Error deriving S&P rating from Moody's: {e}")
            return None
    
    def calculate_moody_recovery_rate(self, asset: Any, mdy_rating: str, mdy_dp_rating: str) -> Decimal:
        """
        VBA: MoodyRecoveryRate method
        Calculate recovery rate based on rating difference and asset category
        """
        try:
            # DIP assets get fixed rate
            if getattr(asset, 'dip', False):
                return Decimal('0.5000')
            
            # Calculate rating difference
            rating_diff = self.return_ratings_rank(mdy_dp_rating) - self.return_ratings_rank(mdy_rating)
            
            # Get asset category
            asset_category = getattr(asset, 'mdy_asset_category', 'OTHER')
            
            # Find matching recovery rate from matrix
            for matrix in self._recovery_matrices_cache:
                if (matrix.asset_category == asset_category and
                    matrix.rating_diff_min <= rating_diff <= matrix.rating_diff_max and
                    not matrix.is_dip):
                    return matrix.recovery_rate
            
            # Fallback to generic category
            for matrix in self._recovery_matrices_cache:
                if (matrix.asset_category == 'OTHER' and
                    matrix.rating_diff_min <= rating_diff <= matrix.rating_diff_max and
                    not matrix.is_dip):
                    return matrix.recovery_rate
            
            # Final fallback
            return Decimal('0.3000')
            
        except Exception as e:
            logger.error(f"Error calculating recovery rate: {e}")
            return Decimal('0.3000')
    
    def _get_moodys_rating_senior_secured_loan(self, asset: Any) -> str:
        """Helper method for senior secured loan Moody's rating"""
        # 1. Facility rating with outlook adjustments
        facility_rating = getattr(asset, 'mdy_facility_rating', '')
        if facility_rating and facility_rating != "NR":
            facility_outlook = getattr(asset, 'mdy_facility_outlook', '')
            if facility_outlook == "Upgrade":
                return self.notch_rating(self.return_ratings_rank(facility_rating), RatingAgency.MOODYS, 1)
            elif facility_outlook == "Downgrade":
                return self.notch_rating(self.return_ratings_rank(facility_rating), RatingAgency.MOODYS, -1)
            else:
                return facility_rating
        
        # 2. Issuer rating with outlook adjustments
        issuer_rating = getattr(asset, 'mdy_issuer_rating', '')
        if issuer_rating and issuer_rating != "NR":
            issuer_outlook = getattr(asset, 'mdy_issuer_outlook', '')
            if issuer_outlook in ["Downgrade", "Negative"]:
                return self.notch_rating(self.return_ratings_rank(issuer_rating), RatingAgency.MOODYS, -1)
            else:
                return issuer_rating
        
        # 3. Senior unsecured (notched up)
        snr_unsec_rating = getattr(asset, 'mdy_snr_unsec_rating', '')
        if snr_unsec_rating and snr_unsec_rating != "NR":
            return self.notch_rating(self.return_ratings_rank(snr_unsec_rating), RatingAgency.MOODYS, 2)
        
        # 4. Cross-agency derivation
        derived_from_sp = self.get_derived_moody_rating_from_sp(asset)
        if derived_from_sp:
            return derived_from_sp
        
        return "Caa3"
    
    def _get_moodys_rating_other(self, asset: Any) -> str:
        """Helper method for non-senior secured loan Moody's rating"""
        # Different hierarchy for bonds and other instruments
        facility_rating = getattr(asset, 'mdy_facility_rating', '')
        if facility_rating and facility_rating != "NR":
            return facility_rating
        
        snr_unsec_rating = getattr(asset, 'mdy_snr_unsec_rating', '')
        if snr_unsec_rating and snr_unsec_rating != "NR":
            return snr_unsec_rating
        
        issuer_rating = getattr(asset, 'mdy_issuer_rating', '')
        if issuer_rating and issuer_rating != "NR":
            return self.notch_rating(self.return_ratings_rank(issuer_rating), RatingAgency.MOODYS, -1)
        
        sub_rating = getattr(asset, 'mdy_sub_rating', '')
        if sub_rating and sub_rating != "NR":
            return self.notch_rating(self.return_ratings_rank(sub_rating), RatingAgency.MOODYS, 1)
        
        derived_from_sp = self.get_derived_moody_rating_from_sp(asset)
        if derived_from_sp:
            return derived_from_sp
        
        return "Caa3"
    
    def _get_base_moodys_rating_for_conversion(self, asset: Any) -> Optional[str]:
        """Helper to get the base Moody's rating for cross-agency conversion"""
        bond_loan = getattr(asset, 'bond_loan', '')
        seniority = getattr(asset, 'seniority', '')
        
        # Use same logic as get_moodys_rating but without the cross-derivation
        if bond_loan == "LOAN" and seniority == "SENIOR SECURED":
            # Facility rating first
            facility_rating = getattr(asset, 'mdy_facility_rating', '')
            if facility_rating and facility_rating != "NR":
                return facility_rating
            
            # Then issuer
            issuer_rating = getattr(asset, 'mdy_issuer_rating', '')
            if issuer_rating and issuer_rating != "NR":
                return issuer_rating
            
            # Then senior unsecured
            snr_unsec_rating = getattr(asset, 'mdy_snr_unsec_rating', '')
            if snr_unsec_rating and snr_unsec_rating != "NR":
                return self.notch_rating(self.return_ratings_rank(snr_unsec_rating), RatingAgency.MOODYS, 2)
        else:
            # Different hierarchy for other instruments
            facility_rating = getattr(asset, 'mdy_facility_rating', '')
            if facility_rating and facility_rating != "NR":
                return facility_rating
            
            snr_unsec_rating = getattr(asset, 'mdy_snr_unsec_rating', '')
            if snr_unsec_rating and snr_unsec_rating != "NR":
                return snr_unsec_rating
        
        return None
    
    def _is_recent_date(self, check_date: date, months_threshold: int) -> bool:
        """Check if date is within specified months of current date"""
        try:
            from datetime import datetime, timedelta
            today = datetime.now().date()
            threshold_date = today - timedelta(days=months_threshold * 30)
            return check_date >= threshold_date
        except:
            return False


class RatingService:
    """Service layer for rating operations"""
    
    def __init__(self, session: Session):
        self.session = session
        self.derivation_engine = RatingDerivationEngine(session)
    
    def initialize_rating_system(self):
        """Initialize rating agencies and scales if not present"""
        # Check if agencies exist
        agency_count = self.session.query(RatingAgencyModel).count()
        if agency_count == 0:
            # Run the migration seed data manually if needed
            logger.info("Rating system not initialized. Please run database migrations.")
    
    def update_asset_ratings(self, asset: Any) -> Dict[str, str]:
        """Update all derived ratings for an asset"""
        try:
            results = {}
            
            # Calculate derived ratings
            results['mdy_rating'] = self.derivation_engine.get_moodys_rating(asset)
            results['mdy_dp_rating'] = self.derivation_engine.get_moodys_default_prob_rating(asset)
            results['mdy_dp_rating_warf'] = self.derivation_engine.get_moodys_default_prob_rating_warf(asset)
            results['sp_rating'] = self.derivation_engine.get_sp_ratings(asset)
            
            # Calculate recovery rate
            recovery_rate = self.derivation_engine.calculate_moody_recovery_rate(
                asset, results['mdy_rating'], results['mdy_dp_rating']
            )
            results['mdy_recovery_rate'] = float(recovery_rate)
            
            return results
            
        except Exception as e:
            logger.error(f"Error updating asset ratings: {e}")
            return {
                'mdy_rating': 'Caa3',
                'mdy_dp_rating': 'Caa3', 
                'mdy_dp_rating_warf': 'Caa3',
                'sp_rating': 'CCC-',
                'mdy_recovery_rate': 0.3000
            }
    
    def create_rating_migration(self, asset_id: str, migration_date: date,
                              previous_ratings: Dict[str, str], new_ratings: Dict[str, str],
                              par_amount: Decimal, portfolio_weight: Decimal) -> RatingMigration:
        """Create a rating migration record"""
        
        # Calculate notch change (using S&P ratings as primary)
        prev_rank = self.derivation_engine.return_ratings_rank(previous_ratings.get('sp', ''))
        new_rank = self.derivation_engine.return_ratings_rank(new_ratings.get('sp', ''))
        notch_change = prev_rank - new_rank  # Positive = upgrade
        
        # Determine migration type
        if new_ratings.get('sp') == 'D':
            migration_type = MigrationType.DEFAULT
        elif notch_change > 0:
            migration_type = MigrationType.UPGRADE
        elif notch_change < 0:
            migration_type = MigrationType.DOWNGRADE
        else:
            migration_type = MigrationType.NO_CHANGE
        
        migration = RatingMigration(
            asset_id=asset_id,
            migration_date=migration_date,
            previous_sp_rating=previous_ratings.get('sp'),
            previous_mdy_rating=previous_ratings.get('mdy'),
            previous_fitch_rating=previous_ratings.get('fitch'),
            new_sp_rating=new_ratings.get('sp'),
            new_mdy_rating=new_ratings.get('mdy'), 
            new_fitch_rating=new_ratings.get('fitch'),
            notch_change=notch_change,
            migration_type=migration_type.value,
            is_default_event=(migration_type == MigrationType.DEFAULT),
            par_amount_at_migration=par_amount,
            portfolio_weight_at_migration=portfolio_weight
        )
        
        self.session.add(migration)
        self.session.commit()
        return migration
    
    def get_portfolio_migration_summary(self, deal_id: str, start_date: date, 
                                      end_date: date) -> Dict[str, Any]:
        """Get portfolio migration summary for a period"""
        migrations = self.session.query(RatingMigration).join('asset').filter(
            RatingMigration.migration_date >= start_date,
            RatingMigration.migration_date <= end_date
        ).all()
        
        summary = {
            'total_migrations': len(migrations),
            'upgrades': len([m for m in migrations if m.migration_type == MigrationType.UPGRADE.value]),
            'downgrades': len([m for m in migrations if m.migration_type == MigrationType.DOWNGRADE.value]),
            'defaults': len([m for m in migrations if m.migration_type == MigrationType.DEFAULT.value]),
            'upgrade_volume': sum(m.par_amount_at_migration or 0 for m in migrations 
                                if m.migration_type == MigrationType.UPGRADE.value),
            'downgrade_volume': sum(m.par_amount_at_migration or 0 for m in migrations
                                  if m.migration_type == MigrationType.DOWNGRADE.value),
            'default_volume': sum(m.par_amount_at_migration or 0 for m in migrations
                                if m.migration_type == MigrationType.DEFAULT.value)
        }
        
        return summary