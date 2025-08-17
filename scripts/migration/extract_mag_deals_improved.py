#!/usr/bin/env python3
"""
Improved CLO Deal Data Extraction from TradeHypoPrelimv32.xlsm
Based on detailed structure analysis of MAG Input worksheets
"""

import pandas as pd
import json
from datetime import datetime
import sys
import os

def safe_convert_value(value):
    """Safely convert Excel values to appropriate Python types"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value) if value != int(value) else int(value)
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.upper() in ['N/A', 'NA', '#N/A', '#VALUE!', '#REF!']:
            return None
        # Try to convert to number if it looks like one
        try:
            if '.' in value or 'e' in value.lower():
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
    return str(value) if value is not None else None

def get_cell_value(df, row, col):
    """Safely get cell value from DataFrame"""
    try:
        if row < len(df) and col < len(df.columns):
            return safe_convert_value(df.iloc[row, col])
    except:
        pass
    return None

def extract_deal_data_improved(worksheet, deal_name):
    """Extract deal data using improved location-based approach"""
    try:
        deal_data = {
            "deal_name": deal_name,
            "basic_info": {},
            "financial_data": {},
            "collateral_info": {},
            "structure_info": {},
            "extracted_at": datetime.now().isoformat()
        }
        
        # Convert worksheet to DataFrame
        df = pd.DataFrame(worksheet.values)
        
        # Key data locations based on analysis (these appear consistent across MAG sheets)
        
        # Basic info from specific locations
        analysis_date = get_cell_value(df, 2, 2)  # Row 2, Col 2: Analysis date
        if analysis_date:
            deal_data["basic_info"]["analysis_date"] = str(analysis_date)
        
        next_payment_date = get_cell_value(df, 3, 2)  # Row 3, Col 2: Next payment date
        if next_payment_date:
            deal_data["basic_info"]["next_payment_date"] = str(next_payment_date)
        
        beg_collection = get_cell_value(df, 4, 2)  # Row 4, Col 2: Beginning collection
        if beg_collection:
            deal_data["basic_info"]["beginning_collection"] = str(beg_collection)
        
        end_collection = get_cell_value(df, 5, 2)  # Row 5, Col 2: End collection
        if end_collection:
            deal_data["basic_info"]["end_collection"] = str(end_collection)
        
        last_payment_date = get_cell_value(df, 6, 2)  # Row 6, Col 2: Last payment date
        if last_payment_date:
            deal_data["basic_info"]["last_payment_date"] = str(last_payment_date)
            
        # Look for closing date and stated maturity in the worksheet
        closing_date = None
        stated_maturity = None
        
        # Search for specific patterns in the data
        for idx, row in df.iterrows():
            for col_idx, cell in enumerate(row):
                if pd.isna(cell):
                    continue
                    
                cell_str = str(cell).lower().strip()
                
                # Look for closing date
                if 'closing date' in cell_str and col_idx + 1 < len(row):
                    closing_date = get_cell_value(df, idx, col_idx + 1)
                    if closing_date:
                        deal_data["basic_info"]["closing_date"] = str(closing_date)
                
                # Look for stated maturity
                elif 'stated maturity' in cell_str and col_idx + 1 < len(row):
                    stated_maturity = get_cell_value(df, idx, col_idx + 1)
                    if stated_maturity:
                        deal_data["basic_info"]["stated_maturity"] = str(stated_maturity)
                
                # Financial data from specific locations
                elif 'reinvestment target balance' in cell_str and col_idx + 1 < len(row):
                    reinvest_balance = get_cell_value(df, idx, col_idx + 1)
                    if reinvest_balance:
                        deal_data["financial_data"]["reinvestment_target_balance"] = reinvest_balance
                
                elif 'jr oc denominator' in cell_str and col_idx + 1 < len(row):
                    jr_oc_denom = get_cell_value(df, idx, col_idx + 1)
                    if jr_oc_denom:
                        deal_data["financial_data"]["jr_oc_denominator"] = jr_oc_denom
                
                elif 'warf threshold' in cell_str and col_idx + 1 < len(row):
                    warf_threshold = get_cell_value(df, idx, col_idx + 1)
                    if warf_threshold:
                        deal_data["financial_data"]["warf_threshold"] = warf_threshold
                
                elif 'weighted average spread' in cell_str and col_idx + 1 < len(row):
                    was = get_cell_value(df, idx, col_idx + 1)
                    if was:
                        deal_data["financial_data"]["weighted_average_spread"] = was
                        
                elif 'warf factor' in cell_str and col_idx + 1 < len(row):
                    warf_factor = get_cell_value(df, idx, col_idx + 1)
                    if warf_factor:
                        deal_data["financial_data"]["warf_factor"] = warf_factor
        
        # Extract collateral data by examining the Deal Collateral section
        # Look for total par amount of assets
        total_par = 0
        asset_count = 0
        
        # Start from row 3 and look for BLKRockID and Par Amount columns
        for idx in range(3, min(200, len(df))):  # Look at first 200 rows
            blk_id = get_cell_value(df, idx, 3)  # BLKRockID column
            par_amount = get_cell_value(df, idx, 4)  # Par Amount column
            
            if blk_id and par_amount and isinstance(par_amount, (int, float)) and par_amount > 0:
                total_par += par_amount
                asset_count += 1
        
        if total_par > 0:
            deal_data["collateral_info"]["total_collateral_balance"] = total_par
            deal_data["collateral_info"]["number_of_assets"] = asset_count
            deal_data["collateral_info"]["average_asset_size"] = total_par / asset_count if asset_count > 0 else 0
        
        # Financial calculations
        if "jr_oc_denominator" in deal_data["financial_data"]:
            deal_data["financial_data"]["total_deal_size"] = deal_data["financial_data"]["jr_oc_denominator"]
        
        # Determine deal status (Revolving vs Amortizing)
        # This is complex logic, but for MAG deals, we can infer from dates
        if analysis_date and stated_maturity:
            try:
                analysis_dt = pd.to_datetime(analysis_date)
                maturity_dt = pd.to_datetime(stated_maturity)
                days_to_maturity = (maturity_dt - analysis_dt).days
                
                deal_data["basic_info"]["days_to_maturity"] = days_to_maturity
                
                # Generally, if more than 2 years to maturity, likely revolving
                if days_to_maturity > 730:  # 2 years
                    deal_data["basic_info"]["deal_status"] = "Revolving"
                else:
                    deal_data["basic_info"]["deal_status"] = "Amortizing"
            except:
                deal_data["basic_info"]["deal_status"] = "Unknown"
        
        # Set issue date from closing date if available
        if "closing_date" in deal_data["basic_info"]:
            deal_data["basic_info"]["issue_date"] = deal_data["basic_info"]["closing_date"]
        
        # Set maturity date from stated maturity if available
        if "stated_maturity" in deal_data["basic_info"]:
            deal_data["basic_info"]["maturity_date"] = deal_data["basic_info"]["stated_maturity"]
        
        return deal_data
        
    except Exception as e:
        print(f"Error extracting data for {deal_name}: {str(e)}")
        return {
            "deal_name": deal_name,
            "error": str(e),
            "extracted_at": datetime.now().isoformat()
        }

def main():
    excel_file = "TradeHypoPrelimv32.xlsm"
    
    if not os.path.exists(excel_file):
        print(f"Error: Excel file {excel_file} not found")
        sys.exit(1)
    
    print(f"Reading Excel file: {excel_file}")
    print("This may take a moment due to file size...")
    
    try:
        # Read the Excel file
        xl_file = pd.ExcelFile(excel_file)
        print(f"Found {len(xl_file.sheet_names)} worksheets")
        
        # MAG deals to extract
        mag_deals = [6, 7, 8, 9, 11, 12, 14, 15, 16, 17]
        
        # Find Input worksheets for each MAG deal
        mag_worksheets = {}
        for sheet_name in xl_file.sheet_names:
            sheet_lower = sheet_name.lower()
            for mag_num in mag_deals:
                if f"mag {mag_num} inputs" in sheet_lower:
                    mag_worksheets[f"MAG{mag_num}"] = sheet_name
                    break
        
        print(f"\nFound MAG Input worksheets: {list(mag_worksheets.keys())}")
        
        extracted_deals = []
        
        for deal_name, sheet_name in mag_worksheets.items():
            print(f"\nExtracting data from {sheet_name} for {deal_name}...")
            try:
                worksheet = xl_file.parse(sheet_name, header=None)
                deal_data = extract_deal_data_improved(worksheet, deal_name)
                extracted_deals.append(deal_data)
                print(f"Successfully extracted data for {deal_name}")
            except Exception as e:
                print(f"Error reading {sheet_name}: {str(e)}")
                extracted_deals.append({
                    "deal_name": deal_name,
                    "error": str(e),
                    "extracted_at": datetime.now().isoformat()
                })
        
        # Save results
        output_file = "mag_deals_improved_extracted.json"
        with open(output_file, 'w') as f:
            json.dump(extracted_deals, f, indent=2, default=str)
        
        print(f"\nExtraction complete! Data saved to {output_file}")
        print(f"Total deals extracted: {len(extracted_deals)}")
        
        # Print detailed summary
        print("\n" + "="*80)
        print("DETAILED EXTRACTION SUMMARY")
        print("="*80)
        
        for deal in extracted_deals:
            print(f"\n{deal['deal_name']}:")
            if 'error' in deal:
                print(f"  ERROR: {deal['error']}")
            else:
                basic_info = deal.get('basic_info', {})
                financial_data = deal.get('financial_data', {})
                collateral_info = deal.get('collateral_info', {})
                
                print(f"  Deal Status: {basic_info.get('deal_status', 'N/A')}")
                print(f"  Issue Date: {basic_info.get('issue_date', basic_info.get('closing_date', 'N/A'))}")
                print(f"  Maturity Date: {basic_info.get('maturity_date', basic_info.get('stated_maturity', 'N/A'))}")
                print(f"  Days to Maturity: {basic_info.get('days_to_maturity', 'N/A')}")
                print(f"  Analysis Date: {basic_info.get('analysis_date', 'N/A')}")
                print(f"  Total Deal Size: {financial_data.get('total_deal_size', financial_data.get('jr_oc_denominator', 'N/A'))}")
                print(f"  Reinvestment Target: {financial_data.get('reinvestment_target_balance', 'N/A')}")
                print(f"  WARF Threshold: {financial_data.get('warf_threshold', 'N/A')}")
                print(f"  WARF Factor: {financial_data.get('warf_factor', 'N/A')}")
                print(f"  Weighted Avg Spread: {financial_data.get('weighted_average_spread', 'N/A')}")
                print(f"  Number of Assets: {collateral_info.get('number_of_assets', 'N/A')}")
                print(f"  Total Collateral: ${collateral_info.get('total_collateral_balance', 'N/A'):,.2f}" if collateral_info.get('total_collateral_balance') else "  Total Collateral: N/A")
                print(f"  Avg Asset Size: ${collateral_info.get('average_asset_size', 'N/A'):,.2f}" if collateral_info.get('average_asset_size') else "  Avg Asset Size: N/A")
        
        # Create database-ready format
        db_format = []
        for deal in extracted_deals:
            if 'error' not in deal:
                basic_info = deal.get('basic_info', {})
                financial_data = deal.get('financial_data', {})
                collateral_info = deal.get('collateral_info', {})
                
                db_record = {
                    "deal_id": deal["deal_name"],
                    "deal_name": f"Magnetar {deal['deal_name']} CLO",
                    "manager": "Magnetar Capital",
                    "issue_date": basic_info.get('issue_date', basic_info.get('closing_date')),
                    "maturity_date": basic_info.get('maturity_date', basic_info.get('stated_maturity')),
                    "deal_size": financial_data.get('total_deal_size', financial_data.get('jr_oc_denominator')),
                    "deal_status": basic_info.get('deal_status', 'Unknown'),
                    "num_assets": collateral_info.get('number_of_assets'),
                    "total_collateral": collateral_info.get('total_collateral_balance'),
                    "avg_asset_size": collateral_info.get('average_asset_size'),
                    "warf_threshold": financial_data.get('warf_threshold'),
                    "weighted_avg_spread": financial_data.get('weighted_average_spread'),
                    "analysis_date": basic_info.get('analysis_date'),
                    "days_to_maturity": basic_info.get('days_to_maturity')
                }
                db_format.append(db_record)
        
        # Save database format
        db_output_file = "mag_deals_database_format.json"
        with open(db_output_file, 'w') as f:
            json.dump(db_format, f, indent=2, default=str)
        
        print(f"\nDatabase-ready format saved to {db_output_file}")
        
        return extracted_deals
        
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()