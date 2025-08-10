"""
Rating Migration Analysis - VBA RatingMigrationItem.cls and RatingMigrationOutput.cls Python implementation

This module implements portfolio-level rating migration analysis and simulation capabilities
with database persistence and statistical analysis.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from decimal import Decimal
from datetime import date, datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import logging
from sqlalchemy.orm import Session
import statistics

from .rating_system import (
    RatingDistributionHistory, 
    PortfolioMigrationStats,
    RatingMigration,
    RatingDerivationEngine
)

logger = logging.getLogger(__name__)


class PeriodFrequency(str, Enum):
    """Period frequency enumeration"""
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUALLY = "SEMI-ANNUALLY" 
    ANNUALLY = "ANNUALLY"


class StatisticType(str, Enum):
    """Statistical analysis types"""
    MIN = "MIN"
    MAX = "MAX"
    AVERAGE = "AVERAGE"
    MEDIAN = "MEDIAN"
    STDDEV = "STDDEV"


@dataclass
class RatingHistogram:
    """Rating distribution data structure - matches VBA RatingHist"""
    upgrades: int = 0
    downgrades: int = 0
    num_aaa: int = 0
    num_aa_plus: int = 0
    num_aa: int = 0
    num_aa_minus: int = 0
    num_a_plus: int = 0
    num_a: int = 0
    num_a_minus: int = 0
    num_bbb_plus: int = 0
    num_bbb: int = 0
    num_bbb_minus: int = 0
    num_bb_plus: int = 0
    num_bb: int = 0
    num_bb_minus: int = 0
    num_b_plus: int = 0
    num_b: int = 0
    num_b_minus: int = 0
    num_ccc_assets: int = 0
    num_defaults: int = 0
    num_matures: int = 0
    num_period_defaults: int = 0
    num_performing: int = 0


@dataclass
class RatingHistogramBalance:
    """Rating distribution balance data - matches VBA RatingHistBal"""
    bal_aaa: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_aa_plus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_aa: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_aa_minus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_a_plus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_a: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_a_minus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_bbb_plus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_bbb: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_bbb_minus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_bb_plus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_bb: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_bb_minus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_b_plus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_b: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_b_minus: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_ccc: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_period_defaults: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_defaults: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_mature: Decimal = field(default_factory=lambda: Decimal('0'))
    bal_performing: Decimal = field(default_factory=lambda: Decimal('0'))
    cdr: Decimal = field(default_factory=lambda: Decimal('0'))  # Cumulative Default Rate


class RatingMigrationItem:
    """
    Python implementation of VBA RatingMigrationItem.cls
    Tracks rating migration history for a single deal across multiple simulations
    """
    
    def __init__(self, deal_name: str, analysis_date: date, maturity_date: date, 
                 num_simulations: int, period_frequency: PeriodFrequency, session: Session):
        self.deal_name = deal_name
        self.analysis_date = analysis_date
        self.maturity_date = maturity_date
        self.num_simulations = num_simulations
        self.period_frequency = period_frequency
        self.session = session
        
        # Calculate periods
        self.num_months = self._get_months_per_period(period_frequency)
        self.payment_dates: List[date] = []
        self.date_to_index: Dict[date, int] = {}
        self._build_payment_schedule()
        
        # Simulation data storage
        # Format: simulation_data[sim_index][period_index] = (RatingHistogram, RatingHistogramBalance)
        self.simulation_data: Dict[int, Dict[int, Tuple[RatingHistogram, RatingHistogramBalance]]] = {}
        self._initialize_simulation_data()
    
    def _get_months_per_period(self, frequency: PeriodFrequency) -> int:
        """Convert period frequency to months"""
        if frequency == PeriodFrequency.ANNUALLY:
            return 12
        elif frequency == PeriodFrequency.SEMI_ANNUALLY:
            return 6
        else:  # QUARTERLY
            return 3
    
    def _build_payment_schedule(self):
        """Build payment date schedule and index mapping"""
        self.date_to_index[self.analysis_date] = 0
        self.payment_dates = [self.analysis_date]
        
        current_date = self.analysis_date
        period_index = 0
        
        while current_date < self.maturity_date:
            period_index += 1
            # Add months to get next payment date
            next_date = self._add_months(current_date, self.num_months)
            if next_date > self.maturity_date:
                next_date = self.maturity_date
            
            self.payment_dates.append(next_date)
            self.date_to_index[next_date] = period_index
            current_date = next_date
    
    def _add_months(self, base_date: date, months: int) -> date:
        """Add months to a date"""
        month = base_date.month - 1 + months
        year = base_date.year + month // 12
        month = month % 12 + 1
        day = min(base_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
        return date(year, month, day)
    
    def _initialize_simulation_data(self):
        """Initialize simulation data structures"""
        for sim_index in range(self.num_simulations):
            self.simulation_data[sim_index] = {}
            for period_index in range(len(self.payment_dates)):
                self.simulation_data[sim_index][period_index] = (
                    RatingHistogram(),
                    RatingHistogramBalance()
                )
    
    def add_rating_and_balance(self, simulation: int, calculation_date: date, 
                              rating: str, balance: Decimal):
        """
        VBA: AddRatingAndBalance method
        Add both rating count and balance for a simulation/date
        """
        self.add_rating(simulation, calculation_date, rating)
        self.add_balance(simulation, calculation_date, rating, balance)
    
    def add_rating(self, simulation: int, calculation_date: date, rating: str):
        """
        VBA: AddRating method
        Add rating count to histogram
        """
        try:
            period_index = self.date_to_index.get(calculation_date)
            if period_index is None:
                logger.warning(f"Date {calculation_date} not found in payment schedule")
                return
            
            sim_index = simulation - 1  # VBA uses 1-based indexing
            if sim_index < 0 or sim_index >= self.num_simulations:
                logger.warning(f"Invalid simulation number: {simulation}")
                return
            
            rating_hist, _ = self.simulation_data[sim_index][period_index]
            
            # Normalize CCC variants
            if rating in ["CCC+", "CCC", "CCC-", "CC", "C"]:
                rating = "CCC"
            
            # Map ratings to histogram fields
            rating_mapping = {
                "AAA": "num_aaa",
                "AA+": "num_aa_plus", 
                "AA": "num_aa",
                "AA-": "num_aa_minus",
                "A+": "num_a_plus",
                "A": "num_a", 
                "A-": "num_a_minus",
                "BBB+": "num_bbb_plus",
                "BBB": "num_bbb",
                "BBB-": "num_bbb_minus",
                "BB+": "num_bb_plus",
                "BB": "num_bb",
                "BB-": "num_bb_minus",
                "B+": "num_b_plus",
                "B": "num_b",
                "B-": "num_b_minus",
                "CCC": "num_ccc_assets",
                "D": "num_period_defaults" if period_index > 0 else "num_defaults",
                "M": "num_matures"
            }
            
            field_name = rating_mapping.get(rating)
            if field_name:
                current_value = getattr(rating_hist, field_name)
                setattr(rating_hist, field_name, current_value + 1)
                
        except Exception as e:
            logger.error(f"Error adding rating: {e}")
    
    def add_balance(self, simulation: int, calculation_date: date, rating: str, balance: Decimal):
        """
        VBA: AddBalance method
        Add balance amount to histogram balance
        """
        try:
            period_index = self.date_to_index.get(calculation_date)
            if period_index is None:
                return
            
            sim_index = simulation - 1
            if sim_index < 0 or sim_index >= self.num_simulations:
                return
            
            _, rating_hist_bal = self.simulation_data[sim_index][period_index]
            
            # Get previous performing balance for CDR calculation
            last_performing_balance = Decimal('0')
            if period_index > 0:
                _, prev_bal = self.simulation_data[sim_index][period_index - 1]
                last_performing_balance = prev_bal.bal_performing
            
            # Normalize CCC variants
            if rating in ["CCC+", "CCC", "CCC-", "CC", "C"]:
                rating = "CCC"
            
            # Map ratings to balance fields
            balance_mapping = {
                "AAA": "bal_aaa",
                "AA+": "bal_aa_plus",
                "AA": "bal_aa", 
                "AA-": "bal_aa_minus",
                "A+": "bal_a_plus",
                "A": "bal_a",
                "A-": "bal_a_minus", 
                "BBB+": "bal_bbb_plus",
                "BBB": "bal_bbb",
                "BBB-": "bal_bbb_minus",
                "BB+": "bal_bb_plus",
                "BB": "bal_bb",
                "BB-": "bal_bb_minus",
                "B+": "bal_b_plus",
                "B": "bal_b",
                "B-": "bal_b_minus",
                "CCC": "bal_ccc",
                "D": "bal_period_defaults" if period_index > 0 else "bal_defaults",
                "M": "bal_mature"
            }
            
            field_name = balance_mapping.get(rating)
            if field_name:
                current_value = getattr(rating_hist_bal, field_name)
                setattr(rating_hist_bal, field_name, current_value + balance)
                
                # Add to performing balance if not default/mature
                if rating not in ["D", "M"]:
                    rating_hist_bal.bal_performing += balance
            
            # Calculate CDR (Cumulative Default Rate)
            if last_performing_balance > 0:
                rating_hist_bal.cdr = rating_hist_bal.bal_period_defaults / last_performing_balance
                # Annualize based on frequency
                if self.num_months == 3:
                    rating_hist_bal.cdr *= Decimal('4')
                elif self.num_months == 6:
                    rating_hist_bal.cdr *= Decimal('2')
                
        except Exception as e:
            logger.error(f"Error adding balance: {e}")
    
    def add_upgrade(self, simulation: int, calculation_date: date):
        """
        VBA: AddUpgrade method
        Record an upgrade event
        """
        try:
            period_index = self.date_to_index.get(calculation_date)
            if period_index is None:
                return
            
            sim_index = simulation - 1
            if sim_index < 0 or sim_index >= self.num_simulations:
                return
            
            rating_hist, _ = self.simulation_data[sim_index][period_index]
            rating_hist.upgrades += 1
            
        except Exception as e:
            logger.error(f"Error adding upgrade: {e}")
    
    def add_downgrade(self, simulation: int, calculation_date: date):
        """
        VBA: AddDowngrade method
        Record a downgrade event
        """
        try:
            period_index = self.date_to_index.get(calculation_date)
            if period_index is None:
                return
            
            sim_index = simulation - 1
            if sim_index < 0 or sim_index >= self.num_simulations:
                return
            
            rating_hist, _ = self.simulation_data[sim_index][period_index]
            rating_hist.downgrades += 1
            
        except Exception as e:
            logger.error(f"Error adding downgrade: {e}")
    
    def update_defaults(self, simulation: int):
        """
        VBA: UpdateDefaults method
        Update cumulative defaults across all periods
        """
        try:
            sim_index = simulation - 1
            if sim_index < 0 or sim_index >= self.num_simulations:
                return
            
            for period_index in range(1, len(self.payment_dates)):
                rating_hist, rating_hist_bal = self.simulation_data[sim_index][period_index]
                prev_rating_hist, prev_rating_hist_bal = self.simulation_data[sim_index][period_index - 1]
                
                # Update cumulative defaults
                rating_hist_bal.bal_defaults = (
                    rating_hist_bal.bal_period_defaults + prev_rating_hist_bal.bal_defaults
                )
                rating_hist.num_defaults = (
                    rating_hist.num_period_defaults + prev_rating_hist.num_defaults
                )
                
        except Exception as e:
            logger.error(f"Error updating defaults: {e}")
    
    def get_simulation_data_point(self, simulation: int, calculation_date: date, field: str) -> Decimal:
        """
        VBA: GetSimDataPoint method
        Get specific data point for a simulation and date
        """
        try:
            period_index = self.date_to_index.get(calculation_date)
            if period_index is None:
                return Decimal('0')
            
            sim_index = simulation - 1
            if sim_index < 0 or sim_index >= self.num_simulations:
                return Decimal('0')
            
            rating_hist, rating_hist_bal = self.simulation_data[sim_index][period_index]
            field_upper = field.upper()
            
            # Map field names to data
            if hasattr(rating_hist, field_upper.lower()):
                return Decimal(str(getattr(rating_hist, field_upper.lower())))
            elif hasattr(rating_hist_bal, field_upper.lower()):
                return getattr(rating_hist_bal, field_upper.lower())
            
            # Handle specific field mappings
            field_mappings = {
                "UPGRADES": rating_hist.upgrades,
                "DOWNGRADES": rating_hist.downgrades, 
                "NUMAAA": rating_hist.num_aaa,
                "NUMAA": rating_hist.num_aa,
                "NUMA": rating_hist.num_a,
                "NUMBBB": rating_hist.num_bbb,
                "NUMBB": rating_hist.num_bb,
                "NUMB": rating_hist.num_b,
                "NUMCCC": rating_hist.num_ccc_assets,
                "NUMPERDEF": rating_hist.num_period_defaults,
                "NUMDEF": rating_hist.num_defaults,
                "NUMMAT": rating_hist.num_matures,
                "NUMPERF": rating_hist.num_performing,
                "BALAAA": rating_hist_bal.bal_aaa,
                "BALAA": rating_hist_bal.bal_aa,
                "BALA": rating_hist_bal.bal_a,
                "BALBBB": rating_hist_bal.bal_bbb,
                "BALBB": rating_hist_bal.bal_bb,
                "BALB": rating_hist_bal.bal_b,
                "BALCCC": rating_hist_bal.bal_ccc,
                "BALPERDEF": rating_hist_bal.bal_period_defaults,
                "BALDEF": rating_hist_bal.bal_defaults,
                "BALMAT": rating_hist_bal.bal_mature,
                "BALPERF": rating_hist_bal.bal_performing,
                "CDR": rating_hist_bal.cdr
            }
            
            return Decimal(str(field_mappings.get(field_upper, 0)))
            
        except Exception as e:
            logger.error(f"Error getting simulation data point: {e}")
            return Decimal('0')
    
    def get_statistic_data(self, statistic: str, field: str, calculation_date: date) -> Decimal:
        """
        VBA: GeStatData method
        Get statistical measure across all simulations for a date/field
        """
        try:
            # Get data for all simulations
            data_points = []
            for sim in range(1, self.num_simulations + 1):
                value = self.get_simulation_data_point(sim, calculation_date, field)
                data_points.append(float(value))
            
            if not data_points:
                return Decimal('0')
            
            # Calculate statistic
            stat_upper = statistic.upper()
            if stat_upper == "MIN":
                result = min(data_points)
            elif stat_upper == "MAX":
                result = max(data_points)
            elif stat_upper == "AVERAGE":
                result = sum(data_points) / len(data_points)
            elif stat_upper == "MEDIAN":
                result = statistics.median(data_points)
            elif stat_upper == "STDDEV":
                result = statistics.stdev(data_points) if len(data_points) > 1 else 0
            else:
                result = 0
            
            return Decimal(str(result))
            
        except Exception as e:
            logger.error(f"Error calculating statistic: {e}")
            return Decimal('0')
    
    def get_simulation_time_series(self, simulation: int, field: str) -> List[Decimal]:
        """
        VBA: GetSimTimeSeries method
        Get time series data for a specific simulation and field
        """
        try:
            time_series = []
            for payment_date in self.payment_dates:
                value = self.get_simulation_data_point(simulation, payment_date, field)
                time_series.append(value)
            return time_series
            
        except Exception as e:
            logger.error(f"Error getting simulation time series: {e}")
            return [Decimal('0')] * len(self.payment_dates)
    
    def save_to_database(self):
        """Save migration data to database"""
        try:
            for sim_index in range(self.num_simulations):
                simulation_number = sim_index + 1
                
                for period_index, payment_date in enumerate(self.payment_dates):
                    rating_hist, rating_hist_bal = self.simulation_data[sim_index][period_index]
                    
                    # Save portfolio migration stats
                    stats = PortfolioMigrationStats(
                        deal_id=self.deal_name,
                        calculation_date=payment_date,
                        simulation_number=simulation_number,
                        total_upgrades=rating_hist.upgrades,
                        total_downgrades=rating_hist.downgrades,
                        total_defaults=rating_hist.num_defaults,
                        period_defaults=rating_hist.num_period_defaults,
                        period_default_dollar_volume=rating_hist_bal.bal_period_defaults,
                        performing_balance=rating_hist_bal.bal_performing,
                        cumulative_default_rate=rating_hist_bal.cdr
                    )
                    self.session.add(stats)
                    
                    # Save rating distribution
                    rating_distributions = [
                        ("AAA", rating_hist.num_aaa, rating_hist_bal.bal_aaa),
                        ("AA+", rating_hist.num_aa_plus, rating_hist_bal.bal_aa_plus),
                        ("AA", rating_hist.num_aa, rating_hist_bal.bal_aa),
                        ("AA-", rating_hist.num_aa_minus, rating_hist_bal.bal_aa_minus),
                        ("A+", rating_hist.num_a_plus, rating_hist_bal.bal_a_plus),
                        ("A", rating_hist.num_a, rating_hist_bal.bal_a),
                        ("A-", rating_hist.num_a_minus, rating_hist_bal.bal_a_minus),
                        ("BBB+", rating_hist.num_bbb_plus, rating_hist_bal.bal_bbb_plus),
                        ("BBB", rating_hist.num_bbb, rating_hist_bal.bal_bbb),
                        ("BBB-", rating_hist.num_bbb_minus, rating_hist_bal.bal_bbb_minus),
                        ("BB+", rating_hist.num_bb_plus, rating_hist_bal.bal_bb_plus),
                        ("BB", rating_hist.num_bb, rating_hist_bal.bal_bb),
                        ("BB-", rating_hist.num_bb_minus, rating_hist_bal.bal_bb_minus),
                        ("B+", rating_hist.num_b_plus, rating_hist_bal.bal_b_plus),
                        ("B", rating_hist.num_b, rating_hist_bal.bal_b),
                        ("B-", rating_hist.num_b_minus, rating_hist_bal.bal_b_minus),
                        ("CCC", rating_hist.num_ccc_assets, rating_hist_bal.bal_ccc),
                        ("D", rating_hist.num_defaults, rating_hist_bal.bal_defaults),
                        ("M", rating_hist.num_matures, rating_hist_bal.bal_mature)
                    ]
                    
                    for rating_bucket, asset_count, balance_amount in rating_distributions:
                        if asset_count > 0 or balance_amount > 0:
                            distribution = RatingDistributionHistory(
                                deal_id=self.deal_name,
                                calculation_date=payment_date,
                                simulation_number=simulation_number,
                                rating_bucket=rating_bucket,
                                asset_count=asset_count,
                                balance_amount=balance_amount
                            )
                            self.session.add(distribution)
            
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Error saving migration data: {e}")
            self.session.rollback()


class RatingMigrationOutput:
    """
    Python implementation of VBA RatingMigrationOutput.cls
    Manages multiple deals and provides statistical analysis across simulations
    """
    
    def __init__(self, deal_names: List[str], num_simulations: int, analysis_date: date,
                 maturity_date: date, period_frequency: PeriodFrequency, session: Session):
        self.deal_names = deal_names
        self.num_simulations = num_simulations
        self.analysis_date = analysis_date
        self.maturity_date = maturity_date
        self.period_frequency = period_frequency
        self.session = session
        
        # Create RatingMigrationItem for each deal
        self.deal_migration_items: Dict[str, RatingMigrationItem] = {}
        for deal_name in deal_names:
            self.deal_migration_items[deal_name] = RatingMigrationItem(
                deal_name, analysis_date, maturity_date, num_simulations, period_frequency, session
            )
        
        # Build common date dictionary
        self.payment_dates = self.deal_migration_items[deal_names[0]].payment_dates
        self.date_to_index = self.deal_migration_items[deal_names[0]].date_to_index
    
    def add_deal_data(self, deal_name: str, collateral_pool: Any, simulation: int):
        """
        VBA: AddDeal method
        Process collateral pool data for a specific deal and simulation
        """
        if deal_name not in self.deal_migration_items:
            logger.warning(f"Deal {deal_name} not found in migration output")
            return
        
        try:
            migration_item = self.deal_migration_items[deal_name]
            
            # This would integrate with the collateral pool to process assets
            # For now, this is a placeholder that would need actual asset data
            logger.info(f"Processing deal {deal_name} simulation {simulation}")
            
        except Exception as e:
            logger.error(f"Error processing deal data: {e}")
    
    def get_simulation_time_series(self, simulation: int, field: str) -> List[List[Any]]:
        """
        VBA: GetSimTimeSeries method
        Get time series data across all deals for a specific simulation
        """
        try:
            # Create output matrix
            output = []
            
            # Header row
            header = ["Period"] + self.deal_names
            output.append(header)
            
            # Data rows
            for payment_date in self.payment_dates:
                row = [payment_date]
                for deal_name in self.deal_names:
                    migration_item = self.deal_migration_items[deal_name]
                    value = migration_item.get_simulation_data_point(simulation, payment_date, field)
                    
                    # Format specific fields
                    if field.upper() == "CDR":
                        formatted_value = f"{float(value):.3%}"
                    elif field.upper() in ["NUMPERDEF", "BALPERDEF"]:
                        formatted_value = f"{float(value):.3f}"
                    else:
                        formatted_value = float(value)
                    
                    row.append(formatted_value)
                output.append(row)
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting simulation time series: {e}")
            return []
    
    def get_statistical_time_series(self, statistic: str, field: str) -> List[List[Any]]:
        """
        VBA: StatTimeSeries and AVGTimeSeries methods
        Get statistical time series across all deals
        """
        try:
            if statistic.upper() == "AVERAGE":
                return self._get_average_time_series(field)
            else:
                # For MIN, MAX, MEDIAN - find the simulation with extreme defaults first
                if statistic.upper() == "MIN":
                    target_sim = self._get_simulation_min_defaults()
                elif statistic.upper() == "MAX":
                    target_sim = self._get_simulation_max_defaults()
                elif statistic.upper() == "MEDIAN":
                    target_sim = self._get_simulation_median_defaults()
                else:
                    target_sim = 1
                
                return self.get_simulation_time_series(target_sim, field)
                
        except Exception as e:
            logger.error(f"Error getting statistical time series: {e}")
            return []
    
    def _get_average_time_series(self, field: str) -> List[List[Any]]:
        """Get average time series across all simulations"""
        try:
            output = []
            
            # Header row
            header = ["Period"] + self.deal_names
            output.append(header)
            
            # Data rows
            for payment_date in self.payment_dates:
                row = [payment_date]
                for deal_name in self.deal_names:
                    migration_item = self.deal_migration_items[deal_name]
                    avg_value = migration_item.get_statistic_data("AVERAGE", field, payment_date)
                    
                    # Format specific fields
                    if field.upper() == "CDR":
                        formatted_value = f"{float(avg_value):.3%}"
                    elif field.upper() in ["NUMPERDEF", "BALPERDEF"]:
                        formatted_value = f"{float(avg_value):.3f}"
                    else:
                        formatted_value = float(avg_value)
                    
                    row.append(formatted_value)
                output.append(row)
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting average time series: {e}")
            return []
    
    def _get_simulation_min_defaults(self) -> int:
        """
        VBA: GetSimMinDefaults method
        Find simulation with minimum total defaults
        """
        try:
            min_defaults = None
            min_simulation = 1
            
            for sim in range(1, self.num_simulations + 1):
                total_defaults = Decimal('0')
                for deal_name in self.deal_names:
                    migration_item = self.deal_migration_items[deal_name]
                    defaults = migration_item.get_simulation_data_point(sim, self.maturity_date, "BALDEF")
                    total_defaults += defaults
                
                if min_defaults is None or total_defaults < min_defaults:
                    min_defaults = total_defaults
                    min_simulation = sim
            
            return min_simulation
            
        except Exception as e:
            logger.error(f"Error finding min defaults simulation: {e}")
            return 1
    
    def _get_simulation_max_defaults(self) -> int:
        """
        VBA: GetSimMaxDefaults method
        Find simulation with maximum total defaults
        """
        try:
            max_defaults = None
            max_simulation = 1
            
            for sim in range(1, self.num_simulations + 1):
                total_defaults = Decimal('0')
                for deal_name in self.deal_names:
                    migration_item = self.deal_migration_items[deal_name]
                    defaults = migration_item.get_simulation_data_point(sim, self.maturity_date, "BALDEF")
                    total_defaults += defaults
                
                if max_defaults is None or total_defaults > max_defaults:
                    max_defaults = total_defaults
                    max_simulation = sim
            
            return max_simulation
            
        except Exception as e:
            logger.error(f"Error finding max defaults simulation: {e}")
            return 1
    
    def _get_simulation_median_defaults(self) -> int:
        """
        VBA: GetSimMedianDefaults method
        Find simulation with median total defaults
        """
        try:
            simulation_defaults = {}
            
            for sim in range(1, self.num_simulations + 1):
                total_defaults = Decimal('0')
                for deal_name in self.deal_names:
                    migration_item = self.deal_migration_items[deal_name]
                    defaults = migration_item.get_simulation_data_point(sim, self.maturity_date, "BALDEF")
                    total_defaults += defaults
                
                simulation_defaults[float(total_defaults)] = sim
            
            # Sort by defaults amount
            sorted_defaults = sorted(simulation_defaults.keys())
            
            # Get median
            if self.num_simulations == 1:
                median_index = 0
            elif self.num_simulations == 3:
                median_index = 1
            else:
                median_index = self.num_simulations // 2
            
            if median_index < len(sorted_defaults):
                median_defaults = sorted_defaults[median_index]
                return simulation_defaults[median_defaults]
            
            return 1
            
        except Exception as e:
            logger.error(f"Error finding median defaults simulation: {e}")
            return 1
    
    def save_all_to_database(self):
        """Save all deal migration data to database"""
        try:
            for migration_item in self.deal_migration_items.values():
                migration_item.save_to_database()
            
        except Exception as e:
            logger.error(f"Error saving all migration data: {e}")


class RatingMigrationService:
    """Service layer for rating migration analysis"""
    
    def __init__(self, session: Session):
        self.session = session
        self.rating_engine = RatingDerivationEngine(session)
    
    def create_migration_analysis(self, deal_names: List[str], num_simulations: int,
                                analysis_date: date, maturity_date: date,
                                period_frequency: PeriodFrequency = PeriodFrequency.QUARTERLY) -> RatingMigrationOutput:
        """Create a new migration analysis"""
        return RatingMigrationOutput(
            deal_names, num_simulations, analysis_date, maturity_date, period_frequency, self.session
        )
    
    def get_deal_migration_summary(self, deal_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get migration summary for a deal over a date range"""
        try:
            # Get portfolio stats from database
            stats = self.session.query(PortfolioMigrationStats).filter(
                PortfolioMigrationStats.deal_id == deal_id,
                PortfolioMigrationStats.calculation_date >= start_date,
                PortfolioMigrationStats.calculation_date <= end_date
            ).all()
            
            if not stats:
                return {"error": "No migration data found for the specified period"}
            
            # Aggregate statistics
            summary = {
                "deal_id": deal_id,
                "period_start": start_date,
                "period_end": end_date,
                "total_periods": len(stats),
                "simulations": len(set(s.simulation_number for s in stats)),
                "avg_upgrades": sum(s.total_upgrades for s in stats) / len(stats),
                "avg_downgrades": sum(s.total_downgrades for s in stats) / len(stats),
                "avg_defaults": sum(s.total_defaults for s in stats) / len(stats),
                "avg_cdr": sum(float(s.cumulative_default_rate or 0) for s in stats) / len(stats),
                "max_cdr": max(float(s.cumulative_default_rate or 0) for s in stats),
                "final_performing_balance": stats[-1].performing_balance if stats else 0
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting deal migration summary: {e}")
            return {"error": str(e)}