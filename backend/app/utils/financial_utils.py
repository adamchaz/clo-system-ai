"""
Financial Utilities Module

Provides advanced financial calculation functions for CLO system including:
- Present value and yield calculations
- IRR and XIRR calculations (Excel compatible)
- Option-adjusted spread (OAS) calculations
- Z-spread calculations
- Monte Carlo simulation utilities
- Financial risk metrics

This complements math_utils.py with more sophisticated financial functions.
"""

from typing import List, Dict, Tuple, Optional, Union, Callable
from datetime import date, datetime
import numpy as np
import scipy.optimize
from scipy.stats import norm
import math
import logging
from decimal import Decimal, getcontext

from .math_utils import DayCount, MathUtils

logger = logging.getLogger(__name__)

# Set precision for financial calculations
getcontext().prec = 28

class FinancialUtils:
    """Advanced financial calculation utilities"""
    
    # IRR and XIRR Calculations
    @staticmethod
    def xirr(cashflows: List[float], dates: List[date], 
             guess: float = 0.1, max_iterations: int = 1000,
             tolerance: float = 1e-12) -> float:
        """
        Calculate XIRR (Extended Internal Rate of Return) for irregular cash flows
        
        This provides Excel Application.WorksheetFunction.Xirr compatibility
        using Newton-Raphson method as implemented in VBA.
        
        Args:
            cashflows: List of cash flow amounts
            dates: List of corresponding dates
            guess: Initial guess for IRR
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance
            
        Returns:
            XIRR as decimal (e.g., 0.15 for 15%)
        """
        if len(cashflows) != len(dates):
            raise ValueError("Cashflows and dates must have same length")
        
        if len(cashflows) < 2:
            raise ValueError("Need at least 2 cashflows for XIRR calculation")
        
        # Convert dates to Excel-style serial numbers for compatibility
        base_date = dates[0]
        days = [(d - base_date).days for d in dates]
        
        def xirr_function(rate: float) -> float:
            """XIRR objective function"""
            return sum(cf / (1 + rate) ** (day / 365.0) 
                      for cf, day in zip(cashflows, days))
        
        def xirr_derivative(rate: float) -> float:
            """Derivative of XIRR function for Newton-Raphson"""
            return sum(-cf * (day / 365.0) / (1 + rate) ** ((day / 365.0) + 1)
                      for cf, day in zip(cashflows, days))
        
        # Newton-Raphson iteration
        rate = guess
        
        for iteration in range(max_iterations):
            try:
                fx = xirr_function(rate)
                
                if abs(fx) < tolerance:
                    return rate
                
                fpx = xirr_derivative(rate)
                
                if abs(fpx) < 1e-15:
                    # Derivative too small, try different starting point
                    rate = guess * (1 + 0.01 * iteration)
                    continue
                
                new_rate = rate - fx / fpx
                
                # Bounds checking to prevent unreasonable rates
                if new_rate < -0.99:
                    new_rate = -0.99 + 0.01 * iteration / max_iterations
                elif new_rate > 10.0:
                    new_rate = 10.0 - 0.01 * iteration / max_iterations
                
                if abs(new_rate - rate) < tolerance:
                    return new_rate
                
                rate = new_rate
                
            except (ZeroDivisionError, OverflowError):
                # Try different starting point
                rate = guess * (1 + 0.1 * iteration / max_iterations)
                continue
        
        logger.warning(f"XIRR did not converge after {max_iterations} iterations")
        raise ValueError("XIRR calculation did not converge")
    
    @staticmethod
    def irr(cashflows: List[float], guess: float = 0.1) -> float:
        """
        Calculate IRR for regular periodic cashflows
        
        Args:
            cashflows: List of periodic cash flows
            guess: Initial guess
            
        Returns:
            IRR as decimal
        """
        if len(cashflows) < 2:
            raise ValueError("Need at least 2 cashflows for IRR calculation")
        
        def irr_function(rate: float) -> float:
            return sum(cf / (1 + rate) ** i for i, cf in enumerate(cashflows))
        
        try:
            result = scipy.optimize.fsolve(irr_function, guess)[0]
            
            # Verify solution
            if abs(irr_function(result)) > 1e-10:
                raise ValueError("IRR calculation did not converge to valid solution")
            
            return result
            
        except Exception as e:
            logger.error(f"IRR calculation failed: {e}")
            raise ValueError("IRR calculation failed")
    
    # Advanced Yield and Spread Calculations
    @staticmethod
    def calc_yield_to_maturity(price: float, cashflows: List[float], 
                              dates: List[date], daycount: DayCount = DayCount.US30_360,
                              frequency: int = 2) -> float:
        """
        Calculate yield to maturity using iterative method
        Enhanced version of VBA CalcYield function
        
        Args:
            price: Current price of the bond
            cashflows: List of cashflow amounts
            dates: List of dates - first date is settlement, rest are cashflow dates
            daycount: Day count convention
            frequency: Compounding frequency per year
        """
        if len(dates) != len(cashflows) + 1:
            raise ValueError("dates must have one more element than cashflows (settlement + cashflow dates)")
        
        if price <= 0:
            raise ValueError("Price must be positive")
        
        # Check if all cashflows are zero or negative
        if all(cf <= 0 for cf in cashflows):
            return 0.0
        
        def yield_objective(y: float) -> float:
            """Objective function for yield calculation"""
            # First date is settlement, rest are cashflow dates
            settlement_date = dates[0]
            cf_dates = dates[1:]
            calculated_pv = MathUtils.calc_pv(
                cashflows, cf_dates, settlement_date, y, daycount, frequency
            )
            return calculated_pv - price
        
        try:
            # Use bisection method for robustness
            low_yield = -0.5
            high_yield = 1.0
            
            # Find initial bounds
            for _ in range(50):
                if yield_objective(low_yield) * yield_objective(high_yield) < 0:
                    break
                if abs(yield_objective(low_yield)) < abs(yield_objective(high_yield)):
                    high_yield = low_yield + 0.1
                else:
                    low_yield = high_yield - 0.1
            else:
                raise ValueError("Could not find suitable bounds for yield calculation")
            
            # Bisection method
            for _ in range(1000):
                mid_yield = (low_yield + high_yield) / 2
                
                if abs(yield_objective(mid_yield)) < 1e-12:
                    return mid_yield
                
                if yield_objective(low_yield) * yield_objective(mid_yield) < 0:
                    high_yield = mid_yield
                else:
                    low_yield = mid_yield
                
                if abs(high_yield - low_yield) < 1e-12:
                    return mid_yield
            
            raise ValueError("Yield calculation did not converge")
            
        except Exception as e:
            logger.error(f"Yield calculation failed: {e}")
            raise ValueError("Yield calculation failed")
    
    @staticmethod
    def calc_z_spread(price: float, cashflows: List[float], dates: List[date],
                     spot_rates: List[float], daycount: DayCount = DayCount.US30_360,
                     frequency: int = 2) -> float:
        """
        Calculate Z-spread (zero-volatility spread)
        Enhanced version of VBA CalcZSpread function
        
        Args:
            price: Current price of the bond
            cashflows: List of cashflow amounts
            dates: List of dates - first date is settlement, rest are cashflow dates
            spot_rates: List of spot rates corresponding to cashflow dates
            daycount: Day count convention
            frequency: Compounding frequency per year
        """
        if len(dates) != len(cashflows) + 1:
            raise ValueError("dates must have one more element than cashflows (settlement + cashflow dates)")
        if len(spot_rates) != len(cashflows):
            raise ValueError("spot_rates must have same length as cashflows")
        
        def z_spread_objective(spread: float) -> float:
            """Objective function for Z-spread calculation"""
            # For now, use a simple approach with average rate + spread
            # In a more sophisticated implementation, we'd discount each cashflow with its corresponding spot rate
            avg_rate = sum(spot_rates) / len(spot_rates)
            settlement_date = dates[0]
            cf_dates = dates[1:]
            calculated_pv = MathUtils.calc_pv(
                cashflows, cf_dates, settlement_date, avg_rate + spread, daycount, frequency
            )
            return calculated_pv - price
        
        try:
            result = scipy.optimize.fsolve(z_spread_objective, 0.01)[0]
            
            # Verify solution
            if abs(z_spread_objective(result)) > 1e-6:
                logger.warning("Z-spread calculation may not have converged properly")
            
            return result
            
        except Exception as e:
            logger.error(f"Z-spread calculation failed: {e}")
            raise ValueError("Z-spread calculation failed")
    
    @staticmethod
    def calc_oas(price: float, cashflow_scenarios: Dict[int, List[float]],
                dates: List[date], rate_scenarios: Dict[int, List[float]],
                daycount: DayCount = DayCount.US30_360, frequency: int = 2) -> float:
        """
        Calculate Option-Adjusted Spread (OAS) using Monte Carlo scenarios
        Enhanced version of VBA CalcOAS function
        
        Args:
            price: Current price of the bond
            cashflow_scenarios: Dict of scenario -> cashflow list
            dates: List of dates - first date is settlement, rest are cashflow dates
            rate_scenarios: Dict of scenario -> rate list
            daycount: Day count convention
            frequency: Compounding frequency per year
        """
        num_scenarios = len(cashflow_scenarios)
        
        if num_scenarios == 0:
            raise ValueError("Need at least one scenario for OAS calculation")
        
        if len(rate_scenarios) != num_scenarios:
            raise ValueError("Number of rate scenarios must match cashflow scenarios")
        
        def oas_objective(oas: float) -> float:
            """Objective function for OAS calculation"""
            total_pv = 0.0
            settlement_date = dates[0]
            
            for scenario in range(num_scenarios):
                cashflows = cashflow_scenarios[scenario]
                rates = rate_scenarios[scenario]
                
                # Use average rate + OAS for simplicity
                avg_rate = sum(rates) / len(rates)
                cf_dates = dates[1:1+len(cashflows)]  # Slice to match cashflow length
                
                scenario_pv = MathUtils.calc_pv(
                    cashflows, cf_dates, settlement_date, avg_rate + oas, daycount, frequency
                )
                total_pv += scenario_pv
            
            avg_pv = total_pv / num_scenarios
            return avg_pv - price
        
        try:
            result = scipy.optimize.fsolve(oas_objective, 0.01)[0]
            
            # Verify solution
            if abs(oas_objective(result)) > 1e-4:
                logger.warning("OAS calculation may not have converged properly")
            
            return result
            
        except Exception as e:
            logger.error(f"OAS calculation failed: {e}")
            raise ValueError("OAS calculation failed")
    
    # Duration and Convexity
    @staticmethod
    def modified_duration(price: float, cashflows: List[float], dates: List[date],
                         yield_rate: float, daycount: DayCount = DayCount.US30_360,
                         frequency: int = 2) -> float:
        """
        Calculate modified duration
        
        Args:
            price: Current price of the bond
            cashflows: List of cashflow amounts
            dates: List of dates - first date is settlement, rest are cashflow dates
            yield_rate: Current yield
            daycount: Day count convention
            frequency: Compounding frequency per year
        """
        # Calculate price at yield + small change
        dy = 0.0001  # 1 basis point
        
        # Settlement date and cashflow dates
        settlement_date = dates[0]
        cf_dates = dates[1:]
        
        price_up = MathUtils.calc_pv(cashflows, cf_dates, settlement_date, 
                                   yield_rate + dy, daycount, frequency)
        price_down = MathUtils.calc_pv(cashflows, cf_dates, settlement_date, 
                                     yield_rate - dy, daycount, frequency)
        
        # Modified duration formula
        duration = -(price_up - price_down) / (2 * price * dy)
        return duration
    
    @staticmethod
    def macaulay_duration(cashflows: List[float], dates: List[date],
                         yield_rate: float, daycount: DayCount = DayCount.US30_360,
                         frequency: int = 2) -> float:
        """
        Calculate Macaulay duration
        
        Args:
            cashflows: List of cashflow amounts
            dates: List of dates - first date is settlement, rest are cashflow dates
            yield_rate: Current yield
            daycount: Day count convention
            frequency: Compounding frequency per year
        """
        pv_total = 0.0
        weighted_time_total = 0.0
        
        settlement_date = dates[0]
        cf_dates = dates[1:]
        
        for cf, cf_date in zip(cashflows, cf_dates):
            # Time to cash flow in years
            time_to_cf = MathUtils.year_frac(settlement_date, cf_date, daycount)
            
            # Present value of this cash flow
            pv_cf = cf / (1 + yield_rate / frequency) ** (time_to_cf * frequency)
            
            pv_total += pv_cf
            weighted_time_total += time_to_cf * pv_cf
        
        if pv_total == 0:
            return 0.0
        
        return weighted_time_total / pv_total
    
    @staticmethod
    def convexity(price: float, cashflows: List[float], dates: List[date],
                 yield_rate: float, daycount: DayCount = DayCount.US30_360,
                 frequency: int = 2) -> float:
        """
        Calculate convexity
        
        Args:
            price: Current price of the bond
            cashflows: List of cashflow amounts
            dates: List of dates - first date is settlement, rest are cashflow dates
            yield_rate: Current yield
            daycount: Day count convention
            frequency: Compounding frequency per year
        """
        dy = 0.0001  # 1 basis point
        
        # Settlement date and cashflow dates
        settlement_date = dates[0]
        cf_dates = dates[1:]
        
        price_up = MathUtils.calc_pv(cashflows, cf_dates, settlement_date, 
                                   yield_rate + dy, daycount, frequency)
        price_down = MathUtils.calc_pv(cashflows, cf_dates, settlement_date, 
                                     yield_rate - dy, daycount, frequency)
        
        # Convexity formula
        convexity_value = (price_up + price_down - 2 * price) / (price * dy ** 2)
        return convexity_value
    
    # Monte Carlo Simulation Utilities
    @staticmethod
    def generate_correlated_random_numbers(correlation_matrix: np.ndarray,
                                         num_simulations: int,
                                         random_seed: Optional[int] = None) -> np.ndarray:
        """
        Generate correlated random numbers using Cholesky decomposition
        
        Args:
            correlation_matrix: Correlation matrix (must be positive semidefinite)
            num_simulations: Number of simulation paths
            random_seed: Optional random seed for reproducibility
            
        Returns:
            Array of shape (num_simulations, num_variables) with correlated random numbers
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        num_variables = correlation_matrix.shape[0]
        
        try:
            # Cholesky decomposition
            chol = np.linalg.cholesky(correlation_matrix)
            
            # Generate independent standard normal random numbers
            independent_randoms = np.random.standard_normal((num_simulations, num_variables))
            
            # Apply correlation structure
            correlated_randoms = independent_randoms @ chol.T
            
            return correlated_randoms
            
        except np.linalg.LinAlgError:
            logger.error("Correlation matrix is not positive definite")
            raise ValueError("Correlation matrix must be positive definite")
    
    @staticmethod
    def black_scholes_option_price(spot: float, strike: float, time_to_expiry: float,
                                 risk_free_rate: float, volatility: float,
                                 option_type: str = "call") -> float:
        """
        Calculate Black-Scholes option price
        
        Args:
            spot: Current price of underlying
            strike: Strike price
            time_to_expiry: Time to expiration in years
            risk_free_rate: Risk-free interest rate
            volatility: Volatility (standard deviation of returns)
            option_type: "call" or "put"
            
        Returns:
            Option price
        """
        if time_to_expiry <= 0:
            # At expiration
            if option_type.lower() == "call":
                return max(spot - strike, 0)
            else:
                return max(strike - spot, 0)
        
        d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        if option_type.lower() == "call":
            price = spot * norm.cdf(d1) - strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
        elif option_type.lower() == "put":
            price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - spot * norm.cdf(-d1)
        else:
            raise ValueError("Option type must be 'call' or 'put'")
        
        return price
    
    # Risk Metrics
    @staticmethod
    def value_at_risk(returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR)
        
        Args:
            returns: List of returns
            confidence_level: Confidence level (e.g., 0.95 for 95% VaR)
            
        Returns:
            VaR as negative number (loss)
        """
        if not returns:
            return 0.0
        
        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        
        if index >= len(sorted_returns):
            return sorted_returns[-1]
        
        return sorted_returns[index]
    
    @staticmethod
    def conditional_value_at_risk(returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR/Expected Shortfall)
        
        Args:
            returns: List of returns
            confidence_level: Confidence level
            
        Returns:
            CVaR as negative number (expected loss beyond VaR)
        """
        if not returns:
            return 0.0
        
        var = FinancialUtils.value_at_risk(returns, confidence_level)
        tail_returns = [r for r in returns if r <= var]
        
        if not tail_returns:
            return var
        
        return sum(tail_returns) / len(tail_returns)
    
    @staticmethod
    def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio
        
        Args:
            returns: List of returns
            risk_free_rate: Risk-free rate
            
        Returns:
            Sharpe ratio
        """
        if not returns:
            return 0.0
        
        excess_returns = [r - risk_free_rate for r in returns]
        avg_excess_return = sum(excess_returns) / len(excess_returns)
        
        if len(excess_returns) < 2:
            return 0.0
        
        std_dev = MathUtils.std_array(excess_returns)
        
        if std_dev == 0:
            return 0.0
        
        return avg_excess_return / std_dev
    
    # Utility Functions
    @staticmethod
    def compound_annual_growth_rate(beginning_value: float, ending_value: float,
                                  years: float) -> float:
        """Calculate Compound Annual Growth Rate (CAGR)"""
        if beginning_value <= 0 or ending_value <= 0 or years <= 0:
            raise ValueError("Values and years must be positive")
        
        return (ending_value / beginning_value) ** (1 / years) - 1
    
    @staticmethod
    def present_value_annuity(payment: float, rate: float, periods: int) -> float:
        """Calculate present value of annuity"""
        if rate == 0:
            return payment * periods
        
        return payment * (1 - (1 + rate) ** -periods) / rate
    
    @staticmethod
    def future_value_annuity(payment: float, rate: float, periods: int) -> float:
        """Calculate future value of annuity"""
        if rate == 0:
            return payment * periods
        
        return payment * (((1 + rate) ** periods - 1) / rate)


# Module-level convenience functions
def xirr(cashflows: List[float], dates: List[date], guess: float = 0.1) -> float:
    """Convenience function for XIRR calculation"""
    return FinancialUtils.xirr(cashflows, dates, guess)

def irr(cashflows: List[float], guess: float = 0.1) -> float:
    """Convenience function for IRR calculation"""
    return FinancialUtils.irr(cashflows, guess)

def value_at_risk(returns: List[float], confidence_level: float = 0.95) -> float:
    """Convenience function for VaR calculation"""
    return FinancialUtils.value_at_risk(returns, confidence_level)

def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """Convenience function for Sharpe ratio calculation"""
    return FinancialUtils.sharpe_ratio(returns, risk_free_rate)