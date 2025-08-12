"""
Credit Migration Module

Converted from VBA CreditMigration.bas module to provide Monte Carlo credit migration
modeling capabilities for the CLO Management System. This module simulates credit 
rating transitions, defaults, and maturities over time using correlation matrices
and transition matrices.

Key Features:
- Monte Carlo simulation of credit rating migrations
- Asset correlation modeling using Cholesky decomposition
- Rating transition matrices with periodic adjustments
- Statistical output generation and analysis
- Support for multiple deal structures and time periods

Author: Converted from VBA by Claude
Date: 2025-01-12
"""

from typing import List, Dict, Optional, Tuple, Any, Union
from datetime import date, datetime, timedelta
from dataclasses import dataclass, field
from enum import IntEnum
import numpy as np
from scipy.stats import norm
from scipy.linalg import cholesky
import pandas as pd
import logging
import random
from collections import defaultdict

from ..utils.math_utils import MathUtils
from ..utils.matrix_utils import MatrixUtils

logger = logging.getLogger(__name__)


class SPRating(IntEnum):
    """S&P Rating enumeration matching VBA enum"""
    AAA = 1
    AA_PLUS = 2
    AA = 3
    AA_MINUS = 4
    A_PLUS = 5
    A = 6
    A_MINUS = 7
    BBB_PLUS = 8
    BBB = 9
    BBB_MINUS = 10
    BB_PLUS = 11
    BB = 12
    BB_MINUS = 13
    B_PLUS = 14
    B = 15
    B_MINUS = 16
    CCC = 17
    DEFAULT = 18


@dataclass
class RatingHist:
    """Rating history for a specific period"""
    upgrades: int = 0
    downgrades: int = 0
    num_aaa: int = 0
    num_aa_plus: int = 0
    num_aa_minus: int = 0
    num_aa: int = 0
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


@dataclass
class RatingHistBal:
    """Rating history balances for a specific period"""
    bal_aaa: float = 0.0
    bal_aa1: float = 0.0
    bal_aa2: float = 0.0
    bal_aa3: float = 0.0
    bal_a1: float = 0.0
    bal_a2: float = 0.0
    bal_a3: float = 0.0
    bal_bbb1: float = 0.0
    bal_bbb2: float = 0.0
    bal_bbb3: float = 0.0
    bal_bb1: float = 0.0
    bal_bb2: float = 0.0
    bal_bb3: float = 0.0
    bal_b1: float = 0.0
    bal_b2: float = 0.0
    bal_b3: float = 0.0
    bal_ccc: float = 0.0
    bal_defaults: float = 0.0
    bal_mature: float = 0.0
    cdr: float = 0.0  # Cumulative Default Rate


@dataclass
class SimHistory:
    """Simulation history for a single simulation run"""
    rating_hist: List[RatingHist] = field(default_factory=list)
    rating_hist_bal: List[RatingHistBal] = field(default_factory=list)


