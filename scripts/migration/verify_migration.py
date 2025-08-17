#!/usr/bin/env python3
"""
Verify migration results
"""

from sqlalchemy import create_engine, text
import json
from datetime import datetime

def verify_migration():
    """Verify the migration results"""
    database_url = "sqlite:///clo_assets_production.db"
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Total count
        result = conn.execute(text("SELECT COUNT(*) as count FROM assets"))
        total_count = result.fetchone()[0]
        print(f"Total assets in database: {total_count}")
        
        # Sample data
        result = conn.execute(text("""
            SELECT blkrock_id, issue_name, issuer_name, par_amount, market_value, mdy_rating, currency
            FROM assets 
            LIMIT 10
        """))
        
        print(f"\nSample migrated assets:")
        for row in result.fetchall():
            print(f"  {row[0]}: {row[1][:30]}... | Par: {row[3]} | MV: {row[4]} | Rating: {row[5]} | Currency: {row[6]}")
        
        # Check for issues
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN blkrock_id IS NULL THEN 1 END) as missing_id,
                COUNT(CASE WHEN issue_name IS NULL THEN 1 END) as missing_name,
                COUNT(CASE WHEN par_amount = 0 THEN 1 END) as zero_par
            FROM assets
        """))
        
        stats = result.fetchone()
        print(f"\nData Quality Check:")
        print(f"  Total records: {stats[0]}")
        print(f"  Missing BLKRockID: {stats[1]}")
        print(f"  Missing issue name: {stats[2]}")
        print(f"  Zero par amount: {stats[3]}")
        
        # Check why only 384 assets extracted
        print(f"\nExpected ~1,003 assets but got {total_count}")
        print(f"This suggests the Excel extraction stopped early or filtered out empty rows")

if __name__ == "__main__":
    verify_migration()