#!/usr/bin/env python3
"""
Analyze clo_tranches vs liabilities table structure and usage
"""

from app.core.database_config import db_config
from sqlalchemy import text

def analyze_table_schemas():
    """Analyze the schemas of both tables"""
    
    print("Database Schema Analysis: clo_tranches vs liabilities")
    print("=" * 60)
    
    try:
        with db_config.get_db_session('postgresql') as db:
            
            # Analyze clo_tranches table
            print("\nCLO_TRANCHES Table Structure:")
            print("-" * 40)
            
            result = db.execute(text('''
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'clo_tranches'
                ORDER BY ordinal_position
            '''))
            
            clo_tranches_cols = result.fetchall()
            if clo_tranches_cols:
                for col in clo_tranches_cols:
                    nullable = "NULL" if col.is_nullable == 'YES' else "NOT NULL"
                    print(f"  {col.column_name:<25} {col.data_type:<20} {nullable}")
                
                # Check for data
                count_result = db.execute(text("SELECT COUNT(*) FROM clo_tranches"))
                count = count_result.fetchone()[0]
                print(f"\nRecords in clo_tranches: {count}")
            else:
                print("  Table not found")
                count = 0
            
            # Analyze liabilities table
            print("\nLIABILITIES Table Structure:")
            print("-" * 40)
            
            result2 = db.execute(text('''
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'liabilities'
                ORDER BY ordinal_position
            '''))
            
            liabilities_cols = result2.fetchall()
            if liabilities_cols:
                for col in liabilities_cols:
                    nullable = "NULL" if col.is_nullable == 'YES' else "NOT NULL"
                    print(f"  {col.column_name:<25} {col.data_type:<20} {nullable}")
                
                # Check for data
                count_result2 = db.execute(text("SELECT COUNT(*) FROM liabilities"))
                count2 = count_result2.fetchone()[0]
                print(f"\nRecords in liabilities: {count2}")
            else:
                print("  Table not found")
                count2 = 0
            
            # Check for overlapping functionality
            print("\nOverlap Analysis:")
            print("-" * 40)
            
            if clo_tranches_cols and liabilities_cols:
                clo_col_names = {col.column_name for col in clo_tranches_cols}
                lib_col_names = {col.column_name for col in liabilities_cols}
                
                common_cols = clo_col_names.intersection(lib_col_names)
                clo_only = clo_col_names - lib_col_names
                lib_only = lib_col_names - clo_col_names
                
                print(f"Common columns ({len(common_cols)}): {sorted(common_cols)}")
                print(f"CLO_tranches only ({len(clo_only)}): {sorted(clo_only)}")
                print(f"Liabilities only ({len(lib_only)}): {sorted(lib_only)}")
            
            # Check table purposes based on column names
            print("\nTable Purpose Analysis:")
            print("-" * 40)
            
            if clo_tranches_cols:
                clo_cols = [col.column_name.lower() for col in clo_tranches_cols]
                clo_purpose = []
                if any('tranche' in col for col in clo_cols):
                    clo_purpose.append("Tranche-specific")
                if any('balance' in col for col in clo_cols):
                    clo_purpose.append("Balance tracking")
                if any('rating' in col for col in clo_cols):
                    clo_purpose.append("Credit ratings")
                print(f"CLO_tranches appears to be for: {', '.join(clo_purpose) if clo_purpose else 'General CLO data'}")
            
            if liabilities_cols:
                lib_cols = [col.column_name.lower() for col in liabilities_cols]
                lib_purpose = []
                if any('liability' in col for col in lib_cols):
                    lib_purpose.append("Liability management")
                if any('payment' in col for col in lib_cols):
                    lib_purpose.append("Payment processing")
                if any('interest' in col for col in lib_cols):
                    lib_purpose.append("Interest calculations")
                print(f"Liabilities appears to be for: {', '.join(lib_purpose) if lib_purpose else 'General liability data'}")
            
            return {
                'clo_tranches_count': count,
                'liabilities_count': count2,
                'clo_cols': len(clo_tranches_cols) if clo_tranches_cols else 0,
                'lib_cols': len(liabilities_cols) if liabilities_cols else 0,
                'common_cols': len(common_cols) if clo_tranches_cols and liabilities_cols else 0
            }
            
    except Exception as e:
        print(f"Error analyzing schemas: {e}")
        return None

def provide_recommendation(data):
    """Provide recommendation on table consolidation"""
    
    print("\nRECOMMENDATION:")
    print("=" * 60)
    
    if not data:
        print("Could not analyze - insufficient data")
        return
    
    clo_count = data['clo_tranches_count']
    lib_count = data['liabilities_count'] 
    clo_cols = data['clo_cols']
    lib_cols = data['lib_cols']
    common_cols = data['common_cols']
    
    print(f"Current state:")
    print(f"  - clo_tranches: {clo_count} records, {clo_cols} columns")
    print(f"  - liabilities: {lib_count} records, {lib_cols} columns")
    print(f"  - Common columns: {common_cols}")
    
    # Decision logic
    if clo_count == 0 and lib_count == 0:
        print("\nDECISION: CONSOLIDATE")
        print("Both tables are empty - use single table for simplicity")
        print("RECOMMENDED ACTION:")
        print("  1. Drop 'liabilities' table")
        print("  2. Use 'clo_tranches' for all CLO tranche/note data")
        print("  3. Add MAG16 tranche data to 'clo_tranches'")
    
    elif clo_count > 0 and lib_count == 0:
        print("\nDECISION: USE CLO_TRANCHES")
        print("CLO_tranches has data, liabilities is empty")
        print("RECOMMENDED ACTION:")
        print("  1. Drop empty 'liabilities' table")
        print("  2. Migrate MAG16 tranches to 'clo_tranches'")
    
    elif clo_count == 0 and lib_count > 0:
        print("\nDECISION: USE LIABILITIES")
        print("Liabilities has data, clo_tranches is empty")
        print("RECOMMENDED ACTION:")
        print("  1. Drop empty 'clo_tranches' table")
        print("  2. Migrate MAG16 tranches to 'liabilities'")
    
    elif common_cols > 3:
        print("\nDECISION: HIGH OVERLAP - CONSOLIDATE")
        print("Tables have significant overlap - avoid duplication")
        print("RECOMMENDED ACTION:")
        print("  1. Merge data into single table")
        print("  2. Choose clearest table name ('clo_tranches' preferred)")
    
    else:
        print("\nDECISION: KEEP BOTH")
        print("Tables may serve different purposes")
        print("RECOMMENDED ACTION:")
        print("  1. Keep both tables")
        print("  2. Clearly document purpose of each")
        print("  3. Use appropriate table for MAG16 data")

def main():
    """Main analysis function"""
    
    # Analyze database schemas
    data = analyze_table_schemas()
    
    # Provide recommendation
    provide_recommendation(data)

if __name__ == "__main__":
    main()