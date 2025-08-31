#!/usr/bin/env python3
"""
Extract Correct MAG16 Thresholds from Excel Columns L-O
Found the concentration test table: L=Test Number, M=Test Name, N=Min/Max, O=Threshold
"""

import os
import sys
import pandas as pd
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from app.core.database import get_db
from sqlalchemy import text

def extract_mag16_thresholds_from_table():
    """Extract thresholds from the concentration test table in columns L-O"""
    print("Extracting MAG16 Thresholds from Excel Table (Columns L-O)")
    print("=" * 65)
    
    excel_file = os.path.join(
        os.path.dirname(__file__), "..", "..", "..",
        "TradeHypoPrelimv32.xlsm"
    )
    
    try:
        # Read worksheet
        df = pd.read_excel(
            excel_file,
            sheet_name="Mag 16 Inputs",
            header=None,
            engine='openpyxl'
        )
        
        print("Found concentration test table structure:")
        print("L=Test Number | M=Test Name | N=Min/Max | O=Threshold")
        print("-" * 60)
        
        # Extract thresholds from the table (rows 3+ contain data)
        mag16_thresholds = {}
        
        # Based on the examination, extract from rows 3-39 where we saw the data
        for row_idx in range(3, min(40, df.shape[0])):
            try:
                # Column L (11) = Test Number
                test_number_cell = str(df.iloc[row_idx, 11]).strip()
                
                # Column M (12) = Test Name  
                test_name_cell = str(df.iloc[row_idx, 12]).strip()
                
                # Column N (13) = Min/Max
                min_max_cell = str(df.iloc[row_idx, 13]).strip()
                
                # Column O (14) = Threshold
                threshold_cell = str(df.iloc[row_idx, 14]).strip()
                
                # Skip empty rows
                if test_number_cell == 'nan' or test_number_cell == '':
                    continue
                
                # Parse test number
                try:
                    test_number = int(float(test_number_cell))
                except ValueError:
                    continue
                
                # Parse threshold value
                threshold_value = parse_threshold(threshold_cell, test_number)
                
                if threshold_value is not None:
                    mag16_thresholds[test_number] = threshold_value
                    
                    # Format for display
                    if test_number == 17 and threshold_value > 100:
                        threshold_str = f"{threshold_value:.0f}"
                    elif test_number == 18 and threshold_value < 1:
                        threshold_str = f"{threshold_value * 10000:.0f} bps"
                    elif threshold_value >= 0.1:
                        threshold_str = f"{threshold_value * 100:.0f}%"
                    else:
                        threshold_str = f"{threshold_value * 100:.1f}%"
                    
                    print(f"Test {test_number:2d}: {test_name_cell[:30]:<30} = {threshold_str}")
                
            except Exception as e:
                print(f"Error processing row {row_idx}: {e}")
                continue
        
        print(f"\\nExtracted {len(mag16_thresholds)} valid thresholds from Excel table")
        return mag16_thresholds
        
    except Exception as e:
        print(f"Excel extraction error: {e}")
        return {}

def parse_threshold(text, test_number):
    """Parse threshold value from Excel cell"""
    if not text or text == 'nan' or text == '':
        return None
    
    try:
        # Handle percentage format
        if '%' in text:
            import re
            numeric_match = re.search(r'(\\d+\\.?\\d*)', text)
            if numeric_match:
                return float(numeric_match.group(1)) / 100
        
        # Handle decimal format (0.9, 0.075, etc.)
        if text.startswith('0.'):
            return float(text)
        
        # Handle WARF values (large numbers for Test 17)
        if test_number == 17 and text.isdigit() and 1000 <= int(text) <= 5000:
            return float(text)
        
        # Handle WAS values (Test 18 - could be in bps)
        if test_number == 18 and text.isdigit() and 100 <= int(text) <= 1000:
            return float(text) / 10000  # Convert bps to decimal
        
        # Handle regular numeric values
        if text.replace('.', '').isdigit():
            value = float(text)
            
            # If it's a reasonable percentage (1-100), convert to decimal
            if 1 <= value <= 100:
                return value / 100
            # If it's already a decimal (0-1), use as is
            elif 0 <= value <= 1:
                return value
            # If it's a large number for WARF/WAS tests
            elif test_number in [17, 18] and value > 100:
                return value
        
    except (ValueError, TypeError):
        pass
    
    return None

def update_database_with_excel_thresholds(thresholds):
    """Update database with correct Excel-extracted thresholds"""
    print(f"\\nUpdating database with {len(thresholds)} Excel-extracted thresholds...")
    
    db = next(get_db())
    
    try:
        # Clear all existing MAG16 thresholds
        db.execute(text("DELETE FROM deal_concentration_thresholds WHERE deal_id = 'MAG16-001'"))
        db.commit()
        
        # Insert correct thresholds
        created_count = 0
        
        for test_id, threshold_value in thresholds.items():
            try:
                db.execute(text("""
                    INSERT INTO deal_concentration_thresholds 
                    (deal_id, test_id, threshold_value, effective_date, mag_version, notes, created_at, updated_at)
                    VALUES (:deal_id, :test_id, :threshold_value, :effective_date, :mag_version, :notes, NOW(), NOW())
                """), {
                    "deal_id": "MAG16-001",
                    "test_id": test_id,
                    "threshold_value": threshold_value,
                    "effective_date": "2016-03-23",
                    "mag_version": "MAG17",
                    "notes": f"Excel MAG16 Table L-O: Test {test_id}"
                })
                
                created_count += 1
                
            except Exception as e:
                print(f"Error creating Test {test_id}: {e}")
                continue
        
        db.commit()
        
        print(f"SUCCESS: Created {created_count} correct MAG16 thresholds")
        
        # Verify key tests
        result = db.execute(text("SELECT test_id, threshold_value FROM deal_concentration_thresholds WHERE deal_id = 'MAG16-001' AND test_id IN (1, 14) ORDER BY test_id"))
        
        print("\\nKey test verification:")
        for test in result.fetchall():
            test_id = test[0]
            threshold = test[1]
            print(f"Test {test_id}: {threshold * 100:.0f}%")
        
        return True
        
    except Exception as e:
        print(f"Database update error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main function"""
    try:
        # Extract from Excel table
        thresholds = extract_mag16_thresholds_from_table()
        
        if thresholds:
            # Update database
            success = update_database_with_excel_thresholds(thresholds)
            
            if success:
                print("\\n" + "=" * 65)
                print("MAG16 Thresholds Correctly Extracted from Excel Columns L-O")
                print("All concentration test values should now be accurate")
        else:
            print("\\nFailed to extract thresholds from Excel table")
            
    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    main()