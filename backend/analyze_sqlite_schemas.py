#!/usr/bin/env python3
"""
SQLite Schema Analysis Tool
Analyzes existing SQLite databases to understand structure for PostgreSQL migration
"""

import sqlite3
import json
import os
from pathlib import Path

def analyze_sqlite_db(db_path):
    """Analyze SQLite database structure"""
    print(f"\n{'='*60}")
    print(f"ANALYZING: {os.path.basename(db_path)}")
    print(f"{'='*60}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found: {db_path}")
        return None
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get file size
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"Size: {size_mb:.1f} MB")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables: {len(tables)}")
        
        db_info = {
            'database': os.path.basename(db_path),
            'size_mb': round(size_mb, 1),
            'tables': {}
        }
        
        for table_name, in tables:
            print(f"\n  Table: {table_name}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_rows = cursor.fetchall()
            
            print(f"    Rows: {row_count:,}")
            print(f"    Columns: {len(columns)}")
            
            table_info = {
                'row_count': row_count,
                'columns': [],
                'sample_data': sample_rows[:2]  # First 2 rows
            }
            
            for col in columns:
                cid, name, type_, notnull, default, pk = col
                print(f"      - {name} ({type_}{'*' if pk else ''}{' NOT NULL' if notnull else ''})")
                table_info['columns'].append({
                    'name': name,
                    'type': type_,
                    'nullable': not bool(notnull),
                    'primary_key': bool(pk),
                    'default': default
                })
            
            db_info['tables'][table_name] = table_info
        
        conn.close()
        return db_info
        
    except Exception as e:
        print(f"ERROR analyzing {db_path}: {e}")
        return None

def main():
    """Main analysis function"""
    print("SQLite Database Schema Analysis")
    print("Preparing for PostgreSQL Migration")
    
    # Database directory
    db_dir = Path("data/databases")
    
    databases = [
        "clo_correlations.db",
        "clo_mag_scenarios.db", 
        "clo_model_config.db",
        "clo_reference_quick.db"
    ]
    
    all_db_info = {}
    
    for db_name in databases:
        db_path = db_dir / db_name
        db_info = analyze_sqlite_db(str(db_path))
        if db_info:
            all_db_info[db_name] = db_info
    
    # Save analysis results
    with open("sqlite_analysis_results.json", "w") as f:
        json.dump(all_db_info, f, indent=2)
    
    print(f"\n{'='*60}")
    print("Analysis Complete!")
    print(f"Results saved to: sqlite_analysis_results.json")
    print(f"{'='*60}")
    
    # Summary
    total_tables = sum(len(db['tables']) for db in all_db_info.values())
    total_rows = sum(
        sum(table['row_count'] for table in db['tables'].values())
        for db in all_db_info.values()
    )
    total_size = sum(db['size_mb'] for db in all_db_info.values())
    
    print(f"\nMIGRATION SUMMARY:")
    print(f"   Databases: {len(all_db_info)}")
    print(f"   Tables: {total_tables}")
    print(f"   Total Rows: {total_rows:,}")
    print(f"   Total Size: {total_size:.1f} MB")

if __name__ == "__main__":
    main()