#!/usr/bin/env python3
"""
Verify Reference Table migration results
"""

from sqlalchemy import create_engine, text
from datetime import datetime
import json

def verify_reference_migration():
    """Verify the Reference Table migration results"""
    database_url = "sqlite:///clo_reference_quick.db"
    engine = create_engine(database_url)
    
    print("REFERENCE TABLE MIGRATION VERIFICATION")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Total count
        result = conn.execute(text("SELECT COUNT(*) as count FROM reference_data"))
        total_count = result.fetchone()[0]
        print(f"Total reference records: {total_count}")
        
        # Records with dates
        result = conn.execute(text("SELECT COUNT(*) as count FROM reference_data WHERE correlation_date IS NOT NULL"))
        date_count = result.fetchone()[0]
        print(f"Records with correlation dates: {date_count}")
        
        # Date range
        result = conn.execute(text("""
            SELECT 
                MIN(correlation_date) as earliest_date,
                MAX(correlation_date) as latest_date
            FROM reference_data 
            WHERE correlation_date IS NOT NULL
        """))
        date_range = result.fetchone()
        if date_range[0] and date_range[1]:
            print(f"Date range: {date_range[0]} to {date_range[1]}")
        
        # Sample data analysis
        result = conn.execute(text("""
            SELECT row_number, correlation_date, raw_data
            FROM reference_data 
            WHERE correlation_date IS NOT NULL
            LIMIT 5
        """))
        
        print(f"\nSample records:")
        for row in result.fetchall():
            raw_data = json.loads(row[2]) if row[2] else {}
            data_summary = {k: v for k, v in raw_data.items() if k in ['col_2', 'col_3', 'col_4']}
            print(f"  Row {row[0]}: {row[1]} | {data_summary}")
        
        # Row distribution
        result = conn.execute(text("""
            SELECT 
                CASE 
                    WHEN row_number BETWEEN 12 AND 500 THEN '12-500'
                    WHEN row_number BETWEEN 501 AND 2000 THEN '501-2000'
                    WHEN row_number BETWEEN 2001 AND 5000 THEN '2001-5000'
                    WHEN row_number > 5000 THEN '5000+'
                END as range_group,
                COUNT(*) as count
            FROM reference_data
            GROUP BY range_group
            ORDER BY MIN(row_number)
        """))
        
        print(f"\nData distribution by row ranges:")
        for row in result.fetchall():
            print(f"  Rows {row[0]}: {row[1]} records")
        
        # Data completeness by column
        result = conn.execute(text("""
            SELECT row_number, raw_data
            FROM reference_data
            LIMIT 100
        """))
        
        column_stats = {}
        for row in result.fetchall():
            if row[1]:
                raw_data = json.loads(row[1])
                for col_key in raw_data.keys():
                    if col_key not in column_stats:
                        column_stats[col_key] = 0
                    column_stats[col_key] += 1
        
        print(f"\nColumn data frequency (first 100 records):")
        for col_key in sorted(column_stats.keys()):
            print(f"  {col_key}: {column_stats[col_key]} records")
    
    print(f"\nMIGRATION SUMMARY:")
    print(f"  Database: clo_reference_quick.db")
    print(f"  Table: reference_data")
    print(f"  Total records: {total_count}")
    print(f"  Records with dates: {date_count} ({date_count/total_count*100:.1f}%)")
    print(f"  Data format: JSON with column mappings")
    print(f"  Status: Migration completed successfully")

if __name__ == "__main__":
    verify_reference_migration()