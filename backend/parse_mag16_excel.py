#!/usr/bin/env python3
"""
Parse MAG16 Inputs Excel sheet to find actual asset data
"""

import pandas as pd
from pathlib import Path

def parse_mag16_excel():
    """Parse MAG16 Inputs sheet for asset data"""
    
    excel_path = Path("../TradeHypoPrelimv32.xlsm")
    
    print(f"Parsing MAG16 asset data from: {excel_path.name}")
    
    try:
        # Read the full sheet without headers first
        df = pd.read_excel(excel_path, sheet_name="Mag 16 Inputs", header=None)
        print(f"Raw sheet dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Look for Bloomberg ID pattern (BLKRockID column)
        blkrock_col = None
        par_col = None
        
        # Search for the header row containing asset data
        for row_idx in range(min(20, df.shape[0])):  # Check first 20 rows for headers
            row_data = df.iloc[row_idx].astype(str).str.lower()
            
            # Look for Bloomberg/BlackRock ID pattern
            for col_idx, cell_value in enumerate(row_data):
                if 'blkrock' in cell_value or 'bloomberg' in cell_value:
                    blkrock_col = col_idx
                    print(f"Found Bloomberg ID column at row {row_idx}, col {col_idx}: '{df.iloc[row_idx, col_idx]}'")
                
                if 'par amount' in cell_value or 'par_amount' in cell_value:
                    par_col = col_idx
                    print(f"Found Par Amount column at row {row_idx}, col {col_idx}: '{df.iloc[row_idx, col_idx]}'")
            
            # If we found both key columns, this is likely the header row
            if blkrock_col is not None and par_col is not None:
                header_row = row_idx
                print(f"Asset data header found at row {header_row}")
                break
        
        if blkrock_col is not None:
            # Extract asset data starting from the row after the header
            asset_start_row = header_row + 1 if 'header_row' in locals() else 2
            
            print(f"\nExtracting asset data starting from row {asset_start_row}...")
            
            # Get all Bloomberg IDs from the column
            bloomberg_ids = df.iloc[asset_start_row:, blkrock_col].dropna()
            
            # Filter out non-asset entries (headers, totals, etc.)
            # Bloomberg IDs typically follow a pattern like BRSYGJK13
            asset_ids = []
            for idx, blk_id in enumerate(bloomberg_ids):
                blk_str = str(blk_id).strip()
                # Bloomberg IDs are typically 8-12 characters, alphanumeric
                if len(blk_str) >= 8 and len(blk_str) <= 12 and blk_str.isalnum():
                    asset_ids.append(blk_str)
                elif blk_str and not any(skip in blk_str.lower() for skip in ['total', 'sum', 'header', 'test', 'unnamed']):
                    asset_ids.append(blk_str)  # Include if it's not obviously a non-asset
            
            print(f"Found {len(asset_ids)} Bloomberg IDs")
            
            # If we found par amounts, check those too
            if par_col is not None:
                par_amounts = df.iloc[asset_start_row:, par_col].dropna()
                numeric_pars = pd.to_numeric(par_amounts, errors='coerce').dropna()
                positive_pars = numeric_pars[numeric_pars > 0]
                
                print(f"Found {len(positive_pars)} positive par amounts")
                
                # Show some sample data
                print(f"\nSample asset data:")
                for i in range(min(10, len(asset_ids))):
                    asset_row_idx = asset_start_row + i
                    if asset_row_idx < df.shape[0]:
                        blk_id = df.iloc[asset_row_idx, blkrock_col]
                        par_val = df.iloc[asset_row_idx, par_col] if par_col is not None else 'N/A'
                        print(f"  Row {asset_row_idx}: {blk_id} | Par: {par_val}")
            
            # Show sample of identified asset IDs
            print(f"\nSample Bloomberg IDs found:")
            for i, asset_id in enumerate(asset_ids[:10]):
                print(f"  {i+1:2d}. {asset_id}")
            
            if len(asset_ids) > 10:
                print(f"  ... and {len(asset_ids) - 10} more")
            
            return len(asset_ids)
        else:
            print("Could not find Bloomberg ID column")
            
            # Alternative: look for any column with many alphanumeric entries
            print("\nSearching for alternative asset identifier columns...")
            for col_idx in range(df.shape[1]):
                col_data = df.iloc[:, col_idx].dropna().astype(str)
                # Look for columns with many entries that could be asset IDs
                potential_ids = [val for val in col_data if len(str(val)) >= 8 and str(val).isalnum()]
                if len(potential_ids) > 100:  # Reasonable threshold for asset count
                    print(f"  Column {col_idx}: {len(potential_ids)} potential asset IDs")
                    print(f"    Sample: {potential_ids[:5]}")
            
            return None
        
    except Exception as e:
        print(f"Error parsing Excel file: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("MAG16 Excel Asset Parser")
    print("=" * 40)
    
    asset_count = parse_mag16_excel()
    
    print("\n" + "=" * 40)
    if asset_count:
        print(f"EXCEL MAG16 ASSET COUNT: {asset_count}")
        print(f"DATABASE MAG16 ASSET COUNT: 195")
        print(f"DIFFERENCE: {asset_count - 195}")
    else:
        print("Could not determine asset count from Excel")
    print("=" * 40)