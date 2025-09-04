#!/usr/bin/env python3
"""
Extract MAG16 tranche structure from Excel
"""

import pandas as pd
from pathlib import Path

def extract_mag16_tranches():
    """Extract MAG16 tranche structure from Excel"""
    
    excel_path = Path("../TradeHypoPrelimv32.xlsm")
    
    print("Extracting MAG16 tranche structure...")
    
    try:
        # Read the Mag 16 Inputs sheet
        df = pd.read_excel(excel_path, sheet_name="Mag 16 Inputs", header=None)
        
        print(f"Sheet dimensions: {df.shape}")
        
        # Look for the tranche structure (we saw it around row 4, cols 36-41)
        print("\nSearching for tranche structure...")
        
        # Check around row 4 for CDO/Class structure
        tranche_row = 3  # Row 4 in Excel (0-indexed)
        
        # Find column headers
        headers = []
        values = []
        
        print(f"Checking row {tranche_row + 1} (Excel row {tranche_row + 1}):")
        
        for col in range(35, 50):  # Check columns 36-50
            if col < df.shape[1]:
                header = df.iloc[tranche_row, col]
                if pd.notna(header):
                    print(f"  Col {col + 1}: {header}")
                    headers.append((col, str(header)))
        
        # Look for balance/amount information in subsequent rows
        print(f"\nLooking for tranche balances in nearby rows...")
        
        tranche_data = {}
        
        # Check several rows after the header row for balance data
        for check_row in range(tranche_row + 1, min(tranche_row + 10, df.shape[0])):
            print(f"\nRow {check_row + 1}:")
            
            for col_idx, header in headers:
                if col_idx < df.shape[1]:
                    value = df.iloc[check_row, col_idx]
                    if pd.notna(value) and value != 0:
                        print(f"  {header}: {value}")
                        
                        # Store tranche data
                        if header not in tranche_data:
                            tranche_data[header] = []
                        tranche_data[header].append({
                            'row': check_row + 1,
                            'value': value
                        })
        
        # Look for "Original Balance" or "Current Balance" keywords
        print(f"\nSearching for balance keywords...")
        
        balance_keywords = ['original balance', 'current balance', 'balance', 'principal', 'amount']
        
        for row_idx in range(df.shape[0]):
            first_col = str(df.iloc[row_idx, 0]).lower() if pd.notna(df.iloc[row_idx, 0]) else ''
            
            if any(keyword in first_col for keyword in balance_keywords):
                print(f"Row {row_idx + 1}: {df.iloc[row_idx, 0]}")
                
                # Check the values in this row for the tranche columns
                for col in range(35, 50):
                    if col < df.shape[1]:
                        value = df.iloc[row_idx, col]
                        if pd.notna(value) and isinstance(value, (int, float)) and value > 0:
                            print(f"  Col {col + 1}: {value:,}")
        
        # Also look for spread information
        print(f"\nSearching for spread/coupon information...")
        
        spread_keywords = ['spread', 'coupon', 'rate', 'margin']
        
        for row_idx in range(df.shape[0]):
            first_col = str(df.iloc[row_idx, 0]).lower() if pd.notna(df.iloc[row_idx, 0]) else ''
            
            if any(keyword in first_col for keyword in spread_keywords):
                print(f"Row {row_idx + 1}: {df.iloc[row_idx, 0]}")
                
                # Check the values in this row for the tranche columns
                for col in range(35, 50):
                    if col < df.shape[1]:
                        value = df.iloc[row_idx, col]
                        if pd.notna(value):
                            print(f"  Col {col + 1}: {value}")
        
        return tranche_data
        
    except Exception as e:
        print(f"Error extracting tranche data: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_database_tranches():
    """Check if MAG16 tranches exist in database"""
    
    print("\n" + "="*50)
    print("Checking database for existing MAG16 tranches...")
    
    try:
        from app.core.database_config import db_config
        from sqlalchemy import text
        
        with db_config.get_db_session('postgresql') as db:
            # Check clo_tranches table
            result = db.execute(text('''
                SELECT * FROM clo_tranches WHERE deal_id = 'MAG16'
            '''))
            
            tranches = result.fetchall()
            
            if tranches:
                print(f"Found {len(tranches)} tranches for MAG16:")
                for tranche in tranches:
                    print(f"  {tranche}")
            else:
                print("No tranches found for MAG16 in database")
            
            # Check liabilities table
            result2 = db.execute(text('''
                SELECT * FROM liabilities WHERE deal_id = 'MAG16' LIMIT 5
            '''))
            
            liabilities = result2.fetchall()
            
            if liabilities:
                print(f"\nFound {len(liabilities)} liabilities for MAG16:")
                for liability in liabilities[:5]:  # Show first 5
                    print(f"  {liability}")
            else:
                print("No liabilities found for MAG16 in database")
    
    except Exception as e:
        print(f"Database check error: {e}")

def main():
    """Main function"""
    
    print("MAG16 Tranche Structure Extraction")
    print("=" * 50)
    
    # Extract from Excel
    tranche_data = extract_mag16_tranches()
    
    # Check database
    check_database_tranches()
    
    print("\n" + "=" * 50)
    print("Extraction complete")

if __name__ == "__main__":
    main()