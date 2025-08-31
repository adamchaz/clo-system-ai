"""
MAG Scenario Models
Database models for MAG scenario parameters and configurations
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, Text
from sqlalchemy.sql import func
from datetime import date, datetime

from ...core.database import Base


class MagScenario(Base):
    """
    MAG Scenario parameters for different MAG versions
    """
    __tablename__ = 'mag_scenarios'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # MAG version and scenario identification
    mag_version = Column(Integer, nullable=False)
    scenario_id = Column(Integer, nullable=False)
    
    # Parameter details
    parameter_name = Column(String(100), nullable=False)
    parameter_value = Column(Text)  # Can store JSON or simple values
    parameter_type = Column(String(20))  # 'numeric', 'boolean', 'string', 'json'
    description = Column(String(255))
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=func.now())
    analysis_date = Column(Date)
    
    def __repr__(self):
        return f"<MagScenario(mag_version={self.mag_version}, parameter={self.parameter_name})>"