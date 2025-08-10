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
        self.incentive_fee = None  # Incentive fee calculator
        
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
                self.incentive_fee
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
        if liquidate:
            liquidation_proceeds = self._liquidate_portfolio()
            self.principal_proceeds[period] += liquidation_proceeds
        
        # Save account states to database if persistence is enabled
        if self.enable_account_persistence:
            self.save_all_accounts()
    
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
        
        # Roll forward fees, triggers, etc.
        # TODO: Implement when components are available