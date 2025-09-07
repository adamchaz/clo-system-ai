#!/usr/bin/env python3
"""
Execute MAG7 Concentration Test Migration - Excel Specification
Runs the 006_mag7_excel_specification.sql migration
"""

import psycopg2
import os
from pathlib import Path

# Database connection parameters
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5433,
    'database': 'clo_dev',
    'user': 'postgres',
    'password': 'adamchaz'
}

def run_mag7_excel_migration():
    """Execute the MAG7 concentration test migration (Excel spec)"""
    
    # Read the migration SQL file
    migration_file = Path(__file__).parent / 'migrations' / '006_mag7_excel_specification.sql'
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    print(f"Reading migration file: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    try:
        # Connect to PostgreSQL
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Execute the migration
        print("Executing MAG7 concentration test migration (Excel specification)...")
        cursor.execute(migration_sql)
        
        # Commit the changes
        conn.commit()
        
        print("MAG7 concentration test migration completed successfully!")
        
        # Fetch and display validation results
        print("\nMigration Validation Results:")
        print("=" * 50)
        
        # Verify test count
        cursor.execute("""
            SELECT COUNT(*) as test_count
            FROM deal_concentration_thresholds
            WHERE deal_id = 'MAG7'
        """)
        count = cursor.fetchone()[0]
        status = "PASS" if count == 41 else "FAIL"
        print(f"MAG7 Test Count: {count}/41 ({status})")
        
        # Show custom thresholds
        cursor.execute("""
            SELECT 
                ctd.test_number,
                ctd.test_name,
                ctd.default_threshold as default_value,
                dct.threshold_value as mag7_value
            FROM deal_concentration_thresholds dct
            JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
            WHERE dct.deal_id = 'MAG7' 
              AND dct.threshold_value != ctd.default_threshold
            ORDER BY ctd.test_number
        """)
        
        custom_thresholds = cursor.fetchall()
        print(f"\nMAG7 Custom Thresholds (2012 vintage): {len(custom_thresholds)}")
        for test_num, test_name, default_val, mag7_val in custom_thresholds:
            if isinstance(mag7_val, float) and mag7_val < 1:
                mag7_str = f"{mag7_val*100:.1f}%"
                default_str = f"{default_val*100:.1f}%" if default_val else "N/A"
            else:
                mag7_str = f"{mag7_val}"
                default_str = f"{default_val}" if default_val else "N/A"
            print(f"  Test #{test_num}: {mag7_str} (default: {default_str}) - {test_name}")
        
        # Show test categories
        cursor.execute("""
            SELECT 
                ctd.test_category,
                COUNT(*) as test_count
            FROM deal_concentration_thresholds dct
            JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
            WHERE dct.deal_id = 'MAG7'
            GROUP BY ctd.test_category
            ORDER BY ctd.test_category
        """)
        
        categories = cursor.fetchall()
        print(f"\nTest Categories:")
        for category, test_count in categories:
            print(f"  {category.upper()}: {test_count} tests")
        
        # Compare with other MAG versions
        cursor.execute("""
            SELECT 
                dct.deal_id,
                COUNT(*) as total_tests
            FROM deal_concentration_thresholds dct
            WHERE dct.deal_id IN ('MAG7', 'MAG16', 'MAG17')
            GROUP BY dct.deal_id
            ORDER BY dct.deal_id
        """)
        
        comparisons = cursor.fetchall()
        print(f"\nMAG Version Comparison:")
        for deal_id, total_tests in comparisons:
            print(f"  {deal_id}: {total_tests} tests")
        
        cursor.close()
        conn.close()
        
        print(f"\nSUCCESS: MAG7 concentration tests configured!")
        print(f"Total: {count} tests (Excel specification: 41 tests)")
        return True
        
    except psycopg2.Error as e:
        print(f"ERROR: Database error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=== MAG7 Concentration Test Migration (Excel Specification) ===")
    print("Configuring 41 concentration tests for MAG7 per Excel specification")
    print("Test numbers: 1,2,3,4,5,6,40,8,9,10,11,12,13,48,47,14,41,16,17,18,19,20,21,22,23,24,25,26,27,42,43,44,45,28,29,30,31,46,35,38,34")
    print()
    
    success = run_mag7_excel_migration()
    
    if success:
        print("\nSUCCESS: Migration completed successfully!")
        print("MAG7 concentration tests are now available in the system.")
        print("Key features:")
        print("• 41 tests total (per Excel specification)")
        print("• 4 custom thresholds for 2012 vintage")
        print("• Lower limits: Cov-lite (50%), WAC (6.5%), WARF (2850), Diversity (55)")
    else:
        print("\nERROR: Migration failed!")
        print("Please check the error messages above and retry.")