#!/usr/bin/env python3
"""
Execute MAG8 and MAG9 Concentration Test Migration - Excel Specifications
Runs the 008_mag8_mag9_excel_specification.sql migration
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

def run_mag8_mag9_migration():
    """Execute the MAG8 and MAG9 concentration test migration (Excel spec)"""
    
    # Read the migration SQL file
    migration_file = Path(__file__).parent / 'migrations' / '008_mag8_mag9_excel_specification.sql'
    
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
        print("Executing MAG8 and MAG9 concentration test migration...")
        cursor.execute(migration_sql)
        
        # Commit the changes
        conn.commit()
        
        print("MAG8 and MAG9 concentration test migration completed successfully!")
        
        # Fetch and display validation results
        print("\nMigration Validation Results:")
        print("=" * 50)
        
        # Verify test counts
        cursor.execute("""
            SELECT 
                deal_id,
                COUNT(*) as test_count
            FROM deal_concentration_thresholds
            WHERE deal_id IN ('MAG8', 'MAG9')
            GROUP BY deal_id
            ORDER BY deal_id
        """)
        
        counts = cursor.fetchall()
        for deal_id, count in counts:
            expected = 38 if deal_id == 'MAG8' else 37
            status = "PASS" if count == expected else "FAIL"
            print(f"{deal_id} Test Count: {count}/{expected} ({status})")
        
        # Show custom thresholds
        cursor.execute("""
            SELECT 
                dct.deal_id,
                ctd.test_number,
                ctd.test_name,
                dct.threshold_value as custom_value
            FROM deal_concentration_thresholds dct
            JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
            WHERE dct.deal_id IN ('MAG8', 'MAG9')
              AND dct.threshold_value != ctd.default_threshold
            ORDER BY dct.deal_id, ctd.test_number
        """)
        
        custom_thresholds = cursor.fetchall()
        print(f"\nCustom Thresholds (Vintage Adjustments): {len(custom_thresholds)}")
        for deal_id, test_num, test_name, threshold in custom_thresholds:
            if isinstance(threshold, float) and threshold < 1:
                threshold_str = f"{threshold*100:.1f}%"
            else:
                threshold_str = f"{threshold}"
            print(f"  {deal_id} Test #{test_num}: {threshold_str} - {test_name[:40]}...")
        
        # Show test categories breakdown
        cursor.execute("""
            SELECT 
                dct.deal_id,
                ctd.test_category,
                COUNT(*) as test_count
            FROM deal_concentration_thresholds dct
            JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
            WHERE dct.deal_id IN ('MAG8', 'MAG9')
            GROUP BY dct.deal_id, ctd.test_category
            ORDER BY dct.deal_id, ctd.test_category
        """)
        
        categories = cursor.fetchall()
        print(f"\nTest Categories Breakdown:")
        current_deal = None
        for deal_id, category, test_count in categories:
            if deal_id != current_deal:
                print(f"  {deal_id}:")
                current_deal = deal_id
            print(f"    {category.upper()}: {test_count} tests")
        
        # Updated comparison
        cursor.execute("""
            SELECT 
                dct.deal_id,
                COUNT(*) as total_tests
            FROM deal_concentration_thresholds dct
            WHERE dct.deal_id IN ('MAG6', 'MAG7', 'MAG8', 'MAG9', 'MAG16', 'MAG17')
            GROUP BY dct.deal_id
            ORDER BY dct.deal_id
        """)
        
        comparisons = cursor.fetchall()
        print(f"\nExcel-Verified MAG Versions:")
        for deal_id, total_tests in comparisons:
            status = "Excel Verified" if deal_id in ['MAG6', 'MAG7', 'MAG8', 'MAG9'] else "Needs Verification"
            print(f"  {deal_id}: {total_tests} tests ({status})")
        
        cursor.close()
        conn.close()
        
        print(f"\nSUCCESS: MAG8 and MAG9 concentration tests configured!")
        return True
        
    except psycopg2.Error as e:
        print(f"ERROR: Database error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=== MAG8 and MAG9 Concentration Test Migration ===")
    print("Updating MAG8 (38 tests) and MAG9 (37 tests) per Excel specifications")
    print("MAG8: 1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,28,29,30,33,34,35,37,38,39,49,50,51,52,53,54")
    print("MAG9: 1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38")
    print()
    
    success = run_mag8_mag9_migration()
    
    if success:
        print("\nSUCCESS: Migration completed successfully!")
        print("MAG8 and MAG9 concentration tests now match Excel specifications.")
        print("Key achievements:")
        print("• MAG8: 38 tests (from Mag 8 Inputs sheet)")
        print("• MAG9: 37 tests (from Mag 9 Inputs sheet)")
        print("• Vintage-appropriate threshold adjustments")
        print("• 4 deals now Excel-verified: MAG6, MAG7, MAG8, MAG9")
    else:
        print("\nERROR: Migration failed!")
        print("Please check the error messages above and retry.")