class CreditMigration:
    """Credit Migration Monte Carlo simulation engine"""
    
    def __init__(self):
        """Initialize credit migration engine"""
        self.tran_matrix: Optional[np.ndarray] = None  # Transition matrix with z-thresholds
        self.corr_matrix: Optional[np.ndarray] = None  # Cholesky decomposition of correlation matrix
        self.asset_order: List[str] = []  # Order of assets in correlation matrix
        self.num_assets: int = 0
        self.num_periods: int = 0
        self.analysis_date: Optional[date] = None
        self.rating_hist: List[RatingHist] = []
        self.rating_hist_bal: List[RatingHistBal] = []
        self.sim_hist: List[SimHistory] = []
        self.sim_count: int = 0
        self.period_type: str = "QUARTERLY"
        self.math_utils = MathUtils()
        self.matrix_utils = MatrixUtils()
    
    def cleanup(self) -> None:
        """Clean up simulation data"""
        self.tran_matrix = None
        self.corr_matrix = None
        self.asset_order.clear()
        self.rating_hist.clear()
        self.rating_hist_bal.clear()
        self.sim_hist.clear()
        self.sim_count = 0
    
    def setup(self, num_sims: int, debug_mode: bool = False, 
             collateral_pool: Optional[Any] = None, 
             period: str = "QUARTERLY") -> None:
        """Setup credit migration simulation"""
        self.period_type = period
        self._setup_transition_matrix(period)
        self._setup_correlation_matrix(collateral_pool)
        
        if debug_mode:
            self._set_randomize_seed()
        
        self.sim_hist = [SimHistory() for _ in range(num_sims)]
        self.sim_count = 0
    
    def _setup_transition_matrix(self, period: str = "QUARTERLY") -> None:
        """Setup transition matrix based on period frequency"""
        # Default annual S&P transition matrix (example values)
        annual_matrix = self._get_default_annual_transition_matrix()
        
        if period.upper() == "ANNUALLY":
            quarterly_matrix = annual_matrix
        elif period.upper() == "SEMI-ANNUALLY":
            # Convert annual to semi-annual
            semi_matrix = self.matrix_utils.matrix_sqrt(annual_matrix)
            quarterly_matrix = self.matrix_utils.matrix_qom(semi_matrix)
        else:
            # Convert annual to quarterly
            semi_matrix = self.matrix_utils.matrix_sqrt(annual_matrix)
            semi_matrix = self.matrix_utils.matrix_qom(semi_matrix)
            quarterly_matrix = self.matrix_utils.matrix_sqrt(semi_matrix)
            quarterly_matrix = self.matrix_utils.matrix_qom(quarterly_matrix)
        
        # Convert to cumulative matrix
        num_ratings = quarterly_matrix.shape[0]
        cumulative_matrix = np.zeros_like(quarterly_matrix)
        
        for i in range(num_ratings):
            for j in range(num_ratings):
                cumulative_matrix[i, j] = np.sum(quarterly_matrix[i, :j+1])
        
        self.tran_matrix = cumulative_matrix
    
    def _get_default_annual_transition_matrix(self) -> np.ndarray:
        """Get default S&P annual transition matrix"""
        # Simplified S&P transition matrix (18x18)
        # In practice, this would be loaded from configuration or database
        matrix = np.zeros((18, 18))
        
        # Fill diagonal with high probability of staying in same rating
        np.fill_diagonal(matrix, 0.85)
        
        # Add some probability for upgrades and downgrades
        for i in range(17):
            if i > 0:
                matrix[i, i-1] = 0.05  # Upgrade
            if i < 16:
                matrix[i, i+1] = 0.08  # Downgrade
            matrix[i, 17] = 0.02  # Default probability
        
        # Default state is absorbing
        matrix[17, 17] = 1.0
        
        # Normalize rows to sum to 1
        for i in range(18):
            row_sum = np.sum(matrix[i, :])
            if row_sum > 0:
                matrix[i, :] /= row_sum
        
        return matrix
    
    def _setup_correlation_matrix(self, collateral_pool: Optional[Any] = None) -> None:
        """Setup asset correlation matrix"""
        if collateral_pool is None:
            # Use default correlation matrix
            correlation_matrix = self._create_default_correlation_matrix()
            self.asset_order = [f"ASSET_{i}" for i in range(correlation_matrix.shape[0])]
        else:
            # Create correlation matrix from collateral pool
            correlation_matrix = self._create_correlation_matrix_from_pool(collateral_pool)
            self.asset_order = collateral_pool.get_asset_ids()
        
        # Perform Cholesky decomposition
        self.corr_matrix = cholesky(correlation_matrix, lower=True)
        self.num_assets = len(self.asset_order)
    
    def _create_default_correlation_matrix(self) -> np.ndarray:
        """Create default correlation matrix for testing"""
        size = 10  # Default portfolio size
        correlation_matrix = np.eye(size) * 1.0
        
        # Add some correlation between assets
        for i in range(size):
            for j in range(size):
                if i != j:
                    correlation_matrix[i, j] = 0.3  # Base correlation
        
        return correlation_matrix
    
    def _create_correlation_matrix_from_pool(self, collateral_pool: Any) -> np.ndarray:
        """Create correlation matrix from collateral pool"""
        asset_ids = collateral_pool.get_asset_ids()
        num_assets = len(asset_ids)
        correlation_matrix = np.eye(num_assets)
        
        # Default correlation table values
        same_issuer_base = 0.7
        same_issuer_rating_adj = 0.05
        same_industry_base = 0.4
        same_industry_rating_adj = 0.03
        different_base = 0.2
        different_rating_adj = 0.02
        
        for i, asset_i in enumerate(asset_ids):
            asset_i_obj = collateral_pool.get_asset(asset_i)
            for j, asset_j in enumerate(asset_ids):
                if i == j:
                    correlation_matrix[i, j] = 1.0
                else:
                    asset_j_obj = collateral_pool.get_asset(asset_j)
                    rating_diff = abs(
                        self._get_rating_rank(asset_i_obj.sp_rating) - 
                        self._get_rating_rank(asset_j_obj.sp_rating)
                    )
                    
                    if asset_i_obj.issuer_id == asset_j_obj.issuer_id:
                        # Same issuer
                        corr = same_issuer_base - rating_diff * same_issuer_rating_adj
                    elif asset_i_obj.sp_industry == asset_j_obj.sp_industry:
                        # Same industry
                        corr = same_industry_base - rating_diff * same_industry_rating_adj
                    else:
                        # Different issuer and industry
                        corr = different_base - rating_diff * different_rating_adj
                    
                    correlation_matrix[i, j] = max(0.0, corr)
                    correlation_matrix[j, i] = correlation_matrix[i, j]
        
        return correlation_matrix
    
    def _get_rating_rank(self, rating: str) -> int:
        """Get numerical rank for rating"""
        rating_map = {
            "AAA": 1, "AA+": 2, "AA": 3, "AA-": 4,
            "A+": 5, "A": 6, "A-": 7,
            "BBB+": 8, "BBB": 9, "BBB-": 10,
            "BB+": 11, "BB": 12, "BB-": 13,
            "B+": 14, "B": 15, "B-": 16,
            "CCC": 17, "D": 18
        }
        return rating_map.get(rating, 18)
    
    def _set_randomize_seed(self) -> None:
        """Set random seed for reproducible results"""
        random.seed(12)
        np.random.seed(12)
    
    def _get_correlated_random(self) -> np.ndarray:
        """Generate correlated random numbers"""
        # Generate independent standard normal random variables
        random_vector = np.random.standard_normal(self.num_assets)
        
        # Apply correlation through Cholesky decomposition
        correlated_random = self.corr_matrix @ random_vector
        
        # Convert to uniform [0,1] using normal CDF
        uniform_random = norm.cdf(correlated_random)
        
        return uniform_random
    
    def run_rating_history(self, analysis_date: date, collateral_pool: Any,
                          deal_collateral: Optional[Dict[str, float]] = None,
                          period: str = "QUARTERLY") -> None:
        """Run rating migration simulation for a single path"""
        self.analysis_date = analysis_date
        
        # Determine period months
        month_step = self.math_utils.get_months(period)
        
        # Calculate number of periods
        if deal_collateral is None:
            last_maturity = collateral_pool.get_last_maturity_date()
        else:
            last_maturity = max(
                collateral_pool.get_asset_maturity(asset_id) 
                for asset_id in deal_collateral.keys()
            )
        
        self.num_periods = self._calculate_num_periods(analysis_date, last_maturity, month_step)
        
        # Initialize rating history
        self.rating_hist = [RatingHist() for _ in range(self.num_periods + 1)]
        self.rating_hist_bal = [RatingHistBal() for _ in range(self.num_periods + 1)]
        
        # Initialize current ratings
        current_ratings = []
        for asset_id in self.asset_order:
            if self._should_include_asset(asset_id, deal_collateral):
                if collateral_pool.is_defaulted(asset_id):
                    rating = "D"
                else:
                    rating = collateral_pool.get_sp_rating(asset_id)
                    if rating in ["CCC+", "CCC-", "CC", "C"]:
                        rating = "CCC"
                
                current_ratings.append(rating)
                self._update_rating_hist(0, rating)
            else:
                current_ratings.append(None)
        
        # Run simulation for each period
        current_date = analysis_date
        for period in range(1, self.num_periods + 1):
            correlated_random = self._get_correlated_random()
            current_date = current_date + timedelta(days=month_step * 30)  # Approximate
            
            for i, asset_id in enumerate(self.asset_order):
                if not self._should_include_asset(asset_id, deal_collateral):
                    continue
                
                if current_ratings[i] == "D":
                    # Asset already defaulted
                    continue
                elif current_ratings[i] == "M":
                    # Asset already matured
                    continue
                elif current_date > collateral_pool.get_asset_maturity(asset_id):
                    # Asset matures this period
                    current_ratings[i] = "M"
                    collateral_pool.add_sp_rating(asset_id, current_date, "M")
                else:
                    # Apply rating migration
                    previous_rating = current_ratings[i]
                    next_rating = self._get_next_rating(previous_rating, correlated_random[i])
                    
                    rating_change = (self._convert_rating_to_enum(previous_rating) - 
                                   self._convert_rating_to_enum(next_rating))
                    
                    if rating_change < 0:
                        self.rating_hist[period].downgrades += 1
                    elif rating_change > 0:
                        self.rating_hist[period].upgrades += 1
                    
                    current_ratings[i] = next_rating
                    collateral_pool.add_sp_rating(asset_id, current_date, next_rating)
                
                self._update_rating_hist(period, current_ratings[i])
            
            # Calculate period defaults
            self.rating_hist[period].num_period_defaults = (
                self.rating_hist[period].num_defaults - 
                self.rating_hist[period - 1].num_defaults
            )
        
        # Calculate balance history
        self._calc_rating_hist_bal(analysis_date, collateral_pool, deal_collateral)
        
        # Store simulation results
        if self.sim_count < len(self.sim_hist):
            self.sim_hist[self.sim_count].rating_hist = self.rating_hist.copy()
            self.sim_hist[self.sim_count].rating_hist_bal = self.rating_hist_bal.copy()
            self.sim_count += 1
    
    def _calculate_num_periods(self, start_date: date, end_date: date, month_step: int) -> int:
        """Calculate number of periods between dates"""
        current_date = start_date
        periods = 0
        
        while current_date < end_date:
            periods += 1
            current_date = self.math_utils.date_add_business("M", month_step, current_date)
        
        return periods
    
    def _should_include_asset(self, asset_id: str, deal_collateral: Optional[Dict[str, float]]) -> bool:
        """Check if asset should be included in simulation"""
        if deal_collateral is None:
            return True
        return asset_id in deal_collateral
    
    def _get_next_rating(self, current_rating: str, z_value: float) -> str:
        """Get next rating based on transition matrix and random value"""
        current_row = self._convert_rating_to_enum(current_rating) - 1  # Convert to 0-based
        
        for col in range(18):
            if self.tran_matrix[current_row, col] > z_value:
                return self._convert_rating_enum_to_str(col + 1)  # Convert back to 1-based
        
        return "D"  # Default if no threshold found
    
    def _convert_rating_to_enum(self, rating: str) -> int:
        """Convert rating string to enum value"""
        rating_map = {
            "AAA": SPRating.AAA,
            "AA+": SPRating.AA_PLUS,
            "AA": SPRating.AA,
            "AA-": SPRating.AA_MINUS,
            "A+": SPRating.A_PLUS,
            "A": SPRating.A,
            "A-": SPRating.A_MINUS,
            "BBB+": SPRating.BBB_PLUS,
            "BBB": SPRating.BBB,
            "BBB-": SPRating.BBB_MINUS,
            "BB+": SPRating.BB_PLUS,
            "BB": SPRating.BB,
            "BB-": SPRating.BB_MINUS,
            "B+": SPRating.B_PLUS,
            "B": SPRating.B,
            "B-": SPRating.B_MINUS,
            "CCC": SPRating.CCC,
            "D": SPRating.DEFAULT
        }
        return rating_map.get(rating, SPRating.DEFAULT)
    
    def _convert_rating_enum_to_str(self, rating_enum: int) -> str:
        """Convert enum value to rating string"""
        enum_map = {
            SPRating.AAA: "AAA",
            SPRating.AA_PLUS: "AA+",
            SPRating.AA: "AA",
            SPRating.AA_MINUS: "AA-",
            SPRating.A_PLUS: "A+",
            SPRating.A: "A",
            SPRating.A_MINUS: "A-",
            SPRating.BBB_PLUS: "BBB+",
            SPRating.BBB: "BBB",
            SPRating.BBB_MINUS: "BBB-",
            SPRating.BB_PLUS: "BB+",
            SPRating.BB: "BB",
            SPRating.BB_MINUS: "BB-",
            SPRating.B_PLUS: "B+",
            SPRating.B: "B",
            SPRating.B_MINUS: "B-",
            SPRating.CCC: "CCC",
            SPRating.DEFAULT: "D"
        }
        return enum_map.get(rating_enum, "D")
    
    def _update_rating_hist(self, period: int, rating: str) -> None:
        """Update rating count for specific period"""
        hist = self.rating_hist[period]
        
        rating_attr_map = {
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
            "D": "num_defaults",
            "M": "num_matures"
        }
        
        attr_name = rating_attr_map.get(rating)
        if attr_name:
            setattr(hist, attr_name, getattr(hist, attr_name) + 1)
    
    def _update_rating_hist_bal(self, period: int, rating: str, balance: float) -> None:
        """Update rating balance for specific period"""
        hist_bal = self.rating_hist_bal[period]
        
        rating_bal_map = {
            "AAA": "bal_aaa",
            "AA+": "bal_aa1",
            "AA": "bal_aa2",
            "AA-": "bal_aa3",
            "A+": "bal_a1",
            "A": "bal_a2",
            "A-": "bal_a3",
            "BBB+": "bal_bbb1",
            "BBB": "bal_bbb2",
            "BBB-": "bal_bbb3",
            "BB+": "bal_bb1",
            "BB": "bal_bb2",
            "BB-": "bal_bb3",
            "B+": "bal_b1",
            "B": "bal_b2",
            "B-": "bal_b3",
            "CCC": "bal_ccc",
            "D": "bal_defaults",
            "M": "bal_mature"
        }
        
        attr_name = rating_bal_map.get(rating)
        if attr_name:
            current_balance = getattr(hist_bal, attr_name)
            setattr(hist_bal, attr_name, current_balance + balance)
    
    def _calc_rating_hist_bal(self, analysis_date: date, collateral_pool: Any,
                             deal_collateral: Optional[Dict[str, float]] = None) -> None:
        """Calculate rating history balances"""
        month_step = self.math_utils.get_months(self.period_type)
        current_ratings = []
        asset_in_pool = []
        original_balance = 0.0
        
        # Initialize current ratings and balances
        for i, asset_id in enumerate(self.asset_order):
            if deal_collateral is None:
                asset_in_pool.append(True)
                par_amount = 1000000.0  # Default par amount
            else:
                in_pool = asset_id in deal_collateral
                asset_in_pool.append(in_pool)
                par_amount = deal_collateral.get(asset_id, 0.0) if in_pool else 0.0
            
            if asset_in_pool[i]:
                if collateral_pool.is_defaulted(asset_id):
                    rating = "D"
                else:
                    rating = collateral_pool.get_sp_rating(asset_id)
                    if rating in ["CCC+", "CCC-", "CC", "C"]:
                        rating = "CCC"
                
                current_ratings.append(rating)
                self._update_rating_hist_bal(0, rating, par_amount)
                original_balance += par_amount
            else:
                current_ratings.append(None)
        
        # Calculate balances for each period
        for period in range(1, self.num_periods + 1):
            current_date = analysis_date + timedelta(days=period * month_step * 30)
            self.rating_hist_bal[period].bal_defaults = self.rating_hist_bal[period - 1].bal_defaults
            
            for i, asset_id in enumerate(self.asset_order):
                if not asset_in_pool[i]:
                    continue
                
                balance = collateral_pool.get_beginning_balance(asset_id, current_date)
                next_rating = collateral_pool.get_sp_rating(asset_id, current_date)
                
                if next_rating == "D" and balance == 0 and current_ratings[i] != "D":
                    # Defaulted on payment date
                    balance = collateral_pool.get_beginning_balance(asset_id, current_date - timedelta(days=1))
                
                maturity_amount = collateral_pool.get_scheduled_principal(asset_id, analysis_date, current_date)
                self.rating_hist_bal[period].bal_mature += maturity_amount
                
                if current_ratings[i] not in ["D", "M"] and next_rating != "M":
                    self._update_rating_hist_bal(period, next_rating, balance)
                
                current_ratings[i] = next_rating
            
            # Calculate CDR
            remaining_balance = (original_balance - 
                               self.rating_hist_bal[period - 1].bal_mature - 
                               self.rating_hist_bal[period - 1].bal_defaults)
            
            if remaining_balance > 0:
                period_defaults = (self.rating_hist_bal[period].bal_defaults - 
                                 self.rating_hist_bal[period - 1].bal_defaults)
                self.rating_hist_bal[period].cdr = 4 * (period_defaults / remaining_balance)
            else:
                break
    
    def get_simulation_results(self) -> Dict[str, Any]:
        """Get comprehensive simulation results"""
        if not self.sim_hist:
            return {}
        
        num_sims = len(self.sim_hist)
        num_periods = len(self.sim_hist[0].rating_hist)
        
        results = {
            "num_simulations": num_sims,
            "num_periods": num_periods,
            "period_type": self.period_type,
            "analysis_date": self.analysis_date,
            "statistics": {}
        }
        
        # Calculate statistics for each metric across all simulations
        metrics = [
            "upgrades", "downgrades", "num_aaa", "num_aa_plus", "num_aa",
            "num_aa_minus", "num_a_plus", "num_a", "num_a_minus",
            "num_bbb_plus", "num_bbb", "num_bbb_minus", "num_bb_plus",
            "num_bb", "num_bb_minus", "num_b_plus", "num_b",
            "num_b_minus", "num_ccc_assets", "num_defaults", "num_matures"
        ]
        
        for period in range(num_periods):
            period_stats = {}
            
            for metric in metrics:
                values = [getattr(sim.rating_hist[period], metric) for sim in self.sim_hist]
                
                period_stats[metric] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": np.mean(values),
                    "median": np.median(values),
                    "std": np.std(values)
                }
            
            results["statistics"][f"period_{period}"] = period_stats
        
        return results
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """Export simulation results to DataFrame"""
        if not self.sim_hist:
            return pd.DataFrame()
        
        rows = []
        
        for sim_idx, sim in enumerate(self.sim_hist):
            for period_idx, (hist, hist_bal) in enumerate(zip(sim.rating_hist, sim.rating_hist_bal)):
                row = {
                    "simulation": sim_idx,
                    "period": period_idx,
                    "upgrades": hist.upgrades,
                    "downgrades": hist.downgrades,
                    "num_aaa": hist.num_aaa,
                    "bal_aaa": hist_bal.bal_aaa,
                    "num_defaults": hist.num_defaults,
                    "bal_defaults": hist_bal.bal_defaults,
                    "cdr": hist_bal.cdr
                    # Add more fields as needed
                }
                rows.append(row)
        
        return pd.DataFrame(rows)