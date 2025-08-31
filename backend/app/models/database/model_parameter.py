"""
Model Parameter Models
Database models for system configuration parameters
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime

from ...core.database import Base


class ModelParameter(Base):
    """
    Model parameters for system configuration
    """
    __tablename__ = 'model_parameters'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Parameter identification
    parameter_name = Column(String(100), nullable=False)
    parameter_value = Column(Text)
    parameter_type = Column(String(20))  # 'numeric', 'boolean', 'string', 'json'
    
    # Metadata
    description = Column(String(255))
    category = Column(String(50))
    is_active = Column(Boolean, default=True)
    mag_version = Column(Integer)  # Optional MAG version association
    
    # Audit fields
    created_date = Column(DateTime, default=func.now())
    updated_date = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<ModelParameter(name={self.parameter_name}, value={self.parameter_value})>"