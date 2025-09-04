#!/usr/bin/env python3
"""
Read Excel file to extract MAG16 Inputs tab asset count
"""

import pandas as pd
from pathlib import Path
import sys

def read_mag16_excel():
    """Read MAG16 Inputs from Excel file"""
    
    # Path to the Excel file
    excel_path = Path("../TradeHypoPrelimv32.xlsm")
    
    if not excel_path.exists():
        print(f"Excel file not found at: {excel_path.absolute()}")
        return None
    
    print(f"Reading Excel file: {excel_path.absolute()}")
    
    try:
        # First, let's see all available sheet names
        print("Available worksheets:")
        excel_file = pd.ExcelFile(excel_path)
        for i, sheet in enumerate(excel_file.sheet_names, 1):
            print(f"  {i}. {sheet}")
        
        # Look for MAG16 related sheets
        mag16_sheets = [sheet for sheet in excel_file.sheet_names if 'MAG16' in sheet.upper()]
        
        if mag16_sheets:
            print(f"\nFound MAG16 sheets: {mag16_sheets}")
            
            for sheet_name in mag16_sheets:
                print(f"\n--- Reading sheet: {sheet_name} ---")
                try:
                    # Read the sheet
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)
                    print(f"Sheet dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
                    
                    # Show column names
                    print("Column names:")
                    for i, col in enumerate(df.columns, 1):
                        print(f"  {i}. {col}")
                    
                    # Look for asset-like data
                    # Assets typically have identifiers, names, par amounts, etc.
                    potential_asset_cols = []
                    for col in df.columns:
                        col_str = str(col).lower()
                        if any(term in col_str for term in ['asset', 'id', 'name', 'par', 'amount', 'security', 'issuer']):
                            potential_asset_cols.append(col)
                    
                    if potential_asset_cols:
                        print(f"\nPotential asset columns: {potential_asset_cols}")
                        
                        # Count non-empty rows in key columns
                        for col in potential_asset_cols[:3]:  # Check first 3 relevant columns
                            non_empty = df[col].dropna().shape[0]
                            non_zero = df[col].replace(0, pd.NA).dropna().shape[0] if pd.api.types.is_numeric_dtype(df[col]) else non_empty
                            print(f"  {col}: {non_empty} non-empty values, {non_zero} non-zero values")
                    
                    # Show first few rows
                    print(f"\nFirst 5 rows of {sheet_name}:")
                    print(df.head().to_string())
                    
                except Exception as e:
                    print(f"Error reading sheet {sheet_name}: {e}")
        else:
            print("\nNo sheets with 'MAG16' in name found")
            print("Looking for 'Inputs' sheets...")
            
            input_sheets = [sheet for sheet in excel_file.sheet_names if 'INPUT' in sheet.upper()]
            if input_sheets:
                print(f"Found Input sheets: {input_sheets}")
                # Could examine these sheets for MAG16 data
            
        return excel_file.sheet_names
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def check_requirements():
    """Check if required packages are installed"""
    try:
        import pandas as pd
        import openpyxl
        print("Required packages available: pandas, openpyxl")
        return True
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Install with: pip install pandas openpyxl")
        return False

if __name__ == "__main__":
    print("MAG16 Excel Asset Counter")
    print("=" * 40)
    
    if not check_requirements():
        sys.exit(1)
    
    sheet_names = read_mag16_excel()
    
    if sheet_names:
        print(f"\nAnalysis complete. Found {len(sheet_names)} total worksheets.")
    else:
        print("Failed to read Excel file.")