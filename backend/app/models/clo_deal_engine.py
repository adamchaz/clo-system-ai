"""
CLO Deal Engine - Master Orchestration Class
Converted from VBA CLODeal.cls - coordinates entire deal calculation lifecycle
"""

from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import date, datetime
from enum import Enum
from dataclasses import dataclass
import logging
from sqlalchemy.orm import Session

from .clo_deal import CLODeal
from .liability import Liability, LiabilityCalculator
from .asset import Asset
from .waterfall_types import WaterfallStep
from .dynamic_waterfall import DynamicWaterfallStrategy
from .accounts import AccountsCalculator, AccountsService, CashType as AccountsCashType
from .reinvestment import Reinvest, ReinvestmentService, ReinvestInfo as ReinvestmentModelInfo, PaymentDates as ReinvestmentPaymentDates
from .incentive_fee import IncentiveFeeStructure
from ..services.incentive_fee import IncentiveFee, IncentiveFeeService


class AccountType(str, Enum):
    """Account types for CLO deal cash management"""
    PAYMENT = "PAYMENT"
    COLLECTION = "COLLECTION"
    RAMP_UP = "RAMP_UP"
    REVOLVER_FUNDING = "REVOLVER_FUNDING"
    EXPENSE_RESERVE = "EXPENSE_RESERVE"
    CUSTODIAL = "CUSTODIAL"
    SUPPLEMENTAL_RESERVE = "SUPPLEMENTAL_RESERVE"
    INTEREST_RESERVE = "INTEREST_RESERVE"
    FUNDING_NOTE = "FUNDING_NOTE"


class CashType(str, Enum):
    """Cash flow types"""
    INTEREST = "INTEREST"
    PRINCIPAL = "PRINCIPAL"
    TOTAL = "TOTAL"


@dataclass
class PaymentDates:
    """Payment date structure for each period"""
    payment_date: date
    collection_begin_date: date
    collection_end_date: date
    interest_determination_date: date


@dataclass
class DealDates:
    """Key deal dates and parameters"""
    analysis_date: date
    closing_date: date
    first_payment_date: date
    maturity_date: date
    reinvestment_end_date: date
    no_call_date: date
    payment_day: int  # Day of month for payments
    months_between_payments: int  # 3 for quarterly
    business_day_convention: str
    determination_date_offset: int
    interest_determination_date_offset: int


@dataclass
class ReinvestmentInfo:
    """Reinvestment strategy parameters"""
    pre_reinvestment_type: str  # "ALL PRINCIPAL", "UNSCHEDULED PRINCIPAL", "NONE"
    pre_reinvestment_pct: Decimal
    post_reinvestment_type: str
    post_reinvestment_pct: Decimal


class Account:
    """
    Account for managing different cash types
    Enhanced with optional database persistence via AccountsCalculator
    """
    
    def __init__(self, account_type: AccountType, deal_id: str = None, period_date: date = None, 
                 session: Session = None, enable_persistence: bool = False):
        self.account_type = account_type
        self.interest_balance = Decimal('0')
        self.principal_balance = Decimal('0')
        
        # Enhanced database persistence support
        self.enable_persistence = enable_persistence
        self._accounts_calculator = None
        
        if enable_persistence and deal_id and period_date and session:
            self._accounts_calculator = AccountsCalculator(deal_id, period_date, session)
            # Load existing balances if available
            self.interest_balance = self._accounts_calculator.interest_proceeds
            self.principal_balance = self._accounts_calculator.principal_proceeds
    
    def add(self, cash_type: CashType, amount: Decimal) -> None:
        """Add cash to account with optional database persistence"""
        if cash_type == CashType.INTEREST:
            self.interest_balance += amount
            if self._accounts_calculator:
                self._accounts_calculator.add(AccountsCashType.INTEREST, amount)
        elif cash_type == CashType.PRINCIPAL:
            self.principal_balance += amount
            if self._accounts_calculator:
                self._accounts_calculator.add(AccountsCashType.PRINCIPAL, amount)
    
    def create_transaction_record(self, cash_type: CashType, amount: Decimal, 
                                 reference_id: str = None, description: str = None,
                                 counterparty: str = None):
        """Create detailed transaction record (requires database persistence)"""
        if self._accounts_calculator:
            accounts_cash_type = AccountsCashType.INTEREST if cash_type == CashType.INTEREST else AccountsCashType.PRINCIPAL
            return self._accounts_calculator.create_transaction(
                accounts_cash_type, amount, reference_id, description, counterparty
            )
        return None
    
    def save(self):
        """Save account state to database (if persistence enabled)"""
        if self._accounts_calculator:
            return self._accounts_calculator.save()
        return None
    
    @property
    def interest_proceeds(self) -> Decimal:
        """Get interest proceeds"""
        return self.interest_balance
    
    @property
    def principal_proceeds(self) -> Decimal:
        """Get principal proceeds"""
        return self.principal_balance
    
    @property
    def total_proceeds(self) -> Decimal:
        """Get total proceeds"""
        return self.interest_balance + self.principal_balance


class CLODealEngine:
    """
    Master CLO Deal Orchestration Engine
    Converted from VBA CLODeal.cls - coordinates entire deal lifecycle
    """
    
    def __init__(self, deal: CLODeal, session: Session, enable_account_persistence: bool = False):
        self.deal = deal
        self.session = session
        self.deal_name = deal.deal_name
        self.enable_account_persistence = enable_account_persistence
        
        # Core components (loaded via setup methods)
        self.liabilities: Dict[str, Liability] = {}
        self.liability_calculators: Dict[str, LiabilityCalculator] = {}
        self.accounts: Dict[AccountType, Account] = {}
        self.fees: Dict[str, Any] = {}  # Fee objects
        self.oc_triggers: Dict[str, Any] = {}  # OC trigger objects
        self.ic_triggers: Dict[str, Any] = {}  # IC trigger objects
        self.waterfall_strategy: Optional[DynamicWaterfallStrategy] = None
        
        # Enhanced account management with database persistence
        self.accounts_service: Optional[AccountsService] = None
        if enable_account_persistence:
            self.accounts_service = AccountsService(session)
        
        # Enhanced reinvestment management
        self.reinvestment_service: Optional[ReinvestmentService] = None
        self.reinvestment_periods: Dict[int, Reinvest] = {}  # period -> Reinvest instance
        self.enable_reinvestment = False
        
        # Enhanced incentive fee management
        self.incentive_fee_service: Optional[IncentiveFeeService] = None
        self.incentive_fee: Optional[IncentiveFee] = None
        self.enable_incentive_fee = False
        self.incentive_fee_structure_id: Optional[int] = None
        
        # Deal configuration
        self.deal_dates: Optional[DealDates] = None
        self.reinvestment_info: Optional[ReinvestmentInfo] = None
        self.clo_inputs: Dict[str, Any] = {}
        self.cf_inputs: Dict[str, Any] = {}
        self.yield_curve = None
        
        # Calculation arrays (period-indexed)
        self.payment_dates: List[PaymentDates] = []
        self.interest_proceeds: List[Decimal] = []
        self.principal_proceeds: List[Decimal] = []
        self.notes_payable: List[Decimal] = []
        self.reinvestment_amounts: List[Decimal] = []
        self.libor_rates: List[Decimal] = []
        
        # Portfolio components
        self.collateral_pool = None  # Portfolio of assets
        self.reinvestment_pool = None  # Reinvested assets
        # Note: incentive_fee is now managed via enhanced incentive fee system above
        
        # State tracking
        self.current_period = 0
        self.last_calculated_period = 0
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def setup_deal_dates(self, deal_dates: DealDates) -> None:
        """Setup deal dates and parameters"""
        self.deal_dates = deal_dates
    
    def setup_reinvestment_info(self, reinvestment_info: ReinvestmentInfo) -> None:
        """Setup reinvestment strategy"""
        self.reinvestment_info = reinvestment_info
    
    def setup_accounts(self, initial_balances: Dict[AccountType, Tuple[Decimal, Decimal]] = None, 
                      period_date: date = None) -> None:
        """Setup CLO accounts with optional initial balances and database persistence"""
        for account_type in AccountType:
            # Create account with optional database persistence
            account = Account(
                account_type,
                deal_id=self.deal.deal_id if self.enable_account_persistence else None,
                period_date=period_date if self.enable_account_persistence else None,
                session=self.session if self.enable_account_persistence else None,
                enable_persistence=self.enable_account_persistence
            )
            
            if initial_balances and account_type in initial_balances:
                interest_bal, principal_bal = initial_balances[account_type]
                account.add(CashType.INTEREST, interest_bal)
                account.add(CashType.PRINCIPAL, principal_bal)
            
            self.accounts[account_type] = account
        
        # Initialize standard account types in database if persistence is enabled
        if self.enable_account_persistence and self.accounts_service:
            self.accounts_service.initialize_account_types()
    
    def setup_reinvestment(self, enable_reinvestment: bool = True,
                          reinvestment_parameters: Dict[str, Any] = None) -> None:
        """Setup reinvestment functionality with parameters"""
        self.enable_reinvestment = enable_reinvestment
        
        if enable_reinvestment:
            self.reinvestment_service = ReinvestmentService(self.session)
            
            # Default reinvestment parameters if not provided
            if not reinvestment_parameters:
                reinvestment_parameters = {
                    'maturity_months': 60,
                    'reinvest_price': 1.0,
                    'spread': 0.05,
                    'floor': 0.01,
                    'liquidation_price': 0.70,
                    'lag_months': 6,
                    'prepayment_rate': 0.15,
                    'default_rate': 0.03,
                    'severity_rate': 0.40
                }
            
            self.reinvestment_parameters = reinvestment_parameters
    
    def create_reinvestment_period(self, period: int, reinvestment_amount: float,
                                  reinvestment_info: ReinvestmentModelInfo = None) -> Optional[Reinvest]:
        """Create reinvestment period for specified period"""
        if not self.enable_reinvestment or not self.reinvestment_service:
            return None
        
        if not self.deal_dates:
            raise RuntimeError("Deal dates must be configured before creating reinvestment periods")
        
        # Create payment dates for reinvestment
        payment_dates = self._create_reinvestment_payment_dates(period)
        
        # Use provided reinvest info or create from parameters
        if not reinvestment_info:
            params = self.reinvestment_parameters
            reinvestment_info = ReinvestmentModelInfo(
                maturity=params.get('maturity_months', 60),
                reinvest_price=params.get('reinvest_price', 1.0),
                spread=params.get('spread', 0.05),
                floor=params.get('floor', 0.01),
                liquidation=params.get('liquidation_price', 0.70),
                lag=params.get('lag_months', 6),
                prepayment=params.get('prepayment_rate', 0.15),
                default=params.get('default_rate', 0.03),
                severity=params.get('severity_rate', 0.40)
            )
        
        # Determine period dates
        period_start = self._get_period_date(period)
        period_end = self._get_period_date(period + reinvestment_info.Maturity // self.deal_dates.months_between_payments)
        
        # Create yield curve reference if available
        yield_curve = getattr(self, 'yield_curve', None)
        
        # Create reinvestment period
        reinvest = self.reinvestment_service.create_reinvestment_period(
            deal_id=self.deal.deal_id,
            period_start=period_start,
            period_end=period_end,
            reinvest_info=reinvestment_info,
            payment_dates=payment_dates,
            months_between_payments=self.deal_dates.months_between_payments,
            yield_curve=yield_curve
        )
        
        # Add reinvestment amount
        reinvest.add_reinvestment(reinvestment_amount)
        
        # Store reinvestment period
        self.reinvestment_periods[period] = reinvest
        
        return reinvest
    
    def _create_reinvestment_payment_dates(self, start_period: int) -> List[ReinvestmentPaymentDates]:
        """Create payment dates for reinvestment starting from specified period"""
        payment_dates = []
        
        # Add index 0 as None (VBA uses 1-based indexing)
        payment_dates.append(None)
        
        # Create payment dates based on deal schedule
        current_period = start_period
        for i in range(1, 50):  # Up to 50 periods for reinvestment
            period_date = self._get_period_date(current_period + i)
            if not period_date:
                break
            
            coll_beg_date = self._get_period_date(current_period + i - 1)
            coll_end_date = period_date - relativedelta(days=1) if period_date else None
            
            if period_date and coll_beg_date and coll_end_date:
                payment_dates.append(ReinvestmentPaymentDates(period_date, coll_beg_date, coll_end_date))
            
            # Stop if we reach deal maturity
            if period_date and self.deal_dates.maturity_date and period_date >= self.deal_dates.maturity_date:
                break
        
        return payment_dates
    
    def _get_period_date(self, period: int) -> Optional[date]:
        """Get payment date for specified period"""
        if not self.deal_dates:
            return None
        
        try:
            # Calculate period date based on first payment date and period
            period_date = (self.deal_dates.first_payment_date + 
                          relativedelta(months=(period - 1) * self.deal_dates.months_between_payments))
            
            # Don't go beyond maturity
            if period_date > self.deal_dates.maturity_date:
                return None
            
            return period_date
        except:
            return None
    
    def save_all_accounts(self) -> Dict[AccountType, Any]:
        """Save all accounts to database (if persistence enabled)"""
        results = {}
        for account_type, account in self.accounts.items():
            if account.enable_persistence:
                results[account_type] = account.save()
        return results
    
    def get_account_summaries(self, period_date: date) -> Dict[str, Dict]:
        """Get account summaries for reporting"""
        summaries = {}
        for account_type, account in self.accounts.items():
            summaries[account_type.value] = {
                'account_type': account_type.value,
                'interest_proceeds': float(account.interest_proceeds),
                'principal_proceeds': float(account.principal_proceeds), 
                'total_proceeds': float(account.total_proceeds)
            }
        return summaries
    
    def setup_liabilities(self, liabilities: Dict[str, Liability]) -> None:
        """Setup liability dictionary and calculators"""
        self.liabilities = liabilities
        # Initialize calculators when payment dates are calculated
    
    def setup_waterfall_strategy(self, waterfall_strategy: DynamicWaterfallStrategy) -> None:
        """Setup waterfall calculation strategy"""
        self.waterfall_strategy = waterfall_strategy
    
    def setup_inputs(self, clo_inputs: Dict[str, Any], cf_inputs: Dict[str, Any]) -> None:
        """Setup calculation inputs"""
        self.clo_inputs = clo_inputs
        self.cf_inputs = cf_inputs
    
    def calculate_payment_dates(self) -> None:
        """
        Calculate payment dates for deal lifecycle
        Converted from VBA CalcPaymentDates()
        """
        if not self.deal_dates:
            raise ValueError("Deal dates must be set before calculating payment dates")
        
        # Calculate first payment date
        first_pay_date = date(
            self.deal_dates.first_payment_date.year,
            self.deal_dates.first_payment_date.month,
            self.deal_dates.payment_day
        )
        
        # Calculate number of periods
        months_diff = self._months_between_dates(first_pay_date, self.deal_dates.maturity_date)
        num_periods = months_diff // self.deal_dates.months_between_payments + 5  # Buffer periods
        
        self.payment_dates = []
        current_payment_date = first_pay_date
        previous_payment_date = None
        period_counter = 1
        
        while current_payment_date <= self.deal_dates.maturity_date:
            if current_payment_date > self.deal_dates.analysis_date:
                
                # Calculate collection dates
                if current_payment_date == first_pay_date:
                    collection_begin_date = self.deal_dates.closing_date
                    interest_determination_date = self.deal_dates.closing_date
                else:
                    if period_counter == 1 and previous_payment_date:
                        # Handle first period after analysis date
                        prev_payment = self._adjust_for_business_day(
                            previous_payment_date, self.deal_dates.business_day_convention
                        )
                    
                    collection_begin_date = self.payment_dates[-1].collection_end_date if self.payment_dates else self.deal_dates.closing_date
                    interest_determination_date = self._get_previous_business_date(
                        self.payment_dates[-1].payment_date if self.payment_dates else current_payment_date,
                        self.deal_dates.interest_determination_date_offset
                    )
                
                # Adjust payment date for business days
                adjusted_payment_date = self._adjust_for_business_day(
                    current_payment_date, self.deal_dates.business_day_convention
                )
                
                collection_end_date = self._get_previous_business_date(
                    adjusted_payment_date, self.deal_dates.determination_date_offset
                )
                
                payment_period = PaymentDates(
                    payment_date=adjusted_payment_date,
                    collection_begin_date=collection_begin_date,
                    collection_end_date=collection_end_date,
                    interest_determination_date=interest_determination_date
                )
                
                self.payment_dates.append(payment_period)
                period_counter += 1
            
            previous_payment_date = current_payment_date
            current_payment_date = self._add_months(
                first_pay_date, 
                (len(self.payment_dates) + (1 if current_payment_date <= self.deal_dates.analysis_date else 0)) * self.deal_dates.months_between_payments
            )
        
        self.logger.info(f"Calculated {len(self.payment_dates)} payment periods")
    
    def deal_setup(self) -> None:
        """
        Initialize all deal components for calculation
        Converted from VBA DealSetup()
        """
        if not self.payment_dates:
            raise ValueError("Payment dates must be calculated before deal setup")
        
        num_periods = len(self.payment_dates)
        
        # Initialize calculation arrays
        self.interest_proceeds = [Decimal('0')] * (num_periods + 1)
        self.principal_proceeds = [Decimal('0')] * (num_periods + 1)
        self.notes_payable = [Decimal('0')] * (num_periods + 1)
        self.reinvestment_amounts = [Decimal('0')] * (num_periods + 1)
        self.libor_rates = [Decimal('0')] * (num_periods + 1)
        
        # Setup liability calculators
        for name, liability in self.liabilities.items():
            calculator = LiabilityCalculator(liability, [pd.payment_date for pd in self.payment_dates])
            self.liability_calculators[name] = calculator
        
        # Setup fees (placeholder - would setup fee objects)
        for fee_name in ["TRUSTEE_FEE", "ADMIN_FEE", "BASE_MANAGER_FEE", "JUNIOR_MANAGER_FEE"]:
            # TODO: Setup fee objects when Fee class is implemented
            pass
        
        # Setup OC/IC triggers (placeholder)
        for trigger_name in ["CLASS_B_OC_TEST", "CLASS_C_OC_TEST", "CLASS_D_OC_TEST", "EVENT_OF_DEFAULT"]:
            # TODO: Setup trigger objects when implemented
            pass
        
        # Setup waterfall strategy
        if self.waterfall_strategy:
            self.waterfall_strategy.setup_deal(
                payment_dates=self.payment_dates,
                liabilities=self.liabilities,
                # Additional waterfall setup parameters
            )
        
        # Move ramp-up account funds to collection account
        if AccountType.RAMP_UP in self.accounts:
            ramp_up_amount = self.accounts[AccountType.RAMP_UP].principal_proceeds
            self.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, ramp_up_amount)
            self.accounts[AccountType.RAMP_UP].add(CashType.PRINCIPAL, -ramp_up_amount)
        
        self.logger.info("Deal setup completed successfully")
    
    def execute_deal_calculation(self) -> None:
        """
        Main deal calculation method
        Converted from VBA Calc2()
        """
        self.logger.info("Starting deal calculation")
        
        # Setup deal
        self.calculate_payment_dates()
        self.deal_setup()
        
        # Setup waterfall strategy
        if self.waterfall_strategy:
            self.waterfall_strategy.setup_waterfall_execution(
                self.payment_dates,
                self.liabilities,
                self.oc_triggers,
                self.ic_triggers,
                self.fees,
                self.incentive_fee  # This will be None if not enabled, or the IncentiveFee instance
            )
        
        liquidate_flag = False
        
        # Process each period
        for period in range(1, len(self.payment_dates) + 1):
            self.current_period = period
            
            # Calculate period cash flows and metrics
            self.calculate_period(period, liquidate_flag)
            
            # Execute waterfall payments
            if self._is_event_of_default() or self._oc_event_of_default_triggered():
                # Event of Default waterfall
                self._execute_eod_waterfall(period)
            else:
                # Normal waterfall
                self._execute_interest_waterfall(period)
                
                # Calculate reinvestment amount
                max_reinvestment = self._calculate_reinvestment_amount(period, liquidate_flag)
                
                self._execute_principal_waterfall(period, max_reinvestment)
                self._execute_note_payment_sequence(period)
                
                # Add reinvestments to pool
                if self.reinvestment_amounts[period] > 0:
                    self._add_reinvestment(self.reinvestment_amounts[period])
            
            # Check liquidation triggers
            if self._check_liquidation_triggers(period):
                liquidate_flag = True
            
            # Check if portfolio is exhausted
            if self._portfolio_exhausted():
                self.last_calculated_period = period
                self._roll_forward_all_components()
                break
            else:
                self._roll_forward_all_components()
        
        self.logger.info(f"Deal calculation completed. Last period: {self.last_calculated_period}")
    
    def calculate_period(self, period: int, liquidate: bool = False) -> None:
        """
        Calculate period-specific metrics and cash flows
        Converted from VBA CalcPeriod2()
        """
        # Get period dates
        last_payment_date = (
            self.payment_dates[period - 2].payment_date if period > 1 
            else self.deal_dates.closing_date
        )
        next_payment_date = self.payment_dates[period - 1].payment_date
        collection_begin_date = self.payment_dates[period - 1].collection_begin_date
        collection_end_date = self.payment_dates[period - 1].collection_end_date
        
        # Determine LIBOR rate
        if period == 1:
            libor_rate = Decimal(str(self.clo_inputs.get("Current LIBOR", 0.05)))
        else:
            # Get rate from yield curve
            int_determination_date = self.payment_dates[period - 1].interest_determination_date
            libor_rate = self._get_libor_rate(int_determination_date)
        
        self.libor_rates[period] = libor_rate
        
        # Add collateral cash flows to collection account
        interest_collections = self._get_collateral_interest_proceeds()
        principal_collections = self._get_collateral_principal_proceeds()
        
        self.accounts[AccountType.COLLECTION].add(CashType.INTEREST, interest_collections)
        self.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, principal_collections)
        
        # Create detailed transaction records if persistence is enabled
        if self.enable_account_persistence and interest_collections > 0:
            self.accounts[AccountType.COLLECTION].create_transaction_record(
                CashType.INTEREST, interest_collections,
                reference_id=f"PERIOD_{period}_COLLECTIONS",
                description=f"Interest collections for period {period}",
                counterparty="Collateral Portfolio"
            )
        
        if self.enable_account_persistence and principal_collections > 0:
            self.accounts[AccountType.COLLECTION].create_transaction_record(
                CashType.PRINCIPAL, principal_collections,
                reference_id=f"PERIOD_{period}_COLLECTIONS", 
                description=f"Principal collections for period {period}",
                counterparty="Collateral Portfolio"
            )
        
        # Handle purchase finance accrued interest
        self._handle_purchase_finance_accrued_interest()
        
        # Calculate liability interest accruals
        for name, calculator in self.liability_calculators.items():
            calculator.calculate_period(period, libor_rate, last_payment_date, next_payment_date)
        
        # Extract proceeds for waterfall
        interest_withdrawal = self.accounts[AccountType.COLLECTION].interest_proceeds
        self.accounts[AccountType.COLLECTION].add(CashType.INTEREST, -interest_withdrawal)
        
        principal_withdrawal = self.accounts[AccountType.COLLECTION].principal_proceeds  
        self.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, -principal_withdrawal)
        
        # Add interest reserve proceeds to interest
        interest_reserve_withdrawal = self.accounts[AccountType.INTEREST_RESERVE].principal_proceeds
        self.accounts[AccountType.INTEREST_RESERVE].add(CashType.PRINCIPAL, -interest_reserve_withdrawal)
        interest_withdrawal += interest_reserve_withdrawal
        
        # Store period proceeds
        self.interest_proceeds[period] = interest_withdrawal
        self.principal_proceeds[period] = principal_withdrawal
        
        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics()
        
        # Calculate fee basis
        fee_basis = (
            portfolio_metrics['total_principal_balance'] + 
            principal_withdrawal + 
            Decimal(str(self.clo_inputs.get("Purchase Finance Accrued Interest", 0)))
        )
        
        # Calculate fees
        for fee_name, fee_calc in self.fees.items():
            # fee_calc.calculate(last_payment_date, next_payment_date, fee_basis, libor_rate)
            pass
        
        # Calculate OC/IC test numerators
        oc_test_numerator = (
            portfolio_metrics['principal_ex_defaults'] +
            portfolio_metrics['mv_defaults'] -
            portfolio_metrics['ccc_adjustment'] +
            principal_withdrawal +
            Decimal(str(self.clo_inputs.get("Purchase Finance Accrued Interest", 0)))
        )
        
        ic_test_numerator = interest_withdrawal
        eod_numerator = portfolio_metrics['principal_ex_defaults'] + portfolio_metrics['mv_defaults'] + principal_withdrawal
        
        # Update waterfall with period calculations
        if self.waterfall_strategy:
            self.waterfall_strategy.calculate_period(
                period, ic_test_numerator, oc_test_numerator, eod_numerator
            )
        
        # Handle liquidation
        # Handle liquidation including reinvestment portfolios
        if liquidate:
            liquidation_proceeds = self._liquidate_portfolio()
            self.principal_proceeds[period] += liquidation_proceeds
            
            # Liquidate any active reinvestment periods
            reinvestment_liquidation_proceeds = self._liquidate_reinvestment_portfolios()
            self.principal_proceeds[period] += reinvestment_liquidation_proceeds
        
        # Process reinvestment periods
        self._process_reinvestment_periods(period)
        
        # Save account states to database if persistence is enabled
        if self.enable_account_persistence:
            self.save_all_accounts()
    
    def _process_reinvestment_periods(self, period: int) -> None:
        """Process active reinvestment periods for the current period"""
        if not self.enable_reinvestment:
            return
        
        reinvestment_proceeds = {"INTEREST": 0.0, "PRINCIPAL": 0.0}
        
        # Process existing reinvestment periods
        for reinvest_period, reinvest in self.reinvestment_periods.items():
            if reinvest_period <= period:
                # Get proceeds from this reinvestment period
                interest_proceeds = reinvest.get_proceeds("INTEREST")
                principal_proceeds = reinvest.get_proceeds("PRINCIPAL")
                
                reinvestment_proceeds["INTEREST"] += interest_proceeds
                reinvestment_proceeds["PRINCIPAL"] += principal_proceeds
                
                # Roll forward the reinvestment period
                reinvest.roll_forward()
        
        # Add reinvestment proceeds to deal accounts
        if reinvestment_proceeds["INTEREST"] > 0:
            self.accounts[AccountType.COLLECTION].add(CashType.INTEREST, Decimal(str(reinvestment_proceeds["INTEREST"])))
            
            if self.enable_account_persistence:
                self.accounts[AccountType.COLLECTION].create_transaction_record(
                    CashType.INTEREST, Decimal(str(reinvestment_proceeds["INTEREST"])),
                    reference_id=f"REINVEST_PERIOD_{period}",
                    description=f"Reinvestment interest proceeds for period {period}",
                    counterparty="Reinvestment Portfolio"
                )
        
        if reinvestment_proceeds["PRINCIPAL"] > 0:
            self.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, Decimal(str(reinvestment_proceeds["PRINCIPAL"])))
            
            if self.enable_account_persistence:
                self.accounts[AccountType.COLLECTION].create_transaction_record(
                    CashType.PRINCIPAL, Decimal(str(reinvestment_proceeds["PRINCIPAL"])),
                    reference_id=f"REINVEST_PERIOD_{period}",
                    description=f"Reinvestment principal proceeds for period {period}",
                    counterparty="Reinvestment Portfolio"
                )
        
        # Check for new reinvestment opportunities
        available_principal = self._calculate_available_reinvestment_principal(period)
        if available_principal > 0:
            self._handle_reinvestment_opportunities(period, available_principal)
    
    def _calculate_available_reinvestment_principal(self, period: int) -> float:
        """Calculate principal available for reinvestment"""
        if not self.enable_reinvestment or not self.reinvestment_info:
            return 0.0
        
        # Get principal collections for the period
        principal_collections = float(self.principal_proceeds.get(period, Decimal('0')))
        
        # Apply reinvestment strategy
        if self._is_reinvestment_period(period):
            # During reinvestment period
            reinvest_type = self.reinvestment_info.pre_reinvestment_type
            reinvest_pct = float(self.reinvestment_info.pre_reinvestment_pct)
        else:
            # After reinvestment period
            reinvest_type = self.reinvestment_info.post_reinvestment_type
            reinvest_pct = float(self.reinvestment_info.post_reinvestment_pct)
        
        if reinvest_type == "NONE":
            return 0.0
        elif reinvest_type == "ALL PRINCIPAL":
            return principal_collections * reinvest_pct
        elif reinvest_type == "UNSCHEDULED PRINCIPAL":
            # Calculate unscheduled principal (prepayments)
            unscheduled_principal = self._calculate_unscheduled_principal(period)
            return unscheduled_principal * reinvest_pct
        
        return 0.0
    
    def _handle_reinvestment_opportunities(self, period: int, available_amount: float) -> None:
        """Handle reinvestment of available principal"""
        if available_amount <= 0:
            return
        
        # Create reinvestment period if amount is significant
        minimum_reinvestment = 100000.0  # $100k minimum
        if available_amount >= minimum_reinvestment:
            reinvest = self.create_reinvestment_period(period, available_amount)
            
            if reinvest and self.enable_account_persistence:
                # Record reinvestment transaction
                self.accounts[AccountType.COLLECTION].create_transaction_record(
                    CashType.PRINCIPAL, -Decimal(str(available_amount)),
                    reference_id=f"REINVEST_CREATE_{period}",
                    description=f"Principal reinvestment in period {period}",
                    counterparty="Reinvestment Portfolio"
                )
    
    def _liquidate_reinvestment_portfolios(self) -> Decimal:
        """Liquidate all active reinvestment portfolios"""
        total_proceeds = Decimal('0')
        
        if not self.enable_reinvestment:
            return total_proceeds
        
        for reinvest_period, reinvest in self.reinvestment_periods.items():
            # Use default liquidation price from reinvestment parameters
            liquidation_price = self.reinvestment_parameters.get('liquidation_price', 0.70)
            proceeds = reinvest.liquidate(liquidation_price)
            total_proceeds += Decimal(str(proceeds))
        
        return total_proceeds
    
    def _is_reinvestment_period(self, period: int) -> bool:
        """Check if we're still in the reinvestment period"""
        if not self.deal_dates:
            return False
        
        period_date = self._get_period_date(period)
        if not period_date:
            return False
        
        return period_date <= self.deal_dates.reinvestment_end_date
    
    def _calculate_unscheduled_principal(self, period: int) -> float:
        """Calculate unscheduled principal (prepayments) for the period"""
        total_unscheduled = 0.0
        
        # Sum unscheduled principal from all assets
        for asset in self.assets_dict.values():
            if hasattr(asset, 'unscheduled_principal_amount'):
                unscheduled = getattr(asset, 'unscheduled_principal_amount', 0.0)
                if isinstance(unscheduled, (int, float)):
                    total_unscheduled += unscheduled
                elif isinstance(unscheduled, Decimal):
                    total_unscheduled += float(unscheduled)
        
        return total_unscheduled
    
    def get_reinvestment_summary(self) -> Dict[str, Any]:
        """Get comprehensive reinvestment summary"""
        summary = {
            'reinvestment_enabled': self.enable_reinvestment,
            'active_periods': len(self.reinvestment_periods),
            'total_reinvested_amount': 0.0,
            'total_current_balance': 0.0,
            'periods': []
        }
        
        if not self.enable_reinvestment:
            return summary
        
        for period, reinvest in self.reinvestment_periods.items():
            # Get reinvestment cash flows
            cash_flows = reinvest.get_collat_cf()
            
            period_summary = {
                'period': period,
                'reinvest_id': getattr(reinvest, 'reinvest_id', None),
                'last_period': reinvest.last_period,
                'current_balances': {
                    'performing': float(reinvest.prin_ball_ex_defaults()),
                    'defaults': float(reinvest.prin_ball_defaults()),
                    'mv_defaults': float(reinvest.mv_defaults())
                }
            }
            
            # Calculate totals
            if len(cash_flows) > 1:  # Skip header row
                total_reinvested = sum(row[0] for row in cash_flows[1:] if len(row) > 0 and isinstance(row[0], (int, float)))
                summary['total_reinvested_amount'] += total_reinvested
            
            summary['total_current_balance'] += period_summary['current_balances']['performing']
            summary['periods'].append(period_summary)
        
        return summary
    
    def calculate_reinvestment_amount(self, period: int, liquidate: bool = False) -> Decimal:
        """
        Calculate reinvestment amount for period
        Converted from VBA CalcReinvestAmount()
        """
        if not self.reinvestment_info:
            return Decimal('0')
        
        # Determine reinvestment type and percentage
        payment_date = self.payment_dates[period - 1].payment_date
        
        if liquidate:
            reinvest_type = "NONE"
            reinvest_pct = Decimal('0')
        elif payment_date <= self.deal_dates.reinvestment_end_date:
            reinvest_type = self.reinvestment_info.pre_reinvestment_type
            reinvest_pct = self.reinvestment_info.pre_reinvestment_pct
        elif payment_date < self.deal_dates.maturity_date:
            reinvest_type = self.reinvestment_info.post_reinvestment_type
            reinvest_pct = self.reinvestment_info.post_reinvestment_pct
        else:
            reinvest_type = "NONE"
            reinvest_pct = Decimal('0')
        
        # Calculate base reinvestment amount
        if reinvest_type.upper() == "ALL PRINCIPAL":
            base_amount = self.principal_proceeds[period]
        elif reinvest_type.upper() == "UNSCHEDULED PRINCIPAL":
            base_amount = self._get_unscheduled_principal_proceeds()
        else:
            base_amount = Decimal('0')
        
        return base_amount * reinvest_pct
    
    def generate_deal_output(self) -> List[List[Any]]:
        """
        Generate deal output report
        Converted from VBA DealOutputs()
        """
        output = []
        
        # Header row
        output.append([
            "Period", "Payment Date", "Collection Begin Date", "Collection End Date",
            "Interest Proceeds", "Principal Proceeds", "Payment of Principal", 
            "Proceeds Reinvested", "LIBOR"
        ])
        
        # Data rows
        for period in range(1, self.last_calculated_period + 1):
            period_data = self.payment_dates[period - 1]
            output.append([
                period,
                period_data.payment_date,
                period_data.collection_begin_date,
                period_data.collection_end_date,
                float(self.interest_proceeds[period]),
                float(self.principal_proceeds[period]),
                float(self.notes_payable[period]),
                float(self.reinvestment_amounts[period]),
                f"{self.libor_rates[period]:.5%}"
            ])
        
        return output
    
    def calculate_risk_measures(self) -> None:
        """
        Calculate risk measures for all liabilities
        Converted from VBA CalcRiskMeasures()
        """
        for name, liability in self.liabilities.items():
            calculator = self.liability_calculators[name]
            risk_measures = calculator.calculate_risk_measures(
                self.yield_curve, 
                self.clo_inputs.get("Analysis Date", date.today())
            )
            
            # Update liability with calculated risk measures
            if risk_measures:
                liability.calculated_yield = risk_measures.get('calculated_yield')
                liability.calculated_dm = risk_measures.get('calculated_dm')
                liability.calculated_price = risk_measures.get('calculated_price')
                liability.weighted_average_life = risk_measures.get('weighted_average_life')
                liability.macaulay_duration = risk_measures.get('macaulay_duration')
                liability.modified_duration = risk_measures.get('modified_duration')
    
    # Private helper methods
    def _months_between_dates(self, start_date: date, end_date: date) -> int:
        """Calculate months between dates"""
        return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
    
    def _add_months(self, base_date: date, months: int) -> date:
        """Add months to date"""
        year = base_date.year + (base_date.month + months - 1) // 12
        month = (base_date.month + months - 1) % 12 + 1
        day = min(base_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)
    
    def _adjust_for_business_day(self, date_to_adjust: date, convention: str) -> date:
        """Adjust date for business day convention"""
        # Simplified - production would use proper business day calendar
        return date_to_adjust
    
    def _get_previous_business_date(self, reference_date: date, offset_days: int) -> date:
        """Get previous business date with offset"""
        # Simplified - production would use proper business day calendar
        from datetime import timedelta
        return reference_date - timedelta(days=offset_days)
    
    def _get_libor_rate(self, determination_date: date) -> Decimal:
        """Get LIBOR rate from yield curve"""
        # Simplified - would use actual yield curve
        return Decimal('0.05')  # 5% default
    
    def _get_collateral_interest_proceeds(self) -> Decimal:
        """Get interest proceeds from collateral pool"""
        # TODO: Implement when CollateralPool is available
        return Decimal('0')
    
    def _get_collateral_principal_proceeds(self) -> Decimal:
        """Get principal proceeds from collateral pool"""
        # TODO: Implement when CollateralPool is available
        return Decimal('0')
    
    def _handle_purchase_finance_accrued_interest(self) -> None:
        """Handle purchase finance accrued interest adjustment"""
        accrued_interest = Decimal(str(self.clo_inputs.get("Purchase Finance Accrued Interest", 0)))
        
        if accrued_interest > 0:
            available_interest = self.accounts[AccountType.COLLECTION].interest_proceeds
            
            if available_interest >= accrued_interest:
                self.accounts[AccountType.COLLECTION].add(CashType.INTEREST, -accrued_interest)
                self.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, accrued_interest)
                self.clo_inputs["Purchase Finance Accrued Interest"] = 0
            else:
                self.accounts[AccountType.COLLECTION].add(CashType.INTEREST, -available_interest)
                self.accounts[AccountType.COLLECTION].add(CashType.PRINCIPAL, available_interest)
                self.clo_inputs["Purchase Finance Accrued Interest"] = float(accrued_interest - available_interest)
    
    def _calculate_portfolio_metrics(self) -> Dict[str, Decimal]:
        """Calculate key portfolio metrics"""
        # TODO: Implement when portfolio components are available
        return {
            'total_principal_balance': Decimal('0'),
            'principal_ex_defaults': Decimal('0'), 
            'principal_defaults': Decimal('0'),
            'mv_defaults': Decimal('0'),
            'ccc_adjustment': Decimal('0')
        }
    
    def _is_event_of_default(self) -> bool:
        """Check if Event of Default is triggered"""
        return self.clo_inputs.get("Event of Default", False)
    
    def _oc_event_of_default_triggered(self) -> bool:
        """Check if OC Event of Default trigger is breached"""
        # TODO: Check actual OC trigger when implemented
        return False
    
    def _execute_interest_waterfall(self, period: int) -> None:
        """Execute interest waterfall payments"""
        if self.waterfall_strategy:
            self.waterfall_strategy.execute_interest_waterfall(
                period, self.interest_proceeds[period], self.principal_proceeds[period]
            )
    
    def _execute_principal_waterfall(self, period: int, max_reinvestment: Decimal) -> None:
        """Execute principal waterfall payments"""
        if self.waterfall_strategy:
            reinvestment_actual = Decimal('0')  # Placeholder
            self.waterfall_strategy.execute_principal_waterfall(
                period, self.principal_proceeds[period], max_reinvestment, 
                reinvestment_actual, self.notes_payable[period]
            )
            self.reinvestment_amounts[period] = reinvestment_actual
    
    def _execute_note_payment_sequence(self, period: int) -> None:
        """Execute note payment sequence"""
        if self.waterfall_strategy:
            self.waterfall_strategy.execute_note_payment_sequence(
                period, self.notes_payable[period]
            )
    
    def _execute_eod_waterfall(self, period: int) -> None:
        """Execute Event of Default waterfall"""
        if self.waterfall_strategy:
            self.waterfall_strategy.execute_eod_waterfall(
                period, self.interest_proceeds[period], self.principal_proceeds[period]
            )
    
    def _calculate_reinvestment_amount(self, period: int, liquidate: bool) -> Decimal:
        """Calculate maximum reinvestment amount"""
        return self.calculate_reinvestment_amount(period, liquidate)
    
    def _add_reinvestment(self, amount: Decimal) -> None:
        """Add reinvestment to reinvestment pool"""
        # TODO: Implement when reinvestment pool is available
        pass
    
    def _check_liquidation_triggers(self, period: int) -> bool:
        """Check if liquidation should be triggered"""
        # Check subordinated distribution trigger
        if "Sub Notes" in self.liabilities:
            sub_notes = self.liabilities["Sub Notes"]
            # calculator = self.liability_calculators["Sub Notes"]
            # current_distribution_pct = calculator.get_current_distribution_percentage(period)
            # call_threshold = Decimal(str(self.cf_inputs.get("Call when Quarterly Sub Dist <", 0)))
            
            # if current_distribution_pct < call_threshold and period < len(self.payment_dates):
            #     next_payment_date = self.payment_dates[period].payment_date
            #     if next_payment_date >= self.deal_dates.no_call_date:
            #         return True
        
        # Check if approaching maturity
        if period == len(self.payment_dates) - 1:
            return True
        
        return False
    
    def _portfolio_exhausted(self) -> bool:
        """Check if portfolio is exhausted"""
        # TODO: Check actual portfolio balances
        return False
    
    def _liquidate_portfolio(self) -> Decimal:
        """Liquidate entire portfolio"""
        # TODO: Implement portfolio liquidation
        return Decimal('0')
    
    def _get_unscheduled_principal_proceeds(self) -> Decimal:
        """Get unscheduled principal proceeds"""
        # TODO: Implement when portfolio components available
        return Decimal('0')
    
    def _roll_forward_all_components(self) -> None:
        """Roll forward all deal components to next period"""
        # Roll forward liabilities
        for calculator in self.liability_calculators.values():
            calculator.roll_forward(self.current_period)
        
        # Roll forward incentive fee
        if self.enable_incentive_fee and self.incentive_fee:
            # Incentive fee rollforward is handled within waterfall execution
            pass
        
        # Roll forward fees, triggers, etc.
        # TODO: Implement when components are available
    
    # ========================================
    # INCENTIVE FEE MANAGEMENT METHODS
    # ========================================
    
    def setup_incentive_fee(
        self,
        enable: bool = True,
        hurdle_rate: float = 0.08,
        incentive_fee_rate: float = 0.20,
        fee_structure_name: str = "Manager Incentive Fee",
        subordinated_payments: Optional[Dict[date, float]] = None
    ) -> None:
        """
        Setup incentive fee system for the CLO deal
        
        Args:
            enable: Enable/disable incentive fee calculations
            hurdle_rate: IRR hurdle rate (e.g., 0.08 for 8%)
            incentive_fee_rate: Fee rate above hurdle (e.g., 0.20 for 20%)
            fee_structure_name: Name for the fee structure
            subordinated_payments: Historical subordinated payments {date: amount}
        """
        self.enable_incentive_fee = enable
        
        if not enable:
            self.incentive_fee_service = None
            self.incentive_fee = None
            self.incentive_fee_structure_id = None
            return
        
        # Initialize incentive fee service
        self.incentive_fee_service = IncentiveFeeService(self.session)
        
        # Create or load fee structure
        self.incentive_fee = IncentiveFee(self.session)
        
        # Setup subordinated payments (use empty dict if none provided)
        if subordinated_payments is None:
            subordinated_payments = {}
        
        # Setup incentive fee with VBA equivalent parameters
        self.incentive_fee.setup(
            i_fee_threshold=hurdle_rate,
            i_incentive_fee=incentive_fee_rate,
            i_payto_sub_notholder=subordinated_payments
        )
        
        # Perform deal setup when we have deal dates
        if self.deal_dates:
            self._setup_incentive_fee_deal_parameters(fee_structure_name)
        
        self.logger.info(f"Incentive fee system initialized: {hurdle_rate:.1%} hurdle, {incentive_fee_rate:.1%} fee")
    
    def _setup_incentive_fee_deal_parameters(self, fee_structure_name: str) -> None:
        """Setup incentive fee deal parameters when deal dates are available"""
        if not self.enable_incentive_fee or not self.incentive_fee:
            return
        
        if not self.deal_dates:
            raise RuntimeError("Deal dates must be configured before setting up incentive fee")
        
        # Calculate estimated number of payments
        num_payments = len(self.payment_dates) if self.payment_dates else self._estimate_payment_periods()
        
        # VBA DealSetup equivalent
        self.incentive_fee.deal_setup(
            i_num_of_payments=num_payments,
            i_close_date=self.deal_dates.closing_date,
            i_analysis_date=self.deal_dates.analysis_date
        )
        
        # Save to database for persistence
        self.incentive_fee_structure_id = self.incentive_fee.save_to_database(
            self.deal.deal_id,
            fee_structure_name
        )
    
    def _estimate_payment_periods(self) -> int:
        """Estimate number of payment periods based on deal dates"""
        if not self.deal_dates:
            return 60  # Default to 60 periods (15 years quarterly)
        
        # Calculate periods from closing to maturity
        months_total = (
            (self.deal_dates.maturity_date - self.deal_dates.closing_date).days / 365.25 * 12
        )
        periods = int(months_total / self.deal_dates.months_between_payments) + 1
        
        return max(periods, 1)
    
    def load_incentive_fee_structure(self, fee_structure_id: int) -> None:
        """
        Load existing incentive fee structure from database
        
        Args:
            fee_structure_id: Database ID of existing fee structure
        """
        self.enable_incentive_fee = True
        self.incentive_fee_service = IncentiveFeeService(self.session)
        self.incentive_fee_structure_id = fee_structure_id
        
        # Load from database
        self.incentive_fee = IncentiveFee.load_from_database(self.session, fee_structure_id)
        
        self.logger.info(f"Loaded incentive fee structure {fee_structure_id}")
    
    def process_incentive_fee_for_period(self, period: int) -> None:
        """
        Process incentive fee calculations for a specific period
        
        This method should be called during the waterfall execution to handle
        subordinated payments and fee calculations.
        
        Args:
            period: Current calculation period
        """
        if not self.enable_incentive_fee or not self.incentive_fee:
            return
        
        # Get period date
        period_date = self._get_period_date(period)
        if not period_date:
            return
        
        # VBA Calc() equivalent
        self.incentive_fee.calc(period_date)
        
        # This is where subordinated payments would be recorded
        # The actual payment amount comes from the waterfall execution
        # For now, we setup the calculation framework
        
        self.logger.debug(f"Processed incentive fee calculation for period {period}")
    
    def record_subordinated_payment(self, period: int, payment_amount: float) -> float:
        """
        Record subordinated noteholder payment and calculate incentive fee
        
        Args:
            period: Current period
            payment_amount: Payment amount to subordinated noteholders
            
        Returns:
            Net payment amount after incentive fee deduction
        """
        if not self.enable_incentive_fee or not self.incentive_fee:
            return payment_amount
        
        # VBA PaymentToSubNotholder() equivalent
        self.incentive_fee.payment_to_sub_notholder(payment_amount)
        
        # Calculate and deduct incentive fee if applicable
        # VBA PayIncentiveFee() equivalent
        net_payment = self.incentive_fee.pay_incentive_fee(payment_amount)
        
        # Log fee calculation
        if net_payment < payment_amount:
            fee_amount = payment_amount - net_payment
            self.logger.info(f"Period {period}: Incentive fee ${fee_amount:,.2f} on ${payment_amount:,.2f} payment")
        
        return net_payment
    
    def finalize_incentive_fee_period(self, period: int) -> None:
        """
        Finalize incentive fee calculations for the period
        
        This should be called at the end of period processing to roll forward
        the incentive fee calculations and update IRR.
        
        Args:
            period: Current period being finalized
        """
        if not self.enable_incentive_fee or not self.incentive_fee:
            return
        
        # VBA Rollfoward() equivalent (preserving VBA typo)
        self.incentive_fee.rollfoward()
        
        # Save updated state to database
        if self.incentive_fee_structure_id:
            self.incentive_fee.save_to_database(
                self.deal.deal_id,
                f"Period {period} Update"
            )
        
        self.logger.debug(f"Finalized incentive fee for period {period}")
    
    def get_incentive_fee_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive summary of incentive fee calculations
        
        Returns:
            Dictionary with incentive fee summary data
        """
        if not self.enable_incentive_fee or not self.incentive_fee:
            return {
                'incentive_fee_enabled': False,
                'total_fees_paid': 0.0,
                'threshold_reached': False,
                'current_period': 0,
                'fee_structure_id': None
            }
        
        # Get VBA output data
        output_data = self.incentive_fee.output()
        
        summary = {
            'incentive_fee_enabled': True,
            'fee_structure_id': self.incentive_fee_structure_id,
            'hurdle_rate': self.incentive_fee.cls_fee_hurdle_rate,
            'incentive_fee_rate': self.incentive_fee.cls_incent_fee,
            'threshold_reached': self.incentive_fee.cls_threshold_reach,
            'current_period': self.incentive_fee.cls_period,
            'total_fees_paid': self.incentive_fee.fee_paid(),
            'cumulative_discounted_payments': self.incentive_fee.cls_cum_dicounted_sub_payments,
            'closing_date': self.incentive_fee.cls_closing_date.isoformat() if self.incentive_fee.cls_closing_date else None,
            'output_data': output_data,
            'subordinated_payments_count': len(self.incentive_fee.cls_sub_payments_dict),
            'period_calculations': []
        }
        
        # Add period-by-period details
        for i in range(1, self.incentive_fee.cls_period):
            if i < len(self.incentive_fee.cls_threshold):
                period_data = {
                    'period': i,
                    'threshold': self.incentive_fee.cls_threshold[i],
                    'fee_paid': self.incentive_fee.cls_fee_paid[i] if i < len(self.incentive_fee.cls_fee_paid) else 0.0,
                    'irr': self.incentive_fee.cls_irr[i] if i < len(self.incentive_fee.cls_irr) else 0.0
                }
                summary['period_calculations'].append(period_data)
        
        return summary
    
    def get_current_incentive_fee_threshold(self) -> float:
        """
        Get current incentive fee threshold amount
        
        Returns:
            Current threshold amount that subordinated payments must exceed
        """
        if not self.enable_incentive_fee or not self.incentive_fee:
            return 0.0
        
        return self.incentive_fee.incentive_fee_threshold()
    
    def is_incentive_fee_threshold_reached(self) -> bool:
        """
        Check if incentive fee threshold has been reached
        
        Returns:
            True if threshold reached, False otherwise
        """
        if not self.enable_incentive_fee or not self.incentive_fee:
            return False
        
        return self.incentive_fee.cls_threshold_reach