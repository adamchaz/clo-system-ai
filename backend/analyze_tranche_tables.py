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
            print("\n📋 CLO_TRANCHES Table Structure:")
            print("-" * 40)
            
            result = db.execute(text('''
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'clo_tranches'
                ORDER BY ordinal_position
            '''))
            
            clo_tranches_cols = result.fetchall()
            if clo_tranches_cols:
                for col in clo_tranches_cols:
                    nullable = "NULL" if col.is_nullable == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col.column_default}" if col.column_default else ""
                    print(f"  {col.column_name:<25} {col.data_type:<20} {nullable}{default}")
                
                # Check for data
                count_result = db.execute(text("SELECT COUNT(*) FROM clo_tranches"))
                count = count_result.fetchone()[0]
                print(f"\nRecords in clo_tranches: {count}")
                
                if count > 0:
                    # Show sample data
                    sample_result = db.execute(text("SELECT * FROM clo_tranches LIMIT 3"))
                    sample_data = sample_result.fetchall()
                    print("\nSample data:")
                    for row in sample_data:
                        print(f"  {dict(row)}")
            else:
                print("  Table not found or empty")
            
            # Analyze liabilities table
            print("\n📋 LIABILITIES Table Structure:")
            print("-" * 40)
            
            result2 = db.execute(text('''
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'liabilities'
                ORDER BY ordinal_position
            '''))
            
            liabilities_cols = result2.fetchall()
            if liabilities_cols:
                for col in liabilities_cols:
                    nullable = "NULL" if col.is_nullable == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col.column_default}" if col.column_default else ""
                    print(f"  {col.column_name:<25} {col.data_type:<20} {nullable}{default}")
                
                # Check for data
                count_result2 = db.execute(text("SELECT COUNT(*) FROM liabilities"))
                count2 = count_result2.fetchone()[0]
                print(f"\nRecords in liabilities: {count2}")
                
                if count2 > 0:
                    # Show sample data
                    sample_result2 = db.execute(text("SELECT * FROM liabilities LIMIT 3"))
                    sample_data2 = sample_result2.fetchall()
                    print("\nSample data:")
                    for row in sample_data2:
                        print(f"  {dict(row)}")
            else:
                print("  Table not found or empty")
            
            # Check for foreign key relationships
            print("\n🔗 Foreign Key Relationships:")
            print("-" * 40)
            
            fk_result = db.execute(text('''
                SELECT 
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND (tc.table_name = 'clo_tranches' OR tc.table_name = 'liabilities')
            '''))
            
            fk_relationships = fk_result.fetchall()
            if fk_relationships:
                for fk in fk_relationships:
                    print(f"  {fk.table_name}.{fk.column_name} -> {fk.foreign_table_name}.{fk.foreign_column_name}")
            else:
                print("  No foreign key relationships found")
            
            # Check for overlapping functionality
            print("\n🔍 Overlap Analysis:")
            print("-" * 40)
            
            clo_col_names = {col.column_name for col in clo_tranches_cols}
            lib_col_names = {col.column_name for col in liabilities_cols}
            
            common_cols = clo_col_names.intersection(lib_col_names)
            clo_only = clo_col_names - lib_col_names
            lib_only = lib_col_names - clo_col_names
            
            print(f"Common columns: {sorted(common_cols)}")
            print(f"CLO_tranches only: {sorted(clo_only)}")
            print(f"Liabilities only: {sorted(lib_only)}")
            
            return {
                'clo_tranches': {
                    'columns': clo_tranches_cols,
                    'count': count if clo_tranches_cols else 0
                },
                'liabilities': {
                    'columns': liabilities_cols, 
                    'count': count2 if liabilities_cols else 0
                },
                'relationships': fk_relationships,
                'overlap': {
                    'common': common_cols,
                    'clo_only': clo_only,
                    'lib_only': lib_only
                }
            }
            
    except Exception as e:
        print(f"Error analyzing schemas: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_code_usage():
    """Check how these tables are used in the codebase"""
    
    print("\n💻 Code Usage Analysis:")
    print("-" * 40)
    
    # This would require scanning the codebase files
    # For now, let's check if there are any model definitions
    
    import glob
    from pathlib import Path
    
    backend_dir = Path("../").resolve()
    
    clo_tranches_refs = 0
    liabilities_refs = 0
    
    # Search Python files for table references
    for py_file in glob.glob(str(backend_dir / "**" / "*.py"), recursive=True):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'clo_tranches' in content.lower():
                    clo_tranches_refs += 1
                if 'liabilities' in content.lower():
                    liabilities_refs += 1
        except:
            continue
    
    print(f"Files referencing 'clo_tranches': {clo_tranches_refs}")
    print(f"Files referencing 'liabilities': {liabilities_refs}")
    
    return {
        'clo_tranches_refs': clo_tranches_refs,
        'liabilities_refs': liabilities_refs
    }

def provide_recommendation(analysis_data, usage_data):
    """Provide recommendation on table consolidation"""
    
    print("\n💡 RECOMMENDATION:")
    print("=" * 60)
    
    if not analysis_data:
        print("❌ Could not analyze - insufficient data")
        return
    
    clo_count = analysis_data['clo_tranches']['count']
    lib_count = analysis_data['liabilities']['count']
    common_cols = analysis_data['overlap']['common']
    
    print(f"Current state:")
    print(f"  - clo_tranches: {clo_count} records")
    print(f"  - liabilities: {lib_count} records")
    print(f"  - Common columns: {len(common_cols)}")
    print(f"  - Code references: CLO({usage_data['clo_tranches_refs']}) vs LIB({usage_data['liabilities_refs']})")
    
    # Decision logic
    if clo_count == 0 and lib_count == 0:
        print("\n✅ CONSOLIDATE: Both tables are empty")
        print("   Recommendation: Use single 'clo_tranches' table for clarity")
        print("   Action: Drop 'liabilities' table, use 'clo_tranches' for all tranche data")
    
    elif clo_count > 0 and lib_count == 0:
        print("\n✅ KEEP CLO_TRANCHES: It has data, liabilities is empty")
        print("   Recommendation: Drop empty 'liabilities' table")
        print("   Action: Use 'clo_tranches' as the primary tranche table")
    
    elif clo_count == 0 and lib_count > 0:
        print("\n✅ KEEP LIABILITIES: It has data, clo_tranches is empty")
        print("   Recommendation: Drop empty 'clo_tranches' table")
        print("   Action: Use 'liabilities' as the primary tranche table")
    
    elif len(common_cols) > 5:
        print("\n⚠️  HIGH OVERLAP: Tables have similar structure")
        print("   Recommendation: Consider consolidation to avoid duplication")
        print("   Action: Merge into single table with clear naming")
    
    else:
        print("\n🤔 DIFFERENT PURPOSES: Tables may serve different functions")
        print("   Recommendation: Keep both if they serve distinct purposes")
        print("   Action: Clearly document the purpose of each table")

def main():
    """Main analysis function"""
    
    # Analyze database schemas
    analysis_data = analyze_table_schemas()
    
    # Check code usage
    usage_data = check_code_usage()
    
    # Provide recommendation
    provide_recommendation(analysis_data, usage_data)

if __name__ == "__main__":
    main()