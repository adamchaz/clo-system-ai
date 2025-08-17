"""
Check PostgreSQL tables for yield curve schema
"""

from sqlalchemy import create_engine, text
from app.core.database_config import db_config

def check_yield_tables():
    engine = db_config.get_engine('postgresql')
    
    with engine.connect() as conn:
        # Get all tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
        all_tables = [row[0] for row in result.fetchall()]
        
        # Filter for yield curve tables
        yield_tables = [t for t in all_tables if 'yield' in t.lower()]
        
        print(f"All tables: {len(all_tables)}")
        print(f"Yield curve tables: {yield_tables}")
        
        # Check if we need to create tables
        expected_tables = ['yield_curves', 'yield_curve_rates', 'forward_rates', 'yield_curve_scenarios']
        missing_tables = [t for t in expected_tables if t not in all_tables]
        
        print(f"Expected yield tables: {expected_tables}")
        print(f"Missing tables: {missing_tables}")
        
        return missing_tables

if __name__ == "__main__":
    check_yield_tables()