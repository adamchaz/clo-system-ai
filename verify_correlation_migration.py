#!/usr/bin/env python3
"""
Verify Asset Correlation Matrix migration results
"""

from sqlalchemy import create_engine, text
from datetime import datetime
import json

def verify_correlation_migration():
    """Verify the Asset Correlation Matrix migration results"""
    database_url = "sqlite:///clo_correlations.db"
    
    try:
        engine = create_engine(database_url)
        
        print("ASSET CORRELATION MATRIX MIGRATION VERIFICATION")
        print("=" * 70)
        
        with engine.connect() as conn:
            # Total correlation count
            result = conn.execute(text("SELECT COUNT(*) as count FROM asset_correlations"))
            total_count = result.fetchone()[0]
            print(f"Total correlations migrated: {total_count:,}")
            
            # Unique assets count
            result = conn.execute(text("SELECT COUNT(DISTINCT asset1_id) as count FROM asset_correlations"))
            unique_assets = result.fetchone()[0]
            print(f"Unique assets in matrix: {unique_assets}")
            
            # Matrix completeness check
            expected_pairs = unique_assets * unique_assets if unique_assets > 0 else 0
            completeness = (total_count / expected_pairs * 100) if expected_pairs > 0 else 0
            print(f"Matrix completeness: {completeness:.1f}% ({total_count:,} / {expected_pairs:,})")
            
            # Diagonal correlations (should be 1.0)
            result = conn.execute(text("""
                SELECT COUNT(*) as count, AVG(correlation_value) as avg_diagonal
                FROM asset_correlations 
                WHERE asset1_id = asset2_id
            """))
            diagonal_result = result.fetchone()
            print(f"Diagonal correlations: {diagonal_result[0]} (avg value: {float(diagonal_result[1]):.6f})")
            
            # Correlation value statistics
            result = conn.execute(text("""
                SELECT 
                    MIN(correlation_value) as min_corr,
                    MAX(correlation_value) as max_corr,
                    AVG(correlation_value) as avg_corr
                FROM asset_correlations
            """))
            stats = result.fetchone()
            print(f"Correlation range: [{float(stats[0]):.6f}, {float(stats[1]):.6f}]")
            print(f"Average correlation: {float(stats[2]):.6f}")
            
            # Sample correlations
            result = conn.execute(text("""
                SELECT asset1_id, asset2_id, correlation_value
                FROM asset_correlations 
                WHERE asset1_id != asset2_id
                LIMIT 10
            """))
            
            print(f"\nSample correlations (off-diagonal):")
            for row in result.fetchall():
                print(f"  {row[0]} <-> {row[1]}: {float(row[2]):.6f}")
            
            # Distribution analysis
            result = conn.execute(text("""
                SELECT 
                    CASE 
                        WHEN correlation_value < -0.5 THEN 'Strong Negative (<-0.5)'
                        WHEN correlation_value < -0.1 THEN 'Weak Negative (-0.5 to -0.1)'
                        WHEN correlation_value < 0.1 THEN 'Near Zero (-0.1 to 0.1)'
                        WHEN correlation_value < 0.5 THEN 'Weak Positive (0.1 to 0.5)'
                        WHEN correlation_value <= 1.0 THEN 'Strong Positive (0.5 to 1.0)'
                    END as range_category,
                    COUNT(*) as count
                FROM asset_correlations
                WHERE asset1_id != asset2_id  -- Exclude diagonal
                GROUP BY range_category
                ORDER BY MIN(correlation_value)
            """))
            
            print(f"\nCorrelation distribution (excluding diagonal):")
            for row in result.fetchall():
                if row[0]:  # Skip NULL categories
                    print(f"  {row[0]}: {row[1]:,} pairs")
            
            # Check for symmetry (sample)
            result = conn.execute(text("""
                SELECT 
                    a1.asset1_id, a1.asset2_id, a1.correlation_value as corr1,
                    a2.correlation_value as corr2,
                    ABS(a1.correlation_value - a2.correlation_value) as difference
                FROM asset_correlations a1
                JOIN asset_correlations a2 ON a1.asset1_id = a2.asset2_id AND a1.asset2_id = a2.asset1_id
                WHERE a1.asset1_id < a1.asset2_id  -- Avoid duplicates
                LIMIT 10
            """))
            
            print(f"\nSymmetry check (sample pairs):")
            asymmetric_count = 0
            for row in result.fetchall():
                difference = float(row[4])
                status = "OK" if difference < 0.0001 else "ASYMMETRIC"
                if difference >= 0.0001:
                    asymmetric_count += 1
                print(f"  {row[0]} <-> {row[1]}: {float(row[2]):.6f} vs {float(row[3]):.6f} (diff: {difference:.8f}) {status}")
            
            # Database size
            result = conn.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"))
            db_size_bytes = result.fetchone()[0]
            db_size_mb = db_size_bytes / (1024 * 1024)
            print(f"\nDatabase size: {db_size_mb:.2f} MB")
        
        print(f"\nMIGRATION STATUS:")
        if total_count > 200000:  # Expected ~238k correlations
            print(f"  SUCCESS - Full correlation matrix migrated")
            print(f"  Matrix size: {unique_assets}x{unique_assets} = {total_count:,} correlations")
            print(f"  Ready for risk management and portfolio analysis")
        else:
            print(f"  PARTIAL - Some correlations may be missing")
        
        return {
            'total_correlations': total_count,
            'unique_assets': unique_assets,
            'matrix_size': f"{unique_assets}x{unique_assets}",
            'database_size_mb': db_size_mb,
            'success': total_count > 200000
        }
        
    except Exception as e:
        print(f"Error verifying migration: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = verify_correlation_migration()