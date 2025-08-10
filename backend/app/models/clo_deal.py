"""
CLO Deal and Tranche Models
Represents CLO structure, tranches, and deal-level information
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any

from ..core.database import Base


class CLODeal(Base):
    """
    CLO Deal master record with key dates and parameters
    """
    __tablename__ = 'clo_deals'
    
    deal_id = Column(String(50), primary_key=True)
    deal_name = Column(String(255), nullable=False)
    manager_name = Column(String(100))
    trustee_name = Column(String(100))
    
    # Key Dates
    pricing_date = Column(Date)
    closing_date = Column(Date)
    effective_date = Column(Date)
    first_payment_date = Column(Date)
    maturity_date = Column(Date)
    reinvestment_end_date = Column(Date)
    no_call_date = Column(Date)
    
    # Deal Parameters
    target_par_amount = Column(Numeric(18,2))
    ramp_up_period = Column(Integer)  # months
    payment_frequency = Column(Integer)  # payments per year
    
    # Status
    deal_status = Column(String(20))  # ACTIVE, CALLED, MATURED
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
    
    # Relationships
    tranches = relationship("CLOTranche", back_populates="deal", cascade="all, delete-orphan")
    assets = relationship("DealAsset", back_populates="deal", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="deal", cascade="all, delete-orphan")
    oc_triggers = relationship("OCTrigger", back_populates="deal", cascade="all, delete-orphan")
    ic_triggers = relationship("ICTrigger", back_populates="deal", cascade="all, delete-orphan")
    fees = relationship("Fee", back_populates="deal", cascade="all, delete-orphan")
    collateral_pools = relationship("CollateralPool", back_populates="deal", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CLODeal({self.deal_id}: {self.deal_name})>"


class CLOTranche(Base):
    """
    CLO Note Tranches with payment terms and current balances
    """
    __tablename__ = 'clo_tranches'
    
    tranche_id = Column(String(50), primary_key=True)
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    tranche_name = Column(String(50), nullable=False)
    
    # Tranche Properties
    initial_balance = Column(Numeric(18,2))
    current_balance = Column(Numeric(18,2))
    coupon_rate = Column(Numeric(10,6))
    coupon_type = Column(String(10))  # FIXED, FLOAT
    index_name = Column(String(20))   # SOFR, LIBOR, etc.
    margin = Column(Numeric(10,6))    # Spread over index
    
    # Rating and Seniority
    mdy_rating = Column(String(10))
    sp_rating = Column(String(10))
    seniority_level = Column(Integer)  # 1=most senior
    
    # Payment Terms
    payment_rank = Column(Integer)     # Payment order in waterfall
    interest_deferrable = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deal = relationship("CLODeal", back_populates="tranches")
    
    def __repr__(self):
        return f"<CLOTranche({self.tranche_id}: {self.tranche_name})>"


class DealAsset(Base):
    """
    Asset positions within CLO deals
    Links assets to specific deals with position details
    """
    __tablename__ = 'deal_assets'
    
    deal_id = Column(String(50), ForeignKey('clo_deals.deal_id'), nullable=False)
    blkrock_id = Column(String(50), ForeignKey('assets.blkrock_id'), nullable=False)
    
    # Position Details
    par_amount = Column(Numeric(18,2), nullable=False)
    purchase_price = Column(Numeric(8,6))  # as % of par
    purchase_date = Column(Date)
    sale_date = Column(Date)
    sale_price = Column(Numeric(8,6))
    
    # Status
    position_status = Column(String(20), default='ACTIVE')  # ACTIVE, SOLD, DEFAULTED
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    deal = relationship("CLODeal", back_populates="assets")
    asset = relationship("Asset", back_populates="deal_positions")
    
    # Composite primary key
    from sqlalchemy import PrimaryKeyConstraint
    __table_args__ = (
        PrimaryKeyConstraint('deal_id', 'blkrock_id'),
    )
    
    def __repr__(self):
        return f"<DealAsset({self.deal_id}: {self.blkrock_id} ${self.par_amount:,.0f})>"


# Add relationship to Asset model
from .asset import Asset
Asset.deal_positions = relationship("DealAsset", back_populates="asset")