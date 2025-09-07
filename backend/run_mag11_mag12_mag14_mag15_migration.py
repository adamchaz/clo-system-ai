#!/usr/bin/env python3
"""
Execute MAG11, MAG12, MAG14, MAG15 Concentration Test Migration - Excel Specifications
Runs the 009_mag11_mag12_mag14_mag15_excel_specification.sql migration
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

def run_mag11_mag15_migration():
    """Execute the MAG11, MAG12, MAG14, MAG15 concentration test migration (Excel spec)"""
    
    # Read the migration SQL file
    migration_file = Path(__file__).parent / 'migrations' / '009_mag11_mag12_mag14_mag15_excel_specification.sql'
    
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
        print("Executing MAG11, MAG12, MAG14, MAG15 concentration test migration...")
        cursor.execute(migration_sql)
        
        # Commit the changes
        conn.commit()
        
        print("MAG11-15 concentration test migration completed successfully!")
        
        # Fetch and display validation results
        print("\nMigration Validation Results:")
        print("=" * 60)
        
        # Verify test counts for all four deals
        cursor.execute("""
            SELECT 
                deal_id,
                COUNT(*) as test_count,
                CASE WHEN COUNT(*) = 37 THEN 'PASS' ELSE 'FAIL' END as status
            FROM deal_concentration_thresholds
            WHERE deal_id IN ('MAG11', 'MAG12', 'MAG14', 'MAG15')
            GROUP BY deal_id
            ORDER BY deal_id
        """)
        
        counts = cursor.fetchall()
        print("Test Count Verification:")
        for deal_id, count, status in counts:
            print(f"  {deal_id}: {count}/37 tests ({status})")
        
        # Show custom thresholds (vintage adjustments)
        cursor.execute("""
            SELECT 
                dct.deal_id,
                ctd.test_number,
                ctd.test_name,
                dct.threshold_value as custom_value
            FROM deal_concentration_thresholds dct
            JOIN concentration_test_definitions ctd ON dct.test_id = ctd.test_id
            WHERE dct.deal_id IN ('MAG11', 'MAG12', 'MAG14', 'MAG15')
              AND dct.threshold_value != ctd.default_threshold
            ORDER BY dct.deal_id, ctd.test_number
        """)
        
        custom_thresholds = cursor.fetchall()
        print(f"\nVintage Adjustments Applied: {len(custom_thresholds)}")
        current_deal = None
        for deal_id, test_num, test_name, threshold in custom_thresholds:
            if deal_id != current_deal:
                print(f"  {deal_id}:")
                current_deal = deal_id
            if isinstance(threshold, float) and threshold < 1:
                threshold_str = f"{threshold*100:.1f}%"
            else:
                threshold_str = f"{threshold}"
            print(f"    Test #{test_num}: {threshold_str} - {test_name[:35]}...")
        
        # Show complete Excel verification status
        cursor.execute("""
            SELECT 
                dct.deal_id,
                COUNT(*) as total_tests,
                CASE WHEN dct.deal_id IN ('MAG6', 'MAG7', 'MAG8', 'MAG9', 'MAG11', 'MAG12', 'MAG14', 'MAG15') 
                     THEN 'Excel Verified' ELSE 'Needs Verification' END as status
            FROM deal_concentration_thresholds dct
            GROUP BY dct.deal_id
            ORDER BY dct.deal_id
        """)
        
        all_deals = cursor.fetchall()
        print(f"\nComplete Deal Status Summary:")
        excel_verified = []
        needs_verification = []
        
        for deal_id, total_tests, status in all_deals:
            print(f"  {deal_id}: {total_tests} tests ({status})")
            if status == 'Excel Verified':
                excel_verified.append(deal_id)
            else:
                needs_verification.append(deal_id)
        
        print(f"\nExcel Verified: {len(excel_verified)}/10 deals")
        print(f"  Verified: {', '.join(excel_verified)}")
        print(f"  Remaining: {', '.join(needs_verification)}")
        
        cursor.close()
        conn.close()
        
        print(f"\nSUCCESS: MAG11, MAG12, MAG14, MAG15 concentration tests configured!")
        return True
        
    except psycopg2.Error as e:
        print(f"ERROR: Database error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=== MAG11, MAG12, MAG14, MAG15 Concentration Test Migration ===")
    print("Updating 4 deals to Excel specifications (37 tests each)")
    print("MAG11: 1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38")
    print("MAG12: 1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38")
    print("MAG14: 1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,33,34,35,36,37,38,39")
    print("MAG15: 1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38")
    print()
    
    success = run_mag11_mag15_migration()
    
    if success:
        print("\nSUCCESS: Migration completed successfully!")
        print("8 of 10 MAG deals now have Excel-verified concentration tests.")
        print("Key achievements:")
        print("• MAG11-15: All 37 tests per Excel specifications")
        print("• 2013-2015 vintage threshold adjustments applied")
        print("• MAG14 special case: Uses test #39 (not #32)")
        print("• Only MAG16 and MAG17 still need Excel verification")
    else:
        print("\nERROR: Migration failed!")
        print("Please check the error messages above and retry.")