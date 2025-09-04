#!/usr/bin/env python3
"""
Count assets in MAG16 Inputs Excel tab
"""

import pandas as pd
from pathlib import Path

def count_mag16_assets():
    """Read MAG16 Inputs sheet and count assets"""
    
    excel_path = Path("../TradeHypoPrelimv32.xlsm")
    
    if not excel_path.exists():
        print(f"Excel file not found at: {excel_path.absolute()}")
        return None
    
    print(f"Reading 'Mag 16 Inputs' sheet from: {excel_path.name}")
    
    try:
        # Read the Mag 16 Inputs sheet
        df = pd.read_excel(excel_path, sheet_name="Mag 16 Inputs")
        print(f"Sheet dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Show column names
        print("\nColumn names:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        
        # Show first few rows to understand structure
        print(f"\nFirst 10 rows:")
        print(df.head(10).to_string())
        
        # Look for asset identifier columns
        print(f"\nAnalyzing asset data...")
        
        # Common asset identifier patterns
        asset_id_cols = []
        for col in df.columns:
            col_str = str(col).lower()
            if any(term in col_str for term in ['id', 'asset', 'security', 'cusip', 'isin', 'bloomberg', 'blkrock']):
                asset_id_cols.append(col)
        
        if asset_id_cols:
            print(f"Found potential asset ID columns: {asset_id_cols}")
            
            # Count non-empty values in each asset ID column
            for col in asset_id_cols:
                non_empty = df[col].dropna().shape[0]
                unique_values = df[col].dropna().nunique()
                print(f"  {col}: {non_empty} non-empty, {unique_values} unique values")
        
        # Look for numeric columns (par amounts, etc.)
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            print(f"\nNumeric columns: {numeric_cols[:5]}...")  # Show first 5
            
            for col in numeric_cols[:3]:  # Check first 3 numeric columns
                non_zero = (df[col] != 0).sum()
                positive = (df[col] > 0).sum()
                print(f"  {col}: {non_zero} non-zero, {positive} positive values")
        
        # Attempt to identify the main asset count
        print(f"\nAsset Count Analysis:")
        print(f"  Total rows in sheet: {df.shape[0]}")
        
        # Remove obviously empty rows
        non_empty_rows = df.dropna(how='all').shape[0]
        print(f"  Non-empty rows: {non_empty_rows}")
        
        # If we found asset ID columns, use the one with most entries
        if asset_id_cols:
            best_col = max(asset_id_cols, key=lambda col: df[col].dropna().shape[0])
            asset_count = df[best_col].dropna().shape[0]
            print(f"  Assets (based on {best_col}): {asset_count}")
        
        # Also check for rows where multiple key columns have data
        if len(df.columns) >= 3:
            # Count rows where at least the first 3 columns have data
            multi_col_count = df.iloc[:, :3].dropna().shape[0]
            print(f"  Rows with data in first 3 columns: {multi_col_count}")
        
        return {
            'total_rows': df.shape[0],
            'non_empty_rows': non_empty_rows,
            'asset_id_cols': asset_id_cols,
            'best_asset_count': asset_count if asset_id_cols else non_empty_rows,
            'dataframe': df
        }
        
    except Exception as e:
        print(f"Error reading Excel sheet: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("MAG16 Asset Counter - Excel Analysis")
    print("=" * 50)
    
    result = count_mag16_assets()
    
    if result:
        print(f"\n" + "=" * 50)
        print("SUMMARY:")
        print(f"Best estimate of MAG16 assets: {result['best_asset_count']}")
        print(f"Total rows in Excel sheet: {result['total_rows']}")
        print("=" * 50